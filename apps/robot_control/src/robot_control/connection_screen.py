"""Connection dialog for selecting host and port."""

from __future__ import annotations

from typing import NamedTuple

import pygame

# ── Colours ────────────────────────────────────────────────────────────

_BG = pygame.Color(30, 30, 30)
_FIELD_BG = pygame.Color(42, 42, 42)
_BORDER = pygame.Color(85, 85, 85)
_ACTIVE = pygame.Color(0, 230, 118)
_TEXT = pygame.Color(224, 224, 224)
_LABEL = pygame.Color(160, 160, 160)
_GREEN = pygame.Color(0, 230, 118)
_GREEN_DIM = pygame.Color(0, 200, 100)
_DARK = pygame.Color(30, 30, 30)
_DD_BG = pygame.Color(48, 48, 48)
_ERROR = pygame.Color(255, 82, 82)

# ── Layout constants ──────────────────────────────────────────────────

_FONT_SZ = 20
_TITLE_SZ = 28
_FIELD_H = 36
_FIELD_W = 380
_LABEL_W = 100
_GAP = 16
_DD_ITEM_H = 30
_MAX_DD = 6
_BTN_W = 180
_BTN_H = 42
_BLINK_MS = 530
_MONO = ("menlo", "consolas", "dejavusansmono", "liberationmono", "monospace")


# ── Public result type ────────────────────────────────────────────────


class ConnectionResult(NamedTuple):
    host: str
    port: int
    camera_port: int


# ── Helpers ───────────────────────────────────────────────────────────


def _mono_font() -> str:
    available = {f.lower() for f in pygame.font.get_fonts()}
    for n in _MONO:
        if n in available:
            return n
    return pygame.font.get_default_font()


def _clip_text() -> str:
    try:
        raw = pygame.scrap.get(pygame.SCRAP_TEXT)
        if raw:
            return raw.decode("utf-8", errors="ignore").rstrip("\x00")
    except Exception:  # noqa: BLE001
        pass
    return ""


# ── Text-field widget ─────────────────────────────────────────────────


