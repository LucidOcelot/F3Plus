from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
STAMP = VENV / ".f3plus-requirements.sha256"
REQ = ROOT / "requirements.txt"
MIN_PYTHON = (3, 11)
MAX_PYTHON = (3, 13)
MIN_SETUP_FREE = 1_500_000_000


def _ensure_visible_windows_console() -> None:
    if os.name != "nt" or os.environ.get("F3PLUS_CONSOLE_READY") == "1":
        return
    no_console = (
        sys.stdout is None
        or sys.stderr is None
        or Path(sys.executable).name.lower() == "pythonw.exe"
    )
    if not no_console:
        return
    python_exe = Path(sys.executable)
    if python_exe.name.lower() == "pythonw.exe":
        sibling = python_exe.with_name("python.exe")
        if sibling.exists():
            python_exe = sibling
    env = os.environ.copy()
    env["F3PLUS_CONSOLE_READY"] = "1"
    cmdline = subprocess.list2cmdline([str(python_exe), str(Path(__file__).resolve())])
    subprocess.Popen(["cmd.exe", "/d", "/k", cmdline], cwd=ROOT, env=env)
    raise SystemExit(0)


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            try:
                stream.write(data)
                stream.flush()
            except (AttributeError, OSError, ValueError):
                pass
        return len(data)

    def flush(self):
        for stream in self.streams:
            try:
                stream.flush()
            except (AttributeError, OSError, ValueError):
                pass


def _enable_startup_log():
    try:
        log = open(ROOT / "F3Plus_startup.log", "a", encoding="utf-8", buffering=1)
        log.write("\n--- Python launcher started ---\n")
        sys.stdout = _Tee(sys.stdout, log)
        sys.stderr = _Tee(sys.stderr, log)
        return log
    except OSError:
        return None


def _check_for_updates() -> None:
    """Update before loading project modules, then restart into the updated launcher."""
    if os.environ.get("F3PLUS_UPDATE_RESTARTED") == "1":
        return
    try:
        from updater import auto_update
        updated, message = auto_update(ROOT)
    except Exception as exc:
        updated, message = False, f"Update check unavailable ({exc}). Continuing with the installed build."
    print("[update] " + message, flush=True)
    if not updated:
        return
    env = os.environ.copy()
    env["F3PLUS_UPDATE_RESTARTED"] = "1"
    os.execve(sys.executable, [sys.executable, str(Path(__file__).resolve())], env)


def _venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _supported_python_info(version_info) -> bool:
    version = (version_info.major, version_info.minor)
    return MIN_PYTHON <= version <= MAX_PYTHON


def _python_runs(py: Path) -> bool:
    probe = (
        "import sys; "
        "v=sys.version_info[:2]; "
        f"raise SystemExit(0 if {MIN_PYTHON!r} <= v <= {MAX_PYTHON!r} else 1)"
    )
    try:
        return subprocess.run(
            [str(py), "-c", probe], cwd=ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=20, check=False,
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _required_modules() -> list[str]:
    modules = ["PySide6", "pynput", "pyperclip"]
    if sys.platform == "darwin":
        modules.append("Quartz")
    return modules


def _required_packages_present(py: Path) -> bool:
    # Code is fixed and module names are passed as argv. This avoids constructing
    # executable Python source from data and keeps subprocess diagnostics sane.
    probe = (
        "import importlib.util,sys\n"
        "missing=[m for m in sys.argv[1:] if importlib.util.find_spec(m) is None]\n"
        "raise SystemExit(1 if missing else 0)\n"
    )
    try:
        return subprocess.run(
            [str(py), "-c", probe, *_required_modules()], cwd=ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=30, check=False,
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _requirements_hash() -> str:
    if not REQ.exists():
        raise RuntimeError("requirements.txt is missing. Re-extract the complete F3+ ZIP and try again.")
    return hashlib.sha256(REQ.read_bytes()).hexdigest()


def _check_python() -> None:
    if not _supported_python_info(sys.version_info):
        found = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        raise RuntimeError(
            f"Python {found} was found, but this F3+ release supports Python "
            f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]} through {MAX_PYTHON[0]}.{MAX_PYTHON[1]}. "
            "Run START_F3PLUS so F3+ can select or prepare a compatible runtime."
        )


def _gb(n: int) -> str:
    return f"{n / 1024**3:.2f} GB"


