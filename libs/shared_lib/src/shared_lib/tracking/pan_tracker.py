"""Pan-axis camera tracker that converts image deviation into pan servo commands."""

from __future__ import annotations

from dataclasses import dataclass, field

from shared_lib.pid import PIDController


@dataclass
class PanTracker:
    pid: PIDController
    max_step: float = 2.0
    _position: float = field(default=0.0, init=False, repr=False)

    def update(self, deviation: float) -> float:
        """Compute pan_percent from a deviation in [-1, +1].

        *deviation* < 0 means target is left, > 0 means right.
        The PID output is treated as a velocity correction that is
        accumulated into the current position so that the servo stays
        in place once the target is centred (deviation ≈ 0).
        The correction is clamped to *max_step* per tick to prevent
        fast movements that cause motion blur.
        Returns clamped pan in [-100, 100].
        """
        correction = self.pid.update(deviation)
        correction = max(-self.max_step, min(self.max_step, correction))
        self._position = max(-100.0, min(100.0, self._position + correction))
        return self._position

    def reset(self, position: float = 0.0) -> None:
        self.pid.reset()
        self._position = position
