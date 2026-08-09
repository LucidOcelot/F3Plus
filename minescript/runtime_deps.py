from __future__ import annotations

"""Runtime bootstrap for optional native community components.

F3+ is offline-first. Cubiomes source is bundled and built locally on
first use. Nether Bedrock Cracker is downloaded only when its single world-seed
recovery workflow is invoked (or when explicitly bootstrapped).
"""

import hashlib
import io
import json
import os
import platform
import shutil
import stat
import tarfile
import urllib.request
import zipfile
from pathlib import Path

from .version import USER_AGENT

ROOT = Path(__file__).resolve().parents[1]
THIRD_PARTY = ROOT / "third_party"
CACHE = THIRD_PARTY / "_bootstrap"

NBC_VERSION = "0.3.0"
NBC_SOURCE_URL = f"https://github.com/19MisterX98/Nether_Bedrock_Cracker/archive/refs/tags/{NBC_VERSION}.zip"
NBC_BINARY_URLS = {
    "Windows": f"https://github.com/19MisterX98/Nether_Bedrock_Cracker/releases/download/{NBC_VERSION}/cracker_gui-x86_64-pc-windows-msvc.exe",
    "Darwin": f"https://github.com/19MisterX98/Nether_Bedrock_Cracker/releases/download/{NBC_VERSION}/cracker_gui-x86_64-apple-darwin",
    "Linux": f"https://github.com/19MisterX98/Nether_Bedrock_Cracker/releases/download/{NBC_VERSION}/bedrock_cracker-x86_64-unknown-linux-gnu",
}
NBC_BINARY_SHA256 = {
    "Windows": "d6f8c3c8cb6645e789cfdc6a020b881e60a724926b0122e49b946b6497176cd9",
}

ZIG_VERSION = "0.13.0"
ZIG_URLS = {
    ("Windows", "x86_64"): f"https://ziglang.org/download/{ZIG_VERSION}/zig-windows-x86_64-{ZIG_VERSION}.zip",
    ("Darwin", "x86_64"): f"https://ziglang.org/download/{ZIG_VERSION}/zig-macos-x86_64-{ZIG_VERSION}.tar.xz",
    ("Darwin", "arm64"): f"https://ziglang.org/download/{ZIG_VERSION}/zig-macos-aarch64-{ZIG_VERSION}.tar.xz",
    ("Linux", "x86_64"): f"https://ziglang.org/download/{ZIG_VERSION}/zig-linux-x86_64-{ZIG_VERSION}.tar.xz",
    ("Linux", "arm64"): f"https://ziglang.org/download/{ZIG_VERSION}/zig-linux-aarch64-{ZIG_VERSION}.tar.xz",
}
ZIG_SHA256 = {
    ("Windows", "x86_64"): "d859994725ef9402381e557c60bb57497215682e355204d754ee3df75ee3c158",
    ("Darwin", "x86_64"): "8b06ed1091b2269b700b3b07f8e3be3b833000841bae5aa6a09b1a8b4773effd",
    ("Darwin", "arm64"): "46fae219656545dfaf4dce12fb4e8685cec5b51d721beee9389ab4194d43394c",
    ("Linux", "x86_64"): "d45312e61ebcc48032b77bc4cf7fd6915c11fa16e4aad116b66c9468211230ea",
    ("Linux", "arm64"): "041ac42323837eb5624068acd8b00cd5777dac4cf91179e8dad7a7e90dd0c556",
}


def _machine() -> str:
    m = platform.machine().lower()
    if m in {"amd64", "x86_64"}: return "x86_64"
    if m in {"arm64", "aarch64"}: return "arm64"
    return m


