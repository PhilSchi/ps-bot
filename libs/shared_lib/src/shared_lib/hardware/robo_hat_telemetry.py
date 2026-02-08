"""Telemetry implementation for Robot HAT."""

from __future__ import annotations

from shared_lib.drive_state import DesiredDriveState
from shared_lib.hardware.telemetry import BaseTelemetry


class RoboHatTelemetry(BaseTelemetry):
    """Telemetry source for Robot HAT hardware."""

    def __init__(self, drive_state: DesiredDriveState) -> None:
        super().__init__(drive_state)

    def _read_battery_voltage(self) -> float:
        """Read battery voltage from Robot HAT ADC."""
        try:
            from robot_hat.utils import get_battery_voltage

            return get_battery_voltage()
        except (OSError, ValueError, ImportError):
            return 0.0
