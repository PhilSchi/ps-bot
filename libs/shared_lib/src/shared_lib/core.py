from __future__ import annotations


def format_greeting(name: str) -> str:
    cleaned = name.strip() or "there"
    return f"Hello, {cleaned}!"
