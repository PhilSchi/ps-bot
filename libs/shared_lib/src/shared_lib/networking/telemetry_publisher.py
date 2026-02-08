"""UDP publisher for streaming telemetry data to a remote receiver."""

from __future__ import annotations

from dataclasses import dataclass, field
import socket
import struct
import threading
import time
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from shared_lib.networking.robot_server import TelemetrySource

# Frame format: 6 floats (speed, steering, pan, tilt, battery_v, cpu_temp)
TELEMETRY_STRUCT = struct.Struct(">ffffff")

TelemetryCallback = Callable[[dict[str, float]], None]


@dataclass
class TelemetryPublisher:
    """Publishes telemetry data via UDP at a fixed rate."""

    target_host: str
    target_port: int
    source: TelemetrySource
    rate_hz: float = 5.0

    _socket: socket.socket | None = field(default=None, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False)

    def start(self) -> None:
        """Start publishing telemetry in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._thread = threading.Thread(target=self._publish_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the publisher and close the socket."""
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None

    def _publish_loop(self) -> None:
        interval = 1.0 / self.rate_hz
        target = (self.target_host, self.target_port)

        while not self._stop_event.is_set():
            start = time.monotonic()

            try:
                data = self.source.get_telemetry()
                frame = self._encode(data)
                if self._socket is not None:
                    self._socket.sendto(frame, target)
            except OSError:
                pass

            elapsed = time.monotonic() - start
            sleep_time = interval - elapsed
            if sleep_time > 0:
                self._stop_event.wait(sleep_time)

    def _encode(self, data: dict[str, float]) -> bytes:
        """Encode telemetry data to binary frame."""
        return TELEMETRY_STRUCT.pack(
            data.get("speed", 0.0),
            data.get("steering", 0.0),
            data.get("pan", 0.0),
            data.get("tilt", 0.0),
            data.get("battery_v", 0.0),
            data.get("cpu_temp", 0.0),
        )


@dataclass
class TelemetryReceiver:
    """Receives telemetry data via UDP."""

    host: str
    port: int
    on_telemetry: TelemetryCallback | None = None

    _socket: socket.socket | None = field(default=None, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False)

    def start(self) -> None:
        """Start receiving telemetry in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.settimeout(0.5)
        self._socket = sock

        self._thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the receiver and close the socket."""
        self._stop_event.set()

        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None

        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    @property
    def local_port(self) -> int | None:
        """Return the bound port, useful when binding to port 0."""
        if self._socket is None:
            return None
        return self._socket.getsockname()[1]

    def _receive_loop(self) -> None:
        while not self._stop_event.is_set():
            if self._socket is None:
                break

            try:
                data, _ = self._socket.recvfrom(TELEMETRY_STRUCT.size)
                if len(data) == TELEMETRY_STRUCT.size:
                    telemetry = self._decode(data)
                    if self.on_telemetry is not None:
                        self.on_telemetry(telemetry)
            except socket.timeout:
                continue
            except OSError:
                break

    def _decode(self, frame: bytes) -> dict[str, float]:
        """Decode binary frame to telemetry data."""
        values = TELEMETRY_STRUCT.unpack(frame)
        return {
            "speed": values[0],
            "steering": values[1],
            "pan": values[2],
            "tilt": values[3],
            "battery_v": values[4],
            "cpu_temp": values[5],
        }