class _Field:
    """Editable text field with dropdown suggestions."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        items: list[str],
        font: pygame.font.Font,
        *,
        digits_only: bool = False,
    ) -> None:
        self.rect = rect
        self.text = text
        self.items = items
        self.font = font
        self.digits_only = digits_only
        self.active = False
        self.cursor = len(text)
        self.dropdown = False
        self.hover = -1
        self._sel = False
        self._blink_on = True
        self._blink_t = 0

    # ── filtering ──

    def _matches(self) -> list[str]:
        if not self.text:
            return list(self.items)
        t = self.text.lower()
        return [s for s in self.items if t in s.lower()]

    def _dd_rect(self) -> pygame.Rect:
        n = min(len(self._matches()), _MAX_DD)
        return pygame.Rect(
            self.rect.x, self.rect.bottom + 2, self.rect.w, max(n, 0) * _DD_ITEM_H
        )

    # ── focus ──

    def focus(self) -> None:
        self.active = True
        self.dropdown = bool(self.items)
        self.hover = -1
        self._reset_blink()

    def blur(self) -> None:
        self.active = False
        self.dropdown = False
        self.hover = -1
        self._sel = False

    def _reset_blink(self) -> None:
        self._blink_on = True
        self._blink_t = pygame.time.get_ticks()

    # ── text input ──

    def insert(self, chars: str) -> None:
        if self.digits_only:
            chars = "".join(c for c in chars if c.isdigit())
        if not chars:
            return
        if self._sel:
            self.text = chars
            self.cursor = len(chars)
            self._sel = False
        else:
            self.text = self.text[: self.cursor] + chars + self.text[self.cursor :]
            self.cursor += len(chars)
        self.dropdown = bool(self.items)
        self._reset_blink()

    def handle_key(self, ev: pygame.event.Event) -> str | None:
        """Handle KEYDOWN.  Returns ``"submit"`` when Enter should submit."""
        ctrl = ev.mod & (pygame.KMOD_META | pygame.KMOD_CTRL)

        # Select-all
        if ev.key == pygame.K_a and ctrl:
            self._sel = True
            self.cursor = len(self.text)
            self._reset_blink()
            return None

        # While all-selected, first keystroke replaces / clears
        if self._sel:
            if ev.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                self.text = ""
                self.cursor = 0
                self._sel = False
                self.dropdown = bool(self.items)
                self._reset_blink()
                return None
            if ev.unicode and ev.unicode.isprintable():
                self._sel = False
                self.insert(ev.unicode)
                return None
            self._sel = False

        if ev.key == pygame.K_BACKSPACE:
            if self.cursor > 0:
                self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
                self.cursor -= 1
                self.dropdown = bool(self.items)
        elif ev.key == pygame.K_DELETE:
            if self.cursor < len(self.text):
                self.text = self.text[: self.cursor] + self.text[self.cursor + 1 :]
                self.dropdown = bool(self.items)
        elif ev.key == pygame.K_LEFT:
            self.cursor = max(0, self.cursor - 1)
        elif ev.key == pygame.K_RIGHT:
            self.cursor = min(len(self.text), self.cursor + 1)
        elif ev.key == pygame.K_HOME:
            self.cursor = 0
        elif ev.key == pygame.K_END:
            self.cursor = len(self.text)
        elif ev.key == pygame.K_DOWN and self.dropdown:
            m = self._matches()
            if m:
                self.hover = min(self.hover + 1, len(m) - 1)
        elif ev.key == pygame.K_UP and self.dropdown:
            self.hover = max(self.hover - 1, -1)
        elif ev.key == pygame.K_RETURN:
            if self.dropdown and self.hover >= 0:
                m = self._matches()
                if 0 <= self.hover < len(m):
                    self.text = m[self.hover]
                    self.cursor = len(self.text)
                    self.dropdown = False
                    self.hover = -1
                return None  # consumed — don't submit form
            return "submit"
        elif ev.unicode and ev.unicode.isprintable():
            self.insert(ev.unicode)

        self._reset_blink()
        return None

    def click_dropdown(self, pos: tuple[int, int]) -> bool:
        """Handle click inside dropdown.  Returns True if consumed."""
        if not self.dropdown:
            return False
        dr = self._dd_rect()
        if dr.w == 0 or not dr.collidepoint(pos):
            return False
        m = self._matches()
        idx = (pos[1] - dr.y) // _DD_ITEM_H
        if 0 <= idx < len(m):
            self.text = m[idx]
            self.cursor = len(self.text)
            self.dropdown = False
            self.hover = -1
        return True

    # ── tick / draw ──

    def update(self) -> None:
        if not self.active:
            return
        now = pygame.time.get_ticks()
        if now - self._blink_t >= _BLINK_MS:
            self._blink_on = not self._blink_on
            self._blink_t = now

    def draw(self, surf: pygame.Surface) -> None:
        # background + border
        pygame.draw.rect(surf, _FIELD_BG, self.rect, border_radius=4)
        border = _ACTIVE if self.active else _BORDER
        pygame.draw.rect(surf, border, self.rect, 2, border_radius=4)

        # selection highlight
        txt_surf = self.font.render(self.text, True, _TEXT)
        ty = self.rect.centery - txt_surf.get_height() // 2
        if self._sel and self.active:
            sw = min(txt_surf.get_width() + 4, self.rect.w - 28)
            sel = pygame.Surface((sw, self.rect.h - 8), pygame.SRCALPHA)
            sel.fill((0, 230, 118, 60))
            surf.blit(sel, (self.rect.x + 6, self.rect.y + 4))

        # text (clipped to field)
        clip = self.rect.inflate(-16, -4)
        old_clip = surf.get_clip()
        surf.set_clip(clip)
        surf.blit(txt_surf, (self.rect.x + 8, ty))
        surf.set_clip(old_clip)

        # cursor
        if self.active and self._blink_on and not self._sel:
            cx = self.rect.x + 8 + self.font.size(self.text[: self.cursor])[0]
            if self.rect.x + 6 <= cx <= self.rect.right - 22:
                pygame.draw.line(
                    surf, _GREEN, (cx, self.rect.y + 8), (cx, self.rect.bottom - 8), 2
                )

        # dropdown arrow
        arr = self.font.render("\u25be", True, _LABEL)
        surf.blit(
            arr, (self.rect.right - 20, self.rect.centery - arr.get_height() // 2)
        )

    def draw_dropdown(self, surf: pygame.Surface) -> None:
        if not self.dropdown or not self.active:
            return
        m = self._matches()
        if not m:
            return
        visible = m[:_MAX_DD]
        dr = self._dd_rect()
        pygame.draw.rect(surf, _DD_BG, dr, border_radius=4)
        pygame.draw.rect(surf, _BORDER, dr, 1, border_radius=4)
        mouse = pygame.mouse.get_pos()
        for i, item in enumerate(visible):
            ir = pygame.Rect(dr.x + 2, dr.y + i * _DD_ITEM_H + 1, dr.w - 4, _DD_ITEM_H - 1)
            is_hover = ir.collidepoint(mouse) or i == self.hover
            if is_hover:
                pygame.draw.rect(surf, _GREEN, ir, border_radius=3)
                t = self.font.render(item, True, _DARK)
            else:
                t = self.font.render(item, True, _TEXT)
            surf.blit(t, (ir.x + 8, ir.centery - t.get_height() // 2))


# ── Main screen function ─────────────────────────────────────────────


def show_connection_screen(
    width: int,
    height: int,
    host: str,
    port: int,
    camera_port: int,
    host_history: list[str],
    port_history: list[int],
    camera_port_history: list[int],
) -> ConnectionResult | None:
    """Show a connection dialog.  Returns chosen values or *None* on quit."""

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Robot Control")
    pygame.font.init()
    try:
        pygame.scrap.init()
    except Exception:  # noqa: BLE001
        pass

    font = pygame.font.SysFont(_mono_font(), _FONT_SZ)
    title_font = pygame.font.SysFont(_mono_font(), _TITLE_SZ)

    # ── layout ──
    form_w = _LABEL_W + _GAP + _FIELD_W
    form_x = (width - form_w) // 2
    field_x = form_x + _LABEL_W + _GAP
    title_y = height // 2 - 140
    base_y = title_y + 70
    row = _FIELD_H + _GAP

    port_strs = [str(p) for p in port_history]
    cam_strs = [str(p) for p in camera_port_history]

    fields = [
        _Field(
            pygame.Rect(field_x, base_y, _FIELD_W, _FIELD_H),
            host, host_history, font,
        ),
        _Field(
            pygame.Rect(field_x, base_y + row, _FIELD_W, _FIELD_H),
            str(port), port_strs, font, digits_only=True,
        ),
        _Field(
            pygame.Rect(field_x, base_y + 2 * row, _FIELD_W, _FIELD_H),
            str(camera_port), cam_strs, font, digits_only=True,
        ),
    ]
    labels = ["Host", "Port", "Camera"]
    fields[0].focus()

    btn_rect = pygame.Rect(
        (width - _BTN_W) // 2, base_y + 3 * row + 8, _BTN_W, _BTN_H
    )
    error = ""
    clock = pygame.time.Clock()

    # ── event loop ──
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return None

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return None

                # paste
                if ev.key == pygame.K_v and (
                    ev.mod & (pygame.KMOD_META | pygame.KMOD_CTRL)
                ):
                    active = next((f for f in fields if f.active), None)
                    if active:
                        clip = _clip_text()
                        if clip:
                            active.insert(clip)
                    continue

                # tab / shift-tab
                if ev.key == pygame.K_TAB:
                    idx = next((i for i, f in enumerate(fields) if f.active), -1)
                    if idx >= 0:
                        fields[idx].blur()
                    step = -1 if ev.mod & pygame.KMOD_SHIFT else 1
                    nxt = (idx + step) % len(fields)
                    fields[nxt].focus()
                    continue

                # forward to active field
                active = next((f for f in fields if f.active), None)
                if active:
                    action = active.handle_key(ev)
                    if action == "submit":
                        result = _validate(fields)
                        if isinstance(result, str):
                            error = result
                        else:
                            return result

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                pos = ev.pos
                # check open dropdowns first (z-order)
                dd_hit = False
                for f in fields:
                    if f.active and f.dropdown and f.click_dropdown(pos):
                        dd_hit = True
                        break
                if dd_hit:
                    continue

                # check fields
                focused = False
                for f in fields:
                    if f.rect.collidepoint(pos):
                        for other in fields:
                            other.blur()
                        f.focus()
                        focused = True
                        break

                if not focused:
                    # button click?
                    if btn_rect.collidepoint(pos):
                        result = _validate(fields)
                        if isinstance(result, str):
                            error = result
                        else:
                            return result
                    else:
                        for f in fields:
                            f.blur()

        # ── update ──
        for f in fields:
            f.update()

        # ── draw ──
        screen.fill(_BG)

        # title
        ts = title_font.render("Robot Control", True, _GREEN)
        screen.blit(ts, ts.get_rect(center=(width // 2, title_y)))

        # labels + fields
        for i, (lbl, fld) in enumerate(zip(labels, fields)):
            ly = base_y + i * row + (_FIELD_H - font.get_linesize()) // 2
            screen.blit(font.render(lbl, True, _LABEL), (form_x, ly))
            fld.draw(screen)

        # button
        mouse = pygame.mouse.get_pos()
        bc = _GREEN_DIM if btn_rect.collidepoint(mouse) else _GREEN
        pygame.draw.rect(screen, bc, btn_rect, border_radius=6)
        bl = font.render("Connect", True, _DARK)
        screen.blit(bl, bl.get_rect(center=btn_rect.center))

        # error
        if error:
            es = font.render(error, True, _ERROR)
            screen.blit(es, es.get_rect(center=(width // 2, btn_rect.bottom + 24)))

        # dropdowns on top
        for f in fields:
            f.draw_dropdown(screen)

        pygame.display.flip()
        clock.tick(30)


def _validate(fields: list[_Field]) -> ConnectionResult | str:
    host = fields[0].text.strip()
    if not host:
        return "Host cannot be empty"
    try:
        port = int(fields[1].text.strip())
    except ValueError:
        return "Invalid port number"
    if not 1 <= port <= 65535:
        return "Port must be 1\u201365535"
    try:
        cam = int(fields[2].text.strip())
    except ValueError:
        return "Invalid camera port"
    if not 1 <= cam <= 65535:
        return "Camera port must be 1\u201365535"
    return ConnectionResult(host, port, cam)
