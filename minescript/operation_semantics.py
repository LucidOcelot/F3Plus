from __future__ import annotations

"""Final 2.x semantic cleanup for catalog entries that still shared one report.

The catalog intentionally preserves historical IDs, but a different button must either
perform a different job or clearly act as a named view over shared math.  This layer is
installed last so it can replace the remaining generic/duplicate families without
changing stable IDs or the underlying reusable calculation engines.
"""

import math
from collections import Counter
from typing import Any


INTERNAL_RESULT_KEYS = {
    "implementation", "implementation_detail", "operation", "display_name",
    "source", "backend", "mc_enum",
}


def _friendly_duration(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    if seconds < 3600:
        minutes = int(seconds // 60)
        rest = seconds - minutes * 60
        return f"{minutes} min {rest:.0f} sec"
    hours = int(seconds // 3600)
    minutes = int((seconds - hours * 3600) // 60)
    return f"{hours} hr {minutes} min"


def _direction(dx: float, dz: float) -> str:
    if abs(dx) < 1e-9 and abs(dz) < 1e-9:
        return "at the origin"
    angle = (math.degrees(math.atan2(dx, -dz)) + 360.0) % 360.0
    names = ("north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest")
    return names[int((angle + 22.5) // 45.0) % 8]


def _bearing(dx: float, dz: float) -> float:
    return (math.degrees(math.atan2(-dx, dz)) + 360.0) % 360.0


def _parse_points(text: Any, prefix: str = "Stop") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for token in str(text or "").split(";"):
        parts = [part.strip() for part in token.split(",")]
        if len(parts) < 3:
            continue
        try:
            x, y, z = map(float, parts[:3])
        except ValueError:
            continue
        label = parts[3] if len(parts) > 3 and parts[3] else f"{prefix} {len(rows) + 1}"
        rows.append({"name": label, "x": x, "y": y, "z": z})
    return rows


def _distance3(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.dist((float(a["x"]), float(a["y"]), float(a["z"])), (float(b["x"]), float(b["y"]), float(b["z"])))


def _horizontal(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.hypot(float(b["x"]) - float(a["x"]), float(b["z"]) - float(a["z"]))


def _greedy_route(start: dict[str, Any], stops: list[dict[str, Any]], return_to_start: bool = False):
    remaining = list(stops)
    current = start
    ordered: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []
    total = 0.0
    while remaining:
        nxt = min(remaining, key=lambda row: _horizontal(current, row))
        dist = _horizontal(current, nxt)
        dx = nxt["x"] - current["x"]
        dz = nxt["z"] - current["z"]
        segments.append({
            "from": current["name"], "to": nxt["name"],
            "horizontal_blocks": round(dist, 2),
            "direction": _direction(dx, dz),
        })
        total += dist
        ordered.append(nxt)
        remaining.remove(nxt)
        current = nxt
    if return_to_start and ordered:
        dist = _horizontal(current, start)
        segments.append({
            "from": current["name"], "to": start["name"],
            "horizontal_blocks": round(dist, 2),
            "direction": _direction(start["x"] - current["x"], start["z"] - current["z"]),
        })
        total += dist
    return ordered, segments, total


def _navigation_coordinate(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    x1 = float(p.get("x1", p.get("x", 0.0)))
    y1 = float(p.get("y1", 64.0))
    z1 = float(p.get("z1", p.get("z", 0.0)))
    x2 = float(p.get("x2", 100.0))
    y2 = float(p.get("y2", 70.0))
    z2 = float(p.get("z2", 100.0))
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1

    if name == "Distance":
        horizontal = math.hypot(dx, dz)
        return {
            "purpose": "Travel-oriented distance between two Minecraft positions",
            "start": [x1, y1, z1], "target": [x2, y2, z2],
            "horizontal_distance_blocks": round(horizontal, 3),
            "distance_3d_blocks": round(math.sqrt(horizontal * horizontal + dy * dy), 3),
            "vertical_change_blocks": round(dy, 3),
            "bearing_degrees": round(_bearing(dx, dz), 2),
            "direction": _direction(dx, dz),
        }
    if name == "Midpoint":
        midpoint = [(x1 + x2) / 2.0, (y1 + y2) / 2.0, (z1 + z2) / 2.0]
        return {
            "purpose": "Find the halfway build/travel coordinate",
            "midpoint": midpoint,
            "midpoint_chunk": [math.floor(midpoint[0] / 16), math.floor(midpoint[2] / 16)],
            "distance_from_each_endpoint_blocks": round(math.dist((x1, y1, z1), tuple(midpoint)), 3),
        }
    if name == "Delta XYZ":
        return {
            "purpose": "Signed coordinate change from start to target",
            "delta_x": dx, "delta_y": dy, "delta_z": dz,
            "horizontal_change_blocks": round(math.hypot(dx, dz), 3),
            "direction": _direction(dx, dz),
        }
    if name == "Travel Time":
        distance = max(0.0, float(p.get("distance", 1000.0)))
        speed = max(0.001, float(p.get("speed", 5.6)))
        seconds = distance / speed
        return {
            "purpose": "Estimate travel time from a supplied movement speed",
            "distance_blocks": distance,
            "speed_blocks_per_second": speed,
            "travel_seconds": round(seconds, 3),
            "travel_time": _friendly_duration(seconds),
        }
    if name == "Chunk Border":
        x = float(p.get("x", 80)); z = float(p.get("z", -48))
        cx, cz = math.floor(x / 16), math.floor(z / 16)
        xmin, xmax = cx * 16, cx * 16 + 15
        zmin, zmax = cz * 16, cz * 16 + 15
        candidates = [
            (abs(x - xmin), "west", [xmin, z]), (abs(xmax - x), "east", [xmax, z]),
            (abs(z - zmin), "north", [x, zmin]), (abs(zmax - z), "south", [x, zmax]),
        ]
        dist, side, target = min(candidates, key=lambda row: row[0])
        return {
            "purpose": "Find the nearest edge of the current 16×16 chunk",
            "block": [x, z], "chunk": [cx, cz],
            "chunk_block_bounds": {"x": [xmin, xmax], "z": [zmin, zmax]},
            "nearest_border": side, "distance_to_border_blocks": round(dist, 3),
            "nearest_border_point": target,
        }
    if name == "Chunk Line Navigator":
        x = float(p.get("x", 80)); z = float(p.get("z", -48))
        x0 = math.floor(x / 16) * 16
        z0 = math.floor(z / 16) * 16
        x_lines = (x0, x0 + 16)
        z_lines = (z0, z0 + 16)
        x_line = min(x_lines, key=lambda value: abs(x - value))
        z_line = min(z_lines, key=lambda value: abs(z - value))
        if abs(x - x_line) <= abs(z - z_line):
            target = [x_line, z]; axis = "X"; delta = x_line - x
        else:
            target = [x, z_line]; axis = "Z"; delta = z_line - z
        return {
            "purpose": "Snap movement onto the nearest chunk grid line",
            "current_block": [x, z], "line_axis": axis,
            "target_block": target, "signed_move_blocks": round(delta, 3),
            "distance_to_line_blocks": round(abs(delta), 3),
            "grid_interval_blocks": 16,
        }
    if name == "Region":
        x = float(p.get("x", 512)); z = float(p.get("z", -512))
        rx, rz = math.floor(x / 512), math.floor(z / 512)
        return {
            "purpose": "Convert a block coordinate to its Anvil region",
            "block": [x, z], "region": [rx, rz],
            "chunk_range": {"x": [rx * 32, rx * 32 + 31], "z": [rz * 32, rz * 32 + 31]},
            "block_range": {"x": [rx * 512, rx * 512 + 511], "z": [rz * 512, rz * 512 + 511]},
        }
    if name == "Region Border":
        x = float(p.get("x", 512)); z = float(p.get("z", -512))
        rx, rz = math.floor(x / 512), math.floor(z / 512)
        xmin, xmax = rx * 512, rx * 512 + 511
        zmin, zmax = rz * 512, rz * 512 + 511
        rows = [
            (abs(x - xmin), "west", [xmin, z]), (abs(xmax - x), "east", [xmax, z]),
            (abs(z - zmin), "north", [x, zmin]), (abs(zmax - z), "south", [x, zmax]),
        ]
        dist, side, target = min(rows, key=lambda row: row[0])
        return {
            "purpose": "Locate the nearest edge of the current 32×32-chunk region",
            "region": [rx, rz], "nearest_border": side,
            "distance_to_region_border_blocks": round(dist, 3),
            "nearest_border_point": target,
            "region_block_bounds": {"x": [xmin, xmax], "z": [zmin, zmax]},
        }
    if name == "OW/Nether Conversion":
        x = float(p.get("x", 800.0)); z = float(p.get("z", -800.0))
        to_nether = bool(p.get("to_nether", True))
        factor = 1 / 8 if to_nether else 8
        converted = [x * factor, z * factor]
        return {
            "purpose": "Convert horizontal coordinates using Minecraft's 8:1 Overworld/Nether scale",
            "source_dimension": "Overworld" if to_nether else "Nether",
            "target_dimension": "Nether" if to_nether else "Overworld",
            "source_xz": [x, z], "exact_scaled_xz": converted,
            "nearest_block_xz": [round(converted[0]), round(converted[1])],
            "scale": "8:1",
        }
    return None


def _navigation_route(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name not in {
        "Coordinate Route", "Resource Route", "Structure Tour", "Biome Expedition",
        "Breadcrumb Recorder", "Expedition Recorder", "Survey Mode",
    }:
        return None
    start = {
        "name": "Start", "x": float(p.get("x1", 0.0)),
        "y": float(p.get("y1", 64.0)), "z": float(p.get("z1", 0.0)),
    }

    if name == "Coordinate Route":
        target = {
            "name": "Target", "x": float(p.get("x2", 100.0)),
            "y": float(p.get("y2", 64.0)), "z": float(p.get("z2", 100.0)),
        }
        dx, dz = target["x"] - start["x"], target["z"] - start["z"]
        return {
            "purpose": "One direct coordinate leg",
            "start": start, "target": target,
            "horizontal_blocks": round(_horizontal(start, target), 2),
            "distance_3d_blocks": round(_distance3(start, target), 2),
            "bearing_degrees": round(_bearing(dx, dz), 2), "direction": _direction(dx, dz),
        }

    if name in {"Resource Route", "Structure Tour", "Biome Expedition"}:
        prefix = {"Resource Route": "Resource", "Structure Tour": "Structure", "Biome Expedition": "Biome"}[name]
        stops = _parse_points(p.get("stops", ""), prefix)
        if not stops:
            return {"available": False, "reason": f"Enter one or more {prefix.lower()} stops as x,y,z,label separated by semicolons."}
        loop = name == "Structure Tour" and bool(p.get("return_to_start", True))
        ordered, segments, total = _greedy_route(start, stops, loop)
        key = {"Resource Route": "resource_order", "Structure Tour": "tour_order", "Biome Expedition": "biome_order"}[name]
        return {
            "purpose": {
                "Resource Route": "Nearest-next route through supplied resource locations",
                "Structure Tour": "Loop-capable tour through supplied structure locations",
                "Biome Expedition": "Expedition order through supplied biome destinations",
            }[name],
            "start": start, key: ordered, "segments": segments,
            "total_horizontal_blocks": round(total, 2),
            "return_to_start": loop,
            "routing_method": "greedy nearest-next; not claimed globally optimal",
        }

    points = _parse_points(p.get("points", ""), "Sample")
    interval = max(0.01, float(p.get("sample_interval", 1.0)))
    if name in {"Breadcrumb Recorder", "Expedition Recorder"}:
        if not points:
            return {
                "purpose": "Recorded-path summary",
                "available": False,
                "reason": "No recorded points were supplied. Live coordinate capture feeds this report when recording is active.",
            }
        path = sum(_horizontal(a, b) for a, b in zip(points, points[1:]))
        xs = [row["x"] for row in points]; ys = [row["y"] for row in points]; zs = [row["z"] for row in points]
        if name == "Breadcrumb Recorder":
            return {
                "purpose": "Summarize a breadcrumb track rather than calculate a destination route",
                "points_recorded": len(points), "path_length_blocks": round(path, 2),
                "first_point": points[0], "last_point": points[-1],
                "sample_interval_seconds": interval,
                "recorded_span": {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)], "z": [min(zs), max(zs)]},
            }
        displacement = _horizontal(points[0], points[-1])
        return {
            "purpose": "Summarize expedition progress over a recorded track",
            "samples": len(points), "elapsed_recording_time": _friendly_duration((len(points) - 1) * interval),
            "distance_walked_blocks": round(path, 2), "net_displacement_blocks": round(displacement, 2),
            "start": points[0], "finish": points[-1],
            "furthest_xz_span_blocks": round(math.hypot(max(xs) - min(xs), max(zs) - min(zs)), 2),
        }

    # Survey Mode builds a serpentine sampling plan over a square around the supplied center.
    radius = max(1, int(p.get("radius", 128)))
    spacing = max(1, int(p.get("spacing", 32)))
    y = float(p.get("y1", 64.0))
    coords: list[dict[str, Any]] = []
    zs = list(range(-radius, radius + 1, spacing))
    if zs[-1] != radius:
        zs.append(radius)
    xs = list(range(-radius, radius + 1, spacing))
    if xs[-1] != radius:
        xs.append(radius)
    for row_index, dz in enumerate(zs):
        row_xs = xs if row_index % 2 == 0 else list(reversed(xs))
        for dx in row_xs:
            coords.append({"name": f"Survey {len(coords)+1}", "x": start["x"] + dx, "y": y, "z": start["z"] + dz})
    length = sum(_horizontal(a, b) for a, b in zip(coords, coords[1:]))
    return {
        "purpose": "Generate a repeatable lawnmower-style survey path",
        "center": [start["x"], y, start["z"]], "radius_blocks": radius,
        "sample_spacing_blocks": spacing, "survey_points": coords,
        "point_count": len(coords), "planned_path_blocks": round(length, 2),
    }


def _portal_report(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name not in {"Asymmetric Portal Router", "Reliability Margin", "Bidirectional Link Matrix", "Portal Graph"}:
        return None
    from .seed.portal import asymmetric_sequence, cycles, link_matrix

    portals = asymmetric_sequence(
        start_x=float(p.get("x", 0.0)), start_z=float(p.get("z", 0.0)),
        low_y=float(p.get("low_y", 5.0)), high_y=float(p.get("high_y", 122.0)),
        nether_step=float(p.get("nether_step", 15.0)), stages=max(1, int(p.get("stages", 3))),
    )
    matrix = link_matrix(portals)
    if name == "Asymmetric Portal Router":
        return {
            "purpose": "Show which exit each portal currently selects",
            "portal_count": len(portals),
            "routes": [
                {"entry": row["entry"], "selected_exit": row["exit"], "distance_to_selected": row["distance"], "selection_margin": row["margin"]}
                for row in matrix
            ],
            "cycle_count": len(cycles(portals)),
        }
    if name == "Reliability Margin":
        finite = [row for row in matrix if isinstance(row.get("margin"), (int, float)) and math.isfinite(float(row["margin"]))]
        finite.sort(key=lambda row: float(row["margin"]))
        return {
            "purpose": "Measure how much closer the selected exit is than the runner-up",
            "weakest_margin": finite[0] if finite else None,
            "margins": finite,
            "interpretation": "Larger positive margins mean the selected exit is more separated from its nearest competitor in this modeled portal set.",
        }
    if name == "Bidirectional Link Matrix":
        by_entry = {row["entry"]: row["exit"] for row in matrix}
        rows = []
        for row in matrix:
            exit_name = row["exit"]
            rows.append({
                "entry": row["entry"], "exit": exit_name,
                "returns_to_entry": bool(exit_name and by_entry.get(exit_name) == row["entry"]),
                "distance": row["distance"],
            })
        return {
            "purpose": "Check whether modeled portal links are reciprocal in both directions",
            "links": rows,
            "reciprocal_links": sum(1 for row in rows if row["returns_to_entry"]),
            "nonreciprocal_links": sum(1 for row in rows if row["exit"] and not row["returns_to_entry"]),
        }
    nodes = [{"name": portal.name, "dimension": portal.dimension, "position": list(portal.point)} for portal in portals]
    edges = [{"from": row["entry"], "to": row["exit"], "distance": row["distance"]} for row in matrix if row["exit"]]
    return {
        "purpose": "Graph view of the modeled portal network",
        "nodes": nodes, "edges": edges, "cycles": cycles(portals),
        "node_count": len(nodes), "edge_count": len(edges),
    }


def _build_report(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name not in {"Area", "Volume", "Surface Area", "Perimeter", "Block Count", "Foundation Planner", "Stacks", "Shulkers", "Double Chests"}:
        return None
    w = max(0, int(p.get("width", 16))); l = max(0, int(p.get("length", 20))); h = max(0, int(p.get("height", 8)))
    area = w * l; volume = area * h; perimeter = max(0, 2 * w + 2 * l - 4) if w and l else 0
    surface = 2 * (w * l + w * h + l * h)
    if name == "Area":
        return {"purpose": "Horizontal footprint only", "width_blocks": w, "length_blocks": l, "area_blocks": area}
    if name == "Volume":
        return {"purpose": "Solid rectangular volume", "dimensions": [w, l, h], "volume_blocks": volume}
    if name == "Surface Area":
        return {
            "purpose": "All six outside faces of a rectangular prism",
            "dimensions": [w, l, h], "surface_blocks": surface,
            "top_bottom_blocks": 2 * w * l, "side_blocks": 2 * (w * h + l * h),
        }
    if name == "Perimeter":
        return {"purpose": "One-block-wide boundary around the footprint", "width_blocks": w, "length_blocks": l, "perimeter_blocks": perimeter}
    if name == "Block Count":
        stacks, remainder = divmod(volume, 64)
        return {
            "purpose": "Material count for a solid rectangular build",
            "blocks": volume, "full_stacks": stacks, "loose_blocks": remainder,
            "shulker_boxes_if_64_stack": math.ceil(volume / 1728) if volume else 0,
        }
    if name == "Foundation Planner":
        stacks, remainder = divmod(area, 64)
        return {
            "purpose": "Single filled foundation layer",
            "foundation_dimensions": [w, l], "fill_blocks": area,
            "edge_blocks": perimeter, "interior_blocks": max(0, area - perimeter),
            "full_stacks": stacks, "loose_blocks": remainder,
        }
    if name == "Stacks":
        full, loose = divmod(volume, 64)
        return {
            "purpose": "Convert the build's solid block count to 64-item stacks",
            "build_blocks": volume, "full_stacks": full, "loose_blocks": loose,
            "inventory_stack_slots_required": full + (1 if loose else 0),
        }
    if name == "Shulkers":
        capacity = 64 * 27
        required = math.ceil(volume / capacity) if volume else 0
        return {
            "purpose": "Shulker boxes required for the build's solid block count",
            "build_blocks": volume, "capacity_per_shulker": capacity,
            "shulkers_required": required,
            "blocks_in_last_shulker": volume - capacity * (required - 1) if required else 0,
        }
    capacity = 64 * 54
    required = math.ceil(volume / capacity) if volume else 0
    return {
        "purpose": "Double chests required for the build's solid block count",
        "build_blocks": volume, "capacity_per_double_chest": capacity,
        "double_chests_required": required,
        "blocks_in_last_double_chest": volume - capacity * (required - 1) if required else 0,
    }


def _storage_report(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name not in {"Storage Capacity", "Bulk Materials", "Shulker Requirement", "Chest Requirement"}:
        return None
    stack = max(1, int(p.get("stack_size", 64)))
    if name == "Storage Capacity":
        container = str(p.get("container", "Double Chest"))
        count = max(0, int(p.get("container_count", 1)))
        slots = {"Shulker Box": 27, "Single Chest": 27, "Barrel": 27, "Double Chest": 54, "Player Inventory": 36}.get(container, 54)
        return {
            "purpose": "How many items a chosen set of containers can hold",
            "container": container, "containers": count, "slots_each": slots,
            "stack_size": stack, "total_slots": slots * count,
            "item_capacity": slots * count * stack,
        }
    items = max(0, int(p.get("items", 100000)))
    full_stacks, loose = divmod(items, stack)
    if name == "Bulk Materials":
        return {
            "purpose": "Overview for moving or storing an arbitrary material count",
            "items": items, "stack_size": stack, "full_stacks": full_stacks, "loose_items": loose,
            "shulkers": math.ceil(items / (stack * 27)) if items else 0,
            "double_chests": math.ceil(items / (stack * 54)) if items else 0,
        }
    if name == "Shulker Requirement":
        capacity = stack * 27; needed = math.ceil(items / capacity) if items else 0
        return {
            "purpose": "Shulker boxes needed for a specific item count",
            "items": items, "capacity_per_shulker": capacity, "shulkers_required": needed,
            "items_in_last_shulker": items - capacity * (needed - 1) if needed else 0,
        }
    chest = str(p.get("chest_type", "Double Chest"))
    slots = 54 if chest == "Double Chest" else 27
    capacity = stack * slots; needed = math.ceil(items / capacity) if items else 0
    return {
        "purpose": "Chests or barrels needed for a specific item count",
        "container": chest, "items": items, "capacity_each": capacity,
        "containers_required": needed,
        "items_in_last_container": items - capacity * (needed - 1) if needed else 0,
    }


def _technical_report(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name == "Chunk Loader Planner":
        width = max(1, int(p.get("width_chunks", 16))); length = max(1, int(p.get("length_chunks", 16))); radius = max(0, int(p.get("coverage_radius", 1)))
        step = 2 * radius + 1
        nx, nz = math.ceil(width / step), math.ceil(length / step)
        centers = [[min(width - 1, x * step + radius), min(length - 1, z * step + radius)] for z in range(nz) for x in range(nx)]
        return {
            "purpose": "Lay out enough loader centers to cover a rectangular chunk footprint",
            "footprint_chunks": [width, length], "coverage_radius_chunks": radius,
            "spacing_chunks": step, "loader_count": len(centers), "planned_centers_relative_chunks": centers,
        }
    if name == "Chunk Loader Radius":
        radius = max(0, int(p.get("coverage_radius", 1)))
        side = 2 * radius + 1
        return {
            "purpose": "Visualize the square chunk footprint represented by one planning radius",
            "radius_chunks": radius, "side_chunks": side, "square_chunks": side * side,
            "side_blocks": side * 16,
        }
    if name in {"Loaded Chunk Area", "Render Distance", "Simulation Distance"}:
        key = {"Loaded Chunk Area": "radius_chunks", "Render Distance": "render_distance_chunks", "Simulation Distance": "simulation_distance_chunks"}[name]
        radius = max(0, int(p.get(key, p.get("value", 10))))
        side = 2 * radius + 1
        label = {
            "Loaded Chunk Area": "Geometric square around a reference chunk; actual ticket/loading state can differ",
            "Render Distance": "Client render footprint; rendering does not imply entity simulation",
            "Simulation Distance": "Server/client simulation-distance footprint; ticket rules still affect actual ticking",
        }[name]
        return {
            "purpose": label, key: radius, "side_chunks": side,
            "chunks_in_square": side * side, "side_blocks": side * 16,
            "square_block_area": (side * 16) ** 2,
        }
    if name == "Farm Separation":
        x1 = float(p.get("x1", 0)); z1 = float(p.get("z1", 0)); x2 = float(p.get("x2", 128)); z2 = float(p.get("z2", 0))
        distance = math.hypot(x2 - x1, z2 - z1)
        return {
            "purpose": "Pure center-to-center spacing between two farm sites",
            "site_a": [x1, z1], "site_b": [x2, z2], "horizontal_distance_blocks": round(distance, 2),
            "note": "Use the mechanic-specific planner for the farm type when interaction rules matter.",
        }
    if name == "Iron Farm Spacing":
        distance = max(0.0, float(p.get("center_distance", 128)))
        a = max(0.0, float(p.get("reserved_radius_a", 32))); b = max(0.0, float(p.get("reserved_radius_b", 32)))
        gap = distance - a - b
        return {
            "purpose": "Check physical separation between two reserved iron-farm planning zones",
            "center_distance_blocks": distance, "reserved_radius_a": a, "reserved_radius_b": b,
            "edge_to_edge_gap_blocks": round(gap, 2), "zones_overlap": gap < 0,
            "note": "This is geometry, not a universal version-independent iron-farm village rule.",
        }
    if name in {"Villager Gossip Radius", "Raid Distance"}:
        radius = max(0.0, float(p.get("planning_radius", 32 if name == "Villager Gossip Radius" else 96)))
        return {
            "purpose": "Planning reference radius for villager social interactions" if name == "Villager Gossip Radius" else "Planning reference radius around a raid center",
            "planning_radius_blocks": radius, "diameter_blocks": radius * 2,
            "square_reference_area_blocks": (2 * radius + 1) ** 2,
            "note": "The exact mechanic is version/state dependent; F3+ does not present this planning radius as a universal hard cutoff.",
        }
    if name == "Mob Cap":
        category = str(p.get("category", "Monster"))
        caps = {"Monster": 70, "Creature": 10, "Ambient": 15, "Water Creature": 5, "Water Ambient": 20, "Underground Water Creature": 5, "Axolotl": 5}
        cap = caps.get(category, 70)
        return {
            "purpose": "Quick vanilla-category cap reference",
            "category": category, "base_cap_reference": cap,
            "note": "Use Mob Cap Calculator when you need eligible-chunk scaling or multi-player planning.",
        }
    if name == "Mob Cap Calculator":
        players = max(1, int(p.get("players", 1))); chunks = max(0, int(p.get("eligible_chunks", 289))); base = max(0, int(p.get("category_base_cap", 70)))
        scaled = math.floor(base * chunks / 289)
        return {
            "purpose": "Scale a supplied category cap by eligible chunks",
            "players": players, "eligible_chunks": chunks, "category_base_cap": base,
            "scaled_cap_per_independent_player_area": scaled,
            "simple_independent_player_upper_bound": scaled * players,
            "note": "Overlapping eligible chunks and server-specific spawning rules can reduce the simple upper-bound interpretation.",
        }
    return None


def _planar_spiral(radius: int, turns: int) -> list[list[int]]:
    radius = max(1, int(radius)); turns = max(1, int(turns))
    steps = max(64, radius * turns * 24)
    points: list[list[int]] = []
    seen: set[tuple[int, int]] = set()
    for index in range(steps + 1):
        t = index / steps
        r = radius * t
        angle = 2 * math.pi * turns * t
        point = (round(r * math.cos(angle)), round(r * math.sin(angle)))
        if point not in seen:
            seen.add(point); points.append([point[0], point[1]])
    return points


def _shape_report(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name not in {"Spiral", "Helix"}:
        return None
    from .calculators.core import spiral as helix_points
    radius = max(1, int(p.get("radius", 8))); height = max(1, int(p.get("height", 12))); turns = max(1, int(p.get("secondary", 2)))
    if name == "Spiral":
        points = _planar_spiral(radius, turns)
        return {
            "purpose": "Flat Archimedean-style spiral on the X/Z plane",
            "radius_blocks": radius, "turns": turns, "plane": "XZ", "points": points, "block_count": len(points),
        }
    points = [list(row) for row in helix_points(radius, height, turns)]
    return {
        "purpose": "Three-dimensional helix rising along Y",
        "radius_blocks": radius, "height_blocks": height, "turns": turns,
        "points": points, "block_count": len(points),
    }


def _confidence_attempts(chance: float) -> list[dict[str, Any]]:
    chance = max(0.0, min(1.0, float(chance)))
    rows = []
    for confidence in (0.5, 0.75, 0.9, 0.95, 0.99):
        if chance <= 0:
            needed = None
        elif chance >= 1:
            needed = 1
        else:
            needed = math.ceil(math.log(1 - confidence) / math.log(1 - chance))
        rows.append({"confidence_percent": confidence * 100, "attempts_needed": needed})
    return rows


def _odds(chance: float, attempts: int) -> dict[str, Any]:
    chance = max(0.0, min(1.0, float(chance))); attempts = max(0, int(attempts))
    one = 1 - (1 - chance) ** attempts
    return {
        "single_attempt_percent": round(chance * 100, 6),
        "attempts": attempts,
        "chance_at_least_one_percent": round(one * 100, 6),
        "chance_none_percent": round((1 - one) * 100, 6),
        "expected_successes": round(chance * attempts, 6),
    }


def _probability_report(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    contexts = {
        "Enchantment Probability": ("enchanting attempts", "Chance to see a target enchantment within a fixed number of attempts"),
        "RNG Probability Calculator": ("attempts", "General independent-event probability calculator"),
        "Loot Odds Calculator": ("loot rolls", "Target loot probability across repeated independent rolls"),
        "Rare Drop Odds": ("kills/rolls", "How many attempts are needed to reach common confidence targets for a rare drop"),
        "Barter Odds": ("gold ingots / barters", "Target barter probability and ingot thresholds"),
        "Trial Reward Odds": ("reward attempts", "Target reward probability across repeated trial reward events"),
        "Enchantment Odds": ("rerolls", "Reroll thresholds for a target enchanting outcome"),
    }
    if name not in contexts:
        return None
    chance = float(p.get("probability", p.get("target_chance", 0.05)))
    attempts = max(0, int(p.get("attempts", 20)))
    unit, purpose = contexts[name]
    base = _odds(chance, attempts)
    base.update({"purpose": purpose, "attempt_unit": unit})
    if name in {"Rare Drop Odds", "Barter Odds", "Trial Reward Odds", "Enchantment Odds"}:
        base["confidence_thresholds"] = _confidence_attempts(chance)
    return base


def _java_sequence(seed: int, count: int) -> list[int]:
    from .rng_tools import sequence
    return list(sequence(int(seed), max(0, int(count))))


def _sequence_report(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name not in {"RNG Sequence Viewer", "RNG Timeline", "Enchantment Sequence Simulator"}:
        return None
    seed = int(p.get("seed", 12345)); count = max(1, int(p.get("attempts", p.get("count", 20))))
    values = _java_sequence(seed, count if name != "Enchantment Sequence Simulator" else count * 3)
    if name == "RNG Sequence Viewer":
        return {
            "purpose": "Inspect raw 31-bit java.util.Random outputs",
            "seed": seed,
            "values": [{"index": i, "decimal": value, "hex": hex(value)} for i, value in enumerate(values)],
        }
    if name == "RNG Timeline":
        rows = []
        previous = None
        for i, value in enumerate(values):
            rows.append({
                "index": i, "value": value,
                "normalized_0_to_1": round(value / float((1 << 31) - 1), 9),
                "delta_from_previous": None if previous is None else value - previous,
            })
            previous = value
        return {
            "purpose": "Show how a deterministic Java RNG sequence changes over time",
            "seed": seed, "timeline": rows,
            "minimum": min(values), "maximum": max(values), "mean": round(sum(values) / len(values), 3),
        }
    groups = []
    for index in range(count):
        draws = values[index * 3:index * 3 + 3]
        groups.append({"attempt": index + 1, "model_draws": draws})
    return {
        "purpose": "Group deterministic Java RNG draws into enchanting-attempt-sized bundles",
        "seed": seed, "simulated_attempts": groups,
        "note": "This exposes RNG progression only; it does not claim the three numbers are exact modern enchantment offers without version-specific enchanting state.",
    }


def _target_event_report(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    contexts = {
        "Mob Drop Simulator": ("kills", "target mob drop"),
        "Structure Loot Simulator": ("chest rolls", "target structure-loot item"),
        "Trial Chamber Loot Simulator": ("vault/reward rolls", "target trial-chamber reward"),
        "Fishing Loot Simulator": ("casts", "target fishing result"),
        "Archaeology Loot Simulator": ("completed brushes", "target archaeology item"),
        "Piglin Barter Simulator": ("gold ingots", "target barter result"),
        "Trial Spawner Reward Simulator": ("reward events", "target trial-spawner reward"),
    }
    if name not in contexts:
        return None
    unit, target = contexts[name]
    chance = float(p.get("probability", p.get("target_chance", 0.05)))
    attempts = max(0, int(p.get("attempts", 20)))
    report = _odds(chance, attempts)
    report.update({
        "purpose": f"Model the user-supplied probability of a {target}",
        "attempt_unit": unit,
        "target": target,
        "confidence_thresholds": _confidence_attempts(chance),
        "model_limit": "Independent target-event model. Exact selected-version loot tables are not fabricated from this probability input.",
    })
    return report


def _parse_weights(text: Any) -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    for token in str(text or "").split(";"):
        if ":" not in token:
            continue
        label, raw = token.split(":", 1)
        try:
            weight = float(raw.strip())
        except ValueError:
            continue
        if label.strip() and weight > 0:
            rows.append((label.strip(), weight))
    return rows


def _loot_table_report(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name != "Loot Table Simulator":
        return None
    from .qa_features import JavaRandom
    rows = _parse_weights(p.get("entries", "common:70;uncommon:23;rare:7"))
    if not rows:
        return {"available": False, "reason": "Enter weighted entries as label:weight separated by semicolons."}
    attempts = max(1, int(p.get("attempts", 100))); rng = JavaRandom(int(p.get("seed", 12345)))
    total = sum(weight for _, weight in rows); counts = Counter({label: 0 for label, _ in rows})
    first: list[str] = []
    for _ in range(attempts):
        q = rng.next_double() * total; running = 0.0; selected = rows[-1][0]
        for label, weight in rows:
            running += weight
            if q <= running:
                selected = label; break
        counts[selected] += 1
        if len(first) < 50:
            first.append(selected)
    return {
        "purpose": "Simulate a user-supplied weighted table rather than a hidden generic rarity profile",
        "entries": [{"label": label, "weight": weight, "normalized_percent": round(weight / total * 100, 4)} for label, weight in rows],
        "rolls": attempts,
        "results": [{"label": label, "count": counts[label], "observed_percent": round(counts[label] / attempts * 100, 4)} for label, _ in rows],
        "first_results": first,
        "note": "Weights are supplied by the user. Paste values from a version-appropriate table when exact selected-version modeling is required.",
    }


def _generation_report(name: str, p: dict[str, Any], executor) -> dict[str, Any] | None:
    if name not in {"Decoration RNG", "Feature Placement RNG", "Ore Placement Simulator", "Tree Generation Simulator", "Geode Generator", "Trial Chamber Generation", "Structure Placement Preview"}:
        return None
    from .qa_features import JavaRandom
    seed = int(p.get("seed", 12345)); cx = int(p.get("cx", 0)); cz = int(p.get("cz", 0)); attempts = max(1, min(10000, int(p.get("attempts", 20))))
    mixed = seed + cx * 341873128712 + cz * 132897987541
    rng = JavaRandom(mixed)
    if name == "Decoration RNG":
        rolls = [rng.next_float() for _ in range(attempts)]
        return {
            "purpose": "Inspect deterministic decoration-stage random draws without pretending they are finished features",
            "world_seed": seed, "chunk": [cx, cz], "draw_count": attempts,
            "draws": [{"index": i, "roll": round(value, 9)} for i, value in enumerate(rolls)],
            "minimum_roll": min(rolls), "maximum_roll": max(rolls), "mean_roll": sum(rolls) / len(rolls),
        }
    if name == "Feature Placement RNG":
        min_y = int(p.get("min_y", -64)); max_y = int(p.get("max_y", 319))
        if max_y < min_y: min_y, max_y = max_y, min_y
        span = max_y - min_y + 1
        rows = [{"index": i, "x": cx * 16 + rng.next_int(16), "y": min_y + rng.next_int(span), "z": cz * 16 + rng.next_int(16)} for i in range(attempts)]
        return {
            "purpose": "Preview raw candidate positions from a deterministic placement-position model",
            "world_seed": seed, "chunk": [cx, cz], "y_range": [min_y, max_y], "candidate_positions": rows,
            "note": "A candidate RNG position is not proof that a configured Minecraft feature actually places there.",
        }
    if name == "Ore Placement Simulator":
        min_y = int(p.get("min_y", -64)); max_y = int(p.get("max_y", 64))
        if max_y < min_y: min_y, max_y = max_y, min_y
        span = max_y - min_y + 1; rows = []
        for i in range(attempts):
            y = min_y + (rng.next_int(span) + rng.next_int(span)) // 2
            rows.append({"index": i, "x": cx * 16 + rng.next_int(16), "y": y, "z": cz * 16 + rng.next_int(16)})
        y_counts = Counter(row["y"] for row in rows)
        return {
            "purpose": "Triangular-height candidate model for ore-placement planning",
            "world_seed": seed, "chunk": [cx, cz], "height_provider": "triangle", "y_range": [min_y, max_y],
            "candidate_positions": rows, "most_common_sampled_y": max(y_counts, key=y_counts.get),
            "note": "Ore configured features differ by ore and version; this models the supplied triangular range only.",
        }
    if name == "Tree Generation Simulator":
        chance = max(0.0, min(1.0, float(p.get("probability", 0.05))))
        rows = []
        for i in range(attempts):
            x = cx * 16 + rng.next_int(16); z = cz * 16 + rng.next_int(16); roll = rng.next_float()
            if roll < chance:
                rows.append({"attempt": i + 1, "x": x, "z": z, "roll": round(roll, 9)})
        return {
            "purpose": "User-configured tree-attempt probability model",
            "attempts": attempts, "configured_success_percent": chance * 100,
            "successful_attempts": len(rows), "successful_positions": rows,
            "observed_success_percent": round(len(rows) / attempts * 100, 3),
            "note": "Biome vegetation configuration, density/noise, survival checks, and neighboring blocks are not inferred from this single probability.",
        }
    if name == "Geode Generator":
        chance = max(0.0, min(1.0, float(p.get("probability", 0.05))))
        chunks = []
        side = math.ceil(math.sqrt(attempts))
        for index in range(attempts):
            qx = cx + index % side; qz = cz + index // side; roll = rng.next_float()
            if roll < chance:
                chunks.append({"chunk": [qx, qz], "block_center": [qx * 16 + 8, qz * 16 + 8], "roll": round(roll, 9)})
        return {
            "purpose": "Chunk-level geode-frequency model over a small deterministic sample grid",
            "chunks_tested": attempts, "configured_chunk_chance_percent": chance * 100,
            "modeled_geode_chunks": chunks, "modeled_geode_count": len(chunks),
            "expected_count": round(chance * attempts, 3),
            "note": "This is a frequency model, not exact modern geode configured-feature reproduction.",
        }
    from .restored_features import structure_candidates
    from .world.versioning import resolve_cubiomes_mc
    selected = str(getattr(executor, "minecraft_version", "1.21.3")); mc = resolve_cubiomes_mc(selected)
    radius = max(1, int(p.get("radius", 64)))
    target = "Trial Chamber" if name == "Trial Chamber Generation" else str(p.get("structure", "Village"))
    result = structure_candidates(target, seed, cx, cz, radius, mc=mc)
    points = list(result.get("candidate_chunks", []))
    return {
        "purpose": "Trial-chamber placement candidate preview" if name == "Trial Chamber Generation" else "Selected structure placement-candidate preview",
        "structure": target, "search_center_chunk": [cx, cz], "radius_chunks": radius,
        "candidate_count": len(points), "candidate_chunks": points[:512],
        "nearest_candidate": points[0] if points else None,
        "note": "Placement candidates still require the selected-version biome/terrain viability stage before they become generated structures.",
    }


def _resource_usage_report(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    units = {
        "Food Usage": "food items", "Rocket Usage": "firework rockets", "Fuel Usage": "fuel items",
        "Torch Usage": "torches", "Bone Meal Usage": "bone meal",
    }
    if name not in units:
        return None
    rate = max(0.0, float(p.get("rate_per_hour", p.get("amount", 64.0))))
    hours = max(0.0, float(p.get("hours", 1.0)))
    total = rate * hours
    full, loose = divmod(int(math.ceil(total)), 64)
    return {
        "purpose": f"Plan {units[name]} consumption over time",
        "resource": units[name], "rate_per_hour": rate, "hours": hours,
        "estimated_items": round(total, 3), "full_64_stacks": full, "loose_items_after_full_stacks": loose,
    }


def _fields_for(spec):
    n = spec.name
    if spec.top == "Navigation" and spec.submenu == "Routes":
        if n == "Coordinate Route":
            return [("x1", "Start X", 0.0, "float"), ("y1", "Start Y", 64.0, "float"), ("z1", "Start Z", 0.0, "float"), ("x2", "Target X", 100.0, "float"), ("y2", "Target Y", 64.0, "float"), ("z2", "Target Z", 100.0, "float")]
        if n in {"Resource Route", "Structure Tour", "Biome Expedition"}:
            label = {"Resource Route": "Resource stops", "Structure Tour": "Structure stops", "Biome Expedition": "Biome stops"}[n]
            fields = [("x1", "Start X", 0.0, "float"), ("y1", "Start Y", 64.0, "float"), ("z1", "Start Z", 0.0, "float"), ("stops", f"{label} — x,y,z,label separated by ;", "80,64,0,A;80,64,80,B;0,64,80,C", "text")]
            if n == "Structure Tour": fields.append(("return_to_start", "Return to start", True, "bool"))
            return fields
        if n in {"Breadcrumb Recorder", "Expedition Recorder"}:
            return [("points", "Recorded points — x,y,z separated by ;", "0,64,0;16,64,0;32,64,16", "text"), ("sample_interval", "Seconds between samples", 1.0, "float")]
        if n == "Survey Mode":
            return [("x1", "Survey center X", 0.0, "float"), ("y1", "Survey Y", 64.0, "float"), ("z1", "Survey center Z", 0.0, "float"), ("radius", "Survey radius (blocks)", 128, "int"), ("spacing", "Sample spacing (blocks)", 32, "int")]
    if spec.top == "Seed Tools" and spec.submenu == "Nether" and n in {"Asymmetric Portal Router", "Reliability Margin", "Bidirectional Link Matrix", "Portal Graph"}:
        return [("x", "Starting Overworld X", 0.0, "float"), ("z", "Starting Overworld Z", 0.0, "float"), ("stages", "Asymmetric stages", 3, "int"), ("low_y", "Low Nether Y", 5.0, "float"), ("high_y", "High Nether Y", 122.0, "float"), ("nether_step", "Nether portal separation", 15.0, "float")]
    if spec.top == "Calculators" and spec.submenu == "Storage":
        if n == "Storage Capacity": return [("container", "Container", ["Double Chest", "Single Chest", "Barrel", "Shulker Box", "Player Inventory"], "choice"), ("container_count", "Number of containers", 1, "int"), ("stack_size", "Item stack size", 64, "int")]
        if n == "Chest Requirement": return [("items", "Items to store", 100000, "int"), ("stack_size", "Item stack size", 64, "int"), ("chest_type", "Container", ["Double Chest", "Single Chest", "Barrel"], "choice")]
        if n in {"Bulk Materials", "Shulker Requirement"}: return [("items", "Items to store", 100000, "int"), ("stack_size", "Item stack size", 64, "int")]
    if spec.top == "Calculators" and spec.submenu == "Technical":
        if n == "Chunk Loader Planner": return [("width_chunks", "Area width (chunks)", 16, "int"), ("length_chunks", "Area length (chunks)", 16, "int"), ("coverage_radius", "Coverage radius per loader (chunks)", 1, "int")]
        if n == "Chunk Loader Radius": return [("coverage_radius", "Coverage radius (chunks)", 1, "int")]
        if n == "Loaded Chunk Area": return [("radius_chunks", "Loaded radius (chunks)", 10, "int")]
        if n == "Render Distance": return [("render_distance_chunks", "Render distance (chunks)", 12, "int")]
        if n == "Simulation Distance": return [("simulation_distance_chunks", "Simulation distance (chunks)", 10, "int")]
        if n == "Farm Separation": return [("x1", "Farm A X", 0.0, "float"), ("z1", "Farm A Z", 0.0, "float"), ("x2", "Farm B X", 128.0, "float"), ("z2", "Farm B Z", 0.0, "float")]
        if n == "Iron Farm Spacing": return [("center_distance", "Center-to-center distance", 128.0, "float"), ("reserved_radius_a", "Reserved radius A", 32.0, "float"), ("reserved_radius_b", "Reserved radius B", 32.0, "float")]
        if n in {"Villager Gossip Radius", "Raid Distance"}: return [("planning_radius", "Planning radius (blocks)", 32.0 if n == "Villager Gossip Radius" else 96.0, "float")]
        if n == "Mob Cap": return [("category", "Mob category", ["Monster", "Creature", "Ambient", "Water Creature", "Water Ambient", "Underground Water Creature", "Axolotl"], "choice")]
        if n == "Mob Cap Calculator": return [("players", "Players", 1, "int"), ("eligible_chunks", "Eligible spawning chunks", 289, "int"), ("category_base_cap", "Base category cap", 70, "int")]
    if spec.top == "Calculators" and spec.submenu == "Resource Usage" and n in {"Food Usage", "Rocket Usage", "Fuel Usage", "Torch Usage", "Bone Meal Usage"}:
        return [("rate_per_hour", "Items used per hour", 64.0, "float"), ("hours", "Hours", 1.0, "float")]
    if spec.top == "RNG Tools":
        if n in {"RNG Sequence Viewer", "RNG Timeline", "Enchantment Sequence Simulator"}: return [("seed", "Java RNG seed", 12345, "int"), ("attempts", "Values / attempts", 20, "int")]
        if n == "Loot Table Simulator": return [("entries", "Weighted entries label:weight separated by ;", "common:70;uncommon:23;rare:7", "text"), ("attempts", "Rolls", 100, "int"), ("seed", "RNG seed", 12345, "int")]
        if spec.submenu == "Generation RNG":
            if n in {"Trial Chamber Generation", "Structure Placement Preview"}:
                fields = [("seed", "World seed", 123456789, "text"), ("cx", "Center chunk X", 0, "int"), ("cz", "Center chunk Z", 0, "int"), ("radius", "Search radius (chunks)", 64, "int")]
                if n == "Structure Placement Preview": fields.append(("structure", "Structure", "Village", "text"))
                return fields
            fields = [("seed", "RNG/world seed", 12345, "int"), ("cx", "Chunk X", 0, "int"), ("cz", "Chunk Z", 0, "int"), ("attempts", "Attempts / samples", 20, "int")]
            if n in {"Tree Generation Simulator", "Geode Generator"}: fields.append(("probability", "Configured success chance 0..1", 0.05, "float"))
            if n in {"Feature Placement RNG", "Ore Placement Simulator"}: fields.extend([("min_y", "Minimum Y", -64, "int"), ("max_y", "Maximum Y", 64 if n == "Ore Placement Simulator" else 319, "int")])
            return fields
    return None


def install() -> None:
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_semantic_cleanup_v2_installed", False):
        return
    previous_execute = FeatureExecutor.execute
    previous_fields = FeatureExecutor.input_fields

    def input_fields(self, feature):
        spec = self.spec(feature)
        fields = _fields_for(spec)
        return fields if fields is not None else previous_fields(self, feature)

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        values = self.defaults(spec)
        values.update(params or {})
        data = None

        if spec.top == "Navigation" and spec.submenu == "Coordinates":
            data = _navigation_coordinate(spec.name, values)
        if data is None and spec.top == "Navigation" and spec.submenu == "Routes":
            data = _navigation_route(spec.name, values)
        if data is None and spec.top == "Seed Tools" and spec.submenu == "Nether":
            data = _portal_report(spec.name, values)
        if data is None and spec.top == "Calculators" and spec.submenu == "Build":
            data = _build_report(spec.name, values)
        if data is None and spec.top == "Calculators" and spec.submenu == "Storage":
            data = _storage_report(spec.name, values)
        if data is None and spec.top == "Calculators" and spec.submenu == "Technical":
            data = _technical_report(spec.name, values)
        if data is None and spec.top == "Calculators" and spec.submenu == "Shapes":
            data = _shape_report(spec.name, values)
        if data is None and spec.top == "Calculators" and spec.submenu == "Resource Usage":
            data = _resource_usage_report(spec.name, values)
        if data is None and spec.top == "RNG Tools":
            data = _loot_table_report(spec.name, values)
            if data is None: data = _probability_report(spec.name, values)
            if data is None: data = _sequence_report(spec.name, values)
            if data is None: data = _target_event_report(spec.name, values)
            if data is None and spec.submenu == "Generation RNG": data = _generation_report(spec.name, values, self)

        if data is not None:
            status = "unavailable" if data.get("available") is False else "ok"
            return self._result(spec, status, data)
        return previous_execute(self, spec, values, dry_run)

    FeatureExecutor.input_fields = input_fields
    FeatureExecutor.execute = execute
    FeatureExecutor._semantic_cleanup_v2_installed = True
