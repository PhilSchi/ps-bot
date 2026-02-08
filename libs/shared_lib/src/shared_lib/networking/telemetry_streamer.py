"""Telemetry streamer that sends data over an existing RobotSocketServer connection."""

from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared_lib.networking.robot_server import RobotSocketServer, TelemetrySource


@dataclass
class TelemetryStreamer:
    """Streams telemetry data to connected clients via RobotSocketServer."""

    server: RobotSocketServer
    source: TelemetrySource
    rate_hz: float = 5.0

    _thread: threading.Thread | None = field(default=None, init=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False)

    def start(self) -> None:
        """Start streaming telemetry in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the telemetry streamer."""
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _stream_loop(self) -> None:
        interval = 1.0 / self.rate_hz

        while not self._stop_event.is_set():
            start = time.monotonic()

            if self.server.has_client:
                try:
                    data = self.source.get_telemetry()
                    self.server.send_telemetry(data)
                except Exception:
                    pass

            elapsed = time.monotonic() - start
            sleep_time = interval - elapsed
            if sleep_time > 0:
                self._stop_event.wait(sleep_time)
