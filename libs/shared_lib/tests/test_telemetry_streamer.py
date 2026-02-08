import socket
import struct
import threading
import time

from shared_lib.networking.robot_server import (
    RobotSocketServer,
    TELEMETRY_STRUCT,
    TYPE_TELEMETRY,
)
from shared_lib.networking.telemetry_streamer import TelemetryStreamer


class MockTelemetrySource:
    """Mock telemetry source for testing."""

    def __init__(self) -> None:
        self.speed = 50.0
        self.steering = -25.0
        self.pan = 10.0
        self.tilt = -5.0
        self.battery_v = 7.4
        self.cpu_temp = 45.0

    def get_telemetry(self) -> dict[str, float]:
        return {
            "speed": self.speed,
            "steering": self.steering,
            "pan": self.pan,
            "tilt": self.tilt,
            "battery_v": self.battery_v,
            "cpu_temp": self.cpu_temp,
        }


def test_telemetry_streamer_sends_over_tcp() -> None:
    server = RobotSocketServer("127.0.0.1", 0)
    server.start()
    assert server._socket is not None
    port = server._socket.getsockname()[1]

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    source = MockTelemetrySource()
    streamer = TelemetryStreamer(server=server, source=source, rate_hz=50.0)

    client = socket.create_connection(("127.0.0.1", port), timeout=2)
    client.settimeout(2.0)

    try:
        streamer.start()

        # Receive telemetry frame
        data = client.recv(TELEMETRY_STRUCT.size)
        assert len(data) == TELEMETRY_STRUCT.size

        # Decode and verify
        values = TELEMETRY_STRUCT.unpack(data)
        assert values[0] == TYPE_TELEMETRY
        assert abs(values[1] - 50.0) < 0.01  # speed
        assert abs(values[2] - (-25.0)) < 0.01  # steering
        assert abs(values[3] - 10.0) < 0.01  # pan
        assert abs(values[4] - (-5.0)) < 0.01  # tilt
        assert abs(values[5] - 7.4) < 0.01  # battery_v
        assert abs(values[6] - 45.0) < 0.01  # cpu_temp

    finally:
        streamer.stop()
        client.close()
        server.stop()
        server_thread.join(timeout=1.0)


def test_telemetry_streamer_only_sends_when_client_connected() -> None:
    server = RobotSocketServer("127.0.0.1", 0)
    server.start()

    source = MockTelemetrySource()
    streamer = TelemetryStreamer(server=server, source=source, rate_hz=50.0)

    streamer.start()
    time.sleep(0.1)  # Give it time to try sending

    # Should not crash when no client is connected
    assert not server.has_client

    streamer.stop()
    server.stop()
