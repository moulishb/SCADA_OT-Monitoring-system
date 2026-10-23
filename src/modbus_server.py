import threading
import time

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import StartTcpServer

from wind_farm import WindFarm


# One wind farm, three turbine objects
farm = WindFarm()



# Store each turbine's Modbus device context
devices = {}

for device_id in range(1, 4):
    devices[device_id] = ModbusDeviceContext(
        ir=ModbusSequentialDataBlock(1, [0] * 10),
        hr=ModbusSequentialDataBlock(1,[2000] * 10)
    )

context = ModbusServerContext(
    devices=devices,
    single=False
)


def update_registers():
    """Periodically update Modbus input registers."""

    while True:
        readings = farm.update()

        for device_id, turbine in enumerate(readings, start=1):

            registers = [
                int(turbine["wind_speed_ms"] * 10),
                int(turbine["rotor_rpm"] * 10),
                int(turbine["power_kw"]),
                int(turbine["gearbox_temp_c"] * 10),
                1 if turbine["status"] == "Running" else 0,
            ]

            turbine_object = farm.turbines[device_id - 1]
            # Function code 4 = input registers
            context[device_id].setValues(
                3, 0, [int(turbine_object.power_limit_kw)]
            )

            print(
                f"{turbine['turbine_id']} | "
                f"Wind: {turbine['wind_speed_ms']:.1f} m/s | "
                f"Power: {turbine['power_kw']:.1f} kW"
            )

        print("-" * 50)
        time.sleep(3)


if __name__ == "__main__":

    print("Starting Wind Farm Modbus/TCP Server...")

    # Run simulated telemetry updates in background
    updater = threading.Thread(
        target=update_registers,
        daemon=True
    )
    updater.start()

    # Bind locally; not accessible from other machines
    StartTcpServer(
        context=context,
        address=("127.0.0.1", 5020)
    )