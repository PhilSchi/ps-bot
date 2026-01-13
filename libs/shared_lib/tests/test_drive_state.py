from shared_lib.drive_state import DesiredDriveState, DesiredStateUpdater


def test_desired_drive_state_clamps_and_snapshots() -> None:
    state = DesiredDriveState()

    state.set_drive_percent(150)
    state.set_steer_percent(-150)
    state.set_pan_percent(12.5)
    state.set_tilt_percent(-12.5)

    assert state.snapshot() == (100.0, -100.0, 12.5, -12.5)


def test_desired_state_updater_updates_axes_with_scaling() -> None:
    state = DesiredDriveState()
    updater = DesiredStateUpdater(state)

    updater.on_axis(4, 0.5)
    assert state.snapshot() == (-50.0, 0.0, 0.0, 0.0)

    updater.on_axis(3, 0.75)
    assert state.snapshot() == (-50.0, 75.0, 0.0, 0.0)

    updater.on_axis(0, 1.0)
    assert state.snapshot() == (-50.0, 75.0, -100.0, 0.0)

    updater.on_axis(1, -1.0)
    assert state.snapshot() == (-50.0, 75.0, -100.0, 100.0)


def test_desired_state_updater_deadzone_zeroes_small_input() -> None:
    state = DesiredDriveState()
    updater = DesiredStateUpdater(state)

    updater.on_axis(4, 0.04)
    assert state.snapshot() == (0.0, 0.0, 0.0, 0.0)
