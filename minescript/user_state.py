from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .config import APP_DIR


PROJECTS_FILE = APP_DIR / "world-projects.json"
RESULTS_FILE = APP_DIR / "result-history.json"
MACROS_FILE = APP_DIR / "custom-macros.json"
ROUTES_FILE = APP_DIR / "saved-routes.json"


def _read(path: Path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value
    except (OSError, UnicodeError, json.JSONDecodeError):
        return default


def _write(path: Path, value) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_projects() -> list[dict[str, Any]]:
    value = _read(PROJECTS_FILE, [])
    return [dict(row) for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def save_projects(rows: list[dict[str, Any]]) -> None:
    _write(PROJECTS_FILE, rows)


def load_results() -> list[dict[str, Any]]:
    value = _read(RESULTS_FILE, [])
    return [dict(row) for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def record_result(operation: str, workbench: str, version: str, data: Any, note: str = "", limit: int = 100) -> dict[str, Any]:
    rows = load_results()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": str(operation),
        "workbench": str(workbench),
        "minecraft_version": str(version),
        "note": str(note or ""),
        "data": data,
    }
    rows.insert(0, entry)
    del rows[max(1, int(limit)):]
    _write(RESULTS_FILE, rows)
    return entry


def clear_results() -> None:
    _write(RESULTS_FILE, [])


def load_macros() -> dict[str, dict[str, Any]]:
    value = _read(MACROS_FILE, {})
    return {str(key): dict(row) for key, row in value.items() if isinstance(row, dict)} if isinstance(value, dict) else {}


def save_macros(value: dict[str, dict[str, Any]]) -> None:
    _write(MACROS_FILE, value)


def load_routes() -> list[dict[str, Any]]:
    value = _read(ROUTES_FILE, [])
    return [dict(row) for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def save_routes(rows: list[dict[str, Any]]) -> None:
    _write(ROUTES_FILE, rows)
