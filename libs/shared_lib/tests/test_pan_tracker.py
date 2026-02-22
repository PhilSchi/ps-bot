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
    assert tracker._position == 0.0


def test_position_accumulates() -> None:
    """When deviation stays positive, position keeps increasing."""
    pid = PIDController(kp=10.0)
    tracker = PanTracker(pid=pid)
    p1 = tracker.update(0.5)
    p2 = tracker.update(0.5)
    assert p2 > p1 > 0


def test_position_holds_when_deviation_zero() -> None:
    """Once a position is reached, deviation=0 should keep it stable."""
    pid = PIDController(kp=10.0)
    tracker = PanTracker(pid=pid)
    tracker.update(0.5)  # move right
    pos_before = tracker.update(0.5)
    pos_after = tracker.update(0.0)  # target centred
    assert pos_after == pos_before  # position unchanged
