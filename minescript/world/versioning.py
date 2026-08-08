from __future__ import annotations

from dataclasses import dataclass
import re

TARGET_VERSION = "26.3-snapshot-7"


class UnsupportedMinecraftVersion(ValueError):
    pass


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


def _numeric_prefix(version: str) -> str:
    match = re.search(r"(?<!\d)(\d+(?:\.\d+){1,2})", str(version))
    if not match:
        raise UnsupportedMinecraftVersion(f"Unrecognized Minecraft version: {version!r}")
    return match.group(1)


def cubiomes_enum_for_version(version: str) -> int:
    raw = _numeric_prefix(version)
    if raw in _CUBIOMES_EXACT:
        return _CUBIOMES_EXACT[raw]
    parts = tuple(int(part) for part in raw.split("."))
    if parts[0] >= 26:
        raise UnsupportedMinecraftVersion(
            f"Bundled Cubiomes does not yet implement Minecraft {version}. "
            "F3+ will not substitute an older world-generation version."
        )
    if parts[:2] == (1, 16) and len(parts) >= 3:
        return 19 if parts[2] == 1 else 20
    if parts[:2] == (1, 19) and len(parts) >= 3:
        if parts[2] <= 2:
            return 23
        if parts[2] <= 4:
            return 24
    if parts[:2] == (1, 20) and len(parts) >= 3 and parts[2] <= 6:
        return 25
    if parts[:2] == (1, 21) and len(parts) >= 3:
        if parts[2] <= 1:
            return 26
        if parts[2] <= 3:
            return 27
    raise UnsupportedMinecraftVersion(
        f"Minecraft {version} does not have an explicit bundled Cubiomes mapping in this build."
    )


def cubiomes_support(version: str) -> dict:
    try:
        enum = cubiomes_enum_for_version(version)
        return {
            "supported": True,
            "selected_version": version,
            "cubiomes_enum": enum,
            "exact_version_mapping": True,
        }
    except UnsupportedMinecraftVersion as exc:
        return {
            "supported": False,
            "selected_version": version,
            "cubiomes_enum": None,
            "reason": str(exc),
        }


def resolve_native(feature: str, selected_version: str = TARGET_VERSION):
    implementation = NATIVE.get(feature)
    if implementation:
        return FeatureSupport(feature, selected_version, implementation, "F3+", "Native", True)
    return None
