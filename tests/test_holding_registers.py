from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("127.0.0.1", port=5020)

assert client.connect(), "Could not connect to Modbus server"

try:
    for device_id in range(1, 4):
        result = client.read_holding_registers(
            address=0,
            count=1,
            device_id=device_id
        )

        assert not result.isError(), (
            f"Modbus error for device {device_id}: {result}"
        )

        power_limit = result.registers[0]

        assert 0 <= power_limit <= 2000

        print(
            f"WT-0{device_id} | "
            f"Power Limit: {power_limit} kW"
        )

    print("CP2.4.2 READ TEST PASSED")

finally:
    client.close()