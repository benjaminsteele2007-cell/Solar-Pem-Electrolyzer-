# fake_pico.py
# Simulates a Raspberry Pi Pico streaming sensor data over USB serial.
# Pulls predicted values from the system simulation and emits them as CSV
# on stdout — identical format to what real Pico firmware will produce.
# Pipe this into serial_reader.py for end-to-end pipeline testing.

import argparse
import random
import sys
import os
import time

# ── PATH SETUP ───────────────────────────────────────────────────────
# Add the simulation package directory so we can import without installing.
_SIM_DIR = os.path.join(os.path.dirname(__file__), "..", "simulation")
sys.path.insert(0, _SIM_DIR)

from system_sim import run_simulation, SCENARIOS
from solar_model import panel_voltage as compute_panel_voltage

# ── CSV FORMAT ───────────────────────────────────────────────────────
CSV_HEADER = (
    "timestamp,cell_voltage,cell_current,"
    "panel_voltage,panel_current,panel_power,"
    "cell_temp,panel_temp,battery_soc"
)


# ── DATA GENERATION ──────────────────────────────────────────────────

def _noisy(value, stdev):
    """Returns value with Gaussian noise applied at the given standard deviation."""
    return value + random.gauss(0, stdev)


def build_csv_row(row, start_time):
    """
    Converts one simulation result dict into a CSV data line.

    Computes derived panel quantities via solar_model and adds realistic
    Gaussian sensor noise to every reading before formatting.

    row        : single timestep dict returned by run_simulation
    start_time : unix epoch of the virtual session start
    returns    : formatted CSV string (no trailing newline)
    """
    timestamp = start_time + row["hour"] * 3600

    # ── derived panel quantities ─────────────────────────────────────
    pv          = compute_panel_voltage(row["irradiance"], row["panel_temp"])
    pan_current = row["solar_power"] / pv if pv > 0 else 0.0

    # ── clean values ─────────────────────────────────────────────────
    cell_voltage  = row["cell_voltage"]
    cell_current  = row["delivered_current"]
    panel_voltage = pv
    panel_current = pan_current
    panel_power   = row["solar_power"]
    cell_temp     = row["panel_temp"] - 8 + (row["cell_voltage"] - 1.23) * 15
    panel_temp    = row["panel_temp"]
    battery_soc   = row["battery_soc"]

    # ── add sensor noise ─────────────────────────────────────────────
    cell_voltage  = _noisy(cell_voltage,  0.005)
    cell_current  = _noisy(cell_current,  0.01)
    panel_voltage = _noisy(panel_voltage, 0.02)
    panel_current = _noisy(panel_current, 0.015)
    panel_power   = _noisy(panel_power,   0.05)
    cell_temp     = _noisy(cell_temp,     0.15)
    panel_temp    = _noisy(panel_temp,    0.3)
    battery_soc   = _noisy(battery_soc,   0.002)

    return (
        f"{timestamp:.3f},"
        f"{cell_voltage:.4f},"
        f"{cell_current:.4f},"
        f"{panel_voltage:.4f},"
        f"{panel_current:.4f},"
        f"{panel_power:.3f},"
        f"{cell_temp:.2f},"
        f"{panel_temp:.2f},"
        f"{battery_soc:.4f}"
    )


# ── STREAMING ────────────────────────────────────────────────────────

def stream(scenario_name, fast):
    """
    Runs the simulation for the chosen scenario and streams CSV rows to stdout.

    scenario_name : key from SCENARIOS dict
    fast          : if True, emit all rows immediately; if False, 1 second delay
                    between rows to mimic real Pico hardware at 1 Hz sampling
    """
    if scenario_name not in SCENARIOS:
        valid = ", ".join(SCENARIOS.keys())
        sys.exit(f"Unknown scenario '{scenario_name}'. Valid options: {valid}")

    scenario   = SCENARIOS[scenario_name]
    results    = run_simulation(scenario)
    start_time = time.time()
    random.seed(hash(scenario_name))

    print(CSV_HEADER, flush=True)

    for row in results:
        print(build_csv_row(row, start_time), flush=True)
        if not fast:
            time.sleep(1)


# ── CLI ──────────────────────────────────────────────────────────────

def parse_args():
    """
    Parses command-line arguments for scenario selection and output speed.

    returns : argparse.Namespace with attributes: scenario, fast
    """
    parser = argparse.ArgumentParser(
        description="Simulate Pico sensor stream over stdout as CSV."
    )
    parser.add_argument(
        "--scenario",
        default="clear_summer_day",
        help="Scenario name from SCENARIOS (default: clear_summer_day)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Dump all rows immediately instead of 1-second real-time delay",
    )
    return parser.parse_args()


# ── ENTRY POINT ──────────────────────────────────────────────────────

if __name__ == "__main__":
    args = parse_args()
    stream(scenario_name=args.scenario, fast=args.fast)
