"""App entry point helpers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .controller import BluetoothGameController
from .protocol import TelemetryData
from .robot_client import RobotSocketClient
from .settings import AppSettings


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream controller input to a robot.")
    parser.add_argument("--host", help="Robot host (saved to settings).")
    parser.add_argument("--port", type=int, help="Robot port (saved to settings).")
    parser.add_argument(
        "--settings",
        default="settings.json",
        help="Path to settings file (default: settings.json).",
    )
    return parser.parse_args()


def _on_telemetry(data: TelemetryData) -> None:
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

    host = args.host or settings.host
    port = args.port if args.port is not None else settings.port

    if args.host is not None or args.port is not None:
        settings.host = host
        settings.port = port
        settings.save(settings_path)
        print(f"Saved settings to {settings_path}")

    client = RobotSocketClient(host, port, on_telemetry=_on_telemetry)
    try:
        client.connect()
    except OSError as exc:
        print(f"Socket error connecting to {host}:{port} -> {exc}")
        return

    client.start_receiving()

    controller = BluetoothGameController(print_events=False)
    controller.on_axis = client.send_axis
    controller.on_button = client.send_button
    controller.on_hat = client.send_hat

    try:
        controller.run()
    except RuntimeError as exc:
        print(f"\nController error: {exc}")
    finally:
        print()  # newline after \r output
        client.close()


if __name__ == "__main__":
    main()
