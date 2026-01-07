"""TCP server for streaming controller data to a robot handler."""

from __future__ import annotations

from dataclasses import dataclass, field
import socket
import struct
import threading
from typing import Callable

TYPE_BUTTON = 0
TYPE_AXIS = 1
TYPE_HAT = 2

AXIS_SCALE = 1000
FRAME_STRUCT = struct.Struct(">BBh")

AxisHandler = Callable[[int, float], None]
ButtonHandler = Callable[[int, bool], None]
HatHandler = Callable[[int, tuple[int, int]], None]


@dataclass
class RobotSocketServer:
    host: str
    port: int
    on_axis: AxisHandler | None = None
    on_button: ButtonHandler | None = None
    on_hat: HatHandler | None = None
    backlog: int = 1
    recv_timeout: float = 0.5

    _socket: socket.socket | None = None
    _client: socket.socket | None = None
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False)

    def start(self) -> None:
        if self._socket is not None:
            return

        self._stop_event.clear()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(self.backlog)
        self._socket = sock

    def serve_forever(self) -> None:
        if self._socket is None:
            self.start()
        assert self._socket is not None

        while not self._stop_event.is_set():
            try:
                client, _ = self._socket.accept()
            except OSError:
                break

            self._client = client
            try:
                client.settimeout(self.recv_timeout)
                self._serve_client(client)
            finally:
                try:
                    client.close()
                finally:
                    self._client = None

    def stop(self) -> None:
        self._stop_event.set()

        client = self._client
        if client is not None:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                client.close()
            finally:
                if self._client is client:
                    self._client = None

        sock = self._socket
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            finally:
                if self._socket is sock:
                    self._socket = None

    def _serve_client(self, client: socket.socket) -> None:
        buffer = bytearray()
        frame_size = FRAME_STRUCT.size

        while not self._stop_event.is_set():
            try:
                chunk = client.recv(1024)
            except socket.timeout:
                continue

            if not chunk:
                break

            buffer.extend(chunk)
            while len(buffer) >= frame_size:
                frame = bytes(buffer[:frame_size])
                del buffer[:frame_size]
                self._handle_frame(frame)

    def _handle_frame(self, frame: bytes) -> None:
        msg_type, index, value = FRAME_STRUCT.unpack(frame)
        if msg_type == TYPE_AXIS:
            if self.on_axis is not None:
                self.on_axis(index, value / AXIS_SCALE)
            return
        if msg_type == TYPE_BUTTON:
            if self.on_button is not None:
                self.on_button(index, bool(value))
            return
        if msg_type == TYPE_HAT:
            if not 0 <= value <= 8:
                raise ValueError(f"Hat value must be in range 0..8. Got: {value}")
            x = value // 3 - 1
            y = value % 3 - 1
            if self.on_hat is not None:
                self.on_hat(index, (x, y))
            return
        raise ValueError(f"Unknown frame type: {msg_type}")
