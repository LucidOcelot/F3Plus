from __future__ import annotations

"""Small dependency-free updater used by launcher.py before F3+ starts.

Git checkouts fast-forward from origin/main. Extracted ZIP installs compare a saved
commit SHA with GitHub's main branch and overlay an immutable commit archive. User
configuration lives under ~/.f3plus and is never touched by this updater.
"""

import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

REPOSITORY = "LucidOcelot/F3Plus"
BRANCH = "main"
API_HEAD = f"https://api.github.com/repos/{REPOSITORY}/commits/{BRANCH}"
STATE_FILE = ".f3plus-update.json"
USER_AGENT = "F3Plus-Updater/2.0"
EXCLUDED_TOP_LEVEL = {
    ".git", ".venv", ".runtime", STATE_FILE, "F3Plus_startup.log",
    "__pycache__", "build", "dist",
}


def _request(url: str, timeout: int = 6):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": USER_AGENT}),
        timeout=timeout,
    )


def _remote_sha() -> str:
    with _request(API_HEAD, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    sha = str(payload.get("sha", "")).strip()
    if len(sha) < 12:
        raise RuntimeError("GitHub returned an invalid F3+ commit identifier")
    return sha


def _git(root: Path, *args: str, timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False,
    )


def _git_update(root: Path) -> tuple[bool, str] | None:
    if not (root / ".git").is_dir() or shutil.which("git") is None:
        return None
    dirty = _git(root, "status", "--porcelain", "--untracked-files=no")
    if dirty.returncode != 0:
        return False, "Git checkout detected, but repository status could not be read; update skipped."
    if dirty.stdout.strip():
        return False, "Tracked local changes detected; automatic update skipped to avoid overwriting them."
    fetch = _git(root, "fetch", "--quiet", "origin", BRANCH, timeout=30)
    if fetch.returncode != 0:
        return False, "Update check could not reach GitHub; continuing with the installed build."
    local = _git(root, "rev-parse", "HEAD").stdout.strip()
    remote = _git(root, "rev-parse", f"origin/{BRANCH}").stdout.strip()
    if local and local == remote:
        return False, "F3+ is current."
    merge = _git(root, "merge", "--ff-only", f"origin/{BRANCH}", timeout=45)
    if merge.returncode != 0:
        return False, "A newer build exists but the checkout could not fast-forward; continuing without modifying files."
    return True, f"Updated F3+ to {remote[:12]}."


def _read_state(root: Path) -> dict:
    try:
        value = json.loads((root / STATE_FILE).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def _write_state(root: Path, sha: str) -> None:
    try:
        (root / STATE_FILE).write_text(
            json.dumps({"repository": REPOSITORY, "branch": BRANCH, "sha": sha}, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def _overlay_tree(source: Path, root: Path) -> None:
    for item in source.iterdir():
        if item.name in EXCLUDED_TOP_LEVEL:
            continue
        destination = root / item.name
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copytree(item, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(item, destination)
    if os.name != "nt":
        for name in ("START_F3PLUS.sh", "START_F3PLUS.command"):
            path = root / name
            if path.exists():
                try:
                    path.chmod(path.stat().st_mode | 0o111)
                except OSError:
                    pass


def _archive_update(root: Path) -> tuple[bool, str]:
    remote = _remote_sha()
    state = _read_state(root)
    if state.get("sha") == remote:
        return False, "F3+ is current."
    url = f"https://github.com/{REPOSITORY}/archive/{remote}.zip"
    with tempfile.TemporaryDirectory(prefix="f3plus-update-") as tmp_text:
        tmp = Path(tmp_text)
        archive = tmp / "update.zip"
        with _request(url, timeout=20) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(tmp / "unpacked")
        roots = [p for p in (tmp / "unpacked").iterdir() if p.is_dir()]
        if len(roots) != 1 or not (roots[0] / "main.py").is_file() or not (roots[0] / "minescript" / "__init__.py").is_file():
            raise RuntimeError("Downloaded update did not contain a valid F3+ source tree")
        _overlay_tree(roots[0], root)
    _write_state(root, remote)
    return True, f"Updated F3+ to {remote[:12]}."


def auto_update(root: Path) -> tuple[bool, str]:
    """Check GitHub and update the working tree. Failures never block offline launch."""
    if os.environ.get("F3PLUS_SKIP_UPDATE") == "1":
        return False, "Automatic update skipped by F3PLUS_SKIP_UPDATE."
    try:
        git_result = _git_update(root)
        if git_result is not None:
            return git_result
        return _archive_update(root)
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, urllib.error.URLError) as exc:
        return False, f"Update check unavailable ({exc}). Continuing with the installed build."
