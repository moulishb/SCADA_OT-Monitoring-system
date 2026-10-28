import time
from pymodbus.client import ModbusTcpClient

HOST = "127.0.0.1"
PORT = 5020
DEVICE_ID = 2
REGISTER = 0

client = ModbusTcpClient(HOST, port=PORT, timeout=3)


def read_limit():
    response = client.read_holding_registers(
        address=REGISTER,
        count=1,
        device_id=DEVICE_ID
    )
    assert not response.isError(), str(response)
    return response.registers[0]


try:
    assert client.connect(), "Cannot connect to server"

    before = read_limit()
    print(f"WT-02 limit BEFORE: {before} kW")

    # Attempt to bypass the HTTP command gateway.
    attempted_limit = 1500 if before != 1500 else 1000

    try:
        response = client.write_register(
            address=REGISTER,
            value=attempted_limit,
            device_id=DEVICE_ID
        )
        print(f"Direct write response: {response}")

        if response.isError():
            print("Server returned a Modbus exception.")

    except Exception as error:
        print(f"Direct write raised: {type(error).__name__}: {error}")

    # Reconnect to inspect the actual register state.
    client.close()
    time.sleep(0.5)

    assert client.connect(), "Cannot reconnect after write attempt"

    immediate = read_limit()
    time.sleep(4)
    later = read_limit()

    print(f"WT-02 immediately after: {immediate} kW")
    print(f"WT-02 after refresh:    {later} kW")

    assert immediate == before, (
        "SECURITY FAILURE: Direct write changed the register!"
    )

    assert later == before, (
        "SECURITY FAILURE: Register state changed after refresh!"
    )

    print("PASS: Direct Modbus write did not change the setpoint.")

finally:
    client.close()