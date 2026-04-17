# electrolyzer_model.py
# Models the voltage behavior of the H-TEC E208 PEM electrolyzer.
# Calculates each overpotential contribution separately.
# The sum of all terms gives the real operating voltage at a given current.

import math
from config import (
    FARADAY_CONSTANT,
    GAS_CONSTANT,
    OPERATING_TEMP,
    REVERSIBLE_VOLTAGE,
    ELECTRONS_PER_H2,
    MEMBRANE_RESISTANCE,
    CELL_AREA,
    MAX_VOLTAGE,
    MIN_VOLTAGE
)

def activation_overpotential(current):
    """
    Calculates activation overpotential using the Tafel equation.
    
    current  : operating current in Amps (A)
    returns  : activation overpotential in Volts (V)
    """
    exchange_current = 0.001        # Exchange current density (A/cm²) — PEM typical
    current_density = current / CELL_AREA
    tafel_slope = (GAS_CONSTANT * OPERATING_TEMP) / (0.5 * FARADAY_CONSTANT)
    eta_act = tafel_slope * math.log(current_density / exchange_current)
    return eta_act


def ohmic_overpotential(current):
    """
    Calculates ohmic overpotential using Ohm's law.

    current  : operating current in Amps (A)
    returns  : ohmic overpotential in Volts (V)
    """
    resistance = MEMBRANE_RESISTANCE / CELL_AREA
    eta_ohm = current * resistance
    return eta_ohm


def concentration_overpotential(current):
    """
    Calculates concentration overpotential.
    Negligible at this scale but modeled for completeness.

    current  : operating current in Amps (A)
    returns  : concentration overpotential in Volts (V)
    """
    limiting_current = MAX_VOLTAGE * CELL_AREA   
    eta_con = (GAS_CONSTANT * OPERATING_TEMP) / (ELECTRONS_PER_H2 * FARADAY_CONSTANT) \
              * math.log(1 - (current / limiting_current))
    return abs(eta_con)


def cell_voltage(current):
    """
    Calculates total real cell voltage at a given current.
    Sums all overpotential contributions.

    current  : operating current in Amps (A)
    returns  : dictionary with voltage breakdown and total (V)
    """
    eta_act = activation_overpotential(current)
    eta_ohm = ohmic_overpotential(current)
    eta_con = concentration_overpotential(current)
    
    v_total = REVERSIBLE_VOLTAGE + eta_act + eta_ohm + eta_con

    return {
        "reversible"    : REVERSIBLE_VOLTAGE,
        "activation"    : eta_act,
        "ohmic"         : eta_ohm,
        "concentration" : eta_con,
        "total"         : v_total
    }


if __name__ == "__main__":
    print(f"{'Current (A)':<15} {'V_rev':<10} {'V_act':<10} {'V_ohm':<10} {'V_con':<10} {'V_total':<10}")
    print("-" * 65)
    for i in [0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
        v = cell_voltage(i)
        print(f"{i:<15} {v['reversible']:<10.4f} {v['activation']:<10.4f} {v['ohmic']:<10.4f} {v['concentration']:<10.4f} {v['total']:<10.4f}")