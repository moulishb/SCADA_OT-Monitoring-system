import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "src")
)

from turbine import WindTurbine


turbine = WindTurbine("WT-02")

# At rated wind speed, initially generate 2000 kW
before = turbine.update(12.0)
assert before["power_kw"] == 2000

# Reduce the power limit
result = turbine.set_power_limit(1000)
assert result["result"] == "UPDATED"

after = turbine.update(12.0)
assert after["power_kw"] == 1000

print("Before:", before["power_kw"], "kW")
print("After:", after["power_kw"], "kW")

# Verify invalid commands are rejected
for invalid_limit in [-100, 2500, float("nan")]:
    try:
        turbine.set_power_limit(invalid_limit)
        raise AssertionError("Invalid limit was accepted!")
    except ValueError:
        print(f"Correctly rejected: {invalid_limit}")

assert turbine.power_limit_kw == 1000

print("CP2.4.1 PASSED")