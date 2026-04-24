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
    AMBIENT_TEMP,
    PANEL_VMP,
    PANEL_IMP,
)

# Temperature coefficient for voltage — silicon panels lose roughly
# 0.4% of voltage per degree Celsius above standard test conditions
TEMP_COEFFICIENT = -0.004


def panel_voltage(irradiance, temp_celsius=25.0):
    """
    Calculates operating voltage at the maximum power point.

    Voltage is nearly constant across irradiance levels (real panel behaviour) —
    it only sags slightly at low irradiance, modelled with a small fractional
    exponent so the curve stays in the 15–18 V range under normal operation
    and approaches 0 V only as irradiance approaches 0.

    irradiance    : solar irradiance in W/m²
    temp_celsius  : panel surface temperature in °C
    returns       : voltage in Volts (V)
    """
    if irradiance <= 0:
        return 0.0

    irradiance_fraction = irradiance / STANDARD_IRRADIANCE
    delta_temp = temp_celsius - 25.0
    v_temp_corrected = PANEL_VMP * (1 + TEMP_COEFFICIENT * delta_temp)

    # Small exponent keeps voltage near Vmp across most of the irradiance range
    return v_temp_corrected * (irradiance_fraction ** 0.05)


def panel_current(irradiance, temp_celsius=25.0):
    """
    Calculates current output from the solar panel.

    Current scales linearly with irradiance — at standard 1000 W/m² the panel
    delivers IMP; at half irradiance it delivers half IMP.

    irradiance    : solar irradiance in W/m²
    temp_celsius  : panel surface temperature in °C (accepted for API symmetry)
    returns       : current in Amps (A)
    """
    if irradiance <= 0:
        return 0.0

    return PANEL_IMP * (irradiance / STANDARD_IRRADIANCE)


def panel_power(irradiance, temp_celsius=25.0):
    """
    Calculates total power output from the solar panel as V × I.

    irradiance    : solar irradiance in W/m²
    temp_celsius  : panel surface temperature in °C
    returns       : power in Watts (W)
    """
    return panel_voltage(irradiance, temp_celsius) * panel_current(irradiance, temp_celsius)


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