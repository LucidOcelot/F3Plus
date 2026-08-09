from __future__ import annotations

from dataclasses import dataclass
import re

from ..version import TARGET_MINECRAFT_ID

TARGET_VERSION = TARGET_MINECRAFT_ID
LATEST_CUBIOMES_RELEASE = "1.21.3"
LATEST_CUBIOMES_ENUM = 27


class UnsupportedMinecraftVersion(ValueError):
    """Retained for callers that explicitly require exact generation support."""


@dataclass(frozen=True)
class FeatureSupport:
    feature: str
    selected_version: str
    implementation_version: str
    source: str
    confidence: str
    exact: bool
    note: str = ""


NATIVE = {
    "coordinates": TARGET_VERSION,
    "slime_chunks": TARGET_VERSION,
    "portal_math": TARGET_VERSION,
    "build_calculators": TARGET_VERSION,
    "macro_engine": TARGET_VERSION,
}

_CUBIOMES_EXACT = {
    "1.0": 3, "1.1": 4, "1.2": 5, "1.3": 6, "1.4": 7, "1.5": 8,
    "1.6": 9, "1.7": 10, "1.8": 11, "1.9": 12, "1.10": 13,
    "1.11": 14, "1.12": 15, "1.13": 16, "1.14": 17, "1.15": 18,
    "1.16.1": 19, "1.16.5": 20, "1.17": 21, "1.18": 22,
    "1.19.2": 23, "1.19.4": 24, "1.20.6": 25, "1.21.1": 26,
    "1.21.3": 27,
}

_ENUM_VERSION = {value: key for key, value in _CUBIOMES_EXACT.items()}


def _numeric_prefix(version: str) -> str:
    match = re.search(r"(?<!\d)(\d+(?:\.\d+){1,2})", str(version))
    if not match:
        raise UnsupportedMinecraftVersion(f"Unrecognized Minecraft version: {version!r}")
    return match.group(1)


def _mapped_version(raw: str) -> tuple[int, str] | None:
    if raw in _CUBIOMES_EXACT:
        return _CUBIOMES_EXACT[raw], raw
    parts = tuple(int(part) for part in raw.split("."))
    if parts[:2] == (1, 16) and len(parts) >= 3:
        return (19, "1.16.1") if parts[2] == 1 else (20, "1.16.5")
    if parts[:2] == (1, 19) and len(parts) >= 3:
        if parts[2] <= 2:
            return 23, "1.19.2"
        if parts[2] <= 4:
            return 24, "1.19.4"
    if parts[:2] == (1, 20) and len(parts) >= 3 and parts[2] <= 6:
        return 25, "1.20.6"
    if parts[:2] == (1, 21) and len(parts) >= 3:
        if parts[2] <= 1:
            return 26, "1.21.1"
        if parts[2] <= 3:
            return 27, "1.21.3"
    return None


def cubiomes_resolution(version: str) -> dict:
    """Resolve the selected version to the safest bundled Cubiomes rules.

    Unsupported versions keep the selected version visible, warn the user, and
    calculate against the newest stable release explicitly supported by the bundled
    Cubiomes revision.
    """
    selected = str(version or "").strip() or "unknown"
    try:
        raw = _numeric_prefix(selected)
        mapped = _mapped_version(raw)
    except (UnsupportedMinecraftVersion, ValueError):
        raw = ""
        mapped = None

    if mapped is not None:
        enum, implementation = mapped
        exact = raw == implementation
        reason = "" if exact else (
            f"Bundled Cubiomes does not have an exact {selected} ruleset; "
            f"calculations use its supported {implementation} rules."
        )
        return {
            "selected_version": selected,
            "calculation_version": implementation,
            "cubiomes_enum": enum,
            "exact": exact,
            "fallback": not exact,
            "reason": reason,
        }

    return {
        "selected_version": selected,
        "calculation_version": LATEST_CUBIOMES_RELEASE,
        "cubiomes_enum": LATEST_CUBIOMES_ENUM,
        "exact": False,
        "fallback": True,
        "reason": (
            f"Bundled Cubiomes does not implement Minecraft {selected}. "
            f"World-generation calculations use the newest stable release supported "
            f"by this build ({LATEST_CUBIOMES_RELEASE}) instead. Results are not exact "
            f"for {selected}."
        ),
    }


def cubiomes_enum_for_version(version: str) -> int:
    """Return the enum used for calculations, including the explicit stable fallback."""
    return int(cubiomes_resolution(version)["cubiomes_enum"])


def require_exact_cubiomes_mc(version: str) -> int:
    """Return a Cubiomes enum only when the selected version itself is exact."""
    resolved = cubiomes_resolution(version)
    if not resolved["exact"]:
        raise UnsupportedMinecraftVersion(str(resolved["reason"]))
    return int(resolved["cubiomes_enum"])


def resolve_cubiomes_mc(version: str) -> int:
    """Return the effective bundled Cubiomes enum for a selected Minecraft version."""
    return cubiomes_enum_for_version(version)


def cubiomes_support(version: str) -> dict:
    resolved = cubiomes_resolution(version)
    return {
        "supported": bool(resolved["exact"]),
        "selected_supported": bool(resolved["exact"]),
        "selected_version": resolved["selected_version"],
        "calculation_version": resolved["calculation_version"],
        "cubiomes_enum": resolved["cubiomes_enum"],
        "exact_version_mapping": bool(resolved["exact"]),
        "fallback_used": bool(resolved["fallback"]),
        "reason": resolved["reason"],
    }


def resolve_native(feature: str, selected_version: str = TARGET_VERSION):
    implementation = NATIVE.get(feature)
    if implementation:
        return FeatureSupport(feature, selected_version, implementation, "F3+", "Native", True)
    return None
