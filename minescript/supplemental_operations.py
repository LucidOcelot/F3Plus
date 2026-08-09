from __future__ import annotations

"""Small operation families that do not warrant separate engines.

These functions preserve useful calculators and setup generators that historically lived
inside a runtime installer.  They are ordinary pure dispatch helpers now.
"""

import math
from typing import Any

from .navigation.routes import Point, breadcrumb_simplify, greedy_route
from . import wizards


def input_fields(spec):
    name = spec.name
    if spec.top == "Wizards" or name.endswith("Wizard") or name.endswith("Setup"):
        return wizard_fields(name)
    if spec.top == "Navigation" and name == "Multi-stop Route":
        return [
            ("x1", "Start X", 0.0, "float"), ("y1", "Start Y", 64.0, "float"), ("z1", "Start Z", 0.0, "float"),
            ("stops", "Stops x,y,z,name separated by ;", "80,64,0,A;80,64,80,B;0,64,80,C", "text"),
            ("return_to_start", "Return to start", False, "bool"),
        ]
    if spec.top == "Navigation" and name == "Breadcrumb Simplifier":
        return [("points", "Points x,y,z separated by ;", "0,64,0;8,64,0;16,64,0;16,64,8", "text"), ("tolerance", "Minimum spacing", 2.0, "float")]
    if name == "Material Progress":
        return [("target", "Target item count", 10000.0, "float"), ("current", "Current item count", 2500.0, "float")]
    if name == "Resource Goal Calculator":
        return [("target", "Target item count", 10000.0, "float"), ("current", "Current item count", 2500.0, "float"), ("rate_per_hour", "Collection rate/hour", 1000.0, "float")]
    return None


def report(spec, params: dict[str, Any]):
    if spec.top == "Navigation" and spec.name in {"Multi-stop Route", "Breadcrumb Simplifier"}:
        return navigation_report(spec.name, params)
    if spec.top == "Wizards" or spec.name.endswith("Wizard") or spec.name.endswith("Setup"):
        value = wizard_report(spec.name, params)
        if value is not None:
            return value
    value = redstone_report(spec, params)
    if value is None:
        value = farm_and_technical_report(spec, params)
    return value


def _parse_point_rows(text: str, names: bool = False) -> list[Point]:
    out = []
    for index, raw in enumerate(str(text or "").split(";"), 1):
        parts = [part.strip() for part in raw.split(",")]
        if len(parts) < 3:
            continue
        try:
            x, y, z = map(float, parts[:3])
        except ValueError:
            continue
        label = parts[3] if names and len(parts) > 3 and parts[3] else f"Stop {index}"
        out.append(Point(x, y, z, label))
    return out


def navigation_report(name: str, p: dict[str, Any]):
    if name == "Multi-stop Route":
        origin = Point(float(p.get("x1", 0)), float(p.get("y1", 64)), float(p.get("z1", 0)), "Start")
        points = _parse_point_rows(p.get("stops", ""), names=True)
        if not points:
            return {"available": False, "reason": "Enter at least one valid stop as x,y,z,name."}
        route = greedy_route(origin, points, bool(p.get("return_to_start", False)))
        return {
            "purpose": "Build a greedy nearest-next route through the supplied stops.",
            "origin": [origin.x, origin.y, origin.z],
            "route_order": [{"name": point.name, "x": point.x, "y": point.y, "z": point.z} for point in route["route"]],
            "total_horizontal_distance_blocks": round(float(route["distance"]), 2),
            "return_to_start": bool(route["return_to_start"]),
            "routing_method": "greedy nearest-next; not claimed globally optimal",
        }
    if name == "Breadcrumb Simplifier":
        points = _parse_point_rows(p.get("points", ""))
        if not points:
            return {"available": False, "reason": "Enter valid breadcrumb points as x,y,z separated by semicolons."}
        spacing = max(0.0, float(p.get("tolerance", 2.0)))
        simplified = breadcrumb_simplify(points, spacing)
        return {
            "purpose": "Reduce a breadcrumb trail by keeping points at least the chosen horizontal spacing apart while preserving the end point.",
            "minimum_spacing_blocks": spacing,
            "input_points": len(points),
            "output_points": len(simplified),
            "points": [[point.x, point.y, point.z] for point in simplified],
        }
    return None


