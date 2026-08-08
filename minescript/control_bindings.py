from __future__ import annotations

from dataclasses import fields
from typing import Any

from .config import Keybinds


KEY_ACTIONS = {
    "w": "forward",
    "s": "back",
    "a": "left",
    "d": "right",
    "space": "jump",
    "shift": "sneak",
    "ctrl": "sprint",
    "f": "swap_hands",
    "e": "inventory",
    "1": "hotbar_1",
    "2": "hotbar_2",
    "3": "hotbar_3",
    "4": "hotbar_4",
    "5": "hotbar_5",
    "6": "hotbar_6",
    "7": "hotbar_7",
    "8": "hotbar_8",
    "9": "hotbar_9",
}

MOUSE_ACTIONS = {"left": "attack", "right": "use"}


def binding_names() -> tuple[str, ...]:
    return tuple(field.name for field in fields(Keybinds))


def normalize_binding(value: str) -> str:
    value = str(value or "").strip().lower()
    if not value:
        raise ValueError("Control bindings cannot be blank.")
    aliases = {
        "mouse1": "mouse:left",
        "mouse 1": "mouse:left",
        "lmb": "mouse:left",
        "left mouse": "mouse:left",
        "mouse2": "mouse:right",
        "mouse 2": "mouse:right",
        "rmb": "mouse:right",
        "right mouse": "mouse:right",
        "control": "ctrl",
    }
    return aliases.get(value, value)


class BoundInput:
    """Map canonical Minecraft actions onto the user's configured controls."""

    def __init__(self, backend: Any, keybinds: Keybinds):
        self.backend = backend
        self.keybinds = keybinds

    @property
    def capabilities(self):
        return getattr(self.backend, "capabilities", None)

    def _configured(self, action: str) -> str:
        return normalize_binding(getattr(self.keybinds, action))

    def _key_binding(self, name: str) -> str:
        raw = str(name)
        if raw.lower().startswith("raw:"):
            return normalize_binding(raw.split(":", 1)[1])
        action = KEY_ACTIONS.get(raw.lower())
        return self._configured(action) if action else normalize_binding(raw)

    def _mouse_binding(self, button: str) -> str:
        raw = str(button)
        if raw.lower().startswith("raw:"):
            return f"mouse:{raw.split(':', 1)[1].lower()}"
        action = MOUSE_ACTIONS.get(raw.lower())
        return self._configured(action) if action else f"mouse:{raw.lower()}"

    @staticmethod
    def _is_mouse(binding: str) -> bool:
        return binding.startswith("mouse:")

    @staticmethod
    def _mouse_name(binding: str) -> str:
        return binding.split(":", 1)[1]

    def _down(self, binding: str) -> None:
        if self._is_mouse(binding):
            self.backend.mouse_down(self._mouse_name(binding))
        else:
            self.backend.key_down(binding)

    def _up(self, binding: str) -> None:
        if self._is_mouse(binding):
            self.backend.mouse_up(self._mouse_name(binding))
        else:
            self.backend.key_up(binding)

    def key_down(self, name: str) -> None:
        self._down(self._key_binding(name))

    def key_up(self, name: str) -> None:
        self._up(self._key_binding(name))

    def mouse_down(self, button: str) -> None:
        self._down(self._mouse_binding(button))

    def mouse_up(self, button: str) -> None:
        self._up(self._mouse_binding(button))

    def tap(self, name: str, hold: float = 0.05) -> None:
        binding = self._key_binding(name)
        if self._is_mouse(binding):
            self.backend.click(self._mouse_name(binding), hold)
        else:
            self.backend.tap(binding, hold)

    def chord(self, *names: str, hold: float = 0.04) -> None:
        bindings = [self._key_binding(name) for name in names]
        if all(not self._is_mouse(binding) for binding in bindings):
            self.backend.chord(*bindings, hold=hold)
            return
        import time
        for binding in bindings:
            self._down(binding)
        time.sleep(hold)
        for binding in reversed(bindings):
            self._up(binding)

    def click(self, button: str, hold: float = 0.05) -> None:
        binding = self._mouse_binding(button)
        if self._is_mouse(binding):
            self.backend.click(self._mouse_name(binding), hold)
        else:
            self.backend.tap(binding, hold)

    def move_relative(self, dx: int, dy: int = 0):
        return self.backend.move_relative(dx, dy)

    def release_all(self) -> None:
        self.backend.release_all()
