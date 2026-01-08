from __future__ import annotations

import argparse

from shared_lib.hardware import MyServo

HELP_TEXT = """Commands:
  + / -        nudge by the current step
  ++ / --      nudge by 5x the current step
  set <angle>  set absolute angle
  step <angle> change step size
  zero         set angle to 0
  show         show current angle
  help         show this help
  quit         exit and print the final angle
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Interactive servo zero finder",
    )
    parser.add_argument("--channel", help="Servo channel, e.g. P0")
    parser.add_argument(
        "--min-angle",
        type=float,
        default=-90.0,
        help="Minimum servo angle (default: -90)",
    )
    parser.add_argument(
        "--max-angle",
        type=float,
        default=90.0,
        help="Maximum servo angle (default: 90)",
    )
    parser.add_argument(
        "--start-angle",
        type=float,
        default=0.0,
        help="Starting angle (default: 0)",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=1.0,
        help="Step size in degrees (default: 1)",
    )
    parser.add_argument(
        "--name",
        default="zero-servo",
        help="Servo name for logging (default: zero-servo)",
    )
    return parser


def prompt_channel() -> str:
    while True:
        channel = input("Servo channel (e.g. P0): ").strip()
        if channel:
            return channel
        print("Channel is required.")


def format_angle(angle: float) -> str:
    return f"{angle:.2f}"


def print_banner(servo: MyServo, step: float, current_angle: float) -> None:
    print("Zero servo helper")
    print(
        f"Channel: {servo.channel}  Range: {servo.min_angle}..{servo.max_angle}"
        f"  Step: {step}"
    )
    print(HELP_TEXT)
    print(f"Angle: {format_angle(current_angle)}")


def interactive_loop(servo: MyServo, start_angle: float, step: float) -> float:
    if step <= 0.0:
        raise ValueError("step must be greater than zero")

    current_angle = float(start_angle)
    servo.set_angle(current_angle)
    print_banner(servo, step, current_angle)

    def set_angle(new_angle: float) -> None:
        nonlocal current_angle
        try:
            servo.set_angle(new_angle)
        except ValueError as exc:
            print(f"Angle rejected: {exc}")
            return
        current_angle = new_angle
        print(f"Angle: {format_angle(current_angle)}")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        command = line.lower()
        if command in {"q", "quit", "exit"}:
            break
        if command in {"h", "help", "?"}:
            print(HELP_TEXT)
            continue
        if command in {"s", "show"}:
            print(f"Angle: {format_angle(current_angle)}")
            continue
        if command in {"z", "zero"}:
            set_angle(0.0)
            continue

        if line in {"+", "-", "++", "--"}:
            multiplier = 5.0 if len(line) == 2 else 1.0
            delta = step * multiplier
            if line.startswith("-"):
                delta = -delta
            set_angle(current_angle + delta)
            continue

        parts = line.split()
        if len(parts) == 2 and parts[0].lower() in {"set", "angle"}:
            try:
                target = float(parts[1])
            except ValueError:
                print("Angle must be a number.")
                continue
            set_angle(target)
            continue

        if len(parts) == 2 and parts[0].lower() == "step":
            try:
                new_step = float(parts[1])
            except ValueError:
                print("Step must be a number.")
                continue
            if new_step <= 0.0:
                print("Step must be greater than zero.")
                continue
            step = new_step
            print(f"Step: {step}")
            continue

        if len(parts) == 1:
            try:
                target = float(parts[0])
            except ValueError:
                target = None
            if target is not None:
                set_angle(target)
                continue

        print("Unknown command. Type 'help' for options.")

    return current_angle


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.channel is None:
        args.channel = prompt_channel()

    if args.min_angle >= args.max_angle:
        parser.error("--min-angle must be less than --max-angle")
    if not (args.min_angle <= args.start_angle <= args.max_angle):
        parser.error("--start-angle must be between --min-angle and --max-angle")

    servo = MyServo(
        {
            "channel": args.channel,
            "min_angle": args.min_angle,
            "max_angle": args.max_angle,
            "zero_angle": args.start_angle,
            "name": args.name,
        }
    )

    final_angle = interactive_loop(servo, args.start_angle, args.step)
    print(f"Final angle: {format_angle(final_angle)}")
    print("Use this as your zero offset.")


if __name__ == "__main__":
    main()
