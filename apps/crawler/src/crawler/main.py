from __future__ import annotations

import argparse
import threading

from shared_lib.drive_state import DesiredDriveState, DesiredStateUpdater
from shared_lib.hardware import FusionMotor, FusionServo, SingleMotorChassis
from shared_lib.networking.robot_server import RobotSocketServer

from crawler.controller import CrawlerController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawler controller server")
    parser.add_argument("--host", default="0.0.0.0", help="Server bind host")
    parser.add_argument("--port", type=int, default=9999, help="Server bind port")
    return parser


def build_chassis() -> SingleMotorChassis:
    steering_servo = FusionServo(
        {
            "channel": 0,
            "min_angle": -15.0,
            "max_angle": 15.0,
            "zero_angle": 0.0,
            "name": "steering-servo",
        }
    )
    drive_motor = FusionMotor(
        {
            "motor": "M0",
            "name": "drive",
            "is_reversed": True
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

    print(
        "Crawler server listening on "
        f"{args.host}:{args.port} (drive axis=4, steer axis=3)"
    )
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

    try:
        threads = [server_thread, controller_thread]
        while all(thread.is_alive() for thread in threads):
            for thread in threads:
                thread.join(timeout=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        controller.stop()
        server_thread.join()
        controller_thread.join()
        chassis.stop()


if __name__ == "__main__":
    main()
