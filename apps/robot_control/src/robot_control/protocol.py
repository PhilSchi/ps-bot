"""Binary protocol for controller input frames."""

from __future__ import annotations

import struct

TYPE_BUTTON = 0
TYPE_AXIS = 1
TYPE_HAT = 2

AXIS_SCALE = 1000
FRAME_STRUCT = struct.Struct(">BBh")


def encode_axis(index: int, value: float) -> bytes:
    """Encode an axis value in the range [-1.0, 1.0] scaled by 1000."""
    axis_index = _validate_index(index)
    scaled = int(round(value * AXIS_SCALE))
    scaled = _clamp_int16(scaled)
    return FRAME_STRUCT.pack(TYPE_AXIS, axis_index, scaled)


def encode_button(index: int, pressed: bool) -> bytes:
    """Encode a button state as 0 or 1."""
    button_index = _validate_index(index)
    return FRAME_STRUCT.pack(TYPE_BUTTON, button_index, 1 if pressed else 0)


def encode_hat(index: int, value: tuple[int, int]) -> bytes:
    """Encode a hat value as a small integer from 0 to 8."""
    hat_index = _validate_index(index)
    x, y = value
    if x not in (-1, 0, 1) or y not in (-1, 0, 1):
        raise ValueError(f"Hat values must be -1, 0, or 1. Got: {value}")
    packed = (x + 1) * 3 + (y + 1)
    return FRAME_STRUCT.pack(TYPE_HAT, hat_index, packed)


def _validate_index(index: int) -> int:
    if not 0 <= index <= 255:
        raise ValueError(f"Index must be in range 0..255. Got: {index}")
    return index


def _clamp_int16(value: int) -> int:
    if value < -32768:
        return -32768
    if value > 32767:
        return 32767
    return value
