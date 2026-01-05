import sys
import types

import pytest


fake_robot_hat = types.ModuleType("robot_hat")


class DummyServo:
    def __init__(self, channel: str) -> None:
        self.channel = channel
        self.angles: list[float] = []

    def angle(self, value: float) -> None:
        self.angles.append(value)


fake_robot_hat.Servo = DummyServo
sys.modules.setdefault("robot_hat", fake_robot_hat)

from shared_lib.hardware import MyServo  # noqa: E402


def test_set_angle_validates_and_forwards() -> None:
    servo = MyServo(
        {
            "channel": "P0",
            "min_angle": -90.0,
            "max_angle": 90.0,
            "zero_angle": 0.0,
            "name": "test-servo",
        },
        servo_cls=DummyServo,
    )

    servo.set_angle(12.5)
    assert servo._servo.angles == [12.5]

    with pytest.raises(ValueError):
        servo.set_angle(200.0)
