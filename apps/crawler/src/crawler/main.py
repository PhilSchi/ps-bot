from __future__ import annotations

import argparse
import threading

from shared_lib.drive_state import DesiredDriveState, DesiredStateUpdater
from shared_lib.hardware import FusionMotor, FusionServo, FusionTelemetry, SingleMotorChassis, VilibCameraServer
from shared_lib.networking import RobotSocketServer, TelemetryStreamer

from crawler.controller import CrawlerController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawler controller server")
    parser.add_argument("--host", default="0.0.0.0", help="Server bind host")
    parser.add_argument("--port", type=int, default=9999, help="Server bind port")
    parser.add_argument(
        "--no-camera",
        action="store_true",
        help="Disable the camera streaming thread",
    )
    parser.add_argument(
        "--no-telemetry",
        action="store_true",
        help="Disable telemetry streaming to connected client",
    )
    return parser


def build_chassis() -> SingleMotorChassis:
    steering_servo = FusionServo(
        {
            "channel": 0,
            "min_angle": -40.0,
            "max_angle": 40.0,
            "zero_angle": 8.0,
            "name": "steering-servo",
            "reverse": True
        }
    )
    drive_motor = FusionMotor(
        {
            "motor": "M0",
            "name": "drive",
            "factor": -0.5,
        }
    )
    return SingleMotorChassis(steering_servo, drive_motor)


def main() -> None:
    args = build_parser().parse_args()

    chassis = build_chassis()
    desired_state = DesiredDriveState()
    controller = CrawlerController(chassis, desired_state)
    updater = DesiredStateUpdater(desired_state)
    server = RobotSocketServer(args.host, args.port, on_axis=updater.on_axis)
    camera = VilibCameraServer(vflip=True, hflip=True)

    telemetry_streamer: TelemetryStreamer | None = None
    if not args.no_telemetry:
        telemetry_source = FusionTelemetry(desired_state)
        telemetry_streamer = TelemetryStreamer(
            server=server,
            source=telemetry_source,
            rate_hz=5.0,
        )

    print(
        "Crawler server listening on "
        f"{args.host}:{args.port} (drive axis=4, steer axis=3)"
    )
    if telemetry_streamer:
        print("Telemetry streaming enabled at 5 Hz")
    server_thread = threading.Thread(
        target=server.serve_forever,
        name="robot-socket-server",
    )
    controller_thread = threading.Thread(
        target=controller.serve_forever,
        name="crawler-controller",
    )
    server_thread.start()
    controller_thread.start()
    camera_thread: threading.Thread | None = None
    if not args.no_camera:
        camera_thread = threading.Thread(
            target=camera.serve_forever,
            name="crawler-camera",
        )
        camera_thread.start()
    if telemetry_streamer:
        telemetry_streamer.start()

    try:
        threads = [server_thread, controller_thread]
        if camera_thread is not None:
            threads.append(camera_thread)
        while all(thread.is_alive() for thread in threads):
            for thread in threads:
                thread.join(timeout=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        controller.stop()
        camera.stop()
        if telemetry_streamer:
            telemetry_streamer.stop()
        server_thread.join()
        controller_thread.join()
        if camera_thread is not None:
            camera_thread.join()
        chassis.stop()


if __name__ == "__main__":
    main()
