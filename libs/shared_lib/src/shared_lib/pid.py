"""Reusable PID controller."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class PIDController:
    kp: float = 1.0
    ki: float = 0.0
    kd: float = 0.0
    integral_limit: float = 100.0

    _integral: float = field(default=0.0, init=False, repr=False)
    _prev_error: float = field(default=0.0, init=False, repr=False)
    _prev_time: float | None = field(default=None, init=False, repr=False)

    def update(self, error: float) -> float:
        now = time.monotonic()
        if self._prev_time is None:
            dt = 0.0
        else:
            dt = now - self._prev_time
        self._prev_time = now

        p = self.kp * error

        self._integral += error * dt
        self._integral = max(-self.integral_limit, min(self.integral_limit, self._integral))
        i = self.ki * self._integral

        d = self.kd * ((error - self._prev_error) / dt if dt > 0 else 0.0)
        self._prev_error = error

        return p + i + d

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_error = 0.0
        self._prev_time = None
