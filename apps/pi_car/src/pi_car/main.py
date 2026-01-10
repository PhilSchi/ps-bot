from __future__ import annotations

import argparse
import threading

from shared_lib.hardware import Gimbal, MyServo, PicarxChassis, PicarxMotor
from shared_lib.networking.robot_server import RobotSocketServer

from pi_car.camera import PiCarCameraServer
from pi_car.controller import DesiredDriveState, DesiredStateUpdater, PiCarController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pi car controller server")
    parser.add_argument("--host", default="0.0.0.0", help="Server bind host")
    parser.add_argument("--port", type=int, default=9999, help="Server bind port")
    parser.add_argument(
        "--no-camera",
        action="store_true",
        help="Disable the camera streaming thread",
    )
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


def build_gimbal() -> Gimbal:
    pan_servo = MyServo(
        {
            "channel": "P0",
            "min_angle": -90.0,
            "max_angle": 90.0,
            "zero_angle": 0.0,
            "name": "camera-pan-servo",
        }
    )
    tilt_servo = MyServo(
        {
            "channel": "P1",
            "min_angle": -35.0,
            "max_angle": 65.0,
            "zero_angle": 0.0,
            "name": "camera-tilt-servo",
        }
    )
    return Gimbal(pan_servo, tilt_servo)


def main() -> None:
    args = build_parser().parse_args()

    chassis = build_chassis()
    gimbal = build_gimbal()
    desired_state = DesiredDriveState()
    controller = PiCarController(chassis, desired_state, gimbal=gimbal)
    updater = DesiredStateUpdater(desired_state)
    server = RobotSocketServer(args.host, args.port, on_axis=updater.on_axis)
    camera = PiCarCameraServer(on_axis=updater.on_axis)

    print(
        "Pi car server listening on "
        f"{args.host}:{args.port} (drive axis=4, steer axis=3, pan axis=0, tilt axis=1)"
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
    camera_thread: threading.Thread | None = None
    if not args.no_camera:
        camera_thread = threading.Thread(
            target=camera.serve_forever,
            name="pi-car-camera",
        )
        camera_thread.start()

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
        server_thread.join()
        controller_thread.join()
        if camera_thread is not None:
            camera_thread.join()
        chassis.stop()
        gimbal.center()


if __name__ == "__main__":
    main()
