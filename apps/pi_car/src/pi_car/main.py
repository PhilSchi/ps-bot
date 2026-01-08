from __future__ import annotations

import argparse
import threading

from shared_lib.hardware import MyServo, PicarxChassis, PicarxMotor
from shared_lib.networking.robot_server import RobotSocketServer

from pi_car.controller import DesiredDriveState, DesiredStateUpdater, PiCarController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pi car controller server")
    parser.add_argument("--host", default="0.0.0.0", help="Server bind host")
    parser.add_argument("--port", type=int, default=9999, help="Server bind port")
    return parser


def build_chassis() -> PicarxChassis:
    steering_servo = MyServo(
        {
            "channel": "P2",
            "min_angle": -41.0,
            "max_angle": 19.0,
            "zero_angle": -11.0,
            "name": "steering-servo",
        }
    )
    left_motor = PicarxMotor(
        {
            "direction_pin": "D4",
            "pwm_pin": "P13",
            "forward_direction": 1,
            "name": "left-rear",
        }
    )
    right_motor = PicarxMotor(
        {
            "direction_pin": "D5",
            "pwm_pin": "P12",
            "forward_direction": -1,
            "name": "right-rear",
        }
    )
    return PicarxChassis(steering_servo, left_motor, right_motor)


def main() -> None:
    args = build_parser().parse_args()

    chassis = build_chassis()
    desired_state = DesiredDriveState()
    controller = PiCarController(chassis, desired_state)
    updater = DesiredStateUpdater(desired_state)
    server = RobotSocketServer(args.host, args.port, on_axis=updater.on_axis)

    print(
        "Pi car server listening on "
        f"{args.host}:{args.port} (drive axis=3, steer axis=4)"
    )
    server_thread = threading.Thread(
        target=server.serve_forever,
        name="robot-socket-server",
    )
    controller_thread = threading.Thread(
        target=controller.serve_forever,
        name="pi-car-controller",
    )
    server_thread.start()
    controller_thread.start()

    try:
        while server_thread.is_alive() and controller_thread.is_alive():
            server_thread.join(timeout=0.5)
            controller_thread.join(timeout=0.5)
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
