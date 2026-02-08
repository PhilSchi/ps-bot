"""Simple settings persistence for host/port."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

_MAX_HISTORY = 10


@dataclass
class AppSettings:
    host: str = "127.0.0.1"
    port: int = 9000
    camera_port: int = 9000
    host_history: list[str] = field(default_factory=list)
    port_history: list[int] = field(default_factory=list)
    camera_port_history: list[int] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "AppSettings":
        if not path.exists():
            return cls()

        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            return cls()

        defaults = cls()
        return cls(
            host=data.get("host", defaults.host),
            port=int(data.get("port", defaults.port)),
            camera_port=int(data.get("camera_port", defaults.camera_port)),
            host_history=list(data.get("host_history", [])),
            port_history=[int(p) for p in data.get("port_history", [])],
            camera_port_history=[int(p) for p in data.get("camera_port_history", [])],
        )

    def save(self, path: Path) -> None:
        payload = {
            "host": self.host,
            "port": self.port,
            "camera_port": self.camera_port,
            "host_history": self.host_history,
            "port_history": self.port_history,
            "camera_port_history": self.camera_port_history,
        }
        path.write_text(json.dumps(payload, indent=2) + "\n")

    def add_to_history(self, host: str, port: int, camera_port: int) -> None:
        """Record values in history (most recent first, capped)."""
        _push(self.host_history, host)
        _push(self.port_history, port)
        _push(self.camera_port_history, camera_port)


def _push(history: list, value: object) -> None:  # type: ignore[type-arg]
    if value in history:
        history.remove(value)
    history.insert(0, value)
    del history[_MAX_HISTORY:]
