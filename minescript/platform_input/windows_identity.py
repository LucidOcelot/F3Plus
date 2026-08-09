from __future__ import annotations

"""Identity checks for Windows Minecraft Java discovery.

Window titles are descriptive text, not process identity. A browser tab can contain
"Minecraft" in its title, so discovery validates the owning executable before the
window is offered as a client target.
"""

import ctypes
from ctypes import wintypes

from .base import MinecraftTarget

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def process_image(pid: int) -> str:
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
        ]
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not handle:
            return ""
        try:
            size = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return buffer.value
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        return ""
    return ""


def _executable_name(path: str) -> str:
    # The identity value is a Windows path even when this helper is exercised by
    # Linux/macOS CI. pathlib.Path follows the host separator, so normalize both
    # separators explicitly before taking the basename.
    return str(path or "").replace("\\", "/").rstrip("/").rsplit("/", 1)[-1].lower()


def is_minecraft_java_target(target: MinecraftTarget) -> bool:
    if not target.pid:
        return False
    executable = _executable_name(process_image(int(target.pid)))
    # Title text is never sufficient. If process identity cannot be read, fail
    # closed and leave the client unlinked rather than risk targeting another app.
    return executable in {"java.exe", "javaw.exe"} or executable.startswith("java")


def filter_minecraft_java_targets(targets: list[MinecraftTarget]) -> list[MinecraftTarget]:
    return [target for target in targets if is_minecraft_java_target(target)]
