from __future__ import annotations

"""Gameplay RNG recovery helpers.

This module is intentionally separate from world-seed recovery.  The native
cracker targets the 48-bit java.util.Random LCG state only.  The optional
EnchantmentCracker integration recovers Minecraft enchantment/player RNG state
through Earthcomputer's external MIT-licensed tool.
"""

from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import platform
import shutil
import stat
import subprocess
import urllib.request
import zipfile

MASK = (1 << 48) - 1
MULT = 0x5DEECE66D
ADD = 0xB
MULT_INV = pow(MULT, -1, 1 << 48)

ENCHCRACKER_VERSION = "1.9"
ENCHCRACKER_URL = f"https://github.com/Earthcomputer/EnchantmentCracker/releases/download/v{ENCHCRACKER_VERSION}/enchcracker-{ENCHCRACKER_VERSION}.zip"
ENCHCRACKER_SHA256 = "8e85f4638dd5b6e2c4d9ccf927e20f8b41a1248276d9db26edd35ab8f09bd34a"

ROOT = Path(__file__).resolve().parents[1]
COMMUNITY_DIR = ROOT / ".runtime" / "community" / "enchantmentcracker"
ARCHIVE = COMMUNITY_DIR / f"enchcracker-{ENCHCRACKER_VERSION}.zip"
EXTRACTED = COMMUNITY_DIR / f"enchcracker-{ENCHCRACKER_VERSION}"


def parse_integer(value: int | str) -> int:
    """Parse decimal or 0x-prefixed signed integer text."""
    if isinstance(value, int):
        return value
    text = str(value).strip().replace("_", "")
    if not text:
        raise ValueError("An integer observation is required.")
    sign = -1 if text.startswith("-") else 1
    unsigned = text[1:] if text[:1] in "+-" else text
    base = 16 if unsigned.lower().startswith("0x") else 10
    return sign * int(unsigned, base)


def _u32(value: int | str) -> int:
    return parse_integer(value) & 0xFFFFFFFF


def next_state(state: int) -> int:
    return (int(state) * MULT + ADD) & MASK


def previous_state(state: int) -> int:
    return ((int(state) - ADD) * MULT_INV) & MASK


def advance_state(state: int, steps: int) -> int:
    """Advance or rewind an LCG state using exponentiation by squaring."""
    steps = int(steps)
    if steps < 0:
        mul, add, n = MULT_INV, (-ADD * MULT_INV) & MASK, -steps
    else:
        mul, add, n = MULT, ADD, steps
    acc_mul, acc_add = 1, 0
    while n:
        if n & 1:
            acc_mul = (acc_mul * mul) & MASK
            acc_add = (acc_add * mul + add) & MASK
        add = (add * (mul + 1)) & MASK
        mul = (mul * mul) & MASK
        n >>= 1
    return (int(state) * acc_mul + acc_add) & MASK


def next_bits_from_state(state_before: int, bits: int) -> tuple[int, int]:
    bits = int(bits)
    if not 1 <= bits <= 32:
        raise ValueError("bits must be between 1 and 32")
    state_after = next_state(state_before)
    return state_after, state_after >> (48 - bits)


def recover_from_next_int_pair(first: int | str, second: int | str) -> list[dict]:
    """Recover java.util.Random state from two consecutive unbounded nextInt outputs.

    nextInt() is next(32).  The first output fixes the high 32 bits of the state
    after that call, leaving only 16 bits to enumerate.  The next observation
    filters those candidates.
    """
    a, b = _u32(first), _u32(second)
    found = []
    high = a << 16
    for low in range(1 << 16):
        state_after_first = high | low
        state_after_second = next_state(state_after_first)
        if (state_after_second >> 16) != b:
            continue
        state_before_first = previous_state(state_after_first)
        canonical_setseed = state_before_first ^ MULT
        found.append({
            "state_before_first_output": state_before_first,
            "state_after_first_output": state_after_first,
            "state_after_second_output": state_after_second,
            "canonical_java_setseed_low48": canonical_setseed & MASK,
            "next_int_prediction": _signed32(next_state(state_after_second) >> 16),
        })
    return found


def _signed32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


def _signed64(value: int) -> int:
    value &= 0xFFFFFFFFFFFFFFFF
    return value - (1 << 64) if value & (1 << 63) else value


def split_java_next_long(value: int | str) -> tuple[int, int]:
    """Recover the two next(32) values combined by java.util.Random.nextLong()."""
    raw = parse_integer(value) & 0xFFFFFFFFFFFFFFFF
    low = raw & 0xFFFFFFFF
    high_result = (raw >> 32) & 0xFFFFFFFF
    # Java computes ((long)next(32) << 32) + next(32), where the second int is
    # sign-extended during addition.  Undo that borrow when the low int is negative.
    first = (high_result + (1 if low & 0x80000000 else 0)) & 0xFFFFFFFF
    return _signed32(first), _signed32(low)


