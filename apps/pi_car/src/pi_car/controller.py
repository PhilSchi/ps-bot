from __future__ import annotations

from dataclasses import dataclass

from shared_lib.hardware import PicarxChassis

DRIVE_AXIS = 4
STEER_AXIS = 3


@dataclass
class PiCarController:
    chassis: PicarxChassis
    drive_axis: int = DRIVE_AXIS
    steer_axis: int = STEER_AXIS

    def on_axis(self, index: int, value: float) -> None:
        if index == self.drive_axis:
            self.chassis.set_drive_percent(_scale_axis(value))
        elif index == self.steer_axis:
            self.chassis.set_steering_percent(_scale_axis(value))


def _scale_axis(value: float) -> float:
    percent = -value * 100.0
    if percent < -100.0:
        return -100.0
    if percent > 100.0:
        return 100.0
    return percent
