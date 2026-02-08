import threading
import time

import pytest

from shared_lib.networking.telemetry_publisher import (
    TelemetryPublisher,
    TelemetryReceiver,
)


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


def test_telemetry_publisher_sends_to_receiver() -> None:
    received: list[dict[str, float]] = []
    received_event = threading.Event()

    def on_telemetry(data: dict[str, float]) -> None:
        received.append(data)
        received_event.set()

    receiver = TelemetryReceiver("127.0.0.1", 0, on_telemetry=on_telemetry)
    receiver.start()
    assert receiver.local_port is not None

    source = MockTelemetrySource()
    publisher = TelemetryPublisher(
        target_host="127.0.0.1",
        target_port=receiver.local_port,
        source=source,
        rate_hz=50.0,  # High rate for faster test
    )
    publisher.start()

    try:
        assert received_event.wait(timeout=2.0), "No telemetry received"
        assert len(received) >= 1

        data = received[0]
        assert data["speed"] == pytest.approx(50.0)
        assert data["steering"] == pytest.approx(-25.0)
        assert data["pan"] == pytest.approx(10.0)
        assert data["tilt"] == pytest.approx(-5.0)
        assert data["battery_v"] == pytest.approx(7.4)
        assert data["cpu_temp"] == pytest.approx(45.0)
    finally:
        publisher.stop()
        receiver.stop()


def test_telemetry_publisher_respects_rate() -> None:
    received: list[dict[str, float]] = []

    def on_telemetry(data: dict[str, float]) -> None:
        received.append(data)

    receiver = TelemetryReceiver("127.0.0.1", 0, on_telemetry=on_telemetry)
    receiver.start()
    assert receiver.local_port is not None

    source = MockTelemetrySource()
    publisher = TelemetryPublisher(
        target_host="127.0.0.1",
        target_port=receiver.local_port,
        source=source,
        rate_hz=10.0,  # 10 Hz = 100ms interval
    )
    publisher.start()

    try:
        time.sleep(0.55)  # Should get ~5-6 packets at 10 Hz
        count = len(received)
        assert 4 <= count <= 7, f"Expected 4-7 packets, got {count}"
    finally:
        publisher.stop()
        receiver.stop()


def test_telemetry_handles_missing_fields() -> None:
    received: list[dict[str, float]] = []
    received_event = threading.Event()

    def on_telemetry(data: dict[str, float]) -> None:
        received.append(data)
        received_event.set()

    class SparseSource:
        def get_telemetry(self) -> dict[str, float]:
            return {"speed": 42.0}  # Only speed, rest should default to 0

    receiver = TelemetryReceiver("127.0.0.1", 0, on_telemetry=on_telemetry)
    receiver.start()
    assert receiver.local_port is not None

    publisher = TelemetryPublisher(
        target_host="127.0.0.1",
        target_port=receiver.local_port,
        source=SparseSource(),
        rate_hz=50.0,
    )
    publisher.start()

    try:
        assert received_event.wait(timeout=2.0), "No telemetry received"
        data = received[0]
        assert data["speed"] == pytest.approx(42.0)
        assert data["steering"] == pytest.approx(0.0)
        assert data["battery_v"] == pytest.approx(0.0)
    finally:
        publisher.stop()
        receiver.stop()
