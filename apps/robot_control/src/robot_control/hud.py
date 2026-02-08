"""HUD overlay renderer for the robot control GUI."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from .protocol import TelemetryData

_COLOR_GREEN = pygame.Color(0, 230, 118)  # #00E676
_COLOR_LABEL = pygame.Color(160, 160, 160)
_COLOR_RED = pygame.Color(255, 82, 82)
_COLOR_BG = pygame.Color(30, 30, 30)
_COLOR_NO_VIDEO = pygame.Color(120, 120, 120)

_BAR_ALPHA = 180
_BAR_PAD_X = 18
_BAR_PAD_Y = 6
_FONT_SIZE = 18
_LOW_BATTERY_V = 6.5

_MONO_FONTS = ("menlo", "consolas", "dejavusansmono", "liberationmono", "monospace")


def _find_mono_font() -> str:
    available = {f.lower() for f in pygame.font.get_fonts()}
    for name in _MONO_FONTS:
        if name in available:
            return name
    return pygame.font.get_default_font()


@dataclass
class Hud:
    """Manages the pygame display window and draws HUD overlays."""

    width: int = 960
    height: int = 540

    _screen: pygame.Surface | None = field(default=None, repr=False)
    _font: pygame.font.Font | None = field(default=None, repr=False)

    def init(self) -> None:
        pygame.display.set_caption("Robot Control")
        self._screen = pygame.display.set_mode((self.width, self.height))
        pygame.font.init()
        font_name = _find_mono_font()
        self._font = pygame.font.SysFont(font_name, _FONT_SIZE)

    def render(
        self,
        frame: pygame.Surface | None,
        telemetry: TelemetryData | None,
    ) -> None:
        if self._screen is None or self._font is None:
            return

        if frame is not None:
            scaled = pygame.transform.scale(frame, (self.width, self.height))
            self._screen.blit(scaled, (0, 0))
        else:
            self._screen.fill(_COLOR_BG)
            label = self._font.render("NO VIDEO", True, _COLOR_NO_VIDEO)
            rect = label.get_rect(center=(self.width // 2, self.height // 2))
            self._screen.blit(label, rect)

        self._draw_bar(telemetry)
        pygame.display.flip()

    def close(self) -> None:
        pygame.display.quit()
        self._screen = None
        self._font = None

    # ------------------------------------------------------------------

    def _draw_bar(self, telemetry: TelemetryData | None) -> None:
        assert self._screen is not None and self._font is not None

        line_h = self._font.get_linesize()
        bar_h = line_h * 2 + _BAR_PAD_Y * 3
        bar_y = self.height - bar_h

        bar = pygame.Surface((self.width, bar_h), pygame.SRCALPHA)
        bar.fill((0, 0, 0, _BAR_ALPHA))

        col_w = self.width // 3

        if telemetry is not None:
            cells_row1 = [
                ("SPD", f"{telemetry.speed:6.1f}%", _COLOR_GREEN),
                ("STR", f"{telemetry.steering:6.1f}%", _COLOR_GREEN),
                (
                    "BAT",
                    f"{telemetry.battery_v:6.1f}V",
                    _COLOR_RED if telemetry.battery_v < _LOW_BATTERY_V else _COLOR_GREEN,
                ),
            ]
            cells_row2 = [
                ("PAN", f"{telemetry.pan:6.1f}%", _COLOR_GREEN),
                ("TLT", f"{telemetry.tilt:6.1f}%", _COLOR_GREEN),
                ("CPU", f"{telemetry.cpu_temp:6.1f}\u00b0C", _COLOR_GREEN),
            ]
        else:
            placeholder = "  --.-"
            cells_row1 = [
                ("SPD", f"{placeholder}%", _COLOR_GREEN),
                ("STR", f"{placeholder}%", _COLOR_GREEN),
                ("BAT", f"{placeholder}V", _COLOR_GREEN),
            ]
            cells_row2 = [
                ("PAN", f"{placeholder}%", _COLOR_GREEN),
                ("TLT", f"{placeholder}%", _COLOR_GREEN),
                ("CPU", f"{placeholder}\u00b0C", _COLOR_GREEN),
            ]

        y1 = _BAR_PAD_Y
        y2 = _BAR_PAD_Y + line_h + _BAR_PAD_Y

        for col, (label, value, color) in enumerate(cells_row1):
            x = col * col_w + _BAR_PAD_X
            self._render_cell(bar, x, y1, label, value, color)

        for col, (label, value, color) in enumerate(cells_row2):
            x = col * col_w + _BAR_PAD_X
            self._render_cell(bar, x, y2, label, value, color)

        self._screen.blit(bar, (0, bar_y))

    def _render_cell(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        label: str,
        value: str,
        color: pygame.Color,
    ) -> None:
        assert self._font is not None
        lbl = self._font.render(label, True, _COLOR_LABEL)
        val = self._font.render(value, True, color)
        surface.blit(lbl, (x, y))
        surface.blit(val, (x + lbl.get_width() + 6, y))
