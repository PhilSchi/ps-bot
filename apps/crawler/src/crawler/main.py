from __future__ import annotations

import argparse
import threading

from shared_lib.detection import PersonDetector
from shared_lib.drive_state import DesiredDriveState, DesiredStateUpdater
from shared_lib.hardware import FusionMotor, FusionServo, FusionTelemetry, PanMount, SingleMotorChassis, VilibCameraServer
from shared_lib.networking import RobotSocketServer, TelemetryStreamer
from shared_lib.pid import PIDController
from shared_lib.tracking import TargetFollower

from crawler.controller import CrawlerController
from crawler.follow_coordinator import PersonFollowCoordinator


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


def build_pan_mount() -> PanMount:
    pan_servo = FusionServo(
        {
            "channel": 1,
            "min_angle": -60.0,
            "max_angle": 60.0,
            "zero_angle": 12.0,
            "name": "camera-pan",
        }
    )
    return PanMount(pan_servo)


def main() -> None:
    args = build_parser().parse_args()

    chassis = build_chassis()
    pan_mount = build_pan_mount()
    desired_state = DesiredDriveState()
    controller = CrawlerController(chassis, desired_state, pan_mount)
    detector = PersonDetector(desired_state=desired_state)

    pid = PIDController(kp=50.0, ki=3.0, kd=12.0, integral_limit=75.0)
    follower = TargetFollower(pid=pid, drive_speed=100.0)
    follow_coordinator = PersonFollowCoordinator(
        detector=detector,
        follower=follower,
        desired_state=desired_state,
    )

    updater = DesiredStateUpdater(
        desired_state, on_manual_input=follow_coordinator.on_manual_input
    )
    server = RobotSocketServer(
        args.host,
        args.port,
        on_axis=updater.on_axis,
        on_button=follow_coordinator.on_button,
    )
    camera = VilibCameraServer(vflip=True, hflip=True, modules=[detector])

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
    follow_coordinator.start()
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
        follow_coordinator.stop()
        server.stop()
        controller.stop()
        camera.stop()
        if telemetry_streamer:
            telemetry_streamer.stop()
        server_thread.join()
        controller_thread.join()
        if camera_thread is not None:
            camera_thread.join()
        pan_mount.center()
        chassis.stop()


if __name__ == "__main__":
    main()
