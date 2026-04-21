# plotter.py
# Generates the core visualization plots for the simulation.
# Each plot answers a specific question about cell behavior.
#
# Future additions:
#   - Predicted vs measured V-I curve (after hardware integration) 
#   - Heat dissipation vs current 
#   - Scenario comparisons (clear vs cloudy)

import matplotlib.pyplot as plt
from system_sim import run_simulation, run_vi_sweep, SCENARIOS
from faraday import calculate_production_rate


def plot_vi_curve(save_path=None):
    """
    Plot 1 — V-I curve with stacked overpotential breakdown.
    Shows how much voltage each loss mechanism contributes at every current.
    """
    data = run_vi_sweep(current_min=0.05, current_max=3.0, step=0.05)

    currents      = [row["current"] for row in data]
    reversible    = [row["reversible"] for row in data]
    activation    = [row["activation"] for row in data]
    ohmic         = [row["ohmic"] for row in data]
    concentration = [row["concentration"] for row in data]
    total         = [row["total"] for row in data]

    fig, ax = plt.subplots(figsize=(9, 6))

    # Stacked overpotential regions
    ax.fill_between(currents, 0, reversible,
                    color="#888888", alpha=0.7, label="Thermodynamic (1.23V)")
    ax.fill_between(currents,
                    reversible,
                    [r + a for r, a in zip(reversible, activation)],
                    color="#d17a22", alpha=0.7, label="Activation overpotential")
    ax.fill_between(currents,
                    [r + a for r, a in zip(reversible, activation)],
                    [r + a + o for r, a, o in zip(reversible, activation, ohmic)],
                    color="#2a7fbf", alpha=0.7, label="Ohmic overpotential")
    ax.fill_between(currents,
                    [r + a + o for r, a, o in zip(reversible, activation, ohmic)],
                    total,
                    color="#6b9e3f", alpha=0.7, label="Concentration overpotential")

    # Total voltage line
    ax.plot(currents, total, color="black", linewidth=2, label="Total cell voltage")

    ax.set_xlabel("Current (A)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title("Predicted V-I Curve — Overpotential Breakdown")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 3)
    ax.set_ylim(1.2, 1.7)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_system_over_time(scenario_name="clear_summer_day", save_path=None):
    """
    Plot 2 — Solar, battery, and delivered power across a simulated day.
    Shows the battery's role as a buffer between variable solar and steady demand.
    """
    data = run_simulation(SCENARIOS[scenario_name])

    hours         = [row["hour"] for row in data]
    solar         = [row["solar_power"] for row in data]
    delivered     = [row["delivered_power"] for row in data]
    soc           = [row["battery_soc"] * 100 for row in data]  # percent

    fig, ax1 = plt.subplots(figsize=(9, 6))

    ax1.plot(hours, solar, color="#d17a22", linewidth=2, label="Solar output (W)")
    ax1.plot(hours, delivered, color="#2a7fbf", linewidth=2, linestyle="--",
             label="Delivered to cell (W)")
    ax1.set_xlabel("Hour of simulated day")
    ax1.set_ylabel("Power (W)")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    # Battery SOC on a secondary axis
    ax2 = ax1.twinx()
    ax2.plot(hours, soc, color="#6b9e3f", linewidth=2, label="Battery SOC (%)")
    ax2.set_ylabel("Battery SOC (%)")
    ax2.set_ylim(0, 100)
    ax2.legend(loc="upper right")

    plt.title(f"System Behavior — {scenario_name.replace('_', ' ').title()}")

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_hydrogen_vs_current(save_path=None):
    """
    Plot 3 — Hydrogen production rate as a function of current.
    Demonstrates Faraday's law — perfectly linear relationship.
    """
    currents = [i * 0.1 for i in range(1, 31)]  # 0.1A to 3.0A
    rates = [calculate_production_rate(i) for i in currents]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(currents, rates, color="#2a7fbf", linewidth=2, marker="o", markersize=4)
    ax.set_xlabel("Operating current (A)")
    ax.set_ylabel("Hydrogen production rate (L/hr)")
    ax.set_title("Hydrogen Production vs Current — Faraday's Law")
    ax.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_efficiency_curve(save_path=None):
    """
    Plot 4 — Voltaic efficiency as a function of current.
    Efficiency = thermoneutral voltage / actual voltage.
    Reveals the operating sweet spot.
    """
    data = run_vi_sweep(current_min=0.05, current_max=3.0, step=0.05)

    currents   = [row["current"] for row in data]
    efficiency = [1.48 / row["total"] * 100 for row in data]  # percent

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(currents, efficiency, color="#6b9e3f", linewidth=2)
    ax.set_xlabel("Operating current (A)")
    ax.set_ylabel("Voltaic efficiency (%)")
    ax.set_title("Cell Efficiency vs Operating Current")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    print("Generating all plots...")
    if __name__ == "__main__":
        print ("Generating all plots...")
        plot_vi_curve(save_path="data/plot_vi_curve.png")
        plot_system_over_time(save_path="data/plot_system_over_time.png")
        plot_hydrogen_vs_current(save_path="data/plot_hydrogen_vs_current.png")
        plot_efficiency_curve(save_path="data/plot_efficiency_curve.png")
        print("Done. Plots saved to /data folder.")