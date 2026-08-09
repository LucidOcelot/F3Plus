from __future__ import annotations

"""Shared radius / expand-until-found behavior for location-oriented seed tools.

The historical catalog keeps one stable feature ID per tool. This layer adds a common
search policy to tools where "nothing found in this area" is meaningful without
changing their underlying calculations.
"""

import math
from typing import Any, Callable

SEARCH_MODES = ["Radius search", "Search until found"]
IGNORE_LIMIT_KEY = "ignore_max_generation_limit"
# This is not a user-facing generation/search limit. It exists only to prevent an
# accidental infinite Python loop if a backend can never satisfy an impossible query.
PROCESS_SAFETY_ATTEMPTS = 4096

_STRUCTURE_TARGETS = {
    "Structure Finder", "Village", "Stronghold", "Trial Chamber", "Ancient City",
    "Woodland Mansion", "Ocean Monument", "Desert Pyramid", "Jungle Temple",
    "Swamp Hut", "Igloo", "Pillager Outpost", "Ruined Portal", "Shipwreck",
    "Ocean Ruin", "Buried Treasure", "Mineshaft", "Nether Fortress", "Bastion",
    "End City", "Compound Search", "Isolated Structure Finder",
    "Structure Cluster Finder", "Multi-Target Locator", "Portal-Optimized Structure Search",
}

_BIOME_FINDERS = {
    "Nearest Biome", "Biome Boundary", "Two-Way Biome Intersection",
    "Three-Way Biome Intersection", "Four-Way Biome Intersection",
}

_TERRAIN_FINDERS = {
    "Flat Terrain Finder", "Valley Finder", "Mountain Peak Finder", "Terrain Base Finder",
    "Island Finder", "Peninsula Detector", "River Crossing Finder", "Cliff Locator",
}

_NETHER_FINDERS = {"Fortress Finder", "Bastion Finder", "Fortress+Bastion Finder"}
_SLIME_FINDERS = {"Adjacent Pair", "2x2 Cluster", "Triple Cluster", "Quad Cluster"}
_SPAWNER_CLUSTER_NAMES = {
    "Double Spawner Locator", "Triple Spawner Locator", "Quad Spawner Locator",
    "Spawner Cluster Ranking",
}

_MATCH_LIST_KEYS = (
    "candidate_chunks", "candidates", "matches", "hits", "clusters", "ranked",
    "sample_hits", "boundary_segments", "pairs", "squares", "locations", "results",
)
_MATCH_SINGLE_KEYS = ("nearest", "peak", "valley", "largest", "best")


def supports_search_mode(spec) -> bool:
    if getattr(spec, "top", "") != "Seed Tools":
        return False
    submenu = getattr(spec, "submenu", "")
    name = getattr(spec, "name", "")
    if submenu == "Spawners":
        return True
    if submenu == "Structures":
        return name in _STRUCTURE_TARGETS
    if submenu == "Biomes":
        return name in _BIOME_FINDERS or name in _TERRAIN_FINDERS
    if submenu == "Nether":
        return name in _NETHER_FINDERS
    if submenu == "Slime":
        return name in _SLIME_FINDERS
    return False


def _unit(spec) -> str:
    name = getattr(spec, "name", "")
    if getattr(spec, "submenu", "") == "Biomes" and name not in _TERRAIN_FINDERS:
        return "blocks"
    return "chunks"


def _defaults_for(spec) -> tuple[int, int]:
    submenu = getattr(spec, "submenu", "")
    name = getattr(spec, "name", "")
    if submenu == "Biomes" and name not in _TERRAIN_FINDERS:
        return 256, 4096
    if submenu == "Spawners":
        return 8, 128
    return 32, 512


def _search_radii(start_radius: int, radius_step: int, maximum_radius: int) -> list[int]:
    start = max(0, int(start_radius))
    step = max(1, int(radius_step))
    maximum = max(start, int(maximum_radius))
    radii = [start]
    current = start
    while current < maximum:
        current = min(maximum, current + step)
        if current != radii[-1]:
            radii.append(current)
    return radii


def _terminal_unavailable(result) -> bool:
    if str(getattr(result, "status", "")).lower() == "unavailable":
        return True
    data = getattr(result, "data", {}) or {}
    if not isinstance(data, dict):
        return False
    if data.get("available") is False:
        return True
    if data.get("requires_generated_world") or data.get("requires_seed_worldgen"):
        return True
    return False


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (str, bytes, list, tuple, set, dict)):
        return bool(value)
    return True


