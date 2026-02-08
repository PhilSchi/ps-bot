"""TCP client for streaming controller data to a robot server."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import socket
import threading

from .protocol import (
    TELEMETRY_STRUCT,
    TYPE_TELEMETRY,
    TelemetryData,
    decode_telemetry,
    encode_axis,
    encode_button,
    encode_hat,
)


@dataclass
class RobotSocketClient:
    host: str
    port: int
    connect_timeout: float = 3.0
    on_telemetry: Callable[[TelemetryData], None] | None = None

    _socket: socket.socket | None = None
    _recv_thread: threading.Thread | None = field(default=None, repr=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, repr=False)

    def connect(self) -> None:
        if self._socket is not None:
            return

        sock = socket.create_connection((self.host, self.port), self.connect_timeout)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._socket = sock

    def start_receiving(self) -> None:
        """Start a daemon thread that reads telemetry frames from the socket."""
        if self._socket is None:
            return
        self._stop_event.clear()
        self._socket.settimeout(1.0)
        thread = threading.Thread(target=self._receive_loop, daemon=True)
        thread.start()
        self._recv_thread = thread

    def send_axis(self, axis: int, value: float) -> None:
        self._send(encode_axis(axis, value))

    def send_button(self, button: int, pressed: bool) -> None:
        self._send(encode_button(button, pressed))

    def send_hat(self, hat: int, value: tuple[int, int]) -> None:
        self._send(encode_hat(hat, value))

    def close(self) -> None:
        self._stop_event.set()
        if self._recv_thread is not None:
            self._recv_thread.join(timeout=2.0)
            self._recv_thread = None
        if self._socket is None:
            return
        try:
            self._socket.close()
        finally:
            self._socket = None

    def _send(self, payload: bytes) -> None:
        if self._socket is None:
            self.connect()
        assert self._socket is not None
        self._socket.sendall(payload)

    def _receive_loop(self) -> None:
        buf = bytearray()
        while not self._stop_event.is_set():
            try:
                assert self._socket is not None
                chunk = self._socket.recv(1024)
                if not chunk:
                    break  # connection closed
                buf.extend(chunk)
            except socket.timeout:
                continue
            except OSError:
                break

            while len(buf) >= TELEMETRY_STRUCT.size:
                if buf[0] == TYPE_TELEMETRY:
                    td = decode_telemetry(bytes(buf[: TELEMETRY_STRUCT.size]))
                    if td is not None and self.on_telemetry is not None:
                        self.on_telemetry(td)
                    del buf[: TELEMETRY_STRUCT.size]
                else:
                    del buf[:1]  # skip unknown byte