def redstone_report(spec, p):
    if spec.submenu != "Redstone":
        return None
    name = spec.name
    value = max(0.0, float(p.get("value", 0)))
    secondary = max(0.0, float(p.get("secondary", 0)))
    if name == "Repeater Delay":
        setting = max(1, min(4, int(round(value)))); count = max(1, int(round(secondary))); ticks = setting * count
        return {"repeaters": count, "setting_redstone_ticks_each": setting, "total_redstone_ticks": ticks, "game_ticks": ticks * 2, "seconds": ticks * 0.1}
    if name == "Observer Delay":
        observers = max(1, int(round(value)))
        return {"observers": observers, "delay_game_ticks": observers * 2, "delay_redstone_ticks": observers, "seconds": observers * 0.1, "note": "Models a simple serial observer chain; circuit topology can add other delays."}
    if name == "Pulse Extender":
        total = value + secondary
        return {"base_pulse_redstone_ticks": value, "extension_redstone_ticks": secondary, "output_redstone_ticks": total, "output_seconds": total * 0.1, "note": "Timing arithmetic only; component-specific topology is user supplied."}
    if name == "Clock Period":
        period = value + secondary
        return {"on_redstone_ticks": value, "off_redstone_ticks": secondary, "period_redstone_ticks": period, "period_seconds": period * 0.1, "frequency_hz": 1.0 / max(1e-9, period * 0.1)}
    if name == "Counter Timing":
        events = max(1, int(round(value)))
        return {"events": events, "interval_redstone_ticks": secondary, "elapsed_redstone_ticks": events * secondary, "elapsed_seconds": events * secondary * 0.1}
    if name == "Signal Timing":
        return {"redstone_ticks": value, "game_ticks": value * 2.0, "seconds": value * 0.1}
    return None


def farm_and_technical_report(spec, p):
    name = spec.name
    if name == "Beacon Coverage":
        level = max(1, min(4, int(p.get("spacing", 4)))); radius = 10 + level * 10
        return {"beacon_level": level, "effect_radius_blocks": radius, "diameter_blocks": radius * 2 + 1, "square_footprint_blocks": (radius * 2 + 1) ** 2, "note": "Horizontal planning footprint; vertical/effect behavior follows the selected Minecraft version."}
    if name == "Tree Yield":
        trees = max(0, int(p.get("units", 0))); cycles = max(0.0, float(p.get("hours", 0)))
        return {"trees": trees, "cycles": cycles, "planning_logs_per_tree": 4.0, "estimated_logs": trees * cycles * 4.0, "note": "Explicit planning assumption of four logs/tree; species and harvesting method change real yield."}
    if name == "Crop Yield":
        plants = max(0, int(p.get("units", 0))); harvests = max(0.0, float(p.get("hours", 0))); mean = max(0.0, float(p.get("yield_per_plant", 2.5)))
        return {"plants": plants, "harvests": harvests, "planning_yield_per_plant": mean, "estimated_items": plants * harvests * mean, "note": "User-facing planning mean, not a universal crop drop table."}
    if name == "Sugar Cane Layout":
        plants = max(0, int(p.get("units", 0))); spacing = max(1, int(p.get("spacing", 1)))
        return {"plants": plants, "water_edge_positions_required": plants, "linear_spacing": spacing, "planned_length_blocks": max(0, (plants - 1) * spacing + 1)}
    if name == "Bamboo Layout":
        plants = max(0, int(p.get("units", 0))); spacing = max(1, int(p.get("spacing", 1))); side = math.ceil(math.sqrt(plants)) if plants else 0
        return {"plants": plants, "spacing": spacing, "grid_side_positions": side, "footprint_side_blocks": max(0, (side - 1) * spacing + 1)}
    if name == "Crop Row Calculator":
        plants = max(0, int(p.get("units", 0))); spacing = max(1, int(p.get("spacing", 1))); row_length = max(1, int(round(math.sqrt(max(1, plants))))); rows = math.ceil(plants / row_length) if plants else 0
        return {"plants": plants, "plants_per_row": row_length, "rows": rows, "row_spacing": spacing}
    if name in {"Farm Separation", "Iron Farm Spacing", "Villager Gossip Radius", "Raid Distance"}:
        x = max(0.0, float(p.get("value", 0))); z = max(0.0, float(p.get("secondary", 0)))
        notes = {
            "Farm Separation": "General geometric planner; individual farms have version-specific interference rules.",
            "Iron Farm Spacing": "No universal safe spacing is fabricated; verify selected-version village/iron-golem mechanics.",
            "Villager Gossip Radius": "Planning radius only; gossip/village behavior is not represented as one universal Euclidean constant.",
            "Raid Distance": "Planning distance only; raid center/POI rules are version-specific.",
        }
        return {"requested_x_offset": x, "requested_z_offset": z, "geometric_distance": math.hypot(x, z), "note": notes[name]}
    if name == "Material Progress":
        target = max(0.0, float(p.get("target", p.get("amount", 0)))); current = max(0.0, float(p.get("current", p.get("hours", 0))))
        return {"target": target, "current": current, "remaining": max(0.0, target - current), "percent": 100.0 if target == 0 else min(100.0, current / target * 100.0)}
    if name == "Resource Goal Calculator":
        target = max(0.0, float(p.get("target", p.get("amount", 0)))); current = max(0.0, float(p.get("current", 0))); rate = max(0.0, float(p.get("rate_per_hour", p.get("hours", 0)))); remaining = max(0.0, target - current)
        return {"target": target, "current": current, "remaining": remaining, "rate_per_hour": rate, "hours_remaining": remaining / rate if rate > 0 else None}
    return None