def _has_match(spec, data: dict[str, Any]) -> bool:
    """Return whether a search-oriented result actually found its requested target."""
    if not isinstance(data, dict):
        return False
    name = getattr(spec, "name", "")
    submenu = getattr(spec, "submenu", "")

    if submenu == "Spawners":
        if name in _SPAWNER_CLUSTER_NAMES:
            return _nonempty(data.get("clusters"))
        if "matches_found" in data:
            try:
                return int(data.get("matches_found", 0)) > 0
            except (TypeError, ValueError):
                pass
        return _nonempty(data.get("hits"))

    if name == "Nearest Biome":
        return data.get("nearest") is not None
    if name == "Biome Boundary":
        return _nonempty(data.get("boundary_segments"))
    if name in {"Two-Way Biome Intersection", "Three-Way Biome Intersection", "Four-Way Biome Intersection"}:
        return _nonempty(data.get("candidates"))

    for key in _MATCH_LIST_KEYS:
        if key in data and _nonempty(data.get(key)):
            return True
    for key in _MATCH_SINGLE_KEYS:
        if key in data and data.get(key) is not None:
            return True

    candidate_sets = data.get("candidate_sets")
    if isinstance(candidate_sets, dict) and any(_nonempty(value) for value in candidate_sets.values()):
        return True
    return False


