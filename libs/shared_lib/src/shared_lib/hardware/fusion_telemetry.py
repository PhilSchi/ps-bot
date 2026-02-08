"""Telemetry implementation for Fusion HAT."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shared_lib.drive_state import DesiredDriveState
from shared_lib.hardware.telemetry import BaseTelemetry

if TYPE_CHECKING:
    from fusion_hat.battery import Battery


class FusionTelemetry(BaseTelemetry):
    """Telemetry source for Fusion HAT hardware."""

    def __init__(self, drive_state: DesiredDriveState) -> None:
        super().__init__(drive_state)
        self._battery: Any | None = None

    def _get_battery(self) -> Any | None:
        """Lazy initialization of battery reader."""
        if self._battery is None:
            try:
                from fusion_hat.battery import Battery

                self._battery = Battery()
            except Exception:
                pass
        return self._battery

    def _read_battery_voltage(self) -> float:
        """Read battery voltage from Fusion HAT."""
        battery = self._get_battery()
        if battery is None:
            return 0.0
        try:
            return battery.voltage
        except (OSError, ValueError):
            return 0.0
