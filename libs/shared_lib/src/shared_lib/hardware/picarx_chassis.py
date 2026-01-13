from __future__ import annotations

from .actuator import Actuator
from .chassis import Chassis
from .servo import Servo


class PicarxChassis(Chassis):
    """Chassis implementation for two rear motors with a steering servo."""

    def __init__(
        self,
        steering_servo: Servo,
        left_motor: Actuator,
        right_motor: Actuator,
    ) -> None:
        self._steering_servo = steering_servo
        self._left_motor = left_motor
        self._right_motor = right_motor
        self._steering_percent = 0.0
        self._drive_percent = 0.0

    def set_steering_percent(self, percent: float) -> None:
        self._steering_percent = self._clamp_percent(percent)
        self._steering_servo.set_percent(self._steering_percent)
        self._apply_drive()

    def set_drive_percent(self, percent: float) -> None:
        self._drive_percent = self._clamp_percent(percent)
        self._apply_drive()

    def stop(self) -> None:
        self._drive_percent = 0.0
        self._steering_percent = 0.0
        self._steering_servo.set_percent(self._steering_percent)
        self._apply_drive()

    @staticmethod
    def _clamp_percent(percent: float) -> float:
        return max(-100.0, min(100.0, float(percent)))

    def _apply_drive(self) -> None:
        drive = self._drive_percent
        steering = self._steering_percent
        if steering == 0.0:
            left = drive
            right = drive
        else:
            power_scale = 1.0 - abs(steering) / 100.0
            if steering > 0.0:
                left = drive
                right = drive * power_scale
            else:
                left = drive * power_scale
                right = drive

        self._left_motor.set_percent(left)
        self._right_motor.set_percent(right)
