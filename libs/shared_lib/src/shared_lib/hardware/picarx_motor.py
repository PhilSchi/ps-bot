from __future__ import annotations

from typing import Mapping

from .gpiozero_setup import ensure_lgpio_pin_factory

from .actuator import Actuator

ensure_lgpio_pin_factory()

from robot_hat import PWM, Pin


class PicarxMotor(Actuator):
    def __init__(
        self,
        config: Mapping[str, object],
        pin_cls: type[Pin] | None = None,
        pwm_cls: type[PWM] | None = None,
    ) -> None:
        self.name = str(config.get("name", "motor"))
        self.direction_pin = config["direction_pin"]
        self.pwm_pin = config["pwm_pin"]
        self.forward_direction = int(config.get("forward_direction", 1))
        self.speed_offset = float(config.get("speed_offset", 0.0))
        self.period = int(config.get("period", 4095))
        self.prescaler = int(config.get("prescaler", 10))

        if self.forward_direction not in (-1, 1):
            raise ValueError("forward_direction must be 1 or -1")

        if pin_cls is None:
            pin_cls = Pin
        if pwm_cls is None:
            pwm_cls = PWM

        self._dir_pin = pin_cls(self.direction_pin)
        self._pwm_pin = pwm_cls(self.pwm_pin)
        self._pwm_pin.period(self.period)
        self._pwm_pin.prescaler(self.prescaler)

    def set_percent(self, percent: float) -> None:
        percent = max(-100.0, min(100.0, float(percent)))
        direction = self.forward_direction if percent >= 0 else -self.forward_direction
        speed = abs(percent)
        if speed != 0.0:
            duty = int(speed / 2) + 50
        else:
            duty = 0
        duty -= self.speed_offset
        duty = max(0.0, min(100.0, duty))

        if direction < 0:
            self._dir_pin.high()
        else:
            self._dir_pin.low()

        self._pwm_pin.pulse_width_percent(duty)
