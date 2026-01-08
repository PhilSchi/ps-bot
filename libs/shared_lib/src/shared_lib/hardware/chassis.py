from __future__ import annotations

from typing import Protocol


class Chassis(Protocol):
    """Interface for ground vehicle steering and drive controls."""

    def set_steering_percent(self, percent: float) -> None:
        """Set steering in the range [-100.0, 100.0]; positive turns right."""
        ...

    def set_drive_percent(self, percent: float) -> None:
        """Set drive in the range [-100.0, 100.0]; positive drives forward."""
        ...

    def stop(self) -> None:
        """Stop the drive motors and center steering."""
        ...
