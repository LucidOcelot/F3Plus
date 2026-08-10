from __future__ import annotations

"""Dependency-free updater for F3+.

Normal launch checks and installs the validated Stable channel before loading the
application. Set ``F3PLUS_UPDATE_CHANNEL=preview`` to follow development ``main``.
Set ``F3PLUS_AUTO_UPDATE=0`` (or ``F3PLUS_CHECK_ONLY_UPDATE=1``) for check-only
behavior, or ``F3PLUS_SKIP_UPDATE=1`` to disable the network check entirely.
Update/network failures never block offline launch.
"""

import io
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from minescript.version import VERSION

REPOSITORY = "LucidOcelot/F3Plus"
STATE_FILE = ".f3plus-update.json"
USER_AGENT = f"F3Plus-Updater/{VERSION}"
MAX_ARCHIVE_BYTES = 80 * 1024 * 1024
EXCLUDED_TOP_LEVEL = {".git", ".venv", ".runtime", STATE_FILE, "F3Plus_startup.log", "__pycache__", "build", "dist"}
REQUIRED_UPDATE_FILES = (
    "launcher.py", "main.py", "updater.py", "requirements.txt", "pyproject.toml",
    "minescript/__init__.py", "minescript/app.py", "minescript/app25.py",
)
_FALSE_VALUES = {"0", "false", "no", "off", "disabled"}


def update_channel() -> tuple[str, str]:
    raw = os.environ.get("F3PLUS_UPDATE_CHANNEL", "stable").strip().lower()
    if raw in {"preview", "main", "development", "dev"}:
        return "preview", "main"
    return "stable", "stable"


def _branch() -> str: return update_channel()[1]

def _api_head() -> str: return f"https://api.github.com/repos/{REPOSITORY}/commits/{_branch()}"

def _request(url: str, timeout: int = 6): return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout)


def _remote_sha() -> str:
    with _request(_api_head(), timeout=5) as response: payload = json.loads(response.read().decode("utf-8"))
    sha = str(payload.get("sha", "")).strip()
    if len(sha) < 12: raise RuntimeError("GitHub returned an invalid F3+ commit identifier")
    return sha


def _git(root: Path, *args: str, timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)


def _git_update(root: Path, apply: bool) -> tuple[bool, str] | None:
    if not (root / ".git").is_dir() or shutil.which("git") is None: return None
    channel, branch = update_channel(); dirty = _git(root, "status", "--porcelain", "--untracked-files=no")
    if dirty.returncode != 0: return False, "Git checkout detected, but repository status could not be read; update skipped."
    if dirty.stdout.strip(): return False, "Tracked local changes detected; update installation is disabled to avoid overwriting them."
    fetch = _git(root, "fetch", "--quiet", "origin", branch, timeout=30)
    if fetch.returncode != 0: return False, f"{channel.title()} update check could not reach GitHub; continuing with the installed build."
    local = _git(root, "rev-parse", "HEAD").stdout.strip(); remote = _git(root, "rev-parse", f"origin/{branch}").stdout.strip()
    if local and local == remote: return False, f"F3+ is current on the {channel} channel."
    if not apply: return False, f"F3+ {channel} update available: {remote[:12]}. Check-only mode is enabled."
    ancestor = _git(root, "merge-base", "--is-ancestor", local, remote) if local and remote else None
    if ancestor is not None and ancestor.returncode != 0: return False, f"The {channel} channel is not a fast-forward from this checkout; update skipped to protect local history."
    merge = _git(root, "merge", "--ff-only", f"origin/{branch}", timeout=45)
    if merge.returncode != 0: return False, "A newer validated build exists but the checkout could not fast-forward; continuing without modifying files."
    return True, f"Updated F3+ to {channel} build {remote[:12]}."


