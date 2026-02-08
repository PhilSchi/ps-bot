"""Bluetooth game controller input using pygame."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
import pygame
from pygame.joystick import JoystickType



@dataclass
class BluetoothGameController:
    """Connects to a game controller paired via OS Bluetooth and prints events."""

    joystick_index: int = 0
    deadzone: float = 0.1
    connect_timeout: float = 3.0
    poll_interval: float = 0.2
    calibration_samples: int = 20
    calibration_interval: float = 0.01
    axis_change_threshold: float = 0.05
    print_events: bool = True
    on_axis: Callable[[int, float], None] | None = None
    on_button: Callable[[int, bool], None] | None = None
    on_hat: Callable[[int, tuple[int, int]], None] | None = None

    _pygame: object | None = None
    _joystick: JoystickType | None = None
    _axis_zero: list[float] | None = None
    _axis_state: list[float] | None = None
    _button_state: list[int] | None = None
    _hat_state: list[tuple[int, int]] | None = None

    def connect(self) -> None:
        """Initialize pygame and connect to the controller at joystick_index."""

        pygame.init()
        pygame.joystick.init()

        print(f"pygame.joystick {pygame.joystick.get_count()}")

        deadline = time.monotonic() + self.connect_timeout
        count = pygame.joystick.get_count()
        while count <= self.joystick_index:
            pygame.event.pump()
            count = pygame.joystick.get_count()
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    f"No controller found (detected {count}). "
                    "Try reconnecting, press a button to wake it, or ensure "
                    "it is visible as a game controller."
                )
            pygame.time.wait(int(self.poll_interval * 1000))

        joystick = pygame.joystick.Joystick(self.joystick_index)
        joystick.init()

        self._pygame = pygame
        self._joystick = joystick
        self._axis_zero = self._calibrate_axes()
        self._initialize_state_cache()

        print(f"Connected to controller: {joystick.get_name()}")
        if self._axis_zero:
            rounded = [round(value, 3) for value in self._axis_zero]
            print(f"Axis centers: {rounded}")

    def poll(self) -> None:
        """Process one round of controller events (non-blocking)."""
        if self._pygame is None or self._joystick is None:
            self.connect()
        assert self._pygame is not None
        self._pygame.event.pump()
        self._poll_state()

    def run(self) -> None:
        """Print controller inputs until interrupted."""
        if self._pygame is None or self._joystick is None:
            self.connect()

        assert self._pygame is not None

        try:
            while True:
                self._pygame.event.pump()
                self._poll_state()
                self._pygame.time.wait(10)
        except KeyboardInterrupt:
            print("Controller loop stopped.")
        finally:
            self.close()

    def close(self) -> None:
        """Shutdown pygame and release the controller."""
        if self._joystick is not None:
            self._joystick.quit()
            self._joystick = None
        if self._pygame is not None:
            self._pygame.quit()
            self._pygame = None
        self._axis_zero = None
        self._axis_state = None
        self._button_state = None
        self._hat_state = None

    def _calibrate_axes(self) -> list[float]:
        if self._pygame is None or self._joystick is None:
            return []

        axis_count = self._joystick.get_numaxes()
        if axis_count == 0:
            return []

        sums = [0.0] * axis_count
        for _ in range(self.calibration_samples):
            self._pygame.event.pump()
            for index in range(axis_count):
                sums[index] += self._joystick.get_axis(index)
            self._pygame.time.wait(int(self.calibration_interval * 1000))

        return [value / self.calibration_samples for value in sums]

    def _initialize_state_cache(self) -> None:
        if self._joystick is None:
            return

        axis_count = self._joystick.get_numaxes()
        self._axis_state = []
        for axis in range(axis_count):
            raw = self._joystick.get_axis(axis)
            self._axis_state.append(self._normalize_axis(axis, raw))

        button_count = self._joystick.get_numbuttons()
        self._button_state = [
            self._joystick.get_button(index) for index in range(button_count)
        ]

        hat_count = self._joystick.get_numhats()
        self._hat_state = [self._joystick.get_hat(index) for index in range(hat_count)]

    def _normalize_axis(self, axis: int, raw: float) -> float:
        zero = 0.0
        if self._axis_zero and axis < len(self._axis_zero):
            zero = self._axis_zero[axis]
        centered = raw - zero
        if abs(centered) < self.deadzone:
            return 0.0
        return centered

    def _poll_state(self) -> None:
        if self._joystick is None:
            return
        if self._axis_state is None or self._button_state is None or self._hat_state is None:
            self._initialize_state_cache()
            if self._axis_state is None:
                return

        for axis in range(self._joystick.get_numaxes()):
            raw = self._joystick.get_axis(axis)
            value = self._normalize_axis(axis, raw)
            prev = self._axis_state[axis]
            if abs(value - prev) >= self.axis_change_threshold:
                self._axis_state[axis] = value
                if self.on_axis:
                    self.on_axis(axis, value)
                if self.print_events:
                    print(f"axis_motion: {axis} value={value:.3f} raw={raw:.3f}")

        for index in range(self._joystick.get_numbuttons()):
            pressed = self._joystick.get_button(index)
            prev = self._button_state[index]
            if pressed != prev:
                self._button_state[index] = pressed
                state = "button_down" if pressed else "button_up"
                if self.on_button:
                    self.on_button(index, bool(pressed))
                if self.print_events:
                    print(f"{state}: {index}")

        for index in range(self._joystick.get_numhats()):
            value = self._joystick.get_hat(index)
            prev = self._hat_state[index]
            if value != prev:
                self._hat_state[index] = value
                if self.on_hat:
                    self.on_hat(index, value)
                if self.print_events:
                    print(f"hat_motion: {index} value={value}")