def _fetch(url: str, *, timeout: int = 180, max_bytes: int = 512 * 1024 * 1024) -> bytes:
    """Fetch one pinned upstream payload with a hard size limit."""
    req = urllib.request.Request(url, headers={"User-Agent": f"{USER_AGENT} dependency bootstrap"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        length = r.headers.get("Content-Length")
        if length and int(length) > max_bytes:
            raise RuntimeError("Dependency download is unexpectedly large")
        data = r.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise RuntimeError("Dependency download exceeded the safety limit")
        return data


def _safe_zip(data: bytes, dest: Path, strip_top: bool = False) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = [n for n in z.namelist() if n and not n.endswith("/")]
        top = None
        if strip_top:
            tops = {Path(n).parts[0] for n in names if Path(n).parts}
            if len(tops) == 1: top = next(iter(tops))
        for info in z.infolist():
            rel = Path(info.filename)
            if top and rel.parts and rel.parts[0] == top:
                rel = Path(*rel.parts[1:])
            if not rel.parts: continue
            out = (dest / rel).resolve()
            if dest.resolve() not in out.parents and out != dest.resolve():
                raise RuntimeError("Unsafe ZIP member")
            if info.is_dir():
                out.mkdir(parents=True, exist_ok=True)
            else:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(z.read(info))


def _safe_tar_xz(data: bytes, dest: Path) -> None:
    """Extract a trusted-shape tar.xz without path traversal, links, or device nodes."""
    dest.mkdir(parents=True, exist_ok=True)
    base = dest.resolve()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:xz") as t:
        members = t.getmembers()
        for member in members:
            rel = Path(member.name)
            out = (dest / rel).resolve()
            if base not in out.parents and out != base:
                raise RuntimeError("Unsafe tar member path")
            if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                raise RuntimeError("Unsafe tar member type")
        for member in members:
            if member.isdir():
                (dest / member.name).mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                out = dest / member.name
                out.parent.mkdir(parents=True, exist_ok=True)
                src = t.extractfile(member)
                if src is None:
                    raise RuntimeError("Archive member could not be read")
                with src, open(out, "wb") as fh:
                    shutil.copyfileobj(src, fh)
                try:
                    os.chmod(out, member.mode & 0o777)
                except OSError:
                    pass


def acquire_nether_bedrock_cracker(*, include_source: bool = True) -> dict:
    """Acquire the maintained upstream cracker into third_party.

    The platform binary is preferred so Windows/macOS users do not need Rust.
    Source is also retained when requested to satisfy LGPL relinking/source
    expectations and provide a build fallback.
    """
    bed = THIRD_PARTY / "nether_bedrock_cracker"
    bin_dir = bed / "bin"
    src_dir = bed / "source"
    bin_dir.mkdir(parents=True, exist_ok=True)
    system = platform.system()
    if system not in NBC_BINARY_URLS:
        raise RuntimeError(f"Unsupported platform for automatic Nether Bedrock Cracker acquisition: {system}")
    url = NBC_BINARY_URLS[system]
    name = url.rsplit("/", 1)[-1]
    binary_path = bin_dir / name
    manifest = {"version": NBC_VERSION, "binary_url": url}
    expected = NBC_BINARY_SHA256.get(system)
    if not expected:
        raise RuntimeError(
            f"No independently pinned SHA-256 is available for the {system} Nether Bedrock Cracker 0.3.0 binary. "
            "F3+ will not execute an unverified downloaded binary; use the bundled source with Rust/Cargo instead."
        )
    if not binary_path.exists():
        payload = _fetch(url)
        actual = hashlib.sha256(payload).hexdigest()
        if actual.lower() != expected.lower():
            raise RuntimeError(f"Nether Bedrock Cracker SHA-256 mismatch: expected {expected}, got {actual}")
        tmp = binary_path.with_suffix(binary_path.suffix + ".download")
        tmp.write_bytes(payload)
        tmp.replace(binary_path)
        manifest["binary_sha256"] = actual
    else:
        actual = hashlib.sha256(binary_path.read_bytes()).hexdigest()
        if actual.lower() != expected.lower():
            binary_path.unlink(missing_ok=True)
            raise RuntimeError(f"Cached Nether Bedrock Cracker failed SHA-256 verification: expected {expected}, got {actual}")
        manifest["binary_sha256"] = actual
    if system != "Windows":
        binary_path.chmod(binary_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if include_source and not (src_dir / "Cargo.toml").exists():
        raise RuntimeError(
            "Bundled Nether Bedrock Cracker source is missing. F3+ will not replace it with an unverified source archive; re-extract the complete release."
        )
    (bed / "ACQUISITION.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"binary": str(binary_path), "source": str(src_dir) if (src_dir / "Cargo.toml").exists() else None, **manifest}


def acquire_zig_cc() -> Path:
    system, machine = platform.system(), _machine()
    key = (system, machine)
    url = ZIG_URLS.get(key)
    if not url:
        raise RuntimeError(f"No automatic Zig compiler bootstrap for {system}/{machine}")
    dest = CACHE / f"zig-{ZIG_VERSION}-{system.lower()}-{machine}"
    exe_name = "zig.exe" if system == "Windows" else "zig"
    existing = next(dest.rglob(exe_name), None) if dest.exists() else None
    if existing:
        return existing
    payload = _fetch(url, timeout=300)
    expected = ZIG_SHA256[key]
    actual = hashlib.sha256(payload).hexdigest()
    if actual.lower() != expected.lower():
        raise RuntimeError(f"Zig SHA-256 mismatch: expected {expected}, got {actual}")
    dest.mkdir(parents=True, exist_ok=True)
    if url.endswith(".zip"):
        _safe_zip(payload, dest)
    else:
        _safe_tar_xz(payload, dest)
    exe = next(dest.rglob(exe_name), None)
    if not exe:
        raise RuntimeError("Downloaded Zig archive did not contain the compiler")
    if system != "Windows": exe.chmod(exe.stat().st_mode | 0o111)
    (dest / "F3PLUS_BOOTSTRAP.json").write_text(json.dumps({"url": url, "sha256": hashlib.sha256(payload).hexdigest()}, indent=2) + "\n")
    return exe


def find_or_acquire_c_compiler() -> tuple[list[str], str]:
    for name in ("cc", "clang", "gcc", "cl"):
        path = shutil.which(name)
        if path:
            return [path], name
    zig = acquire_zig_cc()
    return [str(zig), "cc"], "zig cc"