def _setup_locations():
    locations = []
    for raw in (ROOT, tempfile.gettempdir(), Path.home()):
        try:
            path = Path(raw).resolve()
            anchor = path.anchor or str(path)
        except (OSError, RuntimeError):
            continue
        if any(existing[0] == anchor for existing in locations):
            continue
        try:
            free = shutil.disk_usage(path).free
        except OSError:
            continue
        locations.append((anchor, free, path))
    return locations


def _preflight_disk_space() -> None:
    low = [entry for entry in _setup_locations() if entry[1] < MIN_SETUP_FREE]
    if not low:
        return
    lines = [f"{anchor or path}: {_gb(free)} free" for anchor, free, path in low]
    raise RuntimeError(
        "F3+ needs more free disk space before first-run package setup. "
        f"Keep at least {_gb(MIN_SETUP_FREE)} free on the drive used by F3+ and your "
        "temporary/cache folder.\nLow-space location(s):\n - "
        + "\n - ".join(lines)
        + "\n\nFree space or move the extracted F3+ folder to a drive with more room, "
        "then run START_F3PLUS again."
    )


def _failure_kind(output: str) -> str:
    low = output.lower()
    if any(text in low for text in (
        "no space left on device", "not enough space on the disk",
        "there is not enough space on the disk", "os error 112", "errno 28",
    )):
        return "disk"
    if any(text in low for text in (
        "certificate verify failed", "certificate_verify_failed", "connection reset",
        "connection timed out", "temporary failure in name resolution", "could not resolve host",
    )):
        return "network"
    if any(text in low for text in ("access is denied", "permission denied", "winerror 5")):
        return "permission"
    if any(text in low for text in (
        "no matching distribution found", "not a supported wheel", "unsupported platform",
        "python.h: no such file or directory",
    )):
        return "compatibility"
    return "other"


