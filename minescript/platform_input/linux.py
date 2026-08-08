from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import threading
import time

from .base import InputCapabilities, TargetedInputError


def linux_session() -> str:
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "unsupported-display"
    return "headless"


class HyprlandFocusController:
    name = "Hyprland focus switch"
    available = bool(shutil.which("hyprctl"))

    def capture_current(self):
        try:
            data = json.loads(subprocess.check_output(["hyprctl", "activewindow", "-j"], text=True, timeout=4))
            return data.get("pid")
        except Exception:
            return None

    def focus(self, target):
        return bool(target.pid and subprocess.run(
            ["hyprctl", "dispatch", "focuswindow", f"pid:{target.pid}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0)

    def restore(self, token):
        return bool(token and subprocess.run(
            ["hyprctl", "dispatch", "focuswindow", f"pid:{int(token)}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0)


class SwayFocusController:
    name = "Sway focus switch"
    available = bool(shutil.which("swaymsg"))

    def _tree(self):
        return json.loads(subprocess.check_output(["swaymsg", "-t", "get_tree", "-r"], text=True, timeout=5))

    def _focused_pid(self, node):
        if node.get("focused"):
            return node.get("pid")
        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            pid = self._focused_pid(child)
            if pid:
                return pid
        return None

    def capture_current(self):
        try:
            return self._focused_pid(self._tree())
        except Exception:
            return None

    def focus(self, target):
        return bool(target.pid and subprocess.run(
            ["swaymsg", f"[pid={target.pid}]", "focus"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0)

    def restore(self, token):
        return bool(token and subprocess.run(
            ["swaymsg", f"[pid={int(token)}]", "focus"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0)


def wayland_focus_controller():
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        controller = HyprlandFocusController()
        if controller.available:
            return controller
    if os.environ.get("SWAYSOCK"):
        controller = SwayFocusController()
        if controller.available:
            return controller
    return None


_YD_KEY = {
    **{c: n for c, n in zip("1234567890", range(2, 12))},
    "q": 16, "w": 17, "e": 18, "r": 19, "t": 20, "y": 21, "u": 22, "i": 23, "o": 24, "p": 25,
    "a": 30, "s": 31, "d": 32, "f": 33, "g": 34, "h": 35, "j": 36, "k": 37, "l": 38,
    "z": 44, "x": 45, "c": 46, "v": 47, "b": 48, "n": 49, "m": 50,
    "esc": 1, "tab": 15, "enter": 28, "ctrl": 29, "shift": 42, "alt": 56, "space": 57,
    "f1": 59, "f2": 60, "f3": 61, "f4": 62, "f5": 63, "f6": 64, "f7": 65, "f8": 66,
    "f9": 67, "f10": 68, "f11": 87, "f12": 88,
}


def ydotool_socket_candidates() -> list[Path]:
    """Return likely ydotoold sockets in priority order."""
    candidates: list[Path] = []

    def add(value) -> None:
        if not value:
            return
        path = Path(str(value)).expanduser()
        if path not in candidates:
            candidates.append(path)

    add(os.environ.get("YDOTOOL_SOCKET"))
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime:
        add(Path(runtime) / ".ydotool_socket")
    try:
        add(Path("/run/user") / str(os.getuid()) / ".ydotool_socket")
    except AttributeError:
        pass
    add("/tmp/.ydotool_socket")
    add("/run/ydotoold/socket")
    return candidates


def _is_socket(path: Path) -> bool:
    try:
        return stat.S_ISSOCK(path.stat().st_mode)
    except OSError:
        return False


def find_ydotool_socket() -> Path | None:
    for path in ydotool_socket_candidates():
        if _is_socket(path):
            return path
    return None


class LinuxYdotoolInput:
    """Wayland/global virtual input through ydotoold.

    The daemon may be started after F3+ itself. Socket discovery therefore happens
    again before every command instead of being frozen at application startup.
    """

    def __init__(self):
        self.exe = shutil.which("ydotool")
        if not self.exe:
            raise TargetedInputError("ydotool is not installed.")
        self.socket_path: Path | None = find_ydotool_socket()
        self._held_keys: set[str] = set()
        self._held_buttons: set[str] = set()
        self._lock = threading.RLock()
        self.capabilities = InputCapabilities(
            name="Wayland virtual input (ydotool)",
            targeted_keyboard=False,
            targeted_mouse_buttons=False,
            targeted_relative_mouse=False,
            unfocused=False,
            minimized=False,
            focus_switch=False,
            relative_requires_focus=True,
            all_input_requires_focus=True,
            session="wayland",
            background_label="Global uinput; focused app receives input",
            minimized_label="Restore and focus first",
            notes=(
                "ydotool emits global uinput events; it does not target the linked Minecraft window. "
                "F3+ auto-detects common ydotoold socket paths and re-checks them on every command. "
                "On Hyprland/Sway a compositor helper can focus Minecraft; on other Wayland desktops focus Minecraft during the countdown."
            ),
        )

    def _resolve_socket(self) -> Path:
        explicit = os.environ.get("YDOTOOL_SOCKET")
        if explicit:
            candidate = Path(explicit).expanduser()
            if _is_socket(candidate):
                self.socket_path = candidate
                return candidate
        if self.socket_path is not None and _is_socket(self.socket_path):
            return self.socket_path
        found = find_ydotool_socket()
        if found is not None:
            self.socket_path = found
            return found
        checked = ", ".join(str(path) for path in ydotool_socket_candidates())
        raise TargetedInputError(
            "ydotool is installed, but F3+ cannot find a usable ydotoold socket. "
            f"Checked: {checked}. Start ydotoold and ensure the socket is accessible to your user, "
            "or set YDOTOOL_SOCKET to the daemon socket path."
        )

    def _invoke(self, *args, timeout=8):
        socket_path = self._resolve_socket()
        env = os.environ.copy()
        env["YDOTOOL_SOCKET"] = str(socket_path)
        return subprocess.run(
            [self.exe, *map(str, args)],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )

    @staticmethod
    def _failure_text(proc) -> str:
        return "\n".join(part.strip() for part in (proc.stderr, proc.stdout) if part and part.strip())

    def preflight(self) -> None:
        """Verify the active daemon connection without generating a real key press."""
        try:
            proc = self._invoke("key", "0:0", timeout=4)
        except (OSError, subprocess.SubprocessError, TargetedInputError):
            raise
        detail = self._failure_text(proc)
        low = detail.lower()
        bad_notice = any(text in low for text in (
            "failed to connect",
            "connection refused",
            "permission denied",
            "backend unavailable",
            "no such file",
        ))
        if proc.returncode != 0 or bad_notice:
            raise TargetedInputError(
                f"ydotoold is not usable through {self.socket_path}. "
                + (detail if detail else "Check the daemon and socket permissions.")
            )

    def _run(self, *args):
        try:
            proc = self._invoke(*args)
        except (OSError, subprocess.SubprocessError) as exc:
            raise TargetedInputError(f"ydotool could not send input: {exc}") from exc
        detail = self._failure_text(proc)
        low = detail.lower()
        if proc.returncode != 0 or any(text in low for text in (
            "failed to connect",
            "connection refused",
            "permission denied",
            "backend unavailable",
        )):
            raise TargetedInputError(
                "ydotool could not send input through "
                f"{self.socket_path}. "
                + (detail if detail else "Make sure ydotoold is running and the socket is accessible to this user.")
            )

    def _code(self, name):
        key = str(name).lower()
        if key not in _YD_KEY:
            raise TargetedInputError(f"Unsupported Wayland key: {name}")
        return _YD_KEY[key]

    def key_down(self, name):
        with self._lock:
            self._run("key", f"{self._code(name)}:1")
            self._held_keys.add(str(name).lower())

    def key_up(self, name):
        key = str(name).lower()
        with self._lock:
            try:
                self._run("key", f"{self._code(name)}:0")
            finally:
                self._held_keys.discard(key)

    def tap(self, name, hold=.05):
        self.key_down(name)
        try:
            time.sleep(hold)
        finally:
            self.key_up(name)

    def chord(self, *names, hold=.04):
        for name in names:
            self.key_down(name)
        try:
            time.sleep(hold)
        finally:
            for name in reversed(names):
                try:
                    self.key_up(name)
                except Exception:
                    pass

    def mouse_down(self, button):
        name = str(button).lower()
        code = "0x40" if name == "left" else "0x41" if name == "right" else None
        if code is None:
            raise TargetedInputError(f"Unsupported mouse button: {button}")
        self._run("click", code)
        self._held_buttons.add(name)

    def mouse_up(self, button):
        name = str(button).lower()
        code = "0x80" if name == "left" else "0x81" if name == "right" else None
        if code is None:
            raise TargetedInputError(f"Unsupported mouse button: {button}")
        try:
            self._run("click", code)
        finally:
            self._held_buttons.discard(name)

    def click(self, button, hold=.05):
        self.mouse_down(button)
        try:
            time.sleep(hold)
        finally:
            self.mouse_up(button)

    def move_relative(self, dx, dy=0):
        self._run("mousemove", "-x", int(dx), "-y", int(dy))

    def release_all(self):
        for button in list(self._held_buttons):
            try:
                self.mouse_up(button)
            except Exception:
                pass
        for key in list(self._held_keys):
            try:
                self.key_up(key)
            except Exception:
                pass
        self._held_buttons.clear()
        self._held_keys.clear()


def ydotool_available() -> bool:
    return bool(shutil.which("ydotool"))