def recover_from_next_long(value: int | str) -> list[dict]:
    first, second = split_java_next_long(value)
    rows = recover_from_next_int_pair(first, second)
    for row in rows:
        row["observed_next_long"] = _signed64(parse_integer(value))
        row["derived_first_next32"] = first
        row["derived_second_next32"] = second
    return rows


def inspect_state(state: int | str, steps: int = 0, count: int = 5) -> dict:
    state0 = parse_integer(state) & MASK
    moved = advance_state(state0, int(steps))
    cur = moved
    outputs = []
    for _ in range(max(1, min(64, int(count)))):
        cur, value = next_bits_from_state(cur, 32)
        outputs.append(_signed32(value))
    return {
        "input_internal_state": state0,
        "steps_applied": int(steps),
        "state_after_steps": moved,
        "next_int_predictions": outputs,
        "state_after_predictions": cur,
    }


def _safe_extract_zip(data: bytes, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    base = dest.resolve()
    with zipfile.ZipFile(__import__('io').BytesIO(data)) as z:
        for info in z.infolist():
            rel = Path(info.filename)
            if not rel.parts:
                continue
            out = (dest / rel).resolve()
            if base not in out.parents and out != base:
                raise RuntimeError("Unsafe EnchantmentCracker ZIP member")
            if info.is_dir():
                out.mkdir(parents=True, exist_ok=True)
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(z.read(info))


def acquire_enchantment_cracker() -> Path:
    """Download and verify Earthcomputer EnchantmentCracker v1.9 on first use."""
    launcher = find_enchantment_cracker_launcher()
    if launcher:
        return launcher
    COMMUNITY_DIR.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(ENCHCRACKER_URL, headers={"User-Agent": "F3Plus/1.16.2 RNG recovery"})
    with urllib.request.urlopen(req, timeout=180) as response:
        data = response.read(32 * 1024 * 1024)
    digest = hashlib.sha256(data).hexdigest()
    if digest.lower() != ENCHCRACKER_SHA256:
        raise RuntimeError(
            "EnchantmentCracker download failed SHA-256 verification. "
            f"Expected {ENCHCRACKER_SHA256}, got {digest}."
        )
    ARCHIVE.write_bytes(data)
    if EXTRACTED.exists():
        shutil.rmtree(EXTRACTED, ignore_errors=True)
    _safe_extract_zip(data, EXTRACTED)
    launcher = find_enchantment_cracker_launcher()
    if not launcher:
        raise RuntimeError("EnchantmentCracker was verified and extracted, but its launcher was not found.")
    if os.name != "nt":
        try:
            launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            pass
    return launcher


def find_enchantment_cracker_launcher() -> Path | None:
    if not EXTRACTED.exists():
        return None
    names = ["enchcracker.bat"] if os.name == "nt" else ["enchcracker"]
    for name in names:
        matches = list(EXTRACTED.rglob(name))
        if matches:
            return matches[0]
    return None


def _java_candidates() -> list[Path]:
    candidates: list[Path] = []
    name = "java.exe" if os.name == "nt" else "java"
    path_java = shutil.which("java")
    if path_java:
        candidates.append(Path(path_java))
    home = Path.home()
    mc_roots = [
        home / ".minecraft",
        home / "AppData/Roaming/.minecraft",
        home / "Library/Application Support/minecraft",
    ]
    for mc in mc_roots:
        runtime = mc / "runtime"
        if runtime.exists():
            candidates.extend(runtime.rglob(name))
    seen = set()
    return [p for p in candidates if p.is_file() and not (str(p.resolve()) in seen or seen.add(str(p.resolve())))]


def find_java() -> Path | None:
    for java in _java_candidates():
        try:
            result = subprocess.run([str(java), "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            if result.returncode == 0:
                return java
        except Exception:
            continue
    return None


def launch_enchantment_cracker() -> subprocess.Popen:
    launcher = acquire_enchantment_cracker()
    env = os.environ.copy()
    java = find_java()
    if java:
        env["JAVA_HOME"] = str(java.parent.parent)
        env["PATH"] = str(java.parent) + os.pathsep + env.get("PATH", "")
    if os.name == "nt":
        return subprocess.Popen(["cmd.exe", "/d", "/c", str(launcher)], cwd=launcher.parent, env=env)
    return subprocess.Popen([str(launcher)], cwd=launcher.parent, env=env)


def enchantment_cracker_status() -> dict:
    launcher = find_enchantment_cracker_launcher()
    return {
        "version": ENCHCRACKER_VERSION,
        "cached": bool(launcher),
        "launcher": str(launcher) if launcher else None,
        "sha256_expected": ENCHCRACKER_SHA256,
        "java_detected": str(find_java()) if find_java() else None,
        "upstream_support": "Minecraft Java 1.8 through 1.21.11 (upstream v1.9 release)",
        "world_seed": "Not used or recovered by this workflow",
    }
