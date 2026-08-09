from __future__ import annotations

"""Waypoint lookup, distance sorting, and route construction semantics."""

import math
from typing import Any


def _direction(dx: float, dz: float) -> str:
    if dx == 0 and dz == 0:
        return "here"
    angle = (math.degrees(math.atan2(dx, -dz)) + 360.0) % 360.0
    names = ("north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest")
    return names[int((angle + 22.5) // 45.0) % 8]


def _saved_waypoints(executor) -> list[dict[str, Any]]:
    settings = getattr(executor, "settings", None)
    saved = dict(getattr(settings, "waypoints", {}) or {}) if settings is not None else {}
    rows = []
    for name, value in saved.items():
        try:
            x, y, z = float(value[0]), float(value[1]), float(value[2])
        except (TypeError, ValueError, IndexError):
            continue
        rows.append({"name": str(name), "x": x, "y": y, "z": z})
    return rows


def _from_origin(row: dict[str, Any], x: float, y: float, z: float) -> dict[str, Any]:
    dx, dy, dz = row["x"] - x, row["y"] - y, row["z"] - z
    horizontal = math.hypot(dx, dz)
    return {
        **row,
        "horizontal_distance_blocks": round(horizontal, 2),
        "distance_3d_blocks": round(math.sqrt(horizontal * horizontal + dy * dy), 2),
        "vertical_change_blocks": round(dy, 2),
        "direction": _direction(dx, dz),
    }


def _waypoint_report(executor, name: str, p: dict[str, Any]) -> dict[str, Any]:
    points = _saved_waypoints(executor)
    if not points:
        return {
            "available": False,
            "requires_saved_waypoints": True,
            "reason": "Save at least one waypoint in F3+ before running this waypoint operation.",
        }
    x, y, z = float(p.get("x1", 0.0)), float(p.get("y1", 64.0)), float(p.get("z1", 0.0))
    measured = [_from_origin(row, x, y, z) for row in points]

    if name == "Nearest Waypoint":
        nearest = min(measured, key=lambda row: float(row["distance_3d_blocks"]))
        return {
            "purpose": "Find the single saved waypoint nearest to the supplied/current position.",
            "origin": [x, y, z], "nearest_waypoint": nearest,
            "saved_waypoint_count": len(points),
        }

    if name == "Sort Waypoints by Distance":
        measured.sort(key=lambda row: float(row["distance_3d_blocks"]))
        for index, row in enumerate(measured, 1):
            row["rank"] = index
        return {
            "purpose": "Sort every saved waypoint independently by straight-line distance from the origin.",
            "origin": [x, y, z], "waypoints_by_distance": measured,
            "saved_waypoint_count": len(points),
            "note": "This is not a travel route; every distance is measured from the same origin.",
        }

    remaining = list(points)
    current = {"name": "Origin", "x": x, "y": y, "z": z}
    stops = []
    segments = []
    total = 0.0
    while remaining:
        nxt = min(remaining, key=lambda row: math.hypot(row["x"] - current["x"], row["z"] - current["z"]))
        dx, dy, dz = nxt["x"] - current["x"], nxt["y"] - current["y"], nxt["z"] - current["z"]
        horizontal = math.hypot(dx, dz)
        distance3 = math.sqrt(horizontal * horizontal + dy * dy)
        segments.append({
            "from": current["name"], "to": nxt["name"],
            "horizontal_distance_blocks": round(horizontal, 2),
            "distance_3d_blocks": round(distance3, 2),
            "direction": _direction(dx, dz),
        })
        total += horizontal
        stops.append(nxt)
        remaining.remove(nxt)
        current = nxt
    return_to_start = bool(p.get("return_to_start", False))
    if return_to_start and stops:
        horizontal = math.hypot(x - current["x"], z - current["z"])
        segments.append({
            "from": current["name"], "to": "Origin",
            "horizontal_distance_blocks": round(horizontal, 2),
            "distance_3d_blocks": round(math.dist((current["x"], current["y"], current["z"]), (x, y, z)), 2),
            "direction": _direction(x - current["x"], z - current["z"]),
        })
        total += horizontal
    return {
        "purpose": "Create a greedy nearest-next travel route through all saved waypoints.",
        "origin": [x, y, z],
        "route_order": [row["name"] for row in stops],
        "segments": segments,
        "total_horizontal_route_blocks": round(total, 2),
        "return_to_start": return_to_start,
        "routing_method": "greedy nearest-next; not claimed globally optimal",
    }
