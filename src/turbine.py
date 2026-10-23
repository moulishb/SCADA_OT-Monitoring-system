from dataclasses import dataclass

@dataclass
class WindTurbine:
    turbine_id: str
    rated_power_kw: float = 2000.0
    power_limit_kw: float = 2000.0
    
    def set_power_limit(self, new_limit_kw: float) -> dict:
        """Validate and update this turbine's power limit."""

        if not isinstance(new_limit_kw, (int, float)):
            raise ValueError("Power limit must be numeric")

        import math
        if not math.isfinite(new_limit_kw):
            raise ValueError("Power limit must be finite")

        if not 0 <= new_limit_kw <= self.rated_power_kw:
            raise ValueError(
                f"Power limit must be between "
                f"0 and {self.rated_power_kw} kW"
            )

        old_limit = self.power_limit_kw
        self.power_limit_kw = float(new_limit_kw)

        return {
            "turbine_id": self.turbine_id,
            "old_limit_kw": old_limit,
            "new_limit_kw": self.power_limit_kw,
            "result": "UPDATED"
        }

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