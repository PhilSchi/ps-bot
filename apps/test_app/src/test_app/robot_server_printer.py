from __future__ import annotations

from dataclasses import dataclass

from shared_lib.networking.robot_server import RobotSocketServer


@dataclass
class RobotServerPrinter:
    host: str = "0.0.0.0"
    port: int = 9999

    def __post_init__(self) -> None:
        self._server = RobotSocketServer(
            self.host,
            self.port,
            on_axis=self.on_axis,
            on_button=self.on_button,
            on_hat=self.on_hat,
        )

    def serve_forever(self) -> None:
        self._server.start()
        self._server.serve_forever()

    def stop(self) -> None:
        self._server.stop()

    def on_axis(self, index: int, value: float) -> None:
        print(f"Axis {index}: {value:.3f}")

    def on_button(self, index: int, pressed: bool) -> None:
        print(f"Button {index}: {'pressed' if pressed else 'released'}")

    def on_hat(self, index: int, value: tuple[int, int]) -> None:
        print(f"Hat {index}: {value}")
