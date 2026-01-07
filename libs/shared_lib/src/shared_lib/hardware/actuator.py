from __future__ import annotations

from typing import Protocol


class Actuator(Protocol):
    def set_percent(self, percent: float) -> None:
        ...
