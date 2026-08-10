from __future__ import annotations

"""Console entrypoint using the same update and desktop startup path as main.py."""

from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    from main import main as application_main
    return int(application_main() or 0)
