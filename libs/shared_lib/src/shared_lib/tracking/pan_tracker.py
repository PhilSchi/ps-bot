"""Pan-axis camera tracker that converts image deviation into pan servo commands."""

from __future__ import annotations

from dataclasses import dataclass

from shared_lib.pid import PIDController


@dataclass
class PanTracker:
    pid: PIDController

    def update(self, deviation: float) -> float:
        """Compute pan_percent from a deviation in [-1, +1].

        *deviation* < 0 means target is left, > 0 means right.
        Returns clamped pan in [-100, 100].
        """
        raw = self.pid.update(deviation)
        return max(-100.0, min(100.0, raw))

    def reset(self) -> None:
        self.pid.reset()
