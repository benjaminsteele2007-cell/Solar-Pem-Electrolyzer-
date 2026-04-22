# battery_model.py
# Models the LiFePO4 buffer battery between solar panel and the cell.
# Tracks state of charge, manages charge/discharge cycles,
# applies efficiency losses, and triggers warnings and deactivation.

from config import (
    BATTERY_CAPACITY,
    BATTERY_VOLTAGE,
    BATTERY_EFFICIENCY,
    MIN_STATE_OF_CHARGE,
    MAX_STATE_OF_CHARGE,
    BATTERY_WARNING_THRESHOLD,
    BATTERY_CRITICAL_THRESHOLD
)

# Convert battery capacity from mAh to Wh for power calculation
BATTERY_ENERGY_MAX = (BATTERY_CAPACITY / 1000) * BATTERY_VOLTAGE  # Wh


class BatteryModel:
    """
    Simulates the LiFePO4 buffer battery.
    Tracks state of charge and manages power flow between
    the solar panel and electrolyzer cell.
    """

    def __init__(self, initial_soc=0.8):
        """
        Initialize battery at a given state of charge.
        initial_soc : starting state of charge as a fraction (0.0 to 1.0)
        """
        self.soc = initial_soc
        self.status = "idle"
        self.warnings = []

    def energy_available(self):
        """
        Returns usable energy currently in battery in Wh.
        """
        return self.soc * BATTERY_ENERGY_MAX

    def update(self, solar_power, cell_power, timestep_hours):
        """
        Updates battery state for one timestep.

        solar_power    : power coming in from solar panel (W)
        cell_power     : power demanded by electrolyzer cell (W)
        timestep_hours : duration of this timestep in hours (hr)
        returns        : actual power delivered to cell (W)
        """
        net_power = solar_power - cell_power

        if self.soc <= MIN_STATE_OF_CHARGE and net_power < 0:
            self.status = "deactivated"
            return 0

        if net_power > 0:
            self.status = "charging"
            energy_in = net_power * timestep_hours * BATTERY_EFFICIENCY
            self.soc += energy_in / BATTERY_ENERGY_MAX
            self.soc = min(self.soc, MAX_STATE_OF_CHARGE)
            delivered_power = cell_power

        elif net_power < 0:
            self.status = "discharging"
            energy_out = abs(net_power) * timestep_hours / BATTERY_EFFICIENCY
            self.soc -= energy_out / BATTERY_ENERGY_MAX
            self.soc = max(self.soc, MIN_STATE_OF_CHARGE)
            delivered_power = cell_power

        else:
            self.status = "balanced"
            delivered_power = cell_power

        delivered_power = self._check_thresholds(delivered_power)
        return delivered_power

    def _check_thresholds(self, delivered_power):
        """
        Checks state of charge against established safety thresholds.
        Logs warnings and deactivates cell if necessary.
        """
        if self.soc <= MIN_STATE_OF_CHARGE:
            self.status = "deactivated"
            self.warnings.append(
                f"DEACTIVATED - SOC at {self.soc:.1%} below minimum {MIN_STATE_OF_CHARGE:.1%}"
            )
            return 0

        elif self.soc <= BATTERY_CRITICAL_THRESHOLD:
            self.status = "critical"
            self.warnings.append(
                f"CRITICAL WARNING - SOC at {self.soc:.1%}"
            )

        elif self.soc <= BATTERY_WARNING_THRESHOLD:
            self.status = "warning"
            self.warnings.append(
                f"WARNING - SOC at {self.soc:.1%}"
            )

        return delivered_power

    def report(self):
        """
        Prints current battery status.
        """
        print(f"Battery SOC   : {self.soc:.1%}")
        print(f"Energy stored : {self.energy_available():.4f} Wh")
        print(f"Status        : {self.status}")
        if self.warnings:
            print("Warnings:")
            for w in self.warnings:
                print(f"    {w}")


if __name__ == "__main__":
    battery = BatteryModel(initial_soc=0.8)

    print("=== Simulating 5 timesteps ===\n")

    solar_conditions = [8.0, 6.0, 3.0, 1.5, 0.5]
    cell_demand = 4.0

    for i, solar in enumerate(solar_conditions):
        print(f"Timestep {i+1} — Solar: {solar}W  Cell demand: {cell_demand}W")
        delivered = battery.update(solar, cell_demand, timestep_hours=1.0)
        print(f"Delivered to cell: {delivered}W")
        battery.report()
        print()