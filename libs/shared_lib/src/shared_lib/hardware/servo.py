from __future__ import annotations

from typing import Protocol


class Servo(Protocol):
    name: str
    channel: object
    min_angle: float
    max_angle: float
    zero_angle: float
    reverse: bool

    def percent_to_angle(self, percent: float) -> float:
        ...

    def set_percent(self, percent: float) -> None:
        ...

    def set_angle(self, angle: float) -> None:
        ...
