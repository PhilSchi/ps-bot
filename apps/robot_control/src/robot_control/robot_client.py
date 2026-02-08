"""TCP client for streaming controller data to a robot server."""

from __future__ import annotations

from dataclasses import dataclass
import socket

from .protocol import encode_axis, encode_button, encode_hat


@dataclass
class RobotSocketClient:
    host: str
    port: int
    connect_timeout: float = 3.0

    _socket: socket.socket | None = None

    def connect(self) -> None:
        if self._socket is not None:
            return

        sock = socket.create_connection((self.host, self.port), self.connect_timeout)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._socket = sock

    def send_axis(self, axis: int, value: float) -> None:
        self._send(encode_axis(axis, value))

    def send_button(self, button: int, pressed: bool) -> None:
        self._send(encode_button(button, pressed))

    def send_hat(self, hat: int, value: tuple[int, int]) -> None:
        self._send(encode_hat(hat, value))

    def close(self) -> None:
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
