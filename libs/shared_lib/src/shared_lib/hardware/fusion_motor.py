from __future__ import annotations

from typing import Mapping

from .actuator import Actuator

from fusion_hat.motor import Motor as FusionHatMotor


class FusionMotor(Actuator):
    """Motor actuator for Fusion HAT.

    Config keys:
        factor: float (-1.0 to 1.0, default 1.0) – scales and/or reverses
            the input percentage.  A factor of -1 reverses direction,
            0.5 halves the speed, -0.5 reverses at half speed, etc.
    """

    def __init__(
        self,
        config: Mapping[str, object],
        motor_cls: type[FusionHatMotor] | None = None,
    ) -> None:
        self.name = str(config.get("name", "motor"))
        motor_id = config.get("motor")
        pwm_a = config.get("pwm_a")
        pwm_b = config.get("pwm_b")
        freq = config.get("freq")
        max_power = config.get("max")
        min_power = config.get("min")
        self._factor = max(-1.0, min(1.0, float(config.get("factor", 1.0))))

        if motor_cls is None:
            motor_cls = FusionHatMotor

        motor_kwargs: dict[str, object] = {}
        if freq is not None:
            motor_kwargs["freq"] = int(freq)
        if max_power is not None:
            motor_kwargs["max"] = float(max_power)
        if min_power is not None:
            motor_kwargs["min"] = float(min_power)

        if pwm_a is not None or pwm_b is not None:
            if pwm_a is None or pwm_b is None:
                raise ValueError("pwm_a and pwm_b must be provided together")
            self._motor = motor_cls(pwm_a, pwm_b, **motor_kwargs)
        elif motor_id is not None:
            self._motor = motor_cls(str(motor_id), **motor_kwargs)
        else:
            raise ValueError("config must include 'motor' or both 'pwm_a' and 'pwm_b'")

    def set_percent(self, percent: float) -> None:
        percent = max(-100.0, min(100.0, float(percent))) * self._factor
        self._motor.power(percent)

