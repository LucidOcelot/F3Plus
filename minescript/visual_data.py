from __future__ import annotations

"""Pure visual-data preparation for F3+ workbenches.

This module intentionally has no Qt dependency. It converts structured calculator/world
results into coordinate rows and plot series; the desktop UI chooses how to render them.
"""

import math
from collections import defaultdict
from typing import Any


def _num(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def coordinate_rows(name: str, value: list | tuple) -> list[dict[str, Any]] | None:
    if not value or not all(isinstance(row, (list, tuple)) for row in value):
        return None
    widths = {len(row) for row in value if isinstance(row, (list, tuple))}
    if len(widths) != 1:
        return None
    width = next(iter(widths))
    low = name.lower()
    chunkish = any(token in low for token in (
        "candidate", "chunk", "village", "trial chamber", "ocean monument", "outpost",
        "ancient city", "ruined portal", "slime", "fortress", "bastion", "end city",
    ))
    rows: list[dict[str, Any]] = []
    if width == 2:
        for row in value[:250]:
            x, z = row
            if chunkish and isinstance(x, (int, float)) and isinstance(z, (int, float)):
                rows.append({
                    "Chunk X": x, "Chunk Z": z,
                    "Block center X": int(x) * 16 + 8,
                    "Block center Z": int(z) * 16 + 8,
                })
            else:
                rows.append({"X": x, "Z": z})
        return rows
    if width == 3:
        biome_like = "biome" in low or "sample" in low
        for row in value[:250]:
            a, b, c = row
            if biome_like and all(isinstance(q, (int, float)) for q in row):
                try:
                    from .analysis_reports_v2 import biome_name
                    label = biome_name(c)
                except Exception:
                    label = str(c)
                rows.append({"Block X": a, "Block Z": b, "Biome": label})
            else:
                rows.append({"X": a, "Y": b, "Z": c})
        return rows
    if width == 4 and all(isinstance(row[0], str) for row in value):
        return [{"Name": row[0], "X": row[1], "Y": row[2], "Z": row[3]} for row in value[:250]]
    return None


_CONSTRUCTION_SCHEMAS = {
    "Area": [("width", "Width (blocks)", 16, "int"), ("length", "Length (blocks)", 20, "int")],
    "Perimeter": [("width", "Width (blocks)", 16, "int"), ("length", "Length (blocks)", 20, "int")],
    "Foundation Planner": [("width", "Foundation width", 16, "int"), ("length", "Foundation length", 20, "int")],
    "Volume": [("width", "Width", 16, "int"), ("length", "Length", 20, "int"), ("height", "Height", 8, "int")],
    "Surface Area": [("width", "Width", 16, "int"), ("length", "Length", 20, "int"), ("height", "Height", 8, "int")],
    "Block Count": [("width", "Width", 16, "int"), ("length", "Length", 20, "int"), ("height", "Height", 8, "int")],
    "Stacks": [("width", "Build width", 16, "int"), ("length", "Build length", 20, "int"), ("height", "Build height", 8, "int")],
    "Shulkers": [("width", "Build width", 16, "int"), ("length", "Build length", 20, "int"), ("height", "Build height", 8, "int")],
    "Double Chests": [("width", "Build width", 16, "int"), ("length", "Build length", 20, "int"), ("height", "Build height", 8, "int")],
    "Stair Calculator": [("height", "Vertical rise (blocks)", 8, "int"), ("spacing", "Horizontal run per step", 1, "int")],
    "Spiral Staircase Planner": [("width", "Diameter (blocks)", 9, "int"), ("height", "Total height", 16, "int"), ("spacing", "Steps per turn", 12, "int")],
    "Catenary Calculator": [("length", "Span (blocks)", 32, "int"), ("sag", "Center sag (blocks)", 6.0, "float"), ("height", "End height difference", 0, "int")],
    "Roof Pitch": [("width", "Horizontal run", 12, "int"), ("height", "Vertical rise", 6, "int")],
    "Wall Segments": [("width", "Width", 16, "int"), ("length", "Length", 20, "int"), ("spacing", "Target segment length", 4, "int")],
    "Bridge Span": [("length", "Bridge span", 64, "int"), ("spacing", "Support spacing", 8, "int")],
    "Grid": [("width", "Grid width", 32, "int"), ("length", "Grid length", 32, "int"), ("spacing", "Grid spacing", 4, "int")],
    "Lighting Grid": [("width", "Area width", 32, "int"), ("length", "Area length", 32, "int"), ("spacing", "Light spacing", 8, "int")],
    "Pillar Spacing": [("width", "Structure width", 32, "int"), ("length", "Structure length", 32, "int"), ("spacing", "Maximum pillar spacing", 8, "int")],
    "Road Planner": [("length", "Road length", 128, "int"), ("width", "Road width", 5, "int"), ("spacing", "Marker spacing", 16, "int")],
    "Crop Layout": [("width", "Farm width", 32, "int"), ("length", "Farm length", 32, "int"), ("spacing", "Crop spacing", 1, "int")],
    "Gradient Ratio": [("length", "Horizontal run", 32, "int"), ("height", "Vertical rise", 8, "int")],
    "Chunk Grid Builder": [("width", "Width (blocks)", 64, "int"), ("length", "Length (blocks)", 64, "int")],
    "Beacon Offset": [("width", "Build width", 32, "int"), ("length", "Build length", 32, "int"), ("height", "Beacon pyramid level", 4, "int")],
}


def construction_fields(name: str):
    fields = _CONSTRUCTION_SCHEMAS.get(name)
    return list(fields) if fields is not None else None


def shape_fields(name: str):
    if name in {"Circle", "Filled Circle", "Sphere", "Hollow Sphere", "Dome", "Hexagon", "Octagon", "Diamond", "Arch"}:
        return [("radius", "Radius (blocks)", 8, "int")]
    if name in {"Cylinder", "Cone"}:
        return [("radius", "Radius (blocks)", 8, "int"), ("height", "Height (blocks)", 12, "int")]
    if name in {"Spiral", "Helix", "Double Helix"}:
        return [("radius", "Radius", 8, "int"), ("height", "Height / turns", 12, "int")]
    if name == "Ellipse":
        return [("radius", "X radius", 8, "int"), ("secondary", "Z radius", 5, "int")]
    if name == "Pyramid":
        return [("radius", "Base half-width", 8, "int"), ("height", "Height", 8, "int")]
    if name == "Rounded Rectangle":
        return [("radius", "Corner radius", 4, "int"), ("secondary", "Straight section", 12, "int")]
    return None


def _point_from(value, *, pair_is_xz=False):
    if isinstance(value, dict):
        for key in ("position", "block_center", "candidate_block_center", "nearest_border_point", "target_block", "midpoint"):
            if key in value:
                point = _point_from(value[key])
                if point is not None:
                    return point
        for key in ("chunk", "candidate_chunk", "reference_chunk", "center_chunk"):
            if key in value:
                raw = value[key]
                if isinstance(raw, (list, tuple)) and len(raw) >= 2:
                    x, z = _num(raw[0]), _num(raw[1])
                    if x is not None and z is not None:
                        return x * 16 + 8, z * 16 + 8
        x = _num(value.get("x")); z = _num(value.get("z"))
        if x is not None and z is not None:
            return x, z
        return None
    if isinstance(value, (list, tuple)):
        if pair_is_xz and len(value) >= 2:
            x, z = _num(value[0]), _num(value[1])
            return (x, z) if x is not None and z is not None else None
        if len(value) >= 3:
            x, z = _num(value[0]), _num(value[2])
            return (x, z) if x is not None and z is not None else None
        if len(value) >= 2:
            x, z = _num(value[0]), _num(value[1])
            return (x, z) if x is not None and z is not None else None
    return None


def _list_points(value, *, chunk_pairs=False, pair_is_xz=False, limit=1800):
    points = []
    if not isinstance(value, (list, tuple)):
        return points
    for row in value[:limit]:
        if chunk_pairs and isinstance(row, (list, tuple)) and len(row) >= 2:
            x, z = _num(row[0]), _num(row[1])
            if x is not None and z is not None:
                points.append((x * 16 + 8, z * 16 + 8)); continue
        point = _point_from(row, pair_is_xz=pair_is_xz)
        if point is not None:
            points.append(point)
    return points


def seed_series(data: Any) -> tuple[list[tuple[str, list[tuple[float, float]]]], tuple[float, float] | None]:
    series: list[tuple[str, list[tuple[float, float]]]] = []
    center = None
    if isinstance(data, dict):
        for key in ("center_chunk", "reference_chunk"):
            raw = data.get(key)
            if isinstance(raw, (list, tuple)) and len(raw) >= 2:
                x, z = _num(raw[0]), _num(raw[1])
                if x is not None and z is not None:
                    center = (x * 16 + 8, z * 16 + 8); break
    seen = set()

    def add(label, points):
        clean = []
        for point in points:
            key = (round(point[0], 5), round(point[1], 5))
            if key not in seen:
                seen.add(key); clean.append(point)
        if clean and len(series) < 7:
            series.append((str(label).replace("_", " ").title(), clean))

    def walk(node, parent="", depth=0):
        if depth > 6 or len(series) >= 7:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                low = str(key).lower()
                if low in {"candidate_sets", "structure_candidates", "structures"} and isinstance(value, dict):
                    for label, rows in value.items(): add(label, _list_points(rows, chunk_pairs=True))
                    continue
                if low in {"candidate_chunks", "slime_chunks", "chunks"}:
                    add(key, _list_points(value, chunk_pairs=True)); continue
                if low in {"nearest_samples", "biome_samples"}:
                    add(key, _list_points(value, pair_is_xz=True)); continue
                if low in {"hits", "targets", "ranked_sites", "suggested_first_stops", "compound_candidates"} and isinstance(value, list):
                    grouped: dict[str, list[tuple[float, float]]] = {}
                    for row in value:
                        if not isinstance(row, dict): continue
                        point = _point_from(row)
                        if point is None: continue
                        label = row.get("structure") or row.get("type") or row.get("spawner_kind") or row.get("anchor_type") or key
                        if row.get("mobs"): label = "/".join(row.get("mobs") or [])
                        grouped.setdefault(str(label), []).append(point)
                    for label, points in grouped.items(): add(label, points)
                    if grouped: continue
                if low in {"positions", "points", "vertices", "corners", "strand_a", "strand_b", "route_order"}:
                    add(key, _list_points(value)); continue
                if isinstance(value, (dict, list, tuple)): walk(value, str(key), depth + 1)
        elif isinstance(node, (list, tuple)):
            points = _list_points(node)
            if points: add(parent or "Locations", points)
    walk(data)
    return series, center


def construction_series(spec, data: Any):
    series, _ = seed_series(data)
    if series:
        return series
    if not isinstance(data, dict):
        return []
    width = _num(data.get("width_blocks", data.get("width")))
    length = _num(data.get("length_blocks", data.get("length")))
    if width is not None and length is not None and width > 0 and length > 0:
        return [("Footprint", [(0, 0), (width, 0), (width, length), (0, length), (0, 0)])]
    radius = _num(data.get("radius_blocks", data.get("radius")))
    if radius is not None and radius > 0 and getattr(spec, "submenu", "") == "Shapes":
        return [("Shape footprint", [(radius * math.cos(i * math.tau / 96), radius * math.sin(i * math.tau / 96)) for i in range(97)])]
    return []


def extract_coordinate_layers(data: Any) -> dict[str, list[tuple[float, float, str]]]:
    layers: dict[str, list[tuple[float, float, str]]] = defaultdict(list)

    def walk(value: Any, path: str):
        if isinstance(value, dict):
            if isinstance(value.get("x"), (int, float)) and isinstance(value.get("z"), (int, float)):
                layers[path or "Results"].append((float(value["x"]), float(value["z"]), path))
            elif isinstance(value.get("chunk_x"), (int, float)) and isinstance(value.get("chunk_z"), (int, float)):
                layers[path or "Results"].append((float(value["chunk_x"]) * 16 + 8, float(value["chunk_z"]) * 16 + 8, path + " (chunk center)"))
            for key, child in value.items(): walk(child, f"{path}.{key}" if path else str(key))
        elif isinstance(value, (list, tuple)):
            if len(value) in (2, 3) and all(isinstance(x, (int, float)) for x in value):
                x, z = (value[0], value[1]) if len(value) == 2 else (value[0], value[2])
                layers[path or "Results"].append((float(x), float(z), path))
            else:
                for index, child in enumerate(value): walk(child, f"{path}[{index}]")
    walk(data, "")
    compact: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
    for path, points in layers.items():
        key = path.split(".", 1)[0].split("[", 1)[0] or "Results"
        compact[key].extend(points)
    return {key: value for key, value in compact.items() if value}


def visual_ui_capabilities() -> tuple[str, ...]:
    return (
        "wheel zoom", "drag pan", "fit to data", "series visibility",
        "point labels", "copy visible coordinates",
    )
