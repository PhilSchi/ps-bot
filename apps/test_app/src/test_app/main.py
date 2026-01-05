from __future__ import annotations

import argparse
import time

from shared_lib import format_greeting
from shared_lib.hardware import MyServo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test app that uses shared-lib")
    parser.add_argument("--name", default="there", help="Name to greet")
    return parser

def my_servo_test() -> None:
    servo0 = MyServo(
        {
            "channel": "P0",
            "min_angle": -90.0,
            "max_angle": 90.0,
            "zero_angle": 0.0,
            "name": "test-servo",
        }
    )
    servo0.set_percent(50.0)
    time.sleep(2)
    for pct in range(50, -51, -1):
        servo0.set_percent(float(pct))
        time.sleep(0.05)
    time.sleep(2)
    for pct in range(-100, 101, 2):
        servo0.set_percent(float(pct))
        time.sleep(0.02)
    time.sleep(2)
    servo0.set_percent(0.0)

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    print("?? Hallo ??")
    my_servo_test()
    message = format_greeting(args.name)
    print(message)


if __name__ == "__main__":
    main()
