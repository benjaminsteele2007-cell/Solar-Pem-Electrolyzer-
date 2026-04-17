# solar_model.py
# Models the electrical output of the solar panel.
# Takes irradiance and temperature as inputs.
# Outputs voltage, current, and power delivered to the battery buffer.

from config import (
    PANEL_WATTAGE,
    PANEL_EFFICIENCY,
    PANEL_AREA,
    STANDARD_IRRADIANCE,
    OPERATING_TEMP,
    AMBIENT_TEMP
)

# Temperature coefficient for voltage — silicon panels lose roughly
# 0.4% of voltage per degree Celsius above standard test conditions
TEMP_COEFFICIENT = -0.004


def panel_current(irradiance):
    """
    Calculates current output from the solar panel.
    Current scales linearly with irradiance.

    irradiance  : solar irradiance in W/m² (W/m²)
    returns     : current output in Amps (A)
    """
    current = (PANEL_WATTAGE * (irradiance / STANDARD_IRRADIANCE)) / panel_voltage(irradiance)
    return current


def panel_voltage(irradiance, temp_celsius=25.0):
    """
    Calculates voltage output from the solar panel.
    Voltage drops as temperature increases above 25°C standard.

    irradiance    : solar irradiance in W/m² (W/m²)
    temp_celsius  : panel surface temperature in Celsius (°C)
    returns       : voltage output in Volts (V)
    """
    # Rated voltage at standard test conditions
    v_rated = PANEL_WATTAGE / (PANEL_EFFICIENCY * PANEL_AREA * STANDARD_IRRADIANCE) * PANEL_AREA

    # Temperature correction — voltage drops above 25°C
    delta_temp = temp_celsius - 25.0
    v_corrected = v_rated * (1 + TEMP_COEFFICIENT * delta_temp)

    return v_corrected


def panel_power(irradiance, temp_celsius=25.0):
    """
    Calculates total power output from the solar panel.

    irradiance    : solar irradiance in W/m² (W/m²)
    temp_celsius  : panel surface temperature in Celsius (°C)
    returns       : power output in Watts (W)
    """
    power = PANEL_EFFICIENCY * PANEL_AREA * irradiance * (1 + TEMP_COEFFICIENT * (temp_celsius - 25.0))
    return power


if __name__ == "__main__":
    print(f"{'Irradiance (W/m²)':<20} {'Temp (°C)':<12} {'Voltage (V)':<14} {'Power (W)':<12}")
    print("-" * 60)
    conditions = [
        (200, 15.0),
        (400, 20.0),
        (600, 25.0),
        (800, 35.0),
        (1000, 45.0),
    ]
    for irr, temp in conditions:
        v = panel_voltage(irr, temp)
        p = panel_power(irr, temp)
        print(f"{irr:<20} {temp:<12} {v:<14.4f} {p:<12.4f}")