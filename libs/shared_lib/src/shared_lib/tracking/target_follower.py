"""Generic target follower that converts a deviation into steer/drive commands."""

from __future__ import annotations

from dataclasses import dataclass

from shared_lib.pid import PIDController


@dataclass
class TargetFollower:
    pid: PIDController
    drive_speed: float = 30.0

    def update(self, deviation: float) -> tuple[float, float]:
        """Compute (steer%, drive%) from a deviation in [-1, +1].

        *deviation* < 0 means target is left, > 0 means right.
        Returns clamped steer in [-100, 100] and constant drive speed.
        """
        raw_steer = self.pid.update(deviation)
        steer = max(-100.0, min(100.0, raw_steer))
        return steer, self.drive_speed

    def reset(self) -> None:
        self.pid.reset()
