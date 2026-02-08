"""Background MJPEG stream reader that provides frames as pygame Surfaces."""

from __future__ import annotations

import io
import threading
import time
from dataclasses import dataclass, field
from urllib.request import urlopen

import pygame


# JPEG markers
_SOI = b"\xff\xd8"
_EOI = b"\xff\xd9"
_MAX_FRAME_SIZE = 2 * 1024 * 1024  # 2 MB


@dataclass
class MjpegStream:
    """Reads an HTTP MJPEG stream in a background thread."""

    url: str
    reconnect_interval: float = 2.0

    _thread: threading.Thread | None = field(default=None, repr=False)
    _stop: threading.Event = field(default_factory=threading.Event, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _surface: pygame.Surface | None = field(default=None, repr=False)

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def get_frame(self) -> pygame.Surface | None:
        with self._lock:
            return self._surface

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                with urlopen(self.url, timeout=5) as resp:  # noqa: S310
                    self._read_stream(resp)
            except Exception:  # noqa: BLE001
                pass
            if not self._stop.is_set():
                self._stop.wait(self.reconnect_interval)

    def _read_stream(self, resp: object) -> None:
        buf = bytearray()
        while not self._stop.is_set():
            chunk = resp.read(4096)  # type: ignore[union-attr]
            if not chunk:
                break
            buf.extend(chunk)

            # Scan for complete JPEG frames
            while True:
                soi = buf.find(_SOI)
                if soi < 0:
                    buf.clear()
                    break
                if soi > 0:
                    del buf[:soi]

                eoi = buf.find(_EOI, 2)
                if eoi < 0:
                    # Incomplete frame — guard against runaway buffer
                    if len(buf) > _MAX_FRAME_SIZE:
                        buf.clear()
                    break

                jpeg_data = bytes(buf[: eoi + 2])
                del buf[: eoi + 2]

                surface = self._decode_jpeg(jpeg_data)
                if surface is not None:
                    with self._lock:
                        self._surface = surface

    @staticmethod
    def _decode_jpeg(data: bytes) -> pygame.Surface | None:
        try:
            return pygame.image.load(io.BytesIO(data))
        except Exception:  # noqa: BLE001
            return None
