# system_sim.py
# Top-level executive simulation that connects solar, battery, and electrolyzer models. 
# Steps through time, logs results, and outputs a full data set for plotting. 

import math
import os
import random
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
    Models irradiance using a sine curve with realistic outdoor variability.

    Two noise layers are always applied:
      - Cloud events: 12% chance per timestep of a 30-70% irradiance drop
      - Atmospheric scatter: ±5% multiplicative noise every timestep
    """
    total_hours = scenario["simulation_hours"]
    peak = scenario["peak_irradiance"]

    if hour < 0 or hour > total_hours:
        return 0

    base_irradiance = peak * math.sin(math.pi * hour / total_hours)

    cloud_factor = 1.0
    if random.random() < 0.12:
        cloud_factor = random.uniform(0.30, 0.70)

    noise = random.uniform(0.95, 1.05)

    return max(0, base_irradiance * cloud_factor * noise)


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
    "chaotic_clear_day": {
        "target_current"      : 1.0,
        "initial_soc"         : 0.8,
        "simulation_hours"    : 12,
        "timestep_minutes"    : 10,
        "peak_irradiance"     : 1000,
        "peak_temperature"    : 50,
        "ambient_temperature" : 22,
        "chaotic"             : True,   # enables atmospheric scatter + cloud events
    },
    "high_current": {
        "target_current"      : 2.5,
        "initial_soc"         : 0.8,
        "simulation_hours"    : 12,
        "timestep_minutes"    : 10,
        "peak_irradiance"     : 1000,
        "peak_temperature"    : 50,
        "ambient_temperature" : 22,
    },
    "cloudy_high_current": {
        "target_current"      : 2.5,
        "initial_soc"         : 0.8,
        "simulation_hours"    : 12,
        "timestep_minutes"    : 10,
        "peak_irradiance"     : 400,
        "peak_temperature"    : 28,
        "ambient_temperature" : 18,
    },
}


if __name__ == "__main__":
    # Deferred import to avoid circular dependency (plotter imports from system_sim at module level)
    from plotter import (plot_system_over_time, plot_vi_curve,
                         plot_hydrogen_vs_current, plot_efficiency_curve)

    comparison_runs = [
        ("high_current",        "high_current",        "plot_high_current.png",        1),
        ("cloudy_day",          "cloudy",              "plot_cloudy.png",              2),
        ("cloudy_high_current", "cloudy_high_current", "plot_cloudy_high_current.png", 3),
    ]

    for scenario_key, folder, filename, seed in comparison_runs:
        random.seed(seed)
        scenario = SCENARIOS[scenario_key]
        out_dir  = os.path.join("data", folder)
        os.makedirs(out_dir, exist_ok=True)
        save_path = os.path.join(out_dir, filename)

        data = run_simulation(scenario)

        total_h2  = sum(row["h2_liters"] for row in data)
        min_soc   = min(row["battery_soc"] for row in data)
        statuses  = {row["battery_status"] for row in data}

        print(f"\n{'=' * 50}")
        print(f"  Scenario : {scenario_key.replace('_', ' ').title()}")
        print(f"  Current  : {scenario['target_current']} A  |  Peak irradiance: {scenario['peak_irradiance']} W/m²")
        print(f"  Total H2 : {total_h2:.4f} L")
        print(f"  Min SOC  : {min_soc:.1%}")
        print(f"  Warning  : {'YES' if 'warning'  in statuses else 'no'}")
        print(f"  Critical : {'YES' if 'critical' in statuses else 'no'}")
        print(f"  Plot     : {save_path}")

        # Re-seed so plot_system_over_time's internal run_simulation sees the
        # same random sequence and matches what the summary above printed.
        random.seed(seed)
        plot_system_over_time(scenario_name=scenario_key, save_path=save_path)

        op_current = scenario["target_current"]
        plot_vi_curve(
            save_path=os.path.join(out_dir, "plot_vi_curve.png"),
            operating_current=op_current,
        )
        plot_hydrogen_vs_current(
            save_path=os.path.join(out_dir, "plot_hydrogen_vs_current.png"),
            operating_current=op_current,
        )
        plot_efficiency_curve(
            save_path=os.path.join(out_dir, "plot_efficiency_curve.png"),
            operating_current=op_current,
        )

    print(f"\n{'=' * 50}")
    print("All scenarios complete.")