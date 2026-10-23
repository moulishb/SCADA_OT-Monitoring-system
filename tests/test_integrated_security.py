import json
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pymodbus.client import ModbusTcpClient


GATEWAY_URL = "http://127.0.0.1:8081/command"
OPERATOR_TOKEN = "wind-lab-operator-2026"
LOG_FILE = (
    Path(__file__).resolve().parents[1]
    / "logs"
    / "ot_events.jsonl"
)


def send_command(token, limit):
    payload = json.dumps({
        "turbine_id": "WT-02",
        "power_limit_kw": limit,
    }).encode("utf-8")

    request = Request(
        GATEWAY_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Operator-Token": token,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.loads(
            error.read().decode("utf-8")
        )


def read_modbus(client, function, address):
    if function == "holding":
        response = client.read_holding_registers(
            address=address,
            count=1,
            device_id=2,
        )
    else:
        response = client.read_input_registers(
            address=address,
            count=1,
            device_id=2,
        )

    assert not response.isError(), str(response)
    return response.registers[0]


def read_events():
    if not LOG_FILE.exists():
        return []
    return [
        json.loads(line)
        for line in LOG_FILE.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


def run_scenario(client, name, token, requested,
                 expected_http, expected_limit,
                 expected_reason):

    status, body = send_command(token, requested)

    assert status == expected_http, (
        f"{name}: expected HTTP {expected_http}, got {status}"
    )

    # The gateway publishes accepted changes immediately.
    actual_limit = read_modbus(client, "holding", 0)
    assert actual_limit == expected_limit, (
        f"{name}: expected {expected_limit} kW, "
        f"got {actual_limit} kW"
    )

    events = read_events()
    event = events[-1]

    assert event["event_type"] == "OT_COMMAND"
    assert event["reason_code"] == expected_reason
    assert event["turbine_id"] == "WT-02"

    expected_result = (
        "ACCEPTED" if expected_http == 200
        else "REJECTED"
    )
    assert event["result"] == expected_result

    print(
        f"PASS | {name} | "
        f"HTTP {status} | "
        f"Limit {actual_limit} kW | "
        f"{expected_reason}"
    )


def main():
    client = ModbusTcpClient(
        "127.0.0.1", port=5020, timeout=3
    )

    assert client.connect(), "Modbus connection failed"

    try:
        print("\nWIND FARM INTEGRATED SECURITY TEST")
        print("=" * 65)

        run_scenario(
            client,
            "Authorised power reduction",
            OPERATOR_TOKEN,
            1000, 200, 1000, "COMMAND_APPLIED"
        )

        run_scenario(
            client,
            "Invalid operator token",
            "invalid-token",
            1500, 403, 1000, "AUTH_FAILED"
        )

        run_scenario(
            client,
            "Invalid power limit",
            OPERATOR_TOKEN,
            3000, 400, 1000, "INVALID_SETPOINT"
        )

        # Wait for the simulator to refresh telemetry.
        time.sleep(4)

        power = read_modbus(client, "input", 2)
        assert power <= 1000, (
            f"WT-02 generated {power} kW above its limit"
        )
        print(
            f"PASS | Actual turbine power: {power} kW"
        )

        run_scenario(
            client,
            "Authorised power restoration",
            OPERATOR_TOKEN,
            2000, 200, 2000, "COMMAND_APPLIED"
        )

        print("=" * 65)
        print("CP2.4.5 ALL INTEGRATION TESTS PASSED")

    finally:
        # Attempt to restore default power limit
        # even if one of the assertions fails.
        try:
            send_command(OPERATOR_TOKEN, 2000)
        except Exception as error:
            print("Cleanup warning:", error)
        client.close()


if __name__ == "__main__":
    main()