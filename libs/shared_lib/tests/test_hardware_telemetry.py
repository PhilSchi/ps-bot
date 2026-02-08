from unittest.mock import patch

from shared_lib.drive_state import DesiredDriveState
from shared_lib.hardware.telemetry import BaseTelemetry


def test_base_telemetry_returns_drive_state_values() -> None:
    drive_state = DesiredDriveState()
    drive_state.drive = 50.0
    drive_state.steer = -25.0
    drive_state.pan = 10.0
    drive_state.tilt = -5.0

    telemetry = BaseTelemetry(drive_state)
    data = telemetry.get_telemetry()

    assert data["speed"] == 50.0
    assert data["steering"] == -25.0
    assert data["pan"] == 10.0
    assert data["tilt"] == -5.0
    assert data["battery_v"] == 0.0  # Base returns 0


def test_base_telemetry_reads_cpu_temp() -> None:
    drive_state = DesiredDriveState()
    telemetry = BaseTelemetry(drive_state)

    mock_temp = "45000"  # 45.0 degrees
    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = mock_temp

        # Call the protected method directly for testing
        temp = telemetry._read_cpu_temp()

        assert temp == 45.0


def test_base_telemetry_handles_missing_cpu_temp() -> None:
    drive_state = DesiredDriveState()
    telemetry = BaseTelemetry(drive_state)

    with patch("builtins.open", side_effect=OSError("File not found")):
        temp = telemetry._read_cpu_temp()
        assert temp == 0.0
