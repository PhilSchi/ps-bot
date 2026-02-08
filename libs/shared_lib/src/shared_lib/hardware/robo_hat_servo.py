from __future__ import annotations

from typing import Mapping

from .gpiozero_setup import ensure_lgpio_pin_factory
from .servo import Servo

ensure_lgpio_pin_factory()

from robot_hat import Servo as RobotServo

class RoboHatServo(Servo):
    def __init__(
        self,
        config: Mapping[str, object],
        servo_cls: type[RobotServo] | None = None,
    ) -> None:
        self.name = str(config["name"])
        self.channel = config["channel"]
        self.min_angle = float(config["min_angle"])
        self.max_angle = float(config["max_angle"])
        self.zero_angle = float(config["zero_angle"])
        self.reverse = bool(config.get("reverse", False))

        if self.min_angle >= self.max_angle:
            raise ValueError("min_angle must be less than max_angle")
        if not (self.min_angle <= self.zero_angle <= self.max_angle):
            raise ValueError("zero_angle must be between min_angle and max_angle")

        if servo_cls is None:
            servo_cls = RobotServo
        self._servo = servo_cls(self.channel)

    def percent_to_angle(self, percent: float) -> float:
        if percent < -100.0 or percent > 100.0:
            raise ValueError("percent must be between -100 and 100")

        if self.reverse:
            percent = -percent

        half_range = (self.max_angle - self.min_angle) / 2.0
        return self.zero_angle + (percent / 100.0) * half_range

    def set_angle(self, angle: float) -> None:
        angle = float(angle)
        if angle < self.min_angle or angle > self.max_angle:
            raise ValueError("angle must be between min_angle and max_angle")
        self._servo.angle(angle)

    def set_percent(self, percent: float) -> None:
        angle = self.percent_to_angle(percent)
        self._servo.angle(angle)
