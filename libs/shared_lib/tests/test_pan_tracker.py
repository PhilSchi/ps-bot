from shared_lib.pid import PIDController
from shared_lib.tracking import PanTracker


def test_positive_deviation_returns_positive_pan() -> None:
    pid = PIDController(kp=50.0)
    tracker = PanTracker(pid=pid)
    result = tracker.update(0.6)
    assert result > 0


def test_negative_deviation_returns_negative_pan() -> None:
    pid = PIDController(kp=50.0)
    tracker = PanTracker(pid=pid)
    result = tracker.update(-0.4)
    assert result < 0


def test_zero_deviation_returns_zero() -> None:
    pid = PIDController(kp=50.0)
    tracker = PanTracker(pid=pid)
    result = tracker.update(0.0)
    assert result == 0.0


def test_output_clamped_to_100() -> None:
    pid = PIDController(kp=200.0)
    tracker = PanTracker(pid=pid)
    result = tracker.update(1.0)
    assert result == 100.0


def test_output_clamped_to_minus_100() -> None:
    pid = PIDController(kp=200.0)
    tracker = PanTracker(pid=pid)
    result = tracker.update(-1.0)
    assert result == -100.0


def test_reset_clears_pid_state() -> None:
    pid = PIDController(kp=50.0, ki=10.0)
    tracker = PanTracker(pid=pid)
    tracker.update(0.5)
    tracker.reset()
    assert pid._integral == 0.0
    assert pid._prev_time is None
