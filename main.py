from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _bootstrap_if_needed(exc: ModuleNotFoundError) -> int | None:
    if exc.name not in {'PySide6', 'pynput', 'pyperclip', 'Quartz'}:
        return None
    if os.environ.get('F3PLUS_BOOTSTRAPPED') == '1':
        print(f'F3+ could not start because a required package is still missing: {exc.name}', file=sys.stderr)
        print('Run START_F3PLUS again while connected to the internet. If it still fails, copy the setup messages.', file=sys.stderr)
        return 2
    print(f'F3+ needs to finish installing {exc.name}. Starting setup...')
    return subprocess.call([sys.executable, str(ROOT / 'launcher.py')], cwd=ROOT)


def main():
    try:
        from minescript.app import run
    except ModuleNotFoundError as exc:
        handled = _bootstrap_if_needed(exc)
        if handled is not None:
            return handled
        raise
    run()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
