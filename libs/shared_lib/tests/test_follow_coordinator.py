from shared_lib.detection.person_detector import Detection, PersonDetector
from shared_lib.drive_state import DesiredDriveState
from shared_lib.pid import PIDController
from shared_lib.tracking import PanTracker, TargetFollower

from crawler.follow_coordinator import BUTTON_A, PersonFollowCoordinator


def _make_coordinator() -> PersonFollowCoordinator:
    desired = DesiredDriveState()
    detector = PersonDetector.__new__(PersonDetector)
    # Manually initialize minimal fields for testing
    import threading

    detector._lock = threading.Lock()
    detector._detected = False
    detector._detections = []
    camera_pid = PIDController(kp=50.0)
    pan_tracker = PanTracker(pid=camera_pid)
    steer_pid = PIDController(kp=50.0)
    follower = TargetFollower(pid=steer_pid)
    return PersonFollowCoordinator(
        detector=detector,
        pan_tracker=pan_tracker,
        follower=follower,
        desired_state=desired,
        base_drive_speed=100.0,
        drive_exponent=1.0,
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


def test_tick_with_detection_sets_pan_steer_drive() -> None:
    coord = _make_coordinator()
    coord.on_button(BUTTON_A, True)

    # Place a person on the right side: center_x = 0.8, deviation = 0.6
    det = Detection(x=0.7, y=0.2, w=0.2, h=0.5, score=0.9)
    with coord.detector._lock:
        coord.detector._detections = [det]

    coord._tick()
    drive, steer, pan, _ = coord.desired_state.snapshot()
    assert pan > 0  # person is right -> camera pans right
    assert steer > 0  # steering follows camera
    assert drive > 0  # drive forward (reduced by pan)
    assert drive < 100.0  # drive reduced because camera is panned


def test_tick_without_detection_stops() -> None:
    coord = _make_coordinator()
    coord.on_button(BUTTON_A, True)

    # Set some previous movement
    coord.desired_state.set_drive_percent(50.0)
    coord.desired_state.set_steer_percent(30.0)
    coord.desired_state.set_pan_percent(20.0)

    coord._tick()
    drive, steer, pan, _ = coord.desired_state.snapshot()
    assert drive == 0.0
    assert steer == 0.0
    assert pan == 0.0


def test_tick_picks_largest_detection() -> None:
    coord = _make_coordinator()
    coord.on_button(BUTTON_A, True)

    small = Detection(x=0.1, y=0.1, w=0.05, h=0.05, score=0.9)
    large = Detection(x=0.2, y=0.2, w=0.4, h=0.6, score=0.8)
    with coord.detector._lock:
        coord.detector._detections = [small, large]

    coord._tick()
    # Large detection center_x = 0.2 + 0.4/2 = 0.4, deviation = (0.4 - 0.5)*2 = -0.2
    _, _, pan, _ = coord.desired_state.snapshot()
    assert pan < 0  # person is slightly left


def test_deactivation_resets_pan() -> None:
    coord = _make_coordinator()
    coord.on_button(BUTTON_A, True)

    # Simulate some pan state
    coord.desired_state.set_pan_percent(50.0)

    coord.on_button(BUTTON_A, True)  # deactivate
    _, _, pan, _ = coord.desired_state.snapshot()
    assert pan == 0.0


def test_drive_full_when_pan_zero() -> None:
    coord = _make_coordinator()
    coord.on_button(BUTTON_A, True)

    # Person exactly centered: center_x = 0.5, deviation = 0.0
    det = Detection(x=0.4, y=0.2, w=0.2, h=0.5, score=0.9)
    with coord.detector._lock:
        coord.detector._detections = [det]

    coord._tick()
    drive, _, pan, _ = coord.desired_state.snapshot()
    assert pan == 0.0
    assert drive == 100.0  # full base speed when pan is 0
