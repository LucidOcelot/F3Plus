from __future__ import annotations

import platform

from .standard import UnavailableInputBackend
from .base import MinecraftTarget
from .hybrid import HybridTargetedInput, FocusRequiredInput


def create_input_backend(mode: str="auto", title_hint: str="Minecraft", target: MinecraftTarget | None=None):
    mode = (mode or "auto").strip().lower()
    system = platform.system().lower()

    if mode in {"standard", "foreground"}:
        session = ""
        if system == "linux":
            try:
                from .linux import linux_session
                session = linux_session()
            except Exception:
                pass
        try:
            return FocusRequiredInput("Foreground input", session)
        except Exception:
            return UnavailableInputBackend()

    if mode not in {"auto", "targeted", "background"}:
        raise ValueError(f"Unknown input mode: {mode}")

    target_id = target.native_id if target else None
    try:
        if system == "windows":
            from .windows import WindowsTargetedInput
            backend = WindowsTargetedInput(title_hint, target_id)
            if mode == "auto" and target is None and not backend.is_target_available():
                return FocusRequiredInput("Windows foreground fallback", "Win32")
            return HybridTargetedInput(backend)

        if system == "darwin":
            from .macos import MacOSTargetedInput
            backend = MacOSTargetedInput(title_hint, target_id)
            if mode == "auto" and target is None and not backend.is_target_available():
                return FocusRequiredInput("macOS foreground fallback", "Quartz")
            return HybridTargetedInput(backend)

        if system == "linux":
            from .linux import LinuxYdotoolInput, linux_session, ydotool_available
            session = linux_session()
            if session == "wayland":
                if ydotool_available():
                    return LinuxYdotoolInput()
                return FocusRequiredInput("Wayland focus-switch input", session)
            return FocusRequiredInput("Linux foreground input", session)

        return FocusRequiredInput("Foreground input", system)
    except Exception:
        if mode == "auto":
            try:
                return FocusRequiredInput(f"{platform.system()} focus-switch fallback", system)
            except Exception:
                return UnavailableInputBackend()
        raise
