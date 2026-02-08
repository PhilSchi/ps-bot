"""App entry point helpers."""

from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path

import pygame

from .connection_screen import show_connection_screen
from .controller import BluetoothGameController
from .hud import Hud
from .protocol import TelemetryData
from .robot_client import RobotSocketClient
from .settings import AppSettings
from .video_stream import MjpegStream

_DRIVE_AXIS = 4


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream controller input to a robot.")
    parser.add_argument("--host", help="Robot host (saved to settings).")
    parser.add_argument("--port", type=int, help="Robot port (saved to settings).")
    parser.add_argument(
        "--camera-port",
        type=int,
        help="Camera MJPEG stream port (saved to settings, default: 9000).",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Headless mode with terminal output (no video window).",
    )
    parser.add_argument(
        "--settings",
        default="settings.json",
        help="Path to settings file (default: settings.json).",
    )
    return parser.parse_args()


def _on_telemetry_stdout(data: TelemetryData) -> None:
    line = (
        f"Speed: {data.speed:5.1f}% | Steer: {data.steering:5.1f}% | "
        f"Pan: {data.pan:5.1f}% | Tilt: {data.tilt:5.1f}% | "
        f"Bat: {data.battery_v:4.1f}V | CPU: {data.cpu_temp:4.1f}\u00b0C"
    )
    sys.stdout.write(f"\r{line}")
    sys.stdout.flush()


def main() -> None:
    args = _parse_args()
    settings_path = Path(args.settings)
    settings = AppSettings.load(settings_path)

    port = args.port if args.port is not None else settings.port
    camera_port = args.camera_port if args.camera_port is not None else settings.camera_port

    # Persist any CLI overrides
    changed = False
    if args.host is not None:
        settings.host = args.host
        changed = True
    if args.port is not None:
        settings.port = port
        changed = True
    if args.camera_port is not None:
        settings.camera_port = camera_port
        changed = True
    if changed:
        settings.save(settings_path)
        print(f"Saved settings to {settings_path}")

    if args.no_gui:
        host = args.host or settings.host
        _run_headless(host, port)
    else:
        _run_gui(args.host, port, camera_port, settings, settings_path)


def _send_axis(client: RobotSocketClient, axis: int, value: float) -> None:
    if axis == _DRIVE_AXIS:
        value = -value
    client.send_axis(axis, value)


def _run_headless(host: str, port: int) -> None:
    client = RobotSocketClient(host, port, on_telemetry=_on_telemetry_stdout)
    try:
        client.connect()
    except OSError as exc:
        print(f"Socket error connecting to {host}:{port} -> {exc}")
        return

    client.start_receiving()

    controller = BluetoothGameController(print_events=False)
    controller.on_axis = lambda axis, val: _send_axis(client, axis, val)
    controller.on_button = client.send_button
    controller.on_hat = client.send_hat

    try:
        controller.run()
    except RuntimeError as exc:
        print(f"\nController error: {exc}")
    finally:
        print()  # newline after \r output
        client.close()


def _run_gui(
    cli_host: str | None,
    port: int,
    camera_port: int,
    settings: AppSettings,
    settings_path: Path,
) -> None:
    pygame.init()

    # If no --host on CLI, show connection screen first
    if cli_host is not None:
        host = cli_host
    else:
        result = show_connection_screen(
            960, 540,
            settings.host, port, camera_port,
            settings.host_history,
            settings.port_history,
            settings.camera_port_history,
        )
        if result is None:
            pygame.quit()
            return
        host, port, camera_port = result
        settings.host = host
        settings.port = port
        settings.camera_port = camera_port
        settings.add_to_history(host, port, camera_port)
        settings.save(settings_path)

    # Thread-safe telemetry storage
    telemetry_lock = threading.Lock()
    telemetry_data: list[TelemetryData | None] = [None]

    def _on_telemetry_gui(data: TelemetryData) -> None:
        with telemetry_lock:
            telemetry_data[0] = data

    client = RobotSocketClient(host, port, on_telemetry=_on_telemetry_gui)
    try:
        client.connect()
    except OSError as exc:
        print(f"Socket error connecting to {host}:{port} -> {exc}")
        pygame.quit()
        return

    client.start_receiving()

    video = MjpegStream(url=f"http://{host}:{camera_port}/mjpg")
    video.start()

    controller = BluetoothGameController(print_events=False)
    controller.on_axis = lambda axis, val: _send_axis(client, axis, val)
    controller.on_button = client.send_button
    controller.on_hat = client.send_hat

    try:
        controller.connect()
    except RuntimeError as exc:
        print(f"Controller error: {exc}")
        video.stop()
        client.close()
        pygame.quit()
        return

    hud = Hud()
    hud.init()

    clock = pygame.time.Clock()
    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            controller.poll()

            frame = video.get_frame()
            with telemetry_lock:
                telem = telemetry_data[0]

            hud.render(frame, telem)
            clock.tick(30)
    except KeyboardInterrupt:
        pass
    finally:
        video.stop()
        hud.close()
        controller.close()
        client.close()


if __name__ == "__main__":
    main()
