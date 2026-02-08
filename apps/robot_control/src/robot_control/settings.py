"""Simple settings persistence for host/port."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class AppSettings:
    host: str = "127.0.0.1"
    port: int = 9000

    @classmethod
    def load(cls, path: Path) -> "AppSettings":
        if not path.exists():
            return cls()

        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            return cls()

        host = data.get("host", cls().host)
        port = int(data.get("port", cls().port))
        return cls(host=host, port=port)

    def save(self, path: Path) -> None:
        payload = {"host": self.host, "port": self.port}
        path.write_text(json.dumps(payload, indent=2) + "\n")
