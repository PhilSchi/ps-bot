from __future__ import annotations

from typing import Protocol


class PanControl(Protocol):
    """Interface for a single-axis pan control."""

    def set_pan_percent(self, percent: float) -> None:
        """Set pan in the range [-100.0, 100.0]; positive pans right."""
        ...

    def center(self) -> None:
        """Center pan."""
        ...
