from __future__ import annotations

"""Explicit visualization contracts for canonical results.

Visuals are selected from the operation identity and named result fields. F3+ never
interprets arbitrary two-number arrays as coordinates or arbitrary numeric dictionaries
as distributions.
"""

import math
from typing import Any


def _number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _point(value, *, chunk=False):
    if isinstance(value, dict):
        if "x" in value and "z" in value:
            x, z = _number(value.get("x")), _number(value.get("z"))
            return (x, z) if x is not None and z is not None else None
        for key in ("position", "block_center", "candidate_block_center", "nearest_border_point", "target_block", "midpoint", "nether"):
            if key in value:
                return _point(value[key])
        for key in ("chunk", "candidate_chunk", "reference_chunk", "center_chunk"):
            if key in value:
                return _point(value[key], chunk=True)
        return None
    if not isinstance(value, (list, tuple)):
        return None
    if len(value) >= 4 and isinstance(value[0], str):
        x, z = _number(value[1]), _number(value[3])
    elif len(value) >= 3:
        x, z = _number(value[0]), _number(value[2])
    elif len(value) >= 2:
        x, z = _number(value[0]), _number(value[1])
    else:
        return None
    if x is None or z is None:
        return None
    return (x * 16 + 8, z * 16 + 8) if chunk else (x, z)


def _points(rows, *, chunk=False, limit=4000):
    if not isinstance(rows, (list, tuple)):
        return []
    out = []
    for row in rows[:limit]:
        point = _point(row, chunk=chunk)
        if point is not None:
            out.append(point)
    return out


def _dedupe(points):
    seen = set(); out = []
    for x, z in points:
        key = (round(float(x), 6), round(float(z), 6))
        if key not in seen:
            seen.add(key); out.append((float(x), float(z)))
    return out


def _add(series, label, points):
    clean = _dedupe(points)
    if clean:
        series.append((str(label), clean))


def _named_points(data: dict, names: tuple[str, ...], *, chunk=False):
    series = []
    for key in names:
        if key in data:
            _add(series, key.replace("_", " ").title(), _points(data[key], chunk=chunk))
    return series


def map_series(spec, data: Any):
    """Return ``(series, center)`` only for operations with a declared spatial meaning."""
    if not isinstance(data, dict):
        return [], None
    top = str(getattr(spec, "top", "")); sub = str(getattr(spec, "submenu", "")); name = str(getattr(spec, "name", "")); series = []; center = None

    if sub == "Shapes":
        for key in ("points", "vertices", "strand_a", "strand_b"):
            if key in data: _add(series, key.replace("_", " ").title(), _points(data[key]))
        if not series and name == "Rounded Rectangle":
            width, length = _number(data.get("width")), _number(data.get("length"))
            if width and length: _add(series, "Footprint", [(0, 0), (width, 0), (width, length), (0, length), (0, 0)])
        return series, None

    if top == "Calculators" and sub == "Build":
        for key in ("points", "positions", "corners"):
            if key in data: _add(series, key.replace("_", " ").title(), _points(data[key]))
        width = _number(data.get("width_blocks", data.get("width"))); length = _number(data.get("length_blocks", data.get("length")))
        if not series and width and length and name in {"Area", "Perimeter", "Foundation Planner", "Road Planner", "Crop Layout", "Chunk Grid Builder"}:
            _add(series, "Footprint", [(0, 0), (width, 0), (width, length), (0, length), (0, 0)])
        return series, None

    if top == "Navigation" and sub in {"Routes", "Waypoints"}:
        for key in ("route_order", "resource_order", "tour_order", "biome_order", "survey_points", "points", "route"):
            if key in data: _add(series, key.replace("_", " ").title(), _points(data[key]))
        start = _point(data.get("start")); target = _point(data.get("target"))
        if start is not None and target is not None: _add(series, "Route", [start, target])
        elif start is not None: center = start
        return series, center

    if sub in {"Portal Helpers", "Nether"}:
        nodes = data.get("nodes")
        if isinstance(nodes, (list, tuple)): _add(series, "Portals", _points(nodes))
        for key in ("portals", "nether_gates", "route_order", "samples", "ranked"):
            if key in data: _add(series, key.replace("_", " ").title(), _points(data[key]))
        center = _point(data.get("center")) or _point(data.get("ideal_nether"))
        return series, center

    if top == "Seed Tools" and sub in {"Slime", "Structures", "Spawners", "Biomes", "Local Area", "World Analysis"}:
        center = _point(data.get("center_chunk"), chunk=True) or _point(data.get("reference_chunk"), chunk=True)
        for key in ("candidate_chunks", "slime_chunks", "chunks"):
            if key in data: _add(series, key.replace("_", " ").title(), _points(data[key], chunk=True))
        candidate_sets = data.get("candidate_sets") or data.get("structure_candidates")
        if isinstance(candidate_sets, dict):
            for label, rows in candidate_sets.items(): _add(series, str(label), _points(rows, chunk=True))
        for key in ("nearest_samples", "biome_samples", "positions", "points", "ranked"):
            if key in data: _add(series, key.replace("_", " ").title(), _points(data[key]))
        for key in ("peak", "valley", "nearest", "largest"):
            point = _point(data.get(key))
            if point is not None: _add(series, key.title(), [point])
        return series, center

    return [], None