def _automatic_install_enabled() -> bool:
    if os.environ.get("F3PLUS_CHECK_ONLY_UPDATE", "").strip().lower() not in {"", "0", "false", "no", "off", "disabled"}: return False
    raw = os.environ.get("F3PLUS_AUTO_UPDATE", "1").strip().lower()
    return raw not in _FALSE_VALUES


def _manifest(root: Path) -> set[str]:
    out: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file(): continue
        try: rel = path.relative_to(root)
        except ValueError: continue
        if rel.parts and rel.parts[0] in EXCLUDED_TOP_LEVEL: continue
        out.add(rel.as_posix())
    return out


def _archive_url(sha: str) -> str: return f"https://github.com/{REPOSITORY}/archive/{sha}.zip"


def _safe_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts: raise RuntimeError("Update archive contains an unsafe path")
    return path


def _download_archive(sha: str) -> bytes:
    with _request(_archive_url(sha), timeout=20) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_ARCHIVE_BYTES: raise RuntimeError("Update archive is unexpectedly large")
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES: raise RuntimeError("Update archive is unexpectedly large")
    return data


def _extract_archive(data: bytes, destination: Path) -> Path:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        if not members: raise RuntimeError("Update archive is empty")
        roots = set()
        for info in members:
            safe = _safe_member(info.filename)
            if safe.parts: roots.add(safe.parts[0])
        if len(roots) != 1: raise RuntimeError("Update archive has an unexpected layout")
        root_name = next(iter(roots))
        for info in members:
            safe = _safe_member(info.filename)
            target = destination.joinpath(*safe.parts)
            if info.is_dir(): target.mkdir(parents=True, exist_ok=True); continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target.open("wb") as output: shutil.copyfileobj(source, output)
    extracted = destination / root_name
    if not extracted.is_dir(): raise RuntimeError("Update archive did not contain a project directory")
    missing = [name for name in REQUIRED_UPDATE_FILES if not (extracted / name).is_file()]
    if missing: raise RuntimeError("Update archive is incomplete: " + ", ".join(missing))
    return extracted


def _copy_update(source_root: Path, target_root: Path) -> None:
    new_files = _manifest(source_root); old_files = _manifest(target_root)
    for rel in sorted(old_files - new_files, reverse=True):
        target = target_root / rel
        try: target.unlink()
        except OSError: pass
    for rel in sorted(new_files):
        source = source_root / rel; target = target_root / rel; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _archive_update(root: Path, apply: bool) -> tuple[bool, str]:
    channel, _branch_name = update_channel()
    try: remote = _remote_sha()
    except Exception: return False, f"{channel.title()} update check could not reach GitHub; continuing with the installed build."
    state_path = root / STATE_FILE
    try:
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
    except Exception: state = {}
    if state.get("sha") == remote: return False, f"F3+ is current on the {channel} channel."
    if not apply: return False, f"F3+ {channel} update available: {remote[:12]}. Check-only mode is enabled."
    try:
        data = _download_archive(remote)
        with tempfile.TemporaryDirectory(prefix="f3plus-update-") as temp:
            extracted = _extract_archive(data, Path(temp)); _copy_update(extracted, root)
        state_path.write_text(json.dumps({"sha": remote, "channel": channel}, indent=2), encoding="utf-8")
    except Exception as exc:
        return False, f"A {channel} update was found but could not be installed safely ({exc}); continuing with the installed build."
    return True, f"Updated F3+ to {channel} build {remote[:12]}."


def auto_update(root: Path, apply: bool | None = None) -> tuple[bool, str]:
    if os.environ.get("F3PLUS_SKIP_UPDATE", "").strip().lower() not in {"", "0", "false", "no", "off", "disabled"}: return False, "Update check skipped by F3PLUS_SKIP_UPDATE."
    if apply is None: apply = _automatic_install_enabled()
    git_result = _git_update(root, bool(apply))
    if git_result is not None: return git_result
    return _archive_update(root, bool(apply))


def apply_update(root: Path) -> tuple[bool, str]: return auto_update(root, apply=True)
