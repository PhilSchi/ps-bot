from __future__ import annotations

import os


def ensure_lgpio_pin_factory() -> None:
    if os.environ.get("GPIOZERO_PIN_FACTORY"):
        return
    try:
        import lgpio  # noqa: F401
    except Exception:
        return
    os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"
