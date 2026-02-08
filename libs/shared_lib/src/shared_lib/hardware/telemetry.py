"""Base telemetry abstraction for robot hardware."""

from __future__ import annotations

from shared_lib.drive_state import DesiredDriveState

CPU_TEMP_PATH = "/sys/class/thermal/thermal_zone0/temp"


class BaseTelemetry:
    """Base telemetry implementation with common functionality."""

    def __init__(self, drive_state: DesiredDriveState) -> None:
        self.drive_state = drive_state

    def get_telemetry(self) -> dict[str, float]:
        """Return current telemetry values."""
        return {
            "speed": self.drive_state.drive,
            "steering": self.drive_state.steer,
            "pan": self.drive_state.pan,
            "tilt": self.drive_state.tilt,
            "battery_v": self._read_battery_voltage(),
            "cpu_temp": self._read_cpu_temp(),
        }

    def _read_battery_voltage(self) -> float:
        """Read battery voltage. Override in subclasses."""
        return 0.0

    def _read_cpu_temp(self) -> float:
        """Read CPU temperature in Celsius."""
        try:
            with open(CPU_TEMP_PATH) as f:
                return int(f.read().strip()) / 1000.0
        except (OSError, ValueError):
            return 0.0
