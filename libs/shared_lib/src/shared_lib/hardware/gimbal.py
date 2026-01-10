from __future__ import annotations

from .my_servo import MyServo


class Gimbal:
    """Pan/tilt gimbal controlled by two servos."""

    def __init__(self, pan_servo: MyServo, tilt_servo: MyServo) -> None:
        self._pan_servo = pan_servo
        self._tilt_servo = tilt_servo
        self._pan_percent = 0.0
        self._tilt_percent = 0.0

    def set_pan_percent(self, percent: float) -> None:
        self._pan_percent = self._clamp_percent(percent)
        self._pan_servo.set_percent(self._pan_percent)

    def set_tilt_percent(self, percent: float) -> None:
        self._tilt_percent = self._clamp_percent(percent)
        self._tilt_servo.set_percent(self._tilt_percent)

    def center(self) -> None:
        self._pan_percent = 0.0
        self._tilt_percent = 0.0
        self._pan_servo.set_percent(self._pan_percent)
        self._tilt_servo.set_percent(self._tilt_percent)

    @staticmethod
    def _clamp_percent(percent: float) -> float:
        return max(-100.0, min(100.0, float(percent)))
