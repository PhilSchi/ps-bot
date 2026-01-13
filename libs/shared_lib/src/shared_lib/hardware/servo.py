from __future__ import annotations

from typing import Protocol


class Servo(Protocol):
    def set_percent(self, percent: float) -> None:
        ...

    def set_angle(self, angle: float) -> None:
        ...