def _run_visible(cmd: list[str], *, label: str, attempts: int = 1) -> tuple[int, str]:
    combined: list[str] = []
    rc = 127
    for attempt in range(1, attempts + 1):
        suffix = f" (attempt {attempt}/{attempts})" if attempts > 1 else ""
        print(f"      {label}{suffix}")
        print("      Command: " + subprocess.list2cmdline(cmd))
        lines: list[str] = []
        try:
            proc = subprocess.Popen(
                cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                clean = line.rstrip()
                lines.append(clean)
                print("      " + clean)
            rc = proc.wait()
        except OSError as exc:
            lines.append(str(exc))
            print(f"      Could not start command: {exc}")
            rc = 127
        combined.extend(lines)
        if rc == 0:
            return 0, "\n".join(combined)
        kind = _failure_kind("\n".join(lines))
        print(f"      Command failed with exit code {rc}.")
        if kind == "disk":
            print("      Disk space is exhausted; retrying would only fail again.")
            break
        if attempt < attempts:
            print("      Retrying in 2 seconds...")
            time.sleep(2)
    return rc, "\n".join(combined)


def _disk_error_message() -> str:
    spots = _setup_locations()
    summary = ", ".join(f"{anchor}: {_gb(free)} free" for anchor, free, _ in spots)
    if not summary:
        summary = "free-space check unavailable"
    return (
        "Package setup stopped because the disk ran out of free space. No further retries "
        f"were attempted.\nCurrent free space: {summary}.\nFree at least "
        f"{_gb(MIN_SETUP_FREE)} on the affected drive, or move F3+ to a roomier drive, "
        "then run START_F3PLUS again."
    )


def _find_project_uv() -> Path | None:
    uv_name = "uv.exe" if os.name == "nt" else "uv"
    uv_root = ROOT / ".runtime" / "uv"
    direct = uv_root / uv_name
    if direct.is_file():
        return direct
    if not uv_root.exists():
        return None
    return next((path for path in uv_root.rglob(uv_name) if path.is_file()), None)


def _install_requirements(py: Path, *, force_repair: bool = False) -> None:
    _preflight_disk_space()
    uv = _find_project_uv()
    if uv is not None:
        install = [str(uv), "pip", "install", "--python", str(py), "--index-url", "https://pypi.org/simple", "--no-cache"]
        if force_repair:
            install.extend(["--upgrade", "--reinstall"])
        install.extend(["-r", str(REQ)])
        rc, output = _run_visible(install, label="Installing F3+ packages with uv...", attempts=2)
    else:
        print("      Project-local uv is unavailable; using pip for this setup.")
        install = [
            str(py), "-m", "pip", "install", "--disable-pip-version-check", "--no-cache-dir",
            "--index-url", "https://pypi.org/simple", "--prefer-binary",
        ]
        if force_repair:
            install.extend(["--upgrade", "--force-reinstall"])
        install.extend(["-r", str(REQ)])
        rc, output = _run_visible(install, label="Installing F3+ packages with pip...", attempts=2)

    if rc == 0:
        return
    kind = _failure_kind(output)
    if kind == "disk":
        raise RuntimeError(_disk_error_message())
    if kind == "network":
        reason = "The package-index connection failed. Check firewall/TLS settings and access to pypi.org."
    elif kind == "permission":
        reason = "The operating system denied access to a setup file. Move F3+ to a normal writable folder and try again."
    elif kind == "compatibility":
        reason = "A required binary package is unavailable for this Python/OS combination. Use START_F3PLUS so the supported managed Python runtime is selected."
    else:
        reason = "Read the first ERROR line above for the failing package or system error."
    raise RuntimeError("Python package installation failed. " + reason + " Full output is saved in F3Plus_startup.log.")


def ensure_environment() -> Path:
    _check_python()
    py = _venv_python()
    if VENV.exists() and (not py.exists() or not _python_runs(py)):
        print("[1/3] Existing private environment is incompatible or incomplete. Recreating it...")
        shutil.rmtree(VENV, ignore_errors=True)
    if not py.exists():
        _preflight_disk_space()
        print("[1/3] Creating F3+'s private Python environment...")
        venv.EnvBuilder(with_pip=True, clear=False, symlinks=False).create(VENV)
    else:
        print("[1/3] Private Python environment is ready.")

    wanted = _requirements_hash()
    have = STAMP.read_text(encoding="utf-8").strip() if STAMP.exists() else ""
    packages_ready = _required_packages_present(py)
    if have != wanted or not packages_ready:
        if have == wanted and not packages_ready:
            print("[2/3] A required package is missing or damaged. Repairing the private environment...")
        else:
            print("[2/3] Installing required interface and input packages...")
        print("      Package setup requires internet access; normal launches continue offline when the update check cannot connect.")
        _install_requirements(py, force_repair=(have == wanted and not packages_ready))
        if not _required_packages_present(py):
            raise RuntimeError(
                "Package installation completed, but one or more required modules are still unavailable. "
                "See F3Plus_startup.log for complete output."
            )
        STAMP.write_text(wanted + "\n", encoding="utf-8")
    else:
        print("[2/3] Required Python packages are already installed.")
    return py


def prepare_native_dependencies() -> list[str]:
    warnings: list[str] = []
    print("[3/3] Preparing Minecraft calculation components...")
    try:
        from minescript.seed.bundled import bedrock_status, build_cubiomes
        try:
            build_cubiomes()
            print("      Cubiomes is ready.")
        except Exception as exc:
            warnings.append(
                "Cubiomes could not be prepared. Seed/biome tools that depend on it may be unavailable "
                "until setup succeeds. Details: " + str(exc)
            )
        if bedrock_status().executable:
            print("      Nether Bedrock Cracker is ready.")
        else:
            print("      Nether Bedrock Cracker will be prepared when seed recovery is first opened.")
    except Exception as exc:
        warnings.append("Optional Minecraft components were not fully prepared. Details: " + str(exc))
    return warnings


def main() -> int:
    _ensure_visible_windows_console()
    _enable_startup_log()
    _check_for_updates()
    try:
        in_project_venv = Path(sys.prefix).resolve() == VENV.resolve()
    except (OSError, RuntimeError):
        in_project_venv = False
    if in_project_venv or os.environ.get("F3PLUS_BOOTSTRAPPED") == "1":
        return subprocess.call([sys.executable, str(ROOT / "main.py")], cwd=ROOT)

    print("F3+ setup", flush=True)
    print(f"Using Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n")
    try:
        py = ensure_environment()
        warnings = prepare_native_dependencies()
        if warnings:
            print("\nSetup completed with warnings:")
            for warning in warnings:
                print(" - " + warning)
            print("\nF3+ will open now. Features unrelated to those warnings remain available.")
    except Exception as exc:
        print("\nSETUP COULD NOT FINISH", flush=True)
        print(str(exc), flush=True)
        traceback.print_exc()
        return 2

    print("\nOpening F3+...", flush=True)
    env = os.environ.copy()
    env["F3PLUS_BOOTSTRAPPED"] = "1"
    return subprocess.call([str(py), str(ROOT / "main.py")], cwd=ROOT, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
