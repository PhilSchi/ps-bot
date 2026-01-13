from __future__ import annotations

from typing import Mapping

from .servo import Servo

from fusion_hat.servo import Servo as FusionHatServo


class FusionServo(Servo):
    def __init__(
        self,
        config: Mapping[str, object],
        servo_cls: type[FusionHatServo] | None = None,
    ) -> None:
        self.name = str(config["name"])
        self.channel = config["channel"]
        self.min_angle = float(config["min_angle"])
        self.max_angle = float(config["max_angle"])
        self.zero_angle = float(config["zero_angle"])
        self.offset = float(config.get("offset", 0.0))

        if self.min_angle >= self.max_angle:
            raise ValueError("min_angle must be less than max_angle")
        if not (self.min_angle <= self.zero_angle <= self.max_angle):
            raise ValueError("zero_angle must be between min_angle and max_angle")
        
        # self._servo = FusionHatServo(0)

        if servo_cls is None:
            servo_cls = FusionHatServo
        self._servo = servo_cls(
            self.channel,
            offset=self.offset,
            min=self.min_angle,
            max=self.max_angle,
        )

    def percent_to_angle(self, percent: float) -> float:
        if percent < -100.0 or percent > 100.0:
            raise ValueError("percent must be between -100 and 100")

        if percent >= 0.0:
            return self.zero_angle + (percent / 100.0) * (self.max_angle - self.zero_angle)

        return self.zero_angle + (percent / 100.0) * (self.zero_angle - self.min_angle)

    def set_angle(self, angle: float) -> None:
        angle = float(angle)
        if angle < self.min_angle or angle > self.max_angle:
            raise ValueError("angle must be between min_angle and max_angle")
        self._servo.angle(angle)

    def set_percent(self, percent: float) -> None:
        angle = self.percent_to_angle(percent)
        self._servo.angle(angle)
