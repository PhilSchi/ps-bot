from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time

from shared_lib.drive_state import DesiredDriveState
from shared_lib.hardware import Chassis, PanControl


@dataclass
class CrawlerController:
    chassis: Chassis
    desired_state: DesiredDriveState
    pan_mount: PanControl
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
        while not self._stop_event.is_set():
            drive, steer, pan, _ = self.desired_state.snapshot()
            if steer != last_steer:
                self.chassis.set_steering_percent(steer)
                last_steer = steer
            if drive != last_drive:
                self.chassis.set_drive_percent(drive)
                last_drive = drive
            if pan != last_pan:
                self.pan_mount.set_pan_percent(pan)
                last_pan = pan
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        self._stop_event.set()
