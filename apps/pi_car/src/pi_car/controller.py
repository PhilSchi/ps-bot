from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time

from shared_lib.drive_state import DesiredDriveState
from shared_lib.hardware import GimbalControl, PicarxChassis

@dataclass
class PiCarController:
    chassis: PicarxChassis
    desired_state: DesiredDriveState
    gimbal: GimbalControl | None = None
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
        last_pan: float | None = None
        last_tilt: float | None = None
        while not self._stop_event.is_set():
            drive, steer, pan, tilt = self.desired_state.snapshot()
            if steer != last_steer:
                self.chassis.set_steering_percent(steer)
                last_steer = steer
            if drive != last_drive:
                self.chassis.set_drive_percent(drive)
                last_drive = drive
            if self.gimbal is not None:
                if pan != last_pan:
                    self.gimbal.set_pan_percent(pan)
                    last_pan = pan
                if tilt != last_tilt:
                    self.gimbal.set_tilt_percent(tilt)
                    last_tilt = tilt
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        self._stop_event.set()
