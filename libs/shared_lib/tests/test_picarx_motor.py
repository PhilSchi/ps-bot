import sys
import types

from shared_lib.hardware import PicarxMotor


fake_robot_hat = types.ModuleType("robot_hat")


class DummyPin:
    def __init__(self, channel: str) -> None:
        self.channel = channel
        self.state = None

    def high(self) -> None:
        self.state = "high"

    def low(self) -> None:
        self.state = "low"


class DummyPWM:
    def __init__(self, channel: str) -> None:
        self.channel = channel
        self.period_value = None
        self.prescaler_value = None
        self.duty = None

    def period(self, value: int) -> None:
        self.period_value = value

    def prescaler(self, value: int) -> None:
        self.prescaler_value = value

    def pulse_width_percent(self, value: float) -> None:
        self.duty = value


fake_robot_hat.Pin = DummyPin
fake_robot_hat.PWM = DummyPWM
sys.modules.setdefault("robot_hat", fake_robot_hat)


def test_set_percent_forward_and_reverse() -> None:
    motor = PicarxMotor(
        {
            "direction_pin": "D4",
            "pwm_pin": "P13",
            "forward_direction": 1,
            "name": "left",
        },
        pin_cls=DummyPin,
        pwm_cls=DummyPWM,
    )

    motor.set_percent(60)
    assert motor._dir_pin.state == "low"
    assert motor._pwm_pin.duty == 80

    motor.set_percent(-60)
    assert motor._dir_pin.state == "high"
    assert motor._pwm_pin.duty == 80
