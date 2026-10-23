from dataclasses import dataclass

@dataclass
class WindTurbine:
    turbine_id: str
    rated_power_kw: float = 2000.0
    power_limit_kw: float = 2000.0

    def update(self, wind_speed: float) -> dict:
        cut_in = 3.0
        rated = 12.0
        cut_out = 25.0

        if wind_speed < cut_in or wind_speed >= cut_out:
            power = 0.0
            status = "Stopped"
        else:
            fraction = min(
                (wind_speed**3 - cut_in**3)
                / (rated**3 - cut_in**3),
                1.0
            )
            power = min(
                fraction * self.rated_power_kw,
                self.power_limit_kw
            )
            status = "Running"

        rotor_rpm = (
            min(wind_speed * 1.2, 15.0)
            if status == "Running" else 0.0
        )

        gearbox_temp = 25.0 + (power / 100.0) * 1.2

        return {
            "turbine_id": self.turbine_id,
            "wind_speed_ms": wind_speed,
            "rotor_rpm": round(rotor_rpm, 1),
            "power_kw": round(power, 1),
            "gearbox_temp_c": round(gearbox_temp, 1),
            "status": status
        }


if __name__ == "__main__":
    turbine = WindTurbine("WT-01")

    for speed in [2.0, 5.0, 8.0, 12.0, 18.0, 26.0]:
        print(turbine.update(speed))