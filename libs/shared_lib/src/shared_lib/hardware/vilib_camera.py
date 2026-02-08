from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from typing import Any


@dataclass
class VilibCameraServer:
    """Manages camera streaming using SunFounder's Vilib library."""

    vflip: bool = False
    hflip: bool = False
    local_display: bool = False
    web_display: bool = True
    poll_interval: float = 0.5
    _stop_event: threading.Event = field(
        default_factory=threading.Event,
        init=False,
        repr=False,
        compare=False,
    )
    _vilib: Any | None = field(default=None, init=False, repr=False, compare=False)

    def _load_vilib(self) -> Any | None:
        try:
            from vilib import Vilib
        except Exception as exc:
            print(
                "Camera streaming disabled (missing Vilib/picamera2). "
                f"Install with: pip install git+https://github.com/sunfounder/vilib. "
                f"Error: {exc}"
            )
            return None
        return Vilib

    def serve_forever(self) -> None:
        self._stop_event.clear()
        vilib = self._load_vilib()
        if vilib is None:
            return
        self._vilib = vilib
        vilib.camera_start(vflip=self.vflip, hflip=self.hflip)
        vilib.display(local=self.local_display, web=self.web_display)

        while not self._stop_event.is_set():
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        self._stop_event.set()
        vilib = self._vilib
        if vilib is None:
            return
        for attr in ("camera_close", "camera_stop"):
            closer = getattr(vilib, attr, None)
            if callable(closer):
                closer()
                break
