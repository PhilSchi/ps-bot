from shared_lib.hardware import PicarxChassis


class DummyServo:
    def __init__(self) -> None:
        self.percents: list[float] = []

    def set_percent(self, percent: float) -> None:
        self.percents.append(float(percent))


class DummyMotor:
    def __init__(self) -> None:
        self.percents: list[float] = []

    def set_percent(self, percent: float) -> None:
        self.percents.append(float(percent))


def test_drive_and_steering_scale_inner_wheel() -> None:
    servo = DummyServo()
    left_motor = DummyMotor()
    right_motor = DummyMotor()
    chassis = PicarxChassis(servo, left_motor, right_motor)

    chassis.set_drive_percent(50)
    assert left_motor.percents[-1] == 50.0
    assert right_motor.percents[-1] == 50.0

    chassis.set_steering_percent(50)
    assert servo.percents[-1] == 50.0
    assert left_motor.percents[-1] == 50.0
    assert right_motor.percents[-1] == 25.0

    chassis.set_steering_percent(-50)
    assert left_motor.percents[-1] == 25.0
    assert right_motor.percents[-1] == 50.0

    chassis.set_drive_percent(-80)
    assert left_motor.percents[-1] == -40.0
    assert right_motor.percents[-1] == -80.0


def test_stop_centers_steering_and_stops_motors() -> None:
    servo = DummyServo()
    left_motor = DummyMotor()
    right_motor = DummyMotor()
    chassis = PicarxChassis(servo, left_motor, right_motor)

    chassis.set_drive_percent(60)
    chassis.set_steering_percent(30)

    chassis.stop()

    assert servo.percents[-1] == 0.0
    assert left_motor.percents[-1] == 0.0
    assert right_motor.percents[-1] == 0.0
