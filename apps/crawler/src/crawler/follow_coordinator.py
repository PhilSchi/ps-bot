"""Crawler-specific person-following orchestrator."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from shared_lib.detection.person_detector import PersonDetector
from shared_lib.drive_state import DesiredDriveState
from shared_lib.tracking import PanTracker, TargetFollower

BUTTON_A = 2


@dataclass
class PersonFollowCoordinator:
    detector: PersonDetector
    pan_tracker: PanTracker
    follower: TargetFollower
    desired_state: DesiredDriveState
    base_drive_speed: float = 100.0
    drive_exponent: float = 1.0
    update_hz: float = 20.0
    scan_speed: float = 50.0

    _active: bool = field(default=False, init=False, repr=False)
    _scanning: bool = field(default=False, init=False, repr=False)
    _scan_position: float = field(default=0.0, init=False, repr=False)
    _scan_direction: float = field(default=1.0, init=False, repr=False)
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
            self._reset_scan()
            self.pan_tracker.reset()
            self.follower.reset()
            self.desired_state.set_drive_percent(0.0)
            self.desired_state.set_steer_percent(0.0)
            self.desired_state.set_pan_percent(0.0)
            print("Person following: OFF")

    def on_manual_input(self) -> None:
        with self._lock:
            if not self._active:
                return
            self._active = False
        self._reset_scan()
        self.pan_tracker.reset()
        self.follower.reset()
        self.desired_state.set_pan_percent(0.0)
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
            if not self._scanning:
                # Entering scan: start from current tracker position
                self._scan_position = self.pan_tracker._position
                self._scanning = True
            self._advance_scan()
            self.desired_state.set_pan_percent(self._scan_position)
            self.desired_state.set_drive_percent(0.0)
            self.desired_state.set_steer_percent(0.0)
            return

        if self._scanning:
            self.pan_tracker.reset(position=self._scan_position)
            self.follower.reset()
            self._reset_scan()

        # Pick the largest detection (by area)
        best = max(detections, key=lambda d: d.w * d.h)
        center_x = best.x + best.w / 2.0
        deviation = (0.5 - center_x) * 2.0

        # Stage 1: camera pan tracks person in image
        pan_percent = self.pan_tracker.update(deviation)
        self.desired_state.set_pan_percent(pan_percent)

        # Stage 2: steering follows camera direction
        steer, _ = self.follower.update(-pan_percent / 100.0)
        self.desired_state.set_steer_percent(steer)

        # Drive: reduce speed when camera is panned far
        drive = self.base_drive_speed * (1.0 - abs(pan_percent) / 100.0) ** self.drive_exponent
        self.desired_state.set_drive_percent(drive)

    def _advance_scan(self) -> None:
        step = self.scan_speed / self.update_hz * self._scan_direction
        self._scan_position += step
        if self._scan_position >= 100.0:
            self._scan_position = 100.0
            self._scan_direction = -1.0
        elif self._scan_position <= -100.0:
            self._scan_position = -100.0
            self._scan_direction = 1.0

    def _reset_scan(self) -> None:
        self._scan_position = 0.0
        self._scan_direction = 1.0
        self._scanning = False
