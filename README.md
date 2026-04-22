# Solar PEM Electrolyzer

A solar-powered proton exchange membrane (PEM) electrolyzer prototype built over summer 2025. The project pairs a Python simulation with a physical hardware build to measure and explain the real operating behavior of a small PEM cell under variable solar input.

## The scientific question

A PEM electrolyzer splits water into hydrogen and oxygen using electricity. Thermodynamically, the minimum voltage required to drive this reaction is 1.23V. In practice, real cells require 1.8–2.1V. The difference — called **overpotential** — is wasted as heat and comes from three sources:

- **Activation overpotential** — the energy barrier to start the reaction at the electrode surface
- **Ohmic overpotential** — resistive losses in the membrane and electrodes
- **Concentration overpotential** — reactant depletion at high current densities

This project does not attempt to store hydrogen. Instead, it uses the full voltage-current (V-I) behavior of a real cell to quantify the overpotential thresholds and compare them against predictions from a mathematical model. The experimental finding is the gap between predicted and measured voltage at each operating current.

## System architecture

A 10W solar panel feeds a LiFePO4 buffer battery, which smooths the variable solar input and delivers steady power to an H-TEC E208 PEM electrolyzer cell. A Raspberry Pi Pico 2 W running MicroPython reads voltage, current, and temperature sensors on the cell, sends data over USB serial to a laptop, where Python logs and analyzes it.


Hydrogen is not stored. Production volume is measured manually via water displacement during controlled tests.

## The simulation

The simulation lives in `/simulation` and is the predictive baseline the hardware data will be compared against. It is built as six modules, each with one responsibility:

| Module | Purpose |
|--------|---------|
| `config.py` | Physical constants, cell specs, panel specs, battery specs. Every other module pulls from here. |
| `faraday.py` | Hydrogen production as a function of current and time, using Faraday's law. |
| `electrolyzer_model.py` | Predicted cell voltage as a function of current, broken into thermodynamic, activation, ohmic, and concentration components. |
| `solar_model.py` | Panel voltage, current, and power as a function of irradiance and temperature. |
| `battery_model.py` | Battery state of charge tracking, charge/discharge logic, efficiency losses, warning thresholds, and deactivation limits. |
| `system_sim.py` | Connects all models into a time-stepped simulation. Supports named scenarios (clear day, cloudy day, short test) and a V-I sweep function. |
| `plotter.py` | Generates four core plots from simulation data. |

### Current plots

1. **V-I curve with overpotential breakdown** — predicted total voltage at each current, with activation, ohmic, and concentration contributions stacked
2. **System behavior over time** — solar power, battery SOC, and delivered power across a simulated day
3. **Hydrogen production vs current** — Faraday's law reference line
4. **Efficiency vs current** — voltaic efficiency as a function of operating current, revealing the efficiency sweet spot

Predicted vs measured V-I will be added once hardware data is available.

## Current status

**Complete**
- Full simulation architecture, all six modules
- Scenario-based parameterization
- V-I sweep generation
- Core plots generated

**In progress**
- Laptop-side data pipeline (receives simulated Pico data)

**Upcoming**
- Firmware for Pico 2 W
- Electrolyzer cell purchase and integration
- Real V-I data collection
- Predicted vs measured analysis
- Integrated technical report

## Team

- **Ben Steele** — Chemical Engineering. Simulation, electrochemistry, report.
- **Partner name** — Computer Engineering. Firmware, sensor integration, embedded systems.

## How to run the simulation

Requires Python 3.10 or later and matplotlib.

```bash
# From the project root
cd simulation
python plotter.py
```

This runs all simulation modules and generates the four core plots in `/data`.

To run the time-series simulation directly:

```bash
python system_sim.py
```

To run the V-I sweep:
```python
from system_sim import run_vi_sweep
data = run_vi_sweep(0.1, 3.0, 0.1)
```

## Repository structure
```python
from system_sim import run_vi_sweep
data = run_vi_sweep(0.1, 3.0, 0.1)
```

## Repository structure
