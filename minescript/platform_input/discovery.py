from __future__ import annotations

import platform
import subprocess

from .base import MinecraftTarget


def _process_targets(session: str = "") -> list[MinecraftTarget]:
    targets: list[MinecraftTarget] = []
    try:
        if platform.system() == "Windows":
            return []
        out = subprocess.check_output(["ps", "-axo", "pid=,command="], text=True, errors="replace", timeout=5)
    except Exception:
        return []

    for line in out.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        command = parts[1]
        low = command.lower()
        if "java" not in low:
            continue
        if not any(x in low for x in ("minecraft", "net.minecraft", ".minecraft", "prismlauncher", "multimc")):
            continue
        targets.append(MinecraftTarget(
            key=f"pid:{pid}", title="Minecraft Java", pid=pid, native_id=pid,
            platform=platform.system(), session=session, minimized=None,
            details=command[:220],
        ))

    seen = set()
    unique = []
    for target in targets:
        if target.pid in seen:
            continue
        seen.add(target.pid)
        unique.append(target)
    return unique


def discover_minecraft_targets(title_hint: str = "Minecraft") -> list[MinecraftTarget]:
    system = platform.system()
    try:
        if system == "Windows":
            from .windows import list_minecraft_windows
            from .windows_identity import filter_minecraft_java_targets
            return filter_minecraft_java_targets(list_minecraft_windows(title_hint))
        if system == "Darwin":
            from .macos import list_minecraft_targets
            found = list_minecraft_targets(title_hint)
            return found or _process_targets("macOS")
        if system == "Linux":
            from .linux import linux_session
            return _process_targets(linux_session())
    except Exception:
        pass
    return _process_targets(system.lower())


def current_linux_session() -> str:
    if platform.system() != "Linux":
        return ""
    from .linux import linux_session
    return linux_session()
