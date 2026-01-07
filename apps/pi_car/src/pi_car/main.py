from __future__ import annotations

import argparse

from shared_lib.hardware import MyServo, PicarxChassis, PicarxMotor
from shared_lib.networking.robot_server import RobotSocketServer

from pi_car.controller import PiCarController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pi car controller server")
    parser.add_argument("--host", default="0.0.0.0", help="Server bind host")
    parser.add_argument("--port", type=int, default=9999, help="Server bind port")
    return parser


def build_chassis() -> PicarxChassis:
    steering_servo = MyServo(
        {
            "channel": "P2",
            "min_angle": -30.0,
            "max_angle": 30.0,
            "zero_angle": 0.0,
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
    controller = PiCarController(chassis)
    server = RobotSocketServer(args.host, args.port, on_axis=controller.on_axis)

    print(
        "Pi car server listening on "
        f"{args.host}:{args.port} (drive axis=3, steer axis=4)"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()


if __name__ == "__main__":
    main()