def wizard_fields(name: str):
    if "Branch" in name: return [("spacing", "Branch spacing", 4, "int"), ("depth", "Branch depth", 32, "int"), ("branches", "Branches", 8, "int"), ("torch_spacing", "Torch spacing", 12, "int")]
    if "Quarry" in name: return [("width", "Width", 16, "int"), ("length", "Length", 16, "int"), ("depth", "Depth", 16, "int")]
    if "Perimeter" in name: return [("width", "Width", 256, "int"), ("length", "Length", 256, "int"), ("depth", "Depth", 64, "int")]
    if "Crop" in name: return [("rows", "Rows", 8, "int"), ("row_length", "Row length", 32.0, "float")]
    if "Tree" in name: return [("sapling_slot", "Sapling hotbar slot", 1, "int"), ("bonemeal_slot", "Bone meal hotbar slot", 2, "int"), ("tool_slot", "Tool hotbar slot", 3, "int")]
    if "Villager" in name: return [("villagers", "Villagers", 20, "int"), ("spacing", "Station spacing", 1, "int")]
    if "Highway" in name: return [("x1", "Start X", 0.0, "float"), ("y1", "Start Y", 64.0, "float"), ("z1", "Start Z", 0.0, "float"), ("x2", "Destination X", 8000.0, "float"), ("y2", "Destination Y", 64.0, "float"), ("z2", "Destination Z", 0.0, "float"), ("speed", "Nether travel speed", 72.7, "float")]
    if "Asymmetric" in name: return [("stages", "Portal stages", 6, "int")]
    if "Portal" in name: return [("portals", "Portal count", 4, "int")]
    if "Build Material" in name: return [("width", "Width", 16, "int"), ("length", "Length", 16, "int"), ("height", "Height", 8, "int")]
    if "Lighting" in name: return [("width", "Width", 32, "int"), ("length", "Length", 32, "int"), ("spacing", "Light spacing", 8, "int")]
    if "Beacon" in name: return [("beacons", "Beacon count", 4, "int"), ("levels", "Pyramid level", 4, "int")]
    return None


def wizard_report(name: str, p: dict[str, Any]):
    if "Branch" in name: return wizards.branch_mine(p.get("spacing", 4), p.get("depth", 32), p.get("branches", 8), p.get("torch_spacing", 12))
    if "Quarry" in name: return wizards.quarry(p.get("width", 16), p.get("length", 16), p.get("depth", 16))
    if "Perimeter" in name: return wizards.perimeter(p.get("width", 256), p.get("length", 256), p.get("depth", 64))
    if "Crop" in name: return wizards.crop(p.get("rows", 8), p.get("row_length", 32))
    if "Tree" in name: return wizards.tree(p.get("sapling_slot", 1), p.get("bonemeal_slot", 2), p.get("tool_slot", 3))
    if "Villager" in name: return wizards.villager_hall(p.get("villagers", 20), p.get("spacing", 1))
    if "Highway" in name:
        start = (p.get("x1", 0), p.get("y1", 64), p.get("z1", 0)); destination = (p.get("x2", 8000), p.get("y2", 64), p.get("z2", 0))
        return wizards.nether_highway(start, destination, p.get("speed", 72.7))
    if "Asymmetric" in name: return wizards.asymmetric_portal(p.get("stages", 6))
    if "Portal" in name: return wizards.portal_network(p.get("portals", 4))
    if "Lighting" in name: return wizards.lighting(p.get("width", 32), p.get("length", 32), p.get("spacing", 8))
    if "Beacon" in name: return wizards.beacon_network(p.get("beacons", 4), p.get("levels", 4))
    if "Build Material" in name: return wizards.build_material(p.get("width", 16), p.get("length", 16), p.get("height", 8))
    return None
