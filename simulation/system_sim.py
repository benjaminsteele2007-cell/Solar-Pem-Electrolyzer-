# system_sim.py
# Top-level executive simulation that connects solar, battery, and electrolyzer models. 
# Steps through time, logs results, and outputs a full data set for plotting. 

import math
from config import OPERATING_TEMP, AMBIENT_TEMP
from solar_model import panel_power, panel_voltage
from battery import BatteryModel
from electrolyzer_model import cell_voltage
from faraday import calculate_liters_h2

# Simulation parameters 
TIMESTEP_MINUTES = 10
TIMESTEP_HOURS = TIMESTEP_MINUTES / 60
SIMULATION_HOURS = 12       # Simulate a 12 hr daylight window
TOTAL_STEPS =  int(SIMULATION_HOURS * 60 / TIMESTEP_MINUTES)

def solar_profile(hour):
    """
    Models irradiance across a day using simple sine curve. 
    Peaks at noon ( hour 6 of 12) at 1000 W/m^2
    hour    : hour into simulated day (0 to 12)
    returns : irradiance in W/m^2 
    """
    if hour < 0 or hour > SIMULATION_HOURS:
        return 0
    irradiance = 1000 * math.sin(math.pi * hour / SIMULATION_HOURS)
    return max(0, irradiance)

def temperature_profile(hour):
    """
    Models panel temperature across the day. 
    Cool in morning, hot at peak sun. 
    returns : panel temperature in Celsius (C)
    """
    base_temp= 20
    peak_gain=25
    temp = base_temp + peak_gain * math.sin(math.pi * hour / SIMULATION_HOURS)
    return temp

# ── DEFAULT SCENARIO ─────────────────────────────────────────────────
DEFAULT_SCENARIO = {
    "target_current"      : 1.0,     # Operating current (A)
    "initial_soc"         : 0.8,     # Starting battery SOC (fraction)
    "simulation_hours"    : 12,      # Daylight window length (hr)
    "timestep_minutes"    : 10,      # Resolution (min)
    "peak_irradiance"     : 1000,    # Noon irradiance (W/m²)
    "peak_temperature"    : 45,      # Hottest panel temp (°C)
    "ambient_temperature" : 20,      # Dawn panel temp (°C)
}


def solar_profile(hour, scenario):
    """
    Models irradiance using a sine curve across the scenario's daylight window.
    """
    total_hours = scenario["simulation_hours"]
    peak = scenario["peak_irradiance"]

    if hour < 0 or hour > total_hours:
        return 0
    irradiance = peak * math.sin(math.pi * hour / total_hours)
    return max(0, irradiance)


def temperature_profile(hour, scenario):
    """
    Models panel temperature using a sine curve.
    Morning cool, peak hot, evening cool again.
    """
    total_hours = scenario["simulation_hours"]
    base = scenario["ambient_temperature"]
    peak_gain = scenario["peak_temperature"] - base

    temp = base + peak_gain * math.sin(math.pi * hour / total_hours)
    return temp


def run_simulation(scenario=None):
    """
    Runs the full system simulation for a given scenario.

    scenario : dictionary of scenario parameters (uses DEFAULT_SCENARIO if None)
    returns  : list of dicts — one per timestep — with all recorded data
    """
    if scenario is None:
        scenario = DEFAULT_SCENARIO

    timestep_hours = scenario["timestep_minutes"] / 60
    total_steps = int(scenario["simulation_hours"] * 60 / scenario["timestep_minutes"])

    battery = BatteryModel(initial_soc=scenario["initial_soc"])
    target_current = scenario["target_current"]
    results = []

    for step in range(total_steps):
        current_hour = step * timestep_hours

        irradiance = solar_profile(current_hour, scenario)
        panel_temp = temperature_profile(current_hour, scenario)

        solar_power = panel_power(irradiance, panel_temp)

        voltage_breakdown = cell_voltage(target_current)
        cell_power_demand = voltage_breakdown["total"] * target_current

        delivered_power = battery.update(solar_power, cell_power_demand, timestep_hours)

        if voltage_breakdown["total"] > 0:
            delivered_current = delivered_power / voltage_breakdown["total"]
        else:
            delivered_current = 0

        h2_liters = calculate_liters_h2(delivered_current, timestep_hours * 3600)

        results.append({
            "hour"             : current_hour,
            "irradiance"       : irradiance,
            "panel_temp"       : panel_temp,
            "solar_power"      : solar_power,
            "cell_voltage"     : voltage_breakdown["total"],
            "cell_demand"      : cell_power_demand,
            "delivered_power"  : delivered_power,
            "delivered_current": delivered_current,
            "battery_soc"      : battery.soc,
            "battery_status"   : battery.status,
            "h2_liters"        : h2_liters
        })

    return results


