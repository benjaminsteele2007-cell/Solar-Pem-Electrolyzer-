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

def run_simulation(target_current=1.0, initial_soc=0.8):
    """
    Runs the full system simulation over the defined daylight window. 

    target_current : current the cell will try to operat at (A)
    initial_soc    : starting battery state of charge (fraction)
    returns        : list of dicts - one per timestep - with all recorded data
    """
    battery = BatteryModel(initial_soc=initial_soc)
    results = []
    
    for step in range(TOTAL_STEPS):
        current_hour = step * TIMESTEP_HOURS

        # Environmental conditions at timestep
        irradiance = solar_profile(current_hour)
        panel_temp = temperature_profile(current_hour)

        # Solar output
        solar_power = panel_power(irradiance, panel_temp)

        # Cell demand at the target current
        voltage_breakdown = cell_voltage(target_current)
        cell_power_demand = voltage_breakdown["total"] * target_current

        # Battery regulates flow
        delivered_power = battery.update(solar_power, cell_power_demand, TIMESTEP_HOURS)

        # Calculate actual current delivered ( P = V*I, so I = P/V)
        if voltage_breakdown["total"] > 0: 
            delivered_current = delivered_power / voltage_breakdown["total"]
        else:
            delivered_current = 0

        # Hydrogen produced at this timestep
        h2_liters = calculate_liters_h2(delivered_current, TIMESTEP_HOURS*3600)

        # Log everything
        results.append({
            "hour"          : current_hour,
            "irradiance"    : irradiance,
            "panel_temp"    : panel_temp,
            "solar_power"   : solar_power, 
            "cell_voltage"  : voltage_breakdown["total"],
            "cell_demand"   : cell_power_demand,
            "delivered_power" : delivered_power,
            "delivered_current" : delivered_current,
            "battery_soc"   : battery.soc, 
            "battery_status"    : battery.status,
            "h2_liters"     : h2_liters
        })
    return results

if __name__ =="__main__":
    data = run_simulation(target_current=1.0, initial_soc=0.8)

    print(f"{'Hour':<8} {'Irr (W/m²)':<12} {'Solar (W)':<12} {'Delivered (W)':<15} {'SOC':<8} {'H2 (L)':<10}")
    print("-" * 70)

    # Print every 6th row to keep output readable (every hour)
    for row in data[::6]:
        print(f"{row['hour']:<8.2f} {row['irradiance']:<12.1f} {row['solar_power']:<12.4f} "
              f"{row['delivered_power']:<15.4f} {row['battery_soc']:<8.1%} {row['h2_liters']:<10.6f}")

    # Totals
    total_h2 = sum(row["h2_liters"] for row in data)
    print(f"\nTotal hydrogen produced over {SIMULATION_HOURS} hours: {total_h2:.4f} liters")

