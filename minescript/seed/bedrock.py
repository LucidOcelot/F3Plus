from __future__ import annotations
from pathlib import Path
import os, shutil, subprocess, platform
from .bundled import bedrock_status
from ..runtime_deps import acquire_nether_bedrock_cracker

ALLOWED_WORLD_SEED_RECOVERY = 'nether_bedrock'


def _mark_executable(path: Path) -> Path:
    if os.name != 'nt':
        path.chmod(path.stat().st_mode | 0o111)
    return path


def executable() -> Path:
    """Return a runnable Nether Bedrock Cracker.

    Prefer a bundled/cached executable. If only source is bundled, first try to
    acquire the pinned upstream platform binary so end users do not need Rust.
    If acquisition is unavailable (for example offline first run), build the
    bundled source when Cargo is installed.
    """
    status = bedrock_status()
    if status.executable:
        return _mark_executable(status.executable)

    source = status.source_dir if (status.source_dir / 'Cargo.toml').exists() else None
    acquire_error: Exception | None = None
    try:
        acquire_nether_bedrock_cracker(include_source=(source is None))
        status = bedrock_status()
        if status.executable:
            return _mark_executable(status.executable)
        if source is None and (status.source_dir / 'Cargo.toml').exists():
            source = status.source_dir
    except Exception as exc:
        acquire_error = exc

    if source is None:
        detail = f' Automatic acquisition failed: {acquire_error}' if acquire_error else ''
        raise RuntimeError('Nether Bedrock Cracker executable/source is unavailable.' + detail)

    cargo = shutil.which('cargo')
    if not cargo:
        detail = f' Automatic binary acquisition failed: {acquire_error}' if acquire_error else ''
        raise RuntimeError('Nether Bedrock Cracker needs its platform binary or Rust/Cargo to build the bundled source.' + detail)

    subprocess.run([cargo, 'build', '--release', '--bin', 'cracker_gui'], cwd=source, check=True)
    built = source / 'target' / 'release' / ('cracker_gui.exe' if os.name == 'nt' else 'cracker_gui')
    if built.exists():
        return _mark_executable(built)
    status = bedrock_status()
    if status.executable:
        return _mark_executable(status.executable)
    raise RuntimeError('Nether Bedrock Cracker built but executable was not found.')


def launch(extra_args: list[str] | None = None) -> subprocess.Popen:
    """Launch the maintained cracker; no alternative world-seed recovery is provided."""
    exe = executable()
    args=[str(exe), *(extra_args or [])]
    if platform.system()=='Darwin' and platform.machine().lower() in {'arm64','aarch64'}:
        arch=shutil.which('arch')
        if arch: args=[arch,'-x86_64',*args]
    return subprocess.Popen(args, cwd=exe.parent)
