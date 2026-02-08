from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any

from shared_lib.drive_state import DesiredDriveState

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Detection:
    """A single detected object, coordinates normalized to 0.0–1.0."""

    x: float
    y: float
    w: float
    h: float
    score: float


@dataclass
class PersonDetector:
    """Camera module that polls Vilib object detection for persons.

    After activation, a background thread reads detection results at
    *poll_hz* and exposes them thread-safely via :attr:`detected` and
    :attr:`detections`.
    """

    desired_state: DesiredDriveState | None = None
    poll_hz: float = 10.0

    _vilib: Any | None = field(default=None, init=False, repr=False)
    _stop_event: threading.Event = field(
        default_factory=threading.Event, init=False, repr=False
    )
    _thread: threading.Thread | None = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _detected: bool = field(default=False, init=False, repr=False)
    _detections: list[Detection] = field(default_factory=list, init=False, repr=False)

    # -- public read API (thread-safe) --

    @property
    def detected(self) -> bool:
        with self._lock:
            return self._detected

    @property
    def detections(self) -> list[Detection]:
        with self._lock:
            return list(self._detections)

    # -- CameraModule protocol --

    def activate(self, vilib: Any) -> None:
        self._vilib = vilib
        self._stop_event.clear()
        vilib.object_detect_switch(True)
        logger.info("PersonDetector: object detection enabled")
        self._thread = threading.Thread(
            target=self._poll_loop, name="person-detector", daemon=True
        )
        self._thread.start()

    def deactivate(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        vilib = self._vilib
        if vilib is not None:
            vilib.object_detect_switch(False)
        logger.info("PersonDetector: object detection disabled")

    # -- internal --

    def _poll_loop(self) -> None:
        interval = 1.0 / self.poll_hz
        vilib = self._vilib
        while not self._stop_event.is_set():
            self._read_detections(vilib)
            self._stop_event.wait(interval)

    def _read_detections(self, vilib: Any) -> None:
        try:
            raw = vilib.object_detection_list_parameter
        except Exception:
            logger.debug("PersonDetector: failed to read detection list", exc_info=True)
            return

        persons: list[Detection] = []
        if isinstance(raw, dict):
            raw = [raw]
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                if item.get("class_name") != "person":
                    continue
                try:
                    persons.append(self._parse(item))
                except (KeyError, TypeError, ValueError):
                    continue

        with self._lock:
            self._detections = persons
            self._detected = len(persons) > 0

        if persons:
            logger.info("PersonDetector: %d person(s) detected", len(persons))

    @staticmethod
    def _parse(item: dict[str, Any]) -> Detection:
        x = int(item["x"])
        y = int(item["y"])
        w = int(item["w"])
        h = int(item["h"])
        score = float(item.get("score", item.get("confidence", 0.0)))

        img_w = int(item.get("img_width", 640))
        img_h = int(item.get("img_height", 480))

        return Detection(
            x=x / img_w,
            y=y / img_h,
            w=w / img_w,
            h=h / img_h,
            score=score,
        )
