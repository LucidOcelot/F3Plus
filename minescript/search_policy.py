from __future__ import annotations

"""Shared bounded / expand-until-found search policy for location tools."""

import math
from typing import Any, Callable

SEARCH_MODES = ["Radius search", "Search until found"]
IGNORE_LIMIT_KEY = "ignore_max_generation_limit"
PROCESS_SAFETY_ATTEMPTS = 4096

_STRUCTURE_TARGETS = {
    "Structure Finder", "Village", "Stronghold", "Trial Chamber", "Ancient City",
    "Woodland Mansion", "Ocean Monument", "Desert Pyramid", "Jungle Temple", "Swamp Hut",
    "Igloo", "Pillager Outpost", "Ruined Portal", "Shipwreck", "Ocean Ruin",
    "Buried Treasure", "Mineshaft", "Nether Fortress", "Bastion", "End City",
    "Compound Search", "Isolated Structure Finder", "Structure Cluster Finder",
    "Multi-Target Locator", "Portal-Optimized Structure Search",
}
_BIOME_FINDERS = {"Nearest Biome", "Biome Boundary", "Two-Way Biome Intersection", "Three-Way Biome Intersection", "Four-Way Biome Intersection"}
_TERRAIN_FINDERS = {"Flat Terrain Finder", "Valley Finder", "Mountain Peak Finder", "Terrain Base Finder", "Island Finder", "Peninsula Detector", "River Crossing Finder", "Cliff Locator"}
_NETHER_FINDERS = {"Fortress Finder", "Bastion Finder", "Fortress+Bastion Finder"}
_SLIME_FINDERS = {"Adjacent Pair", "2x2 Cluster", "Triple Cluster", "Quad Cluster"}
_SPAWNER_CLUSTER_NAMES = {"Double Spawner Locator", "Triple Spawner Locator", "Quad Spawner Locator", "Spawner Cluster Ranking"}
_MATCH_LIST_KEYS = ("candidate_chunks", "candidates", "matches", "hits", "clusters", "ranked", "sample_hits", "boundary_segments", "pairs", "squares", "locations", "results")
_MATCH_SINGLE_KEYS = ("nearest", "peak", "valley", "largest", "best")


def supports(spec) -> bool:
    if getattr(spec, "top", "") != "Seed Tools": return False
    submenu, name = getattr(spec, "submenu", ""), getattr(spec, "name", "")
    if submenu == "Spawners": return True
    if submenu == "Structures": return name in _STRUCTURE_TARGETS
    if submenu == "Biomes": return name in _BIOME_FINDERS or name in _TERRAIN_FINDERS
    if submenu == "Nether": return name in _NETHER_FINDERS
    if submenu == "Slime": return name in _SLIME_FINDERS
    return False


def unit(spec) -> str:
    return "blocks" if getattr(spec, "submenu", "") == "Biomes" and getattr(spec, "name", "") not in _TERRAIN_FINDERS else "chunks"


def defaults_for(spec) -> tuple[int, int]:
    submenu, name = getattr(spec, "submenu", ""), getattr(spec, "name", "")
    if submenu == "Biomes" and name not in _TERRAIN_FINDERS: return 256, 4096
    if submenu == "Spawners": return 8, 128
    return 32, 512


def terrain_fields():
    return [
        ("world_path", "Generated world path", "", "text"),
        ("dimension", "Dimension", ["Overworld", "Nether", "End"], "choice"),
        ("cx", "Center chunk X", 0, "int"), ("cz", "Center chunk Z", 0, "int"),
        ("radius", "Search radius (chunks)", 32, "int"),
    ]


def add_fields(spec, fields):
    fields = terrain_fields() if getattr(spec, "submenu", "") == "Biomes" and getattr(spec, "name", "") in _TERRAIN_FINDERS else list(fields)
    if not supports(spec): return fields
    existing = {field[0] for field in fields}
    if "radius" not in existing:
        u = unit(spec); fields.append(("radius", f"Search radius ({u})", 256 if u == "blocks" else 8, "int")); existing.add("radius")
    u = unit(spec); step, maximum = defaults_for(spec)
    additions = [
        ("search_mode", "Search mode", SEARCH_MODES, "choice"),
        ("radius_step", f"Until-found expansion step ({u})", step, "int"),
        ("max_search_radius", f"Until-found maximum radius ({u})", maximum, "int"),
        (IGNORE_LIMIT_KEY, "Ignore maximum search / generation limit", False, "bool"),
    ]
    fields.extend(field for field in additions if field[0] not in existing)
    return fields


def terminal_unavailable(result) -> bool:
    if str(getattr(result, "status", "")).lower() == "unavailable": return True
    data = getattr(result, "data", {}) or {}
    if not isinstance(data, dict): return False
    return bool(
        data.get("available") is False
        or data.get("requires_generated_world")
        or data.get("requires_seed_worldgen")
    )


def _nonempty(value: Any) -> bool:
    if value is None: return False
    if isinstance(value, bool): return value
    if isinstance(value, (str, bytes, list, tuple, set, dict)): return bool(value)
    return True


