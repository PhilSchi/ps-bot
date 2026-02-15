import time
from unittest.mock import patch

from shared_lib.pid import PIDController


def test_p_only() -> None:
    pid = PIDController(kp=2.0, ki=0.0, kd=0.0)
    assert pid.update(1.0) == 2.0
    assert pid.update(-0.5) == -1.0


def test_i_accumulation() -> None:
    pid = PIDController(kp=0.0, ki=10.0, kd=0.0)
    t = 0.0
    with patch("shared_lib.pid.time") as mock_time:
        mock_time.monotonic.side_effect = lambda: t
        pid.update(1.0)  # first call: dt=0, no integral yet
        t = 1.0
        result = pid.update(1.0)  # dt=1.0, integral = 1.0*1.0 = 1.0
    assert result == 10.0  # ki * integral


def test_d_reaction() -> None:
    pid = PIDController(kp=0.0, ki=0.0, kd=5.0)
    t = 0.0
    with patch("shared_lib.pid.time") as mock_time:
        mock_time.monotonic.side_effect = lambda: t
        pid.update(0.0)  # first call, prev_error=0
        t = 1.0
        result = pid.update(2.0)  # d = 5.0 * (2.0 - 0.0) / 1.0
    assert result == 10.0


def test_anti_windup() -> None:
    pid = PIDController(kp=0.0, ki=1.0, kd=0.0, integral_limit=5.0)
    t = 0.0
    with patch("shared_lib.pid.time") as mock_time:
        mock_time.monotonic.side_effect = lambda: t
        pid.update(100.0)
        t = 1.0
        result = pid.update(100.0)  # integral would be 100 but clamped to 5
    assert result == 5.0  # ki * clamped_integral


def test_reset() -> None:
    pid = PIDController(kp=1.0, ki=1.0, kd=1.0)
    pid.update(5.0)
    pid.reset()
    # After reset, first call should behave like a fresh PID
    assert pid._integral == 0.0
    assert pid._prev_error == 0.0
    assert pid._prev_time is None


def test_negative_error() -> None:
    pid = PIDController(kp=3.0, ki=0.0, kd=0.0)
    assert pid.update(-2.0) == -6.0
