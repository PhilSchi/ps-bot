from __future__ import annotations

from dataclasses import dataclass, field
import math
import threading

DRIVE_AXIS = 4
STEER_AXIS = 3
PAN_AXIS = 0
TILT_AXIS = 1


@dataclass
class DesiredDriveState:
    drive: float = 0.0
    steer: float = 0.0
    pan: float = 0.0
    tilt: float = 0.0
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

    def set_pan_percent(self, percent: float) -> None:
        with self._lock:
            self.pan = _clamp_percent(percent)

    def set_tilt_percent(self, percent: float) -> None:
        with self._lock:
            self.tilt = _clamp_percent(percent)

    def snapshot(self) -> tuple[float, float, float, float]:
        with self._lock:
            return self.drive, self.steer, self.pan, self.tilt


@dataclass
class DesiredStateUpdater:
    desired_state: DesiredDriveState
    drive_axis: int = DRIVE_AXIS
    steer_axis: int = STEER_AXIS
    pan_axis: int = PAN_AXIS
    tilt_axis: int = TILT_AXIS

    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _raw_drive: float = 0.0
    _raw_steer: float = 0.0
    _raw_pan: float = 0.0
    _raw_tilt: float = 0.0

    def on_axis(self, index: int, value: float) -> None:
        # optional: kleine Deadzone gegen Zittern
        if abs(value) < 0.05:
            value = 0.0

        with self._lock:
            if index == self.drive_axis:
                self._raw_drive = -value  # dein Vorzeichen beibehalten
            elif index == self.steer_axis:
                self._raw_steer = value
            elif index == self.pan_axis:
                self._raw_pan = value
            elif index == self.tilt_axis:
                self._raw_tilt = value
            else:
                return

            drive = self._raw_drive
            steer = self._raw_steer
            pan = self._raw_pan
            tilt = self._raw_tilt

        self.desired_state.set_drive_percent(scale_axis(drive))
        self.desired_state.set_steer_percent(scale_axis(steer))
        self.desired_state.set_pan_percent(scale_axis(-pan))
        self.desired_state.set_tilt_percent(scale_axis(-tilt))


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


__all__ = ["DesiredDriveState", "DesiredStateUpdater"]
