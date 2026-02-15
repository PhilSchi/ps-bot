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
    class_name: str = "person"


@dataclass
class PersonDetector:
    """Camera module that polls Vilib object detection.

    Only classes listed in *allowed_classes* are kept — both for the
    data exposed via :attr:`detections` and for the bounding-box overlay
    drawn into the video stream.  Everything else is suppressed.

    Uses EfficientDet-Lite0 (via tflite_runtime) instead of Vilib's
    built-in model for better accuracy.  Replaces ``Vilib.object_detect_fuc``
    so Vilib's camera loop calls our inference automatically.

    After activation, a background thread reads detection results at
    *poll_hz* and exposes them thread-safely via :attr:`detected` and
    :attr:`detections`.
    """

    desired_state: DesiredDriveState | None = None
    poll_hz: float = 10.0
    allowed_classes: frozenset[str] = frozenset({"person"})
    min_score: float = 0.5

    _vilib: Any | None = field(default=None, init=False, repr=False)
    _efficientdet: Any | None = field(default=None, init=False, repr=False)
    _orig_detect_fuc: Any | None = field(default=None, init=False, repr=False)
    _stop_event: threading.Event = field(
        default_factory=threading.Event, init=False, repr=False
    )
    _thread: threading.Thread | None = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _detected: bool = field(default=False, init=False, repr=False)
    _detections: list[Detection] = field(default_factory=list, init=False, repr=False)
    _detection_list: list[dict] = field(default_factory=list, init=False, repr=False)

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

        # Build EfficientDetDetector and replace Vilib's detection function
        from .efficientdet_detector import EfficientDetDetector

        self._efficientdet = EfficientDetDetector()
        self._patch_detect_fuc(vilib)

        logger.info(
            "PersonDetector: EfficientDet-Lite0 active (classes=%s, min_score=%.2f)",
            self.allowed_classes,
            self.min_score,
        )
        self._thread = threading.Thread(
            target=self._poll_loop, name="person-detector", daemon=True
        )
        self._thread.start()

    def deactivate(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._restore_detect_fuc()
        self._efficientdet = None
        logger.info("PersonDetector: object detection disabled")

    # -- Vilib.object_detect_fuc replacement --

    def _patch_detect_fuc(self, vilib: Any) -> None:
        """Replace ``Vilib.object_detect_fuc`` with our EfficientDet pipeline."""
        self._orig_detect_fuc = vilib.object_detect_fuc

        detector = self._efficientdet
        allowed = self.allowed_classes
        min_score = self.min_score
        det_list = self._detection_list

        @staticmethod  # type: ignore[misc]
        def _replacement(img):
            try:
                detections = detector.detect(img, threshold=min_score)
                # Populate shared list for _read_detections()
                det_list.clear()
                for d in detections:
                    if d["class_name"] in allowed and d["score"] >= min_score:
                        det_list.append(d)
                # Draw only allowed detections onto frame
                img = detector.draw(img, detections, allowed, min_score)
            except Exception:
                logger.exception("EfficientDet inference failed")
                det_list.clear()
            return img

        vilib.object_detect_fuc = _replacement

    def _restore_detect_fuc(self) -> None:
        """Restore Vilib's original ``object_detect_fuc``."""
        if self._orig_detect_fuc is None:
            return
        vilib = self._vilib
        if vilib is not None:
            vilib.object_detect_fuc = self._orig_detect_fuc
        self._orig_detect_fuc = None

    # -- internal --

    def _poll_loop(self) -> None:
        interval = 1.0 / self.poll_hz
        while not self._stop_event.is_set():
            self._read_detections()
            self._stop_event.wait(interval)

    def _read_detections(self) -> None:
        matches: list[Detection] = []
        for item in list(self._detection_list):
            if not isinstance(item, dict):
                continue
            try:
                matches.append(self._parse(item))
            except (KeyError, TypeError, ValueError):
                continue

        with self._lock:
            self._detections = matches
            self._detected = len(matches) > 0

        if matches:
            logger.info("PersonDetector: %d object(s) detected", len(matches))

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
            class_name=item.get("class_name", ""),
        )
