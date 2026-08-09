from __future__ import annotations

"""One authoritative view of selected, data, and world-generation versions.

The selected Minecraft version is never silently rewritten.  Backends that cannot
support it receive an explicit fallback version and the UI can surface that choice.
"""

from dataclasses import dataclass
import re


LATEST_CUBIOMES_RELEASE = "1.21.3"
LATEST_CUBIOMES_ENUM = 27


@dataclass(frozen=True)
class VersionContext:
    selected: str
    calculation_version: str
    calculation_enum: int
    calculation_exact: bool
    calculation_reason: str
    data_version: str | None = None
    data_exact: bool = False

    @property
    def uses_worldgen_fallback(self) -> bool:
        return not self.calculation_exact


def _numeric_prefix(value: str) -> tuple[int, ...] | None:
    match = re.search(r"(?<!\d)(\d+(?:\.\d+){1,2})", str(value or ""))
    if not match:
        return None
    try:
        return tuple(int(part) for part in match.group(1).split("."))
    except ValueError:
        return None


def _stable_sort_key(value: str):
    text = str(value or "").lower()
    nums = _numeric_prefix(text) or ()
    snapshot = 1 if any(token in text for token in ("snapshot", "pre", "rc", "experimental")) else 0
    return (*nums, -snapshot, text)


def _installed_data_version(selected: str) -> tuple[str | None, bool]:
    try:
        from .villagers import installed_versions
        versions = installed_versions()
    except Exception:
        versions = {}
    if not versions:
        return None, False
    wanted = str(selected or "").strip().lower().replace(" ", "-")
    for name in versions:
        if name.lower().replace(" ", "-") == wanted:
            return name, True
    stable = [
        name for name in versions
        if not any(token in name.lower() for token in ("snapshot", "pre", "rc", "experimental"))
    ]
    pool = stable or list(versions)
    return max(pool, key=_stable_sort_key), False


def resolve(selected: str) -> VersionContext:
    from .world.versioning import cubiomes_resolution

    selected = str(selected or "").strip() or "unknown"
    worldgen = cubiomes_resolution(selected)
    data_version, data_exact = _installed_data_version(selected)
    return VersionContext(
        selected=selected,
        calculation_version=worldgen["calculation_version"],
        calculation_enum=int(worldgen["cubiomes_enum"]),
        calculation_exact=bool(worldgen["exact"]),
        calculation_reason=str(worldgen.get("reason", "")),
        data_version=data_version,
        data_exact=data_exact,
    )
