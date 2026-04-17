# config.py
# Central configuration file for the solar PEM electrolyzer simulation
# All physical constants and system parameters retained in this file. 
# If a number needs to be changed, it chenges here. 

# Physical constants
FARADAY_CONSTANT = 96485    # Coulombs per mole of electrons(C/mol)
GAS_CONSTANT= 8.314     # Universal gas constant (J/mol*K)
MOLAR_VOLUME= 22.414    # Litters per mold of ideal gas at STP (L/mol)

# Thermodynamics
GIBBS_FREE_ENERGY= 237100   # Gibbs free energy for water splitting (J/mol)
THERMONEUTRAL_VOLTAGE = 1.48    # Thermoneutral voltage (v) - accounts for heat
REVERSIBLE_VOLTAGE = 1.23   # Theoretical minimum cell voltage at STP (V)
ELECTRONS_PER_H2 = 2    # Electrons transfered per H2 molecule 

# H-Tec E208 Cell Specs
CELL_AREA = 10.0    # Active membrane area (cm^2)
MAX_CURRENT_DENSITY = 300   # Maximum safe current density(mA/cm^2)
MAX_VOLTAGE= 2.1    # Maximum operating voltage (V)
MIN_VOLTAGE= 1.6    # Minimum practical operating voltage (V)
MEMBRANE_RESISTANCE=0.2     # Ohmic membrane (omega*cm^2)

# Solar Panel Specs
PANEL_WATTAGE = 10.0    # Rated panel output (w)
PANEL_EFFICIENCY= 0.18  # Panel efficiency (18%)[subject to change]
STANDARD_IRRADIANCE= 1000   # Standard test condition irradiance (W/m^2)[subject to change]
PANEL_AREA = 0.067  # Panel Area (m^2)

# Buffer Battery Specs
BATTERY_CAPACITY = 3000     # Battery capacity (mAh)
BATTERY_VOLTAGE = 3.7   # Nonimal battery voltage (V)
BATTERY_EFFICIENCY=0.95     # Round-trip charge/discharge efficiency(95%)
MIN_STATE_OF_CHARGE=0.2     # Minimum safe charge level (20%)
MAX_STATE_OF_CHARGE=0.95    # Maximum safe charge level (95%)
 
# Operating conditions 
OPERATING_TEMP = 298.15     # Operating temperature in Kelvin (25 degrees C)
AMBIENT_TEMP = 298.15   # Ambient temperature in Kelvin (25 degrees C)
