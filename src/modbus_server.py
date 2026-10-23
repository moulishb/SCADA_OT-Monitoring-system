import hmac
import json
import math
import os
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from security_logger import log_security_event

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import StartTcpServer

from wind_farm import WindFarm


HOST = "127.0.0.1"
MODBUS_PORT = 5020
COMMAND_PORT = 8081

# Lab-only token supplied using an environment variable.
OPERATOR_TOKEN = os.environ.get("OT_OPERATOR_TOKEN")
if not OPERATOR_TOKEN:
    raise RuntimeError("Set OT_OPERATOR_TOKEN before starting")

farm = WindFarm()
farm_lock = threading.RLock()

LOG_FILE = Path(__file__).resolve().parents[1] / "logs" / "ot_events.jsonl"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


class PublishedHoldingBlock(ModbusSequentialDataBlock):
    """External Modbus clients cannot modify published setpoints."""

    def setValues(self, address, values):
        raise ValueError("Direct Modbus writes are disabled")

    def publish(self, address, values):
        super().setValues(address, values)


devices = {}
holding_blocks = {}

for device_id in range(1, 4):
    holding_block = PublishedHoldingBlock(1, [2000] * 10)
    holding_blocks[device_id] = holding_block

    devices[device_id] = ModbusDeviceContext(
        ir=ModbusSequentialDataBlock(1, [0] * 10),
        hr=holding_block,
    )

context = ModbusServerContext(
    devices=devices,
    single=False,
)


def audit(event):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def update_registers():
    while True:
        with farm_lock:
            readings = farm.update()

            for device_id, reading in enumerate(readings, start=1):
                turbine = farm.turbines[device_id - 1]

                registers = [
                    int(reading["wind_speed_ms"] * 10),
                    int(reading["rotor_rpm"] * 10),
                    int(reading["power_kw"]),
                    int(reading["gearbox_temp_c"] * 10),
                    1 if reading["status"] == "Running" else 0,
                ]

                context[device_id].setValues(
                    4, 0, registers
                )

                holding_blocks[device_id].publish(
                    1, [int(turbine.power_limit_kw)]
                )

                print(
                    f"{reading['turbine_id']} | "
                    f"Power: {reading['power_kw']} kW | "
                    f"Limit: {turbine.power_limit_kw} kW"
                )

        time.sleep(3)


class CommandHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path != "/command":
            self.send_json(404, {"error": "Not found"})
            return

        turbine_id = None
        requested_limit = None
        actor = None
        old_limit = None
        new_limit = None

        result = "REJECTED"
        reason_code = "MALFORMED_REQUEST"
        status = 400
        response = {"error": "Invalid request"}

        try:
            length = int(
                self.headers.get("Content-Length", "0")
            )

            if not 0 < length <= 4096:
                raise ValueError("Invalid request size")

            command = json.loads(
                self.rfile.read(length).decode("utf-8")
            )

            if not isinstance(command, dict):
                raise ValueError("Expected JSON object")

            turbine_id = command.get("turbine_id")
            requested_limit = command.get("power_limit_kw")

            token = self.headers.get(
                "X-Operator-Token", ""
            )

            if not hmac.compare_digest(
                token, OPERATOR_TOKEN
            ):
                reason_code = "AUTH_FAILED"
                raise PermissionError(
                    "Invalid operator token"
                )

            actor = "lab_operator"

            if turbine_id not in (
                "WT-01", "WT-02", "WT-03"
            ):
                reason_code = "INVALID_TURBINE"
                raise ValueError("Unknown turbine")

            if (
                type(requested_limit) not in (int, float)
                or not math.isfinite(requested_limit)
                or not 0 <= requested_limit <= 2000
            ):
                reason_code = "INVALID_SETPOINT"
                raise ValueError(
                    "Invalid power limit"
                )

            device_id = int(turbine_id.split("-")[1])

            with farm_lock:
                turbine = farm.turbines[device_id - 1]

                change = turbine.set_power_limit(
                    requested_limit
                )

                old_limit = change["old_limit_kw"]
                new_limit = change["new_limit_kw"]

                holding_blocks[device_id].publish(
                    1, [int(new_limit)]
                )

            result = "ACCEPTED"
            reason_code = "COMMAND_APPLIED"
            status = 200
            response = change

        except PermissionError as error:
            status = 403
            response = {"error": str(error)}

        except (ValueError, UnicodeDecodeError) as error:
            status = 400
            response = {"error": str(error)}

        finally:
            # Use only JSON-safe values in the audit event.
            safe_turbine_id = (
                turbine_id
                if isinstance(turbine_id, str)
                else None
            )

            safe_limit = (
                requested_limit
                if type(requested_limit) in (int, float)
                and math.isfinite(requested_limit)
                else None
            )

            log_security_event(
                result=result,
                reason_code=reason_code,
                source_ip=self.client_address[0],
                turbine_id=safe_turbine_id,
                requested_limit_kw=safe_limit,
                actor=actor,
                old_limit_kw=old_limit,
                new_limit_kw=new_limit,
            )

        self.send_json(status, response)

    def send_json(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        pass


def start_command_gateway():
    server = ThreadingHTTPServer(
        (HOST, COMMAND_PORT),
        CommandHandler
    )
    print(f"Command gateway listening on {HOST}:{COMMAND_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    threading.Thread(
        target=update_registers,
        daemon=True
    ).start()

    threading.Thread(
        target=start_command_gateway,
        daemon=True
    ).start()

    print(f"Modbus server listening on {HOST}:{MODBUS_PORT}")

    StartTcpServer(
        context=context,
        address=(HOST, MODBUS_PORT)
    )