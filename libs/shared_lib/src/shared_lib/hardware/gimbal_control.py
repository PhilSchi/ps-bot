from __future__ import annotations

from typing import Protocol


class GimbalControl(Protocol):
    """Interface for gimbal pan/tilt controls."""

    def set_pan_percent(self, percent: float) -> None:
        """Set pan in the range [-100.0, 100.0]; positive pans right."""
        ...

    def set_tilt_percent(self, percent: float) -> None:
        """Set tilt in the range [-100.0, 100.0]; positive tilts up."""
        ...

    def center(self) -> None:
        """Center pan and tilt."""
        ...
