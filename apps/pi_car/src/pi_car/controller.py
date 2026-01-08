from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
import math

from shared_lib.hardware import PicarxChassis

DRIVE_AXIS = 4
STEER_AXIS = 3


@dataclass
class DesiredDriveState:
    drive: float = 0.0
    steer: float = 0.0
    _lock: threading.Lock = field(
        default_factory=threading.Lock,
        init=False,
        repr=False,
        compare=False,
    )

    def set_drive_percent(self, percent: float) -> None:
        with self._lock:
            self.drive = _clamp_percent(percent)

    def set_steer_percent(self, percent: float) -> None:
        with self._lock:
            self.steer = _clamp_percent(percent)

    def snapshot(self) -> tuple[float, float]:
        with self._lock:
            return self.drive, self.steer


@dataclass
class DesiredStateUpdater:
    desired_state: DesiredDriveState
    drive_axis: int = DRIVE_AXIS
    steer_axis: int = STEER_AXIS

    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _raw_drive: float = 0.0
    _raw_steer: float = 0.0

    def on_axis(self, index: int, value: float) -> None:
        # optional: kleine Deadzone gegen Zittern
        if abs(value) < 0.05:
            value = 0.0

        with self._lock:
            if index == self.drive_axis:
                self._raw_drive = -value  # dein Vorzeichen beibehalten
            elif index == self.steer_axis:
                self._raw_steer = value
            else:
                return

            steer, drive = circle_to_square(self._raw_steer, self._raw_drive)

        self.desired_state.set_drive_percent(scale_axis(drive))
        self.desired_state.set_steer_percent(scale_axis(steer))

@dataclass
class PiCarController:
    chassis: PicarxChassis
    desired_state: DesiredDriveState
    poll_interval: float = 0.02
    _stop_event: threading.Event = field(
        default_factory=threading.Event,
        init=False,
        repr=False,
        compare=False,
    )

    def serve_forever(self) -> None:
        self._stop_event.clear()
        last_drive: float | None = None
        last_steer: float | None = None
        while not self._stop_event.is_set():
            drive, steer = self.desired_state.snapshot()
            if steer != last_steer:
                self.chassis.set_steering_percent(steer)
                last_steer = steer
            if drive != last_drive:
                self.chassis.set_drive_percent(drive)
                last_drive = drive
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        self._stop_event.set()


def _clamp_percent(value: float) -> float:
    if value < -100.0:
        return -100.0
    if value > 100.0:
        return 100.0
    return value


def scale_axis(value: float) -> float:
    percent = value * 100.0
    return _clamp_percent(percent)

def circle_to_square(x: float, y: float) -> tuple[float, float]:
    r = math.hypot(x, y)  # 0..1
    if r < 1e-9:
        return 0.0, 0.0

    ux, uy = x / r, y / r
    m = max(abs(ux), abs(uy))  # zwischen ~0.707 und 1.0
    sx, sy = ux / m, uy / m    # Richtung auf "Quadrat-Rand" gebracht
    return sx * r, sy * r      # und wieder mit "wie weit gedrückt" skaliert