from __future__ import annotations

"""Dependency-free update checker/installer for F3+.

Launch-time behavior is check-only by default.  Updates are installed only when the user
explicitly enables automatic installation (`F3PLUS_AUTO_UPDATE=1`) or calls
:func:`apply_update`.  Update/network failures never block offline launch.
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

REPOSITORY = "LucidOcelot/F3Plus"
BRANCH = "main"
API_HEAD = f"https://api.github.com/repos/{REPOSITORY}/commits/{BRANCH}"
STATE_FILE = ".f3plus-update.json"
USER_AGENT = "F3Plus-Updater/2.3.4"
MAX_ARCHIVE_BYTES = 80 * 1024 * 1024
EXCLUDED_TOP_LEVEL = {".git", ".venv", ".runtime", STATE_FILE, "F3Plus_startup.log", "__pycache__", "build", "dist"}
REQUIRED_UPDATE_FILES = ("launcher.py", "main.py", "updater.py", "requirements.txt", "pyproject.toml", "minescript/__init__.py", "minescript/app.py")


def _request(url: str, timeout: int = 6):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=timeout)


def _remote_sha() -> str:
    with _request(API_HEAD, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    sha = str(payload.get("sha", "")).strip()
    if len(sha) < 12:
        raise RuntimeError("GitHub returned an invalid F3+ commit identifier")
    return sha


def _git(root: Path, *args: str, timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)


def _git_update(root: Path, apply: bool) -> tuple[bool, str] | None:
    if not (root / ".git").is_dir() or shutil.which("git") is None:
        return None
    dirty = _git(root, "status", "--porcelain", "--untracked-files=no")
    if dirty.returncode != 0:
        return False, "Git checkout detected, but repository status could not be read; update skipped."
    if dirty.stdout.strip():
        return False, "Tracked local changes detected; update installation is disabled to avoid overwriting them."
    fetch = _git(root, "fetch", "--quiet", "origin", BRANCH, timeout=30)
    if fetch.returncode != 0:
        return False, "Update check could not reach GitHub; continuing with the installed build."
    local = _git(root, "rev-parse", "HEAD").stdout.strip()
    remote = _git(root, "rev-parse", f"origin/{BRANCH}").stdout.strip()
    if local and local == remote:
        return False, "F3+ is current."
    if not apply:
        return False, f"F3+ update available: {remote[:12]}. Automatic installation is off."
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


def _write_state(root: Path, sha: str, files: list[str]) -> None:
    try:
        (root / STATE_FILE).write_text(json.dumps({"repository": REPOSITORY, "branch": BRANCH, "sha": sha, "files": sorted(set(files))}, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def _allowed_relative(path: PurePosixPath) -> bool:
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        return False
    return path.parts[0] not in EXCLUDED_TOP_LEVEL


def _download_archive(url: str) -> bytes:
    with _request(url, timeout=20) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_ARCHIVE_BYTES:
            raise RuntimeError("GitHub update archive is unexpectedly large")
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES:
        raise RuntimeError("GitHub update archive exceeded the safety limit")
    return data


def _safe_unpack_archive(data: bytes, destination: Path) -> tuple[Path, list[str]]:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = [info for info in archive.infolist() if info.filename and not info.filename.endswith("/")]
        roots = {PurePosixPath(info.filename).parts[0] for info in members if PurePosixPath(info.filename).parts}
        if len(roots) != 1:
            raise RuntimeError("Downloaded update did not contain one repository root")
        archive_root = next(iter(roots)); files: list[str] = []
        for info in archive.infolist():
            raw = PurePosixPath(info.filename)
            if not raw.parts or raw.parts[0] != archive_root:
                continue
            relative = PurePosixPath(*raw.parts[1:])
            if not relative.parts:
                continue
            if not _allowed_relative(relative):
                if relative.parts[0] in EXCLUDED_TOP_LEVEL:
                    continue
                raise RuntimeError("Unsafe path found in GitHub update archive")
            out = destination.joinpath(*relative.parts); resolved = out.resolve(); base = destination.resolve()
            if resolved != base and base not in resolved.parents:
                raise RuntimeError("Unsafe path found in GitHub update archive")
            if info.is_dir():
                out.mkdir(parents=True, exist_ok=True); continue
            out.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, out.open("wb") as target:
                shutil.copyfileobj(source, target)
            files.append(relative.as_posix())
    return destination, files


def _validate_source(source: Path) -> None:
    missing = [relative for relative in REQUIRED_UPDATE_FILES if not (source / relative).is_file()]
    if missing:
        raise RuntimeError("Downloaded update is incomplete: missing " + ", ".join(missing))
    targets = [source / "launcher.py", source / "main.py", source / "updater.py"]
    targets.extend(sorted((source / "minescript").rglob("*.py")))
    for path in targets:
        try:
            text = path.read_text(encoding="utf-8"); compile(text, str(path), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise RuntimeError(f"Downloaded update failed Python syntax validation in {path.relative_to(source)}: {exc}") from exc


def _remove_deleted_files(root: Path, old_files: list[str], new_files: set[str]) -> None:
    candidates = sorted(set(str(value) for value in old_files) - new_files, key=lambda value: value.count("/"), reverse=True); base = root.resolve()
    for text in candidates:
        relative = PurePosixPath(text)
        if not _allowed_relative(relative):
            continue
        target = root.joinpath(*relative.parts)
        try:
            resolved = target.resolve()
        except OSError:
            continue
        if resolved != base and base not in resolved.parents:
            continue
        try:
            if target.is_file() or target.is_symlink():
                target.unlink()
        except OSError:
            continue
        parent = target.parent
        while parent != root:
            try: parent.rmdir()
            except OSError: break
            parent = parent.parent


def _overlay_tree(source: Path, root: Path) -> None:
    for item in source.iterdir():
        if item.name in EXCLUDED_TOP_LEVEL:
            continue
        destination = root / item.name
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True); shutil.copytree(item, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(item, destination)
    if os.name != "nt":
        for name in ("START_F3PLUS.sh", "START_F3PLUS.command"):
            path = root / name
            if path.exists():
                try: path.chmod(path.stat().st_mode | 0o111)
                except OSError: pass


def _archive_update(root: Path, apply: bool) -> tuple[bool, str]:
    remote = _remote_sha(); state = _read_state(root)
    if state.get("sha") == remote:
        return False, "F3+ is current."
    if not apply:
        return False, f"F3+ update available: {remote[:12]}. Automatic installation is off."
    url = f"https://github.com/{REPOSITORY}/archive/{remote}.zip"; data = _download_archive(url)
    with tempfile.TemporaryDirectory(prefix="f3plus-update-") as temp_text:
        unpacked = Path(temp_text) / "unpacked"; source, files = _safe_unpack_archive(data, unpacked); _validate_source(source); _remove_deleted_files(root, list(state.get("files", [])), set(files)); _overlay_tree(source, root)
    _write_state(root, remote, files)
    return True, f"Updated F3+ to {remote[:12]}."


def _run(root: Path, apply: bool) -> tuple[bool, str]:
    try:
        git_result = _git_update(root, apply)
        if git_result is not None:
            return git_result
        return _archive_update(root, apply)
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, urllib.error.URLError, subprocess.SubprocessError) as exc:
        return False, f"Update check unavailable ({exc}). Continuing with the installed build."


def auto_update(root: Path) -> tuple[bool, str]:
    """Check for updates; install only when F3PLUS_AUTO_UPDATE=1 is explicitly set."""
    if os.environ.get("F3PLUS_SKIP_UPDATE") == "1":
        return False, "Update check skipped by F3PLUS_SKIP_UPDATE."
    return _run(root, apply=os.environ.get("F3PLUS_AUTO_UPDATE") == "1")


def apply_update(root: Path) -> tuple[bool, str]:
    """Explicitly check for and install a safe fast-forward/archive update."""
    if os.environ.get("F3PLUS_SKIP_UPDATE") == "1":
        return False, "Update installation skipped by F3PLUS_SKIP_UPDATE."
    return _run(root, apply=True)