def _dict_rows(value, limit=128):
    if not isinstance(value, dict): return []
    rows = []
    for key, raw in list(value.items())[:limit]:
        number = _number(raw)
        if number is not None: rows.append((str(key), number))
    return rows


def _list_value_rows(value, field: str, label_field: str | None = None, limit=512):
    if not isinstance(value, (list, tuple)): return []
    rows = []
    for index, item in enumerate(value[:limit]):
        if isinstance(item, dict):
            number = _number(item.get(field))
            label = str(item.get(label_field, index + 1)) if label_field else str(index + 1)
            if number is not None: rows.append((label, number))
        else:
            number = _number(item)
            if number is not None: rows.append((str(index + 1), number))
    return rows


_CHART_FIELDS = {
    "Ore Distribution": ("ore_counts", "bars"),
    "Ore Exposure Estimate": ("exposed_ore_counts", "bars"),
    "Biome Composition": ("biome_counts", "bars"),
    "Structure Counts": ("structure_counts", "bars"),
    "RNG Sequence Viewer": ("values", "line"),
    "RNG Timeline": ("timeline", "line"),
}


def chart_series(spec, data: Any):
    """Return ``(title, rows, kind)`` for explicitly chartable operation outputs."""
    if not isinstance(data, dict): return None
    name = str(getattr(spec, "name", ""))
    contract = _CHART_FIELDS.get(name)
    if contract:
        key, kind = contract; value = data.get(key)
        if isinstance(value, dict): rows = _dict_rows(value)
        elif name == "RNG Sequence Viewer": rows = _list_value_rows(value, "decimal")
        elif name == "RNG Timeline": rows = _list_value_rows(value, "value")
        else: rows = _list_value_rows(value, "value")
        return (key.replace("_", " ").title(), rows, kind) if len(rows) >= 2 else None

    if name == "Loot Table Simulator":
        rows = _list_value_rows(data.get("results"), "observed_percent", "label")
        return ("Observed result percent", rows, "bars") if len(rows) >= 2 else None

    if name in {"Fishing Loot Simulator", "Piglin Barter Simulator", "Mob Drop Simulator", "Archaeology Loot Simulator", "Trial Chamber Loot Simulator", "Trial Spawner Reward Simulator", "Structure Loot Simulator"}:
        rows = _dict_rows(data.get("counts"))
        return ("Observed counts", rows, "bars") if len(rows) >= 2 else None

    if name in {"Rare Drop Odds", "Barter Odds", "Trial Reward Odds", "Enchantment Odds"}:
        rows = _list_value_rows(data.get("confidence_thresholds"), "attempts_needed", "confidence_percent")
        return ("Attempts by confidence", rows, "bars") if len(rows) >= 2 else None

    return None
