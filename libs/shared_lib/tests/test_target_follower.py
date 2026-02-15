from shared_lib.pid import PIDController
from shared_lib.tracking import TargetFollower


def test_zero_deviation_gives_zero_steer() -> None:
    pid = PIDController(kp=50.0)
    follower = TargetFollower(pid=pid, drive_speed=30.0)
    steer, drive = follower.update(0.0)
    assert steer == 0.0
    assert drive == 30.0


def test_positive_deviation_gives_positive_steer() -> None:
    pid = PIDController(kp=50.0)
    follower = TargetFollower(pid=pid, drive_speed=25.0)
    steer, drive = follower.update(0.5)
    assert steer == 25.0
    assert drive == 25.0


def test_negative_deviation_gives_negative_steer() -> None:
    pid = PIDController(kp=50.0)
    follower = TargetFollower(pid=pid)
    steer, _ = follower.update(-0.5)
    assert steer == -25.0


def test_output_clamped_to_100() -> None:
    pid = PIDController(kp=200.0)
    follower = TargetFollower(pid=pid)
    steer, _ = follower.update(1.0)
    assert steer == 100.0

    steer, _ = follower.update(-1.0)
    assert steer == -100.0


def test_reset_delegates_to_pid() -> None:
    pid = PIDController(kp=50.0, ki=10.0)
    follower = TargetFollower(pid=pid)
    follower.update(1.0)
    follower.reset()
    assert pid._integral == 0.0
    assert pid._prev_time is None