def _exact_regeneration_cap(spec, values: dict[str, Any], requested_max: int) -> tuple[int, str]:
    """Bound exact regenerated spawner expansion unless the user explicitly overrides it."""
    if getattr(spec, "submenu", "") != "Spawners":
        return requested_max, ""
    if str(values.get("world_path", "")).strip() or not bool(values.get("regenerate_from_seed", True)):
        return requested_max, ""
    if bool(values.get(IGNORE_LIMIT_KEY, False)):
        return requested_max, (
            "The configured search/generation maximum is being ignored. Exact reference-world generation may use substantial CPU, memory, disk space, and time."
        )
    try:
        max_chunks = max(1, int(values.get("worldgen_max_chunks", 4096)))
    except (TypeError, ValueError):
        max_chunks = 4096
    cap = max(0, (math.isqrt(max_chunks) - 1) // 2)
    start = max(0, int(values.get("radius", 0)))
    effective = max(start, min(int(requested_max), cap))
    if int(requested_max) > cap:
        return effective, (
            f"Exact regenerated-world search is limited to radius {cap} chunks by the current "
            f"{max_chunks:,}-chunk generation budget. Increase Maximum exact chunks or enable the explicit ignore-limit toggle to search farther."
        )
    return effective, ""


def _decorate(result, summary: dict[str, Any]):
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        updated = dict(data)
        updated["search_summary"] = summary
        result.data = updated
    return result


def _run_until_found(spec, values: dict[str, Any], execute_at_radius: Callable[[int], Any]):
    start = max(0, int(values.get("radius", 0)))
    default_step, default_max = _defaults_for(spec)
    step = max(1, int(values.get("radius_step", default_step)))
    configured_max = max(start, int(values.get("max_search_radius", default_max)))
    ignore_limit = bool(values.get(IGNORE_LIMIT_KEY, False))

    if ignore_limit:
        effective_max = None
        limit_reason = (
            "Configured maximum radius/generation limits are ignored for this run. The search continues outward until a match, a backend error, or the internal runaway-loop guard is reached."
        )
    else:
        effective_max, limit_reason = _exact_regeneration_cap(spec, values, configured_max)

    last = None
    found_radius = None
    attempts = 0
    current = start
    safety_stop = False

    while True:
        if attempts >= PROCESS_SAFETY_ATTEMPTS:
            safety_stop = True
            break
        attempts += 1
        last = execute_at_radius(current)
        if _terminal_unavailable(last):
            break
        if _has_match(spec, getattr(last, "data", {}) or {}):
            found_radius = current
            break
        if not ignore_limit and effective_max is not None and current >= effective_max:
            break
        next_radius = current + step
        if not ignore_limit and effective_max is not None:
            next_radius = min(effective_max, next_radius)
            if next_radius == current:
                break
        current = next_radius

    last_radius = current if attempts else start
    summary = {
        "mode": "Search until found",
        "unit": _unit(spec),
        "start_radius": start,
        "radius_step": step,
        "configured_maximum_radius": configured_max,
        "ignore_maximum_limit": ignore_limit,
        "effective_maximum_radius": effective_max,
        "attempts": attempts,
        "last_radius_searched": last_radius,
        "found": found_radius is not None,
        "found_radius": found_radius,
    }
    if limit_reason:
        summary["limit_note"] = limit_reason
    if safety_stop:
        summary["process_safety_stop"] = (
            f"Stopped after {PROCESS_SAFETY_ATTEMPTS:,} expansion attempts to prevent a non-terminating process. This guard is separate from the user-configured search/generation maximum."
        )
    elif found_radius is None and last is not None and not _terminal_unavailable(last):
        summary["result"] = (
            "No matching target was found before the configured maximum radius."
            if not ignore_limit
            else "No match was found before the search ended because the backend became unavailable."
        )
    return last, summary


def _terrain_fields(spec):
    """Terrain locators scan generated chunks, so their radius is in chunks, not biome-sample blocks."""
    return [
        ("world_path", "Generated world path", "", "text"),
        ("dimension", "Dimension", ["Overworld", "Nether", "End"], "choice"),
        ("cx", "Center chunk X", 0, "int"),
        ("cz", "Center chunk Z", 0, "int"),
        ("radius", "Search radius (chunks)", 32, "int"),
    ]


def _prepare_unbounded_exact_generation(spec, values: dict[str, Any], radius: int) -> dict[str, Any]:
    """Raise the per-attempt exact-generation budget when the user knowingly bypasses it."""
    attempt = dict(values)
    attempt["radius"] = radius
    if not bool(values.get(IGNORE_LIMIT_KEY, False)):
        return attempt
    if getattr(spec, "submenu", "") != "Spawners":
        return attempt
    if str(values.get("world_path", "")).strip() or not bool(values.get("regenerate_from_seed", True)):
        return attempt
    required = (2 * max(0, int(radius)) + 1) ** 2
    try:
        configured = max(1, int(values.get("worldgen_max_chunks", 4096)))
    except (TypeError, ValueError):
        configured = 4096
    attempt["worldgen_max_chunks"] = max(configured, required)
    return attempt


def install() -> None:
    from . import descriptions, tool_guides
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_search_modes_v234_installed", False):
        return

    previous_fields = FeatureExecutor.input_fields
    previous_execute = FeatureExecutor.execute

    def input_fields(self, feature):
        spec = self.spec(feature)
        if getattr(spec, "submenu", "") == "Biomes" and getattr(spec, "name", "") in _TERRAIN_FINDERS:
            fields = _terrain_fields(spec)
        else:
            fields = list(previous_fields(self, spec))
        if not supports_search_mode(spec):
            return fields
        existing = {field[0] for field in fields}
        if "radius" not in existing:
            unit = _unit(spec)
            default_radius = 256 if unit == "blocks" else 8
            fields.append(("radius", f"Search radius ({unit})", default_radius, "int"))
            existing.add("radius")
        unit = _unit(spec)
        default_step, default_max = _defaults_for(spec)
        additions = [
            ("search_mode", "Search mode", SEARCH_MODES, "choice"),
            ("radius_step", f"Until-found expansion step ({unit})", default_step, "int"),
            ("max_search_radius", f"Until-found maximum radius ({unit})", default_max, "int"),
            (IGNORE_LIMIT_KEY, "Ignore maximum search / generation limit", False, "bool"),
        ]
        fields.extend(field for field in additions if field[0] not in existing)
        return fields

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        if not supports_search_mode(spec):
            return previous_execute(self, spec, params, dry_run)

        values = self.defaults(spec)
        values.update(params or {})
        mode = str(values.get("search_mode", SEARCH_MODES[0]))
        if dry_run or mode != "Search until found":
            result = previous_execute(self, spec, values, dry_run)
            if not dry_run:
                radius = max(0, int(values.get("radius", 0)))
                _decorate(result, {
                    "mode": "Radius search",
                    "unit": _unit(spec),
                    "radius": radius,
                    "found": _has_match(spec, getattr(result, "data", {}) or {}),
                    "ignore_maximum_limit": False,
                })
            return result

        def execute_at_radius(radius: int):
            attempt = _prepare_unbounded_exact_generation(spec, values, radius)
            return previous_execute(self, spec, attempt, False)

        result, summary = _run_until_found(spec, values, execute_at_radius)
        return _decorate(result, summary)

    current = descriptions.SPECIAL.get("Dungeon/Pig Spawner Locator", "")
    if "Search until found" not in current:
        descriptions.SPECIAL["Dungeon/Pig Spawner Locator"] = (
            current.rstrip(".")
            + ". Choose Radius search for one bounded area or Search until found to expand outward until a matching spawner is found. The explicit ignore-limit toggle can bypass the configured maximum, including the exact-generation chunk budget."
        )
    tool_guides._OUTPUT_EXACT["Dungeon/Pig Spawner Locator"] = (
        "Returns the selected spawner type, mob identity when encoded in NBT, block position, chunk, distance from the reference, map-ready hits, and the complete bounded/until-found search summary."
    )

    FeatureExecutor.input_fields = input_fields
    FeatureExecutor.execute = execute
    FeatureExecutor._search_modes_v234_installed = True
