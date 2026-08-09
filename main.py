from __future__ import annotations

import os
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
    _update_direct_launch()
    try:
        from minescript.app import run
    except ModuleNotFoundError as exc:
        handled = _bootstrap_if_needed(exc)
        if handled is not None:
            return handled
        raise
    return int(run() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
