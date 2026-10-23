import time
from datetime import datetime

from pymodbus.client import ModbusTcpClient


HOST = "127.0.0.1"
PORT = 5020

TURBINES = {
    1: "WT-01",
    2: "WT-02",
    3: "WT-03",
}


def read_turbine(client, device_id, turbine_name):
    """Read telemetry using Modbus function code 04."""

    response = client.read_input_registers(
        address=0,
        count=5,
        device_id=device_id
    )

    if response.isError():
        print(f"{turbine_name}: Modbus error: {response}")
        return None

    registers = response.registers

    return {
        "turbine_id": turbine_name,
        "wind_speed_ms": registers[0] / 10,
        "rotor_rpm": registers[1] / 10,
        "power_kw": registers[2],
        "gearbox_temp_c": registers[3] / 10,
        "status": "Running" if registers[4] == 1 else "Stopped",
    }


def main():
    client = ModbusTcpClient(
        host=HOST,
        port=PORT,
        timeout=3
    )

    if not client.connect():
        print("Failed to connect to Modbus server.")
        return

    print("Connected to Wind Farm Modbus Server.")

    try:
        while True:
            print(
                f"\nSCADA MONITOR | "
                f"{datetime.now():%Y-%m-%d %H:%M:%S}"
            )
            print("-" * 75)

            total_power = 0

            for device_id, turbine_name in TURBINES.items():
                try:
                    data = read_turbine(
                        client, device_id, turbine_name
                    )

                    if data is None:
                        continue

                    total_power += data["power_kw"]

                    print(
                        f"{data['turbine_id']} | "
                        f"Wind: {data['wind_speed_ms']:5.1f} m/s | "
                        f"Power: {data['power_kw']:4d} kW | "
                        f"Temp: {data['gearbox_temp_c']:5.1f} C | "
                        f"Status: {data['status']}"
                    )

                except Exception as error:
                    print(f"{turbine_name}: {error}")

            print("-" * 75)
            print(f"Total Wind Farm Power: {total_power} kW")

            time.sleep(3)

    except KeyboardInterrupt:
        print("\nSCADA monitoring stopped.")

    finally:
        client.close()


if __name__ == "__main__":
    main()