def has_match(spec, data: dict[str, Any]) -> bool:
    if not isinstance(data, dict): return False
    name, submenu = getattr(spec, "name", ""), getattr(spec, "submenu", "")
    if submenu == "Spawners":
        if name in _SPAWNER_CLUSTER_NAMES: return _nonempty(data.get("clusters"))
        if "matches_found" in data:
            try: return int(data.get("matches_found", 0)) > 0
            except (TypeError, ValueError): pass
        return _nonempty(data.get("hits"))
    if name == "Nearest Biome": return data.get("nearest") is not None
    if name == "Biome Boundary": return _nonempty(data.get("boundary_segments"))
    if name in {"Two-Way Biome Intersection", "Three-Way Biome Intersection", "Four-Way Biome Intersection"}: return _nonempty(data.get("candidates"))
    for key in _MATCH_LIST_KEYS:
        if key in data and _nonempty(data.get(key)): return True
    for key in _MATCH_SINGLE_KEYS:
        if key in data and data.get(key) is not None: return True
    sets = data.get("candidate_sets")
    return isinstance(sets, dict) and any(_nonempty(value) for value in sets.values())


def exact_regeneration_cap(spec, values: dict[str, Any], requested_max: int) -> tuple[int, str]:
    if getattr(spec, "submenu", "") != "Spawners": return requested_max, ""
    if str(values.get("world_path", "")).strip() or not bool(values.get("regenerate_from_seed", True)): return requested_max, ""
    if bool(values.get(IGNORE_LIMIT_KEY, False)):
        return requested_max, "The configured search/generation maximum is being ignored. Exact reference-world generation may use substantial CPU, memory, disk space, and time."
    try: max_chunks = max(1, int(values.get("worldgen_max_chunks", 4096)))
    except (TypeError, ValueError): max_chunks = 4096
    cap = max(0, (math.isqrt(max_chunks) - 1) // 2); start = max(0, int(values.get("radius", 0))); effective = max(start, min(int(requested_max), cap))
    if int(requested_max) > cap:
        return effective, f"Exact regenerated-world search is limited to radius {cap} chunks by the current {max_chunks:,}-chunk generation budget. Increase Maximum exact chunks or enable the explicit ignore-limit toggle to search farther."
    return effective, ""


def decorate(result, summary: dict[str, Any]):
    data = getattr(result, "data", None)
    if isinstance(data, dict): result.data = {**data, "search_summary": summary}
    return result


def prepare_attempt(spec, values: dict[str, Any], radius: int) -> dict[str, Any]:
    attempt = dict(values); attempt["radius"] = radius
    if not bool(values.get(IGNORE_LIMIT_KEY, False)) or getattr(spec, "submenu", "") != "Spawners": return attempt
    if str(values.get("world_path", "")).strip() or not bool(values.get("regenerate_from_seed", True)): return attempt
    required = (2 * max(0, int(radius)) + 1) ** 2
    try: configured = max(1, int(values.get("worldgen_max_chunks", 4096)))
    except (TypeError, ValueError): configured = 4096
    attempt["worldgen_max_chunks"] = max(configured, required); return attempt


def run_until_found(spec, values: dict[str, Any], execute_at_radius: Callable[[int], Any]):
    start = max(0, int(values.get("radius", 0))); default_step, default_max = defaults_for(spec)
    step = max(1, int(values.get("radius_step", default_step))); configured_max = max(start, int(values.get("max_search_radius", default_max))); ignore = bool(values.get(IGNORE_LIMIT_KEY, False))
    if ignore:
        effective_max = None; limit_reason = "Configured maximum radius/generation limits are ignored for this run. The search continues until a match, backend error, or internal runaway-loop guard."
    else: effective_max, limit_reason = exact_regeneration_cap(spec, values, configured_max)
    last = None; found_radius = None; attempts = 0; current = start; last_searched = None; safety_stop = False; backend_unavailable = False
    while True:
        if attempts >= PROCESS_SAFETY_ATTEMPTS: safety_stop = True; break
        candidate = execute_at_radius(current)
        if terminal_unavailable(candidate):
            last = candidate; backend_unavailable = True; break
        last = candidate; attempts += 1; last_searched = current
        if has_match(spec, getattr(last, "data", {}) or {}): found_radius = current; break
        if not ignore and effective_max is not None and current >= effective_max: break
        next_radius = current + step
        if not ignore and effective_max is not None:
            next_radius = min(effective_max, next_radius)
            if next_radius == current: break
        current = next_radius
    summary = {
        "mode": "Search until found", "unit": unit(spec), "start_radius": start,
        "radius_step": step, "configured_maximum_radius": configured_max,
        "ignore_maximum_limit": ignore, "effective_maximum_radius": effective_max,
        "attempts": attempts, "last_radius_searched": last_searched,
        "found": found_radius is not None, "found_radius": found_radius,
    }
    if limit_reason: summary["limit_note"] = limit_reason
    if backend_unavailable:
        summary["stop_reason"] = "Search did not start because the required backend/data source or generated-world prerequisite is unavailable. Fix the reported prerequisite and run again."
    elif safety_stop:
        summary["process_safety_stop"] = f"Stopped after {PROCESS_SAFETY_ATTEMPTS:,} expansion attempts to prevent a non-terminating process."
    elif found_radius is None:
        summary["result"] = "No matching target was found before the configured maximum radius." if not ignore else "No match was found before the backend ended the search."
    return last, summary
