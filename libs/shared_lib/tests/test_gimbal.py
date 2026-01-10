from shared_lib.hardware import Gimbal


class DummyServo:
    def __init__(self) -> None:
        self.percents: list[float] = []

    def set_percent(self, percent: float) -> None:
        self.percents.append(float(percent))


def test_pan_and_tilt_clamp() -> None:
    pan_servo = DummyServo()
    tilt_servo = DummyServo()
    gimbal = Gimbal(pan_servo, tilt_servo)

    gimbal.set_pan_percent(150)
    gimbal.set_tilt_percent(-120)

    assert pan_servo.percents[-1] == 100.0
    assert tilt_servo.percents[-1] == -100.0


def test_center_resets_axes() -> None:
    pan_servo = DummyServo()
    tilt_servo = DummyServo()
    gimbal = Gimbal(pan_servo, tilt_servo)

    gimbal.set_pan_percent(40)
    gimbal.set_tilt_percent(-35)

    gimbal.center()

    assert pan_servo.percents[-1] == 0.0
    assert tilt_servo.percents[-1] == 0.0
