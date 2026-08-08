from __future__ import annotations
import threading
import time

try:
    from pynput import keyboard, mouse
    _PYNPUT_ERROR = None
except Exception as exc:  # Wayland/headless/permission failures must not kill the GUI import.
    keyboard = None
    mouse = None
    _PYNPUT_ERROR = exc


def pynput_available() -> bool:
    return keyboard is not None and mouse is not None


def pynput_error() -> str:
    return "" if _PYNPUT_ERROR is None else str(_PYNPUT_ERROR)


def _key_names():
    if keyboard is None:
        return {}
    return {
        "space": keyboard.Key.space,
        "shift": keyboard.Key.shift,
        "ctrl": keyboard.Key.ctrl,
        "alt": keyboard.Key.alt,
        "enter": keyboard.Key.enter,
        "tab": keyboard.Key.tab,
        "esc": keyboard.Key.esc,
        "f3": keyboard.Key.f3,
    }


class InputEngine:
    """Portable foreground input. Creation fails clearly if pynput has no OS backend."""
    def __init__(self):
        if not pynput_available():
            detail = pynput_error()
            raise RuntimeError(
                "The standard foreground input backend is unavailable on this desktop session."
                + (f" Details: {detail}" if detail else "")
            )
        self.keyboard = keyboard.Controller()
        self.mouse = mouse.Controller()
        self._held_keys: set = set()
        self._held_buttons: set = set()
        self._lock = threading.RLock()

    def _key(self, name: str):
        n = str(name).lower()
        names = _key_names()
        if n in names:
            return names[n]
        if n.startswith("f") and n[1:].isdigit():
            return getattr(keyboard.Key, n, n)
        return n

    def key_down(self, name: str):
        with self._lock:
            k = self._key(name); self.keyboard.press(k); self._held_keys.add(k)

    def key_up(self, name: str):
        with self._lock:
            k = self._key(name)
            try: self.keyboard.release(k)
            finally: self._held_keys.discard(k)

    def tap(self, name: str, hold: float = .05):
        self.key_down(name); time.sleep(hold); self.key_up(name)

    def chord(self, *names: str, hold: float = .04):
        keys = [self._key(n) for n in names]
        with self._lock:
            for k in keys:
                self.keyboard.press(k); self._held_keys.add(k)
        try: time.sleep(hold)
        finally:
            with self._lock:
                for k in reversed(keys):
                    try: self.keyboard.release(k)
                    finally: self._held_keys.discard(k)

    def mouse_down(self, button: str):
        b = mouse.Button.left if button.lower() == "left" else mouse.Button.right
        with self._lock: self.mouse.press(b); self._held_buttons.add(b)

    def mouse_up(self, button: str):
        b = mouse.Button.left if button.lower() == "left" else mouse.Button.right
        with self._lock:
            try: self.mouse.release(b)
            finally: self._held_buttons.discard(b)

    def click(self, button: str, hold: float = .05):
        self.mouse_down(button)
        try: time.sleep(hold)
        finally: self.mouse_up(button)

    def move_relative(self, dx: int, dy: int = 0):
        x, y = self.mouse.position; self.mouse.position = (x + dx, y + dy)

    def release_all(self):
        with self._lock:
            for b in list(self._held_buttons):
                try: self.mouse.release(b)
                except Exception: pass
            for k in list(self._held_keys):
                try: self.keyboard.release(k)
                except Exception: pass
            self._held_buttons.clear(); self._held_keys.clear()
