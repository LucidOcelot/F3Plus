from __future__ import annotations

import platform

from .base import MinecraftTarget


class NoFocusController:
    name = "Manual focus"
    available = False
    def capture_current(self): return None
    def focus(self, target): return False
    def restore(self, token): return False


def create_focus_controller(target: MinecraftTarget | None):
    system = platform.system()
    try:
        if system == "Windows":
            from .windows import WindowsFocusController
            return WindowsFocusController()
        if system == "Darwin":
            from .macos import MacOSFocusController
            return MacOSFocusController()
        if system == "Linux":
            from .linux import linux_session, wayland_focus_controller
            if linux_session() == "wayland":
                controller = wayland_focus_controller()
                if controller:
                    return controller
    except Exception:
        pass
    return NoFocusController()
