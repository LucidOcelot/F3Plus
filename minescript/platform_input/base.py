from __future__ import annotations
from dataclasses import dataclass
import time


@dataclass(frozen=True)
class InputCapabilities:
    name: str
    targeted_keyboard: bool = False
    targeted_mouse_buttons: bool = False
    targeted_relative_mouse: bool = False
    unfocused: bool = False
    minimized: bool = False
    focus_switch: bool = False
    relative_requires_focus: bool = False
    all_input_requires_focus: bool = False
    session: str = ""
    background_label: str = "Foreground only"
    minimized_label: str = "Not available"
    notes: str = ""


@dataclass(frozen=True)
class MinecraftTarget:
    key: str
    title: str
    pid: int | None = None
    native_id: int | str | None = None
    platform: str = ""
    session: str = ""
    minimized: bool | None = None
    details: str = ""

    @property
    def display(self) -> str:
        parts = [self.title or "Minecraft Java"]
        if self.pid:
            parts.append(f"PID {self.pid}")
        if self.minimized is True:
            parts.append("minimized")
        if self.session:
            parts.append(self.session)
        return " — ".join(parts)


class TargetedInputError(RuntimeError):
    pass


class TargetedInputBackend:
    """Contract shared by platform-specific targeted input backends."""
    capabilities = InputCapabilities(name="unsupported")

    def __init__(self, title_hint: str = "Minecraft", target_id=None):
        self.title_hint = title_hint
        self.target = target_id

    def find_target(self):
        raise NotImplementedError

    def ensure_target(self):
        if self.target is None:
            self.target = self.find_target()
        if self.target is None:
            raise TargetedInputError(f"Minecraft window not found ({self.title_hint}).")
        return self.target

    def key_down(self, name):
        raise NotImplementedError

    def key_up(self, name):
        raise NotImplementedError

    def mouse_down(self, button):
        raise NotImplementedError

    def mouse_up(self, button):
        raise NotImplementedError

    def tap(self, name, hold=.05):
        self.key_down(name)
        time.sleep(hold)
        self.key_up(name)

    def chord(self, *names, hold=.04):
        for n in names:
            self.key_down(n)
        time.sleep(hold)
        for n in reversed(names):
            self.key_up(n)

    def click(self, button, hold=.05):
        self.mouse_down(button)
        time.sleep(hold)
        self.mouse_up(button)

    def move_relative(self, dx, dy=0):
        raise TargetedInputError("Relative camera input requires Minecraft focus with this backend.")

    def release_all(self):
        raise NotImplementedError

    def is_target_available(self):
        try:
            return self.ensure_target() is not None
        except Exception:
            return False
