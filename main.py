from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _update_direct_launch() -> None:
    """Official launchers update first; direct main.py runs get the same check."""
    if os.environ.get("F3PLUS_BOOTSTRAPPED") == "1" or os.environ.get("F3PLUS_UPDATE_RESTARTED") == "1":
        return
    try:
        from updater import auto_update
        updated, message = auto_update(ROOT)
        print("[update] " + message)
        if updated:
            env = os.environ.copy(); env["F3PLUS_UPDATE_RESTARTED"] = "1"
            os.execve(sys.executable, [sys.executable, str(Path(__file__).resolve())], env)
    except Exception as exc:
        print(f"[update] Update check unavailable ({exc}). Continuing with the installed build.")


def _java_major(path: Path) -> int | None:
    try:
        proc = subprocess.run([str(path), "-version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = re.search(r'(?:java|openjdk)\s+version\s+"?(\d+)', proc.stdout or "", re.I)
    if not match:
        match = re.search(r'version\s+"?(\d+)', proc.stdout or "", re.I)
    return int(match.group(1)) if match else None


def _minecraft_runtime_roots() -> list[Path]:
    home = Path.home(); roots: list[Path] = []
    appdata = os.environ.get("APPDATA"); local = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles"); program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if appdata: roots.append(Path(appdata) / ".minecraft" / "runtime")
    roots.extend([home / ".minecraft" / "runtime", home / "Library" / "Application Support" / "minecraft" / "runtime"])
    if local:
        local_path = Path(local)
        roots.extend([local_path / "Minecraft Launcher" / "runtime", local_path / ".minecraft" / "runtime"])
        packages = local_path / "Packages"
        try:
            if packages.is_dir():
                for package in packages.glob("Microsoft.4297127D64EC6*"):
                    roots.extend([
                        package / "LocalCache" / "Local" / "runtime",
                        package / "LocalCache" / "Local" / ".minecraft" / "runtime",
                        package / "LocalState" / "runtime",
                    ])
        except OSError:
            pass
    if program_files: roots.append(Path(program_files) / "Minecraft Launcher" / "runtime")
    if program_files_x86: roots.append(Path(program_files_x86) / "Minecraft Launcher" / "runtime")
    out: list[Path] = []
    for root in roots:
        try:
            resolved = root.resolve()
            if resolved.is_dir() and resolved not in out: out.append(resolved)
        except (OSError, RuntimeError):
            pass
    return out


def _prepare_minecraft_java() -> None:
    """Prefer the newest installed Minecraft-managed Java when no explicit runtime is set."""
    if os.environ.get("F3PLUS_JAVA"):
        return
    executable = "java.exe" if os.name == "nt" else "java"
    candidates: list[tuple[int, Path]] = []
    for root in _minecraft_runtime_roots():
        try:
            for path in root.rglob(executable):
                if path.parent.name.lower() != "bin": continue
                major = _java_major(path)
                if major is not None: candidates.append((major, path))
        except OSError:
            continue
    if not candidates:
        return
    major, path = max(candidates, key=lambda row: (row[0], str(row[1])))
    os.environ["F3PLUS_JAVA"] = str(path)
    print(f"[java] Using Minecraft-managed Java {major}: {path}")


def _bootstrap_if_needed(exc: ModuleNotFoundError) -> int | None:
    if exc.name not in {"PySide6", "pynput", "pyperclip", "Quartz"}:
        return None
    if os.environ.get("F3PLUS_BOOTSTRAPPED") == "1":
        print(f"F3+ could not start because a required package is still missing: {exc.name}", file=sys.stderr)
        print("Run START_F3PLUS again while connected to the internet. If it still fails, copy the setup messages.", file=sys.stderr)
        return 2
    print(f"F3+ needs to finish installing {exc.name}. Starting setup...")
    return subprocess.call([sys.executable, str(ROOT / "launcher.py")], cwd=ROOT)


def main() -> int:
    _update_direct_launch(); _prepare_minecraft_java()
    try:
        from minescript.desktop import run
    except ModuleNotFoundError as exc:
        handled = _bootstrap_if_needed(exc)
        if handled is not None:
            return handled
        raise
    return int(run() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
