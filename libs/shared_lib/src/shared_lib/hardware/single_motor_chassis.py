from __future__ import annotations

from .actuator import Actuator
from .chassis import Chassis
from .servo import Servo


class SingleMotorChassis(Chassis):
    """Chassis implementation for one drive motor with a steering servo."""

    def __init__(
        self,
        steering_servo: Servo,
        drive_motor: Actuator,
    ) -> None:
        self._steering_servo = steering_servo
        self._drive_motor = drive_motor
        self._steering_percent = 0.0
        self._drive_percent = 0.0

    def set_steering_percent(self, percent: float) -> None:
        self._steering_percent = self._clamp_percent(percent)
        self._steering_servo.set_percent(self._steering_percent)

    def set_drive_percent(self, percent: float) -> None:
        self._drive_percent = self._clamp_percent(percent)
        self._drive_motor.set_percent(self._drive_percent)

    def stop(self) -> None:
        self._drive_percent = 0.0
        self._steering_percent = 0.0
        self._steering_servo.set_percent(self._steering_percent)
        self._drive_motor.set_percent(self._drive_percent)

    @staticmethod
    def _clamp_percent(percent: float) -> float:
        return max(-100.0, min(100.0, float(percent)))
