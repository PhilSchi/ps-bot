from __future__ import annotations

import argparse

from shared_lib import format_greeting


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test app that uses shared-lib")
    parser.add_argument("--name", default="there", help="Name to greet")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    print("?? Hallo ??")
    message = format_greeting(args.name)
    print(message)


if __name__ == "__main__":
    main()
