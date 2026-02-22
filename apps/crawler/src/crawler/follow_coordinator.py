"""Crawler-specific person-following orchestrator."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from shared_lib.detection.person_detector import PersonDetector
from shared_lib.drive_state import DesiredDriveState
from shared_lib.tracking import TargetFollower

BUTTON_A = 2


@dataclass
class PersonFollowCoordinator:
    detector: PersonDetector
    follower: TargetFollower
    desired_state: DesiredDriveState
    update_hz: float = 20.0

    _active: bool = field(default=False, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _stop_event: threading.Event = field(
        default_factory=threading.Event, init=False, repr=False
    )
    _thread: threading.Thread | None = field(default=None, init=False, repr=False)

    # -- public API --

    @property
    def active(self) -> bool:
        with self._lock:
            return self._active

    def on_button(self, index: int, pressed: bool) -> None:
        if index != BUTTON_A or not pressed:
            return
        with self._lock:
            self._active = not self._active
            now_active = self._active
        if now_active:
            print("Person following: ON")
        else:
            self.follower.reset()
            self.desired_state.set_drive_percent(0.0)
            self.desired_state.set_steer_percent(0.0)
            print("Person following: OFF")

    def on_manual_input(self) -> None:
        with self._lock:
            if not self._active:
                return
            self._active = False
        self.follower.reset()
        print("Person following: OFF (manual override)")

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, name="follow-coordinator", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    # -- internal --

    def _loop(self) -> None:
        interval = 1.0 / self.update_hz
        while not self._stop_event.is_set():
            self._tick()
            self._stop_event.wait(interval)

    def _tick(self) -> None:
        with self._lock:
            if not self._active:
                return

        detections = self.detector.detections
        if not detections:
            self.desired_state.set_drive_percent(0.0)
            self.desired_state.set_steer_percent(0.0)
            return

        # Pick the largest detection (by area)
        best = max(detections, key=lambda d: d.w * d.h)
        center_x = best.x + best.w / 2.0
        deviation = (center_x - 0.5) * 2.0

        steer, drive = self.follower.update(deviation)
        self.desired_state.set_steer_percent(steer)
        self.desired_state.set_drive_percent(drive)
