import random
from turbine import WindTurbine


class WindFarm:
    def __init__(self):
        self.turbines = [
            WindTurbine("WT-01"),
            WindTurbine("WT-02"),
            WindTurbine("WT-03")
        ]

    def update(self):
        results = []

        # random wind speed generated
        base_wind_speed = random.uniform(4.0, 16.0) 

        for turbine in self.turbines:
            local_wind_speed = max(
                0.0,
                base_wind_speed + random.uniform(-1.0, 1.0)
            )

            data = turbine.update(local_wind_speed)
            results.append(data)

        return results


if __name__ == "__main__":
    farm = WindFarm()

    for reading in farm.update():
        print(
            f"{reading['turbine_id']} | "
            f"Wind: {reading['wind_speed_ms']:.1f} m/s | "
            f"Power: {reading['power_kw']:.1f} kW | "
            f"Status: {reading['status']}"
        )