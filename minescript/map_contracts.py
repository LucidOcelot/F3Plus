from __future__ import annotations

"""Conservative coordinate extraction for the legacy top-level Open Map action.

The canonical in-workbench result renderer has operation-specific visual contracts. The
main-window result card does not retain the originating FeatureSpec, so this fallback
accepts only explicitly coordinate-named result fields and coordinate dictionaries. It
never interprets an arbitrary numeric pair as X/Z merely because it has length two.
"""

import math
from collections import defaultdict
from typing import Any


_BLOCK_LIST_KEYS = {
    "positions", "points", "vertices", "corners", "strand_a", "strand_b",
    "route_order", "resource_order", "tour_order", "biome_order", "survey_points",
    "route", "portals", "nether_gates", "nearest_samples", "biome_samples",
}
_CHUNK_LIST_KEYS = {"candidate_chunks", "slime_chunks", "chunks"}
_CONTAINER_KEYS = {
    "candidate_sets", "structure_candidates", "structures", "clusters", "ranked",
    "samples", "hits", "candidates", "matches", "results", "nearest", "peak",
    "valley", "largest", "best", "center", "target", "start", "finish",
}


def _num(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _dict_point(value: dict[str, Any]):
    x, z = _num(value.get("x")), _num(value.get("z"))
    if x is not None and z is not None:
        return x, z
    cx, cz = _num(value.get("chunk_x")), _num(value.get("chunk_z"))
    if cx is not None and cz is not None:
        return cx * 16 + 8, cz * 16 + 8
    for key in ("position", "block_center", "candidate_block_center", "nearest_border_point", "target_block", "midpoint", "nether"):
        raw = value.get(key)
        if isinstance(raw, (list, tuple)) and len(raw) >= 2:
            a = _num(raw[0]); b = _num(raw[2] if len(raw) >= 3 else raw[1])
            if a is not None and b is not None:
                return a, b
    for key in ("chunk", "candidate_chunk", "reference_chunk", "center_chunk"):
        raw = value.get(key)
        if isinstance(raw, (list, tuple)) and len(raw) >= 2:
            a, b = _num(raw[0]), _num(raw[1])
            if a is not None and b is not None:
                return a * 16 + 8, b * 16 + 8
    return None


def _named_sequence_point(row, *, chunk=False):
    if isinstance(row, dict):
        point = _dict_point(row)
        return point
    if not isinstance(row, (list, tuple)):
        return None
    if len(row) >= 4 and isinstance(row[0], str):
        x, z = _num(row[1]), _num(row[3])
    elif len(row) >= 3:
        x, z = _num(row[0]), _num(row[2])
    elif len(row) >= 2:
        x, z = _num(row[0]), _num(row[1])
    else:
        return None
    if x is None or z is None:
        return None
    return (x * 16 + 8, z * 16 + 8) if chunk else (x, z)


def extract_coordinate_layers(data: Any) -> dict[str, list[tuple[float, float, str]]]:
    layers: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
    seen: set[tuple[str, float, float]] = set()

    def add(layer: str, point, detail: str):
        if point is None:
            return
        x, z = point
        key = (layer, round(float(x), 6), round(float(z), 6))
        if key in seen:
            return
        seen.add(key)
        layers[layer].append((float(x), float(z), detail))

    def walk(node: Any, path: str = "Results", named_key: str = "", depth: int = 0):
        if depth > 7:
            return
        if isinstance(node, dict):
            add(path.split(".", 1)[0], _dict_point(node), path)
            for key, child in node.items():
                low = str(key).lower()
                child_path = f"{path}.{key}" if path else str(key)
                if low in _CHUNK_LIST_KEYS and isinstance(child, (list, tuple)):
                    for index, row in enumerate(child[:4000]):
                        add(str(key).replace("_", " ").title(), _named_sequence_point(row, chunk=True), f"{child_path}[{index}] (chunk center)")
                elif low in _BLOCK_LIST_KEYS and isinstance(child, (list, tuple)):
                    for index, row in enumerate(child[:4000]):
                        add(str(key).replace("_", " ").title(), _named_sequence_point(row), f"{child_path}[{index}]")
                elif low in _CONTAINER_KEYS or isinstance(child, dict):
                    walk(child, child_path, low, depth + 1)
        elif isinstance(node, (list, tuple)) and named_key in _CONTAINER_KEYS:
            for index, child in enumerate(node[:4000]):
                if isinstance(child, dict):
                    add(path.split(".", 1)[0], _dict_point(child), f"{path}[{index}]")
                    walk(child, f"{path}[{index}]", named_key, depth + 1)

    walk(data)
    return {key: value for key, value in layers.items() if value}


__all__ = ["extract_coordinate_layers"]
