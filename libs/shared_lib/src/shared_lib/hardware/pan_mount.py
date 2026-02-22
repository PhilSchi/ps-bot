from __future__ import annotations

from .servo import Servo


class PanMount:
    """Single-axis pan mount controlled by one servo."""

    def __init__(self, pan_servo: Servo) -> None:
        self._pan_servo = pan_servo
        self._pan_percent = 0.0

    def set_pan_percent(self, percent: float) -> None:
        self._pan_percent = self._clamp_percent(percent)
        self._pan_servo.set_percent(self._pan_percent)

    def center(self) -> None:
        self._pan_percent = 0.0
        self._pan_servo.set_percent(self._pan_percent)

    @staticmethod
    def _clamp_percent(percent: float) -> float:
        return max(-100.0, min(100.0, float(percent)))