def run_vi_sweep(current_min=0.1, current_max=3.0, step=0.1):
    """
    Runs a V-I sweep across a range of currents.
    Returns the predicted operating voltage and overpotential breakdown
    at each current — the core deliverable of the simulation.

    current_min : starting current (A)
    current_max : ending current (A)
    step        : current increment (A)
    returns     : list of dicts — one per current value
    """
    results = []
    current = current_min

    while current <= current_max:
        v = cell_voltage(current)
        results.append({
            "current"       : round(current, 4),
            "reversible"    : v["reversible"],
            "activation"    : v["activation"],
            "ohmic"         : v["ohmic"],
            "concentration" : v["concentration"],
            "total"         : v["total"]
        })
        current += step

    return results


# ── SCENARIO LIBRARY ─────────────────────────────────────────────────
# Pre-defined scenarios for quick testing and report generation.
SCENARIOS = {
    "clear_summer_day": {
        "target_current"      : 1.0,
        "initial_soc"         : 0.8,
        "simulation_hours"    : 12,
        "timestep_minutes"    : 10,
        "peak_irradiance"     : 1000,
        "peak_temperature"    : 50,
        "ambient_temperature" : 22,
    },
    "cloudy_day": {
        "target_current"      : 1.0,
        "initial_soc"         : 0.8,
        "simulation_hours"    : 12,
        "timestep_minutes"    : 10,
        "peak_irradiance"     : 400,
        "peak_temperature"    : 28,
        "ambient_temperature" : 18,
    },
    "short_test": {
        "target_current"      : 1.0,
        "initial_soc"         : 0.8,
        "simulation_hours"    : 2,
        "timestep_minutes"    : 5,
        "peak_irradiance"     : 800,
        "peak_temperature"    : 35,
        "ambient_temperature" : 20,
    },
}


if __name__ == "__main__":
    # Run the default scenario
    print("=== Running default scenario ===\n")
    data = run_simulation(SCENARIOS["clear_summer_day"])

    print(f"{'Hour':<8} {'Irr (W/m²)':<12} {'Solar (W)':<12} {'Delivered (W)':<15} {'SOC':<8} {'H2 (L)':<10}")
    print("-" * 70)
    for row in data[::6]:
        print(f"{row['hour']:<8.2f} {row['irradiance']:<12.1f} {row['solar_power']:<12.4f} "
              f"{row['delivered_power']:<15.4f} {row['battery_soc']:<8.1%} {row['h2_liters']:<10.6f}")

    total_h2 = sum(row["h2_liters"] for row in data)
    print(f"\nTotal hydrogen: {total_h2:.4f} L")

    # Run the V-I sweep
    print("\n=== Running V-I sweep ===\n")
    sweep = run_vi_sweep(0.1, 3.0, 0.2)
    print(f"{'Current (A)':<12} {'V_act':<10} {'V_ohm':<10} {'V_total':<10}")
    print("-" * 45)
    for row in sweep:
        print(f"{row['current']:<12.2f} {row['activation']:<10.4f} {row['ohmic']:<10.4f} {row['total']:<10.4f}")