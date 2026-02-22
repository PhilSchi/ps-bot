from shared_lib.detection.person_detector import Detection, PersonDetector
from shared_lib.drive_state import DesiredDriveState
from shared_lib.pid import PIDController
from shared_lib.tracking import TargetFollower

from crawler.follow_coordinator import BUTTON_A, PersonFollowCoordinator


def _make_coordinator() -> PersonFollowCoordinator:
    desired = DesiredDriveState()
    detector = PersonDetector.__new__(PersonDetector)
    # Manually initialize minimal fields for testing
    import threading

    detector._lock = threading.Lock()
    detector._detected = False
    detector._detections = []
    pid = PIDController(kp=50.0)
    follower = TargetFollower(pid=pid, drive_speed=30.0)
    return PersonFollowCoordinator(
        detector=detector, follower=follower, desired_state=desired
    )


def test_button_a_toggles_active() -> None:
    coord = _make_coordinator()
    assert not coord.active

    coord.on_button(BUTTON_A, True)
    assert coord.active

    coord.on_button(BUTTON_A, True)
    assert not coord.active


def test_button_a_release_ignored() -> None:
    coord = _make_coordinator()
    coord.on_button(BUTTON_A, False)
    assert not coord.active


def test_non_a_button_ignored() -> None:
    coord = _make_coordinator()
    coord.on_button(0, True)
    assert not coord.active
    coord.on_button(1, True)
    assert not coord.active


def test_manual_input_cancels() -> None:
    coord = _make_coordinator()
    coord.on_button(BUTTON_A, True)
    assert coord.active

    coord.on_manual_input()
    assert not coord.active


def test_manual_input_when_inactive_is_noop() -> None:
    coord = _make_coordinator()
    coord.on_manual_input()  # should not raise
    assert not coord.active


def test_tick_with_detection_sets_steer_and_drive() -> None:
    coord = _make_coordinator()
    coord.on_button(BUTTON_A, True)

    # Place a person on the right side: center_x = 0.8, deviation = 0.6
    det = Detection(x=0.7, y=0.2, w=0.2, h=0.5, score=0.9)
    with coord.detector._lock:
        coord.detector._detections = [det]

    coord._tick()
    _, steer, _, _ = coord.desired_state.snapshot()
    drive, _, _, _ = coord.desired_state.snapshot()
    assert steer > 0  # person is right → steer right
    assert drive == 30.0


def test_tick_without_detection_stops() -> None:
    coord = _make_coordinator()
    coord.on_button(BUTTON_A, True)

    # Set some previous movement
    coord.desired_state.set_drive_percent(50.0)
    coord.desired_state.set_steer_percent(30.0)

    coord._tick()
    drive, steer, _, _ = coord.desired_state.snapshot()
    assert drive == 0.0
    assert steer == 0.0


def test_tick_picks_largest_detection() -> None:
    coord = _make_coordinator()
    coord.on_button(BUTTON_A, True)

    small = Detection(x=0.1, y=0.1, w=0.05, h=0.05, score=0.9)
    large = Detection(x=0.2, y=0.2, w=0.4, h=0.6, score=0.8)
    with coord.detector._lock:
        coord.detector._detections = [small, large]

    coord._tick()
    # Large detection center_x = 0.2 + 0.4/2 = 0.4, deviation = (0.4 - 0.5)*2 = -0.2
    _, steer, _, _ = coord.desired_state.snapshot()
    assert steer < 0  # person is slightly left
