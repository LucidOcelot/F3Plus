from __future__ import annotations

"""Compatibility helpers retained for historical imports.

This module no longer installs or replaces runtime behavior. RNG previews use the
canonical java.util.Random implementation, while navigation/world/villager helpers are
ordinary pure functions consumed explicitly by ``executor_policy``.
"""

import math
from dataclasses import asdict
from typing import Any

from .rng_compat import JavaRandom, rng_tool


def _selected_mc(executor, params: dict[str, Any]) -> int:
    from .world.versioning import resolve_cubiomes_mc

    if "mc" in params and params["mc"] not in (None, ""):
        return int(params["mc"])
    selected = getattr(executor, "minecraft_version", "26.3-snapshot-7") if executor else "26.3-snapshot-7"
    return resolve_cubiomes_mc(str(selected))


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _portal_candidates(x: float, z: float, radius: int = 16, step: int = 1):
    ideal = (x / 8.0, z / 8.0); out = []
    for dz in range(-radius, radius + 1, step):
        for dx in range(-radius, radius + 1, step):
            candidate = (round(ideal[0] + dx), round(ideal[1] + dz)); error = _distance(candidate, ideal)
            out.append((error, error * 8.0, candidate))
    out.sort(key=lambda row: (row[0], abs(row[2][0]), abs(row[2][1])))
    return out


def portal_tool(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    x = float(p.get("x", p.get("x1", 0.0))); z = float(p.get("z", p.get("z1", 0.0))); other_x = float(p.get("other_x", p.get("x2", 0.0))); other_z = float(p.get("other_z", p.get("z2", 0.0))); radius = max(1, int(p.get("radius", 16))); candidates = _portal_candidates(x, z, min(radius, 64))
    if name == "Portal Cost Optimizer":
        walking_weight = max(0.0, float(p.get("walking_weight", 1.0))); error_weight = max(0.0, float(p.get("error_weight", 4.0))); origin_nether = (other_x, other_z); rows = []
        for _error, ow_error, candidate in candidates:
            walk = _distance(origin_nether, candidate); rows.append({"nether": candidate, "link_error_blocks_overworld": ow_error, "nether_walk": walk, "cost": walk * walking_weight + ow_error * error_weight})
        rows.sort(key=lambda row: row["cost"]); return {"operation": name, "overworld_target": (x, z), "reference_nether": origin_nether, "ranked": rows[:64], "best": rows[0]}
    if name == "Portal Reliability Heatmap":
        rows = []
        for error, ow_error, candidate in candidates:
            score = max(0.0, 1.0 - error / max(1.0, radius)); rows.append({"nether": candidate, "error_nether": error, "error_overworld": ow_error, "reliability": round(score, 5)})
        return {"operation": name, "center": (x / 8.0, z / 8.0), "radius": radius, "samples": rows, "note": "Reliability is a geometric margin score, not a probability of portal linking."}
    if name == "Destination Gate Planner":
        best = candidates[0]; return {"operation": name, "overworld_destination": (x, z), "ideal_nether": (x / 8.0, z / 8.0), "recommended_nether_block": best[2], "rounding_error_overworld_blocks": best[1], "verification": "Verify competing portals within the vanilla search radius before relying on the route."}
    if name == "Multi-Destination Optimizer":
        raw = p.get("destinations"); destinations: list[tuple[float, float]] = []
        if isinstance(raw, str):
            for token in raw.split(";"):
                parts = [value.strip() for value in token.split(",")]
                if len(parts) >= 2:
                    try: destinations.append((float(parts[0]), float(parts[1])))
                    except ValueError: pass
        if not destinations: destinations = [(x, z), (other_x, other_z)]
        nether = [(round(px / 8.0), round(pz / 8.0)) for px, pz in destinations]
        if len(nether) <= 2: order = list(range(len(nether)))
        else:
            remaining = set(range(1, len(nether))); order = [0]
            while remaining:
                last = order[-1]; nxt = min(remaining, key=lambda index: _distance(nether[last], nether[index])); remaining.remove(nxt); order.append(nxt)
        total = sum(_distance(nether[a], nether[b]) for a, b in zip(order, order[1:])); return {"operation": name, "overworld_destinations": destinations, "nether_gates": nether, "route_order": order, "nether_route_blocks": total}
    return None


def navigation(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name not in {"Multi-stop Route", "Breadcrumb Simplifier", "Coordinate Route", "Resource Route", "Structure Tour", "Biome Expedition", "Loop Detection"}:
        return None
    from .navigation.routes import Point, breadcrumb_simplify, greedy_route
    if name == "Breadcrumb Simplifier":
        points = []
        for token in str(p.get("points", "0,64,0;8,64,0;16,64,0;16,64,8")).split(";"):
            values = [value.strip() for value in token.split(",")]
            if len(values) < 3: continue
            try: points.append(Point(float(values[0]), float(values[1]), float(values[2])))
            except ValueError: pass
        tolerance = max(0.01, float(p.get("tolerance", 2.0))); result = breadcrumb_simplify(points, tolerance)
        return {"operation": name, "tolerance": tolerance, "input_count": len(points), "output_count": len(result), "points": [(point.x, point.y, point.z) for point in result]}
    if name == "Loop Detection":
        parsed = []
        for token in str(p.get("points", "0,64,0;20,64,0;20,64,20;0,64,20;1,64,1")).split(";"):
            values = [value.strip() for value in token.split(",")]
            if len(values) < 3: continue
            try: parsed.append(tuple(map(float, values[:3])))
            except ValueError: pass
        epsilon = max(0.01, float(p.get("epsilon", 4.0))); repeats = []
        for i, first in enumerate(parsed):
            for j in range(i + 2, len(parsed)):
                distance = math.dist(first, parsed[j])
                if distance <= epsilon: repeats.append({"first": i, "second": j, "distance": distance})
        return {"operation": name, "epsilon": epsilon, "loops": repeats, "has_loop": bool(repeats)}
    text = str(p.get("stops", p.get("points", "80,64,0,A;80,64,80,B;0,64,80,C"))); start = Point(float(p.get("x1", 0)), float(p.get("y1", 64)), float(p.get("z1", 0)), "Start"); stops = []
    for token in text.split(";"):
        values = [value.strip() for value in token.split(",")]
        if len(values) < 3: continue
        try: stops.append(Point(float(values[0]), float(values[1]), float(values[2]), values[3] if len(values) > 3 else f"Stop {len(stops)+1}"))
        except ValueError: pass
    route = greedy_route(start, stops, bool(p.get("return_to_start", False)))
    return {"operation": name, "start": (start.x, start.y, start.z), "route": [(point.name, point.x, point.y, point.z) for point in route["route"]], "distance": route["distance"]}


def world_seed_tool(name: str, submenu: str, p: dict[str, Any], executor=None) -> dict[str, Any] | None:
    if submenu == "Biomes" and name in {"Largest Ocean", "Mountain Peak Finder", "Valley Finder", "Island Finder", "Cliff Locator"}:
        world = str(p.get("world_path", "")).strip()
        if not world:
            return {"operation": name, "requires_generated_world": True, "reason": "This feature identifies generated terrain shape. Select a Java world save so F3+ can inspect actual chunks instead of substituting biome samples."}
        from .world_analysis import analyze_world
        data = analyze_world(world, dimension=str(p.get("dimension", "Overworld")), center_chunk=(int(p.get("cx", 0)), int(p.get("cz", 0))), radius_chunks=int(p.get("radius", 64))); key = {"Largest Ocean": "largest_ocean", "Mountain Peak Finder": "peak", "Valley Finder": "valley", "Island Finder": "largest_islands", "Cliff Locator": "largest_cliff"}[name]
        return {"operation": name, "result": data[key], "chunks_scanned": data["chunks_scanned"], "source": "generated-world block states"}
    if submenu == "World Analysis" and name in {"Ore Distribution", "Ore Exposure Estimate", "Cave Exposure Estimate", "Technical World Score", "Resource Score"}:
        world = str(p.get("world_path", "")).strip()
        if not world: return {"operation": name, "requires_generated_world": True, "reason": "Select a generated Java world save. F3+ does not substitute unrelated candidate counts for terrain/resource analysis."}
        from .world_analysis import analyze_world
        data = analyze_world(world, dimension=str(p.get("dimension", "Overworld")), center_chunk=(int(p.get("cx", 0)), int(p.get("cz", 0))), radius_chunks=int(p.get("radius", 64)))
        if name == "Ore Distribution": result = {"ore_counts": data["ore_counts"], "ore_by_y": data["ore_by_y"]}
        elif name == "Ore Exposure Estimate": result = {"exposed_ore_counts": data["exposed_ore_counts"], "limitations": data["limitations"]}
        elif name == "Cave Exposure Estimate": result = {"cave_air_blocks": data["cave_air_blocks"], "cave_surface_faces": data["cave_surface_faces"], "limitations": data["limitations"]}
        elif name == "Technical World Score": result = {"technical_world_score": data["technical_world_score"], "resource_score": data["resource_score"], "peak": data["peak"], "largest_cliff": data["largest_cliff"]}
        else: result = {"resource_score": data["resource_score"], "ore_counts": data["ore_counts"]}
        return {"operation": name, "chunks_scanned": data["chunks_scanned"], "source": "generated-world block states", **result}
    return portal_tool(name, p)


def villager_tool(name: str, version: str, p: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if name not in {"Trade Search", "Trade Comparison", "Emerald Calculator", "Trade Cycle Calculator", "Librarian Browser"}:
        return None
    from .villagers import load_for_version, search
    params = dict(p or {}); trades, source = load_for_version(version)
    if not trades: return {"operation": name, "available": False, "source": source, "reason": "No compatible villager trade definitions were found."}
    query = str(params.get("query", "")).strip(); profession = str(params.get("profession", "")).strip().lower() or None; level = int(params.get("level", 0) or 0) or None; rows = search(trades, query, profession, level)
    if name == "Librarian Browser":
        rows = [trade for trade in trades if trade.profession == "librarian" and (not query or query.lower() in (trade.name + " " + trade.wants + " " + trade.gives).lower())]; return {"operation": name, "source": source, "count": len(rows), "trades": [trade.dict() for trade in rows]}
    if name == "Trade Search": return {"operation": name, "source": source, "query": query, "count": len(rows), "trades": [trade.dict() for trade in rows[:500]]}
    if name == "Trade Comparison":
        item = query.lower(); matches = [trade for trade in trades if not item or item in (trade.gives + " " + trade.name).lower()]; matches.sort(key=lambda trade: (trade.level, str(trade.wants), -float(trade.max_uses or 0))); return {"operation": name, "source": source, "item": query, "count": len(matches), "ranked": [trade.dict() for trade in matches[:200]]}
    cycles = max(1, int(params.get("cycles", 1)))
    if name == "Emerald Calculator":
        emerald_in = 0.0; emerald_out = 0.0; details = []
        for trade in rows:
            uses = min(cycles, int(trade.max_uses or cycles)); wants = trade.wants.lower(); gives = trade.gives.lower(); emerald_in += uses if "emerald" in wants else 0; emerald_out += uses if "emerald" in gives else 0; details.append({"trade": trade.name, "uses": uses, "wants": trade.wants, "gives": trade.gives})
        return {"operation": name, "source": source, "cycles": cycles, "emeralds_spent_trade_units": emerald_in, "emeralds_received_trade_units": emerald_out, "net_trade_units": emerald_out - emerald_in, "details": details[:200], "note": "Variable trade providers are reported as trade-unit flow rather than fabricated exact quantities."}
    return {"operation": name, "source": source, "cycles": cycles, "trades": [{"name": trade.name, "max_uses": trade.max_uses, "cycles_before_restock": math.ceil(cycles / max(1, int(trade.max_uses or 1)))} for trade in rows[:200]]}


def safety_descriptor(name: str, p: dict[str, Any], executor=None) -> dict[str, Any]:
    settings = getattr(executor, "settings", None) if executor else None; mapping = {"Runtime Limit": ("runtime_limit_seconds", "seconds"), "Action Counter": ("action_limit", "limit"), "Delayed Start": ("delayed_start_seconds", "delay"), "Recovery Attempts": ("recovery_attempts", "attempts"), "Restore Hotbar": ("restore_hotbar_slot", "slot"), "Stuck Detection": ("stuck_window_seconds", "seconds"), "Focus Loss Stop": ("focus_loss_stop", "enabled")}; field = mapping.get(name)
    if field is None: return {"control": name, "implemented": True}
    setting_name, param_name = field; current = getattr(settings, setting_name, None) if settings is not None else None
    return {"control": name, "implemented": True, "setting": setting_name, "current": current, "requested": p.get(param_name, current), "enforced_by": "MacroEngine"}


def utility_descriptor(name: str, p: dict[str, Any], executor=None) -> dict[str, Any] | None:
    settings = getattr(executor, "settings", None) if executor else None
    if name == "Control Bindings": return {"action": "edit_control_bindings", "persistent": True, "bindings": asdict(settings.keybinds) if settings is not None else {}, "applies_to": "all macro input through BoundInput"}
    if name == "Turn Calibration": return {"action": "turn_calibration", "current_mouse_units_per_90": getattr(settings, "turn_units_per_90", 900) if settings is not None else 900, "persistent": True}
    if name == "Movement Calibration": return {"action": "movement_calibration", "current_blocks_per_second": getattr(settings, "movement_blocks_per_second", 4.317) if settings is not None else 4.317, "persistent": True}
    if name in {"Backup Settings", "Export Profiles", "Import Profiles"}: return {"action": name.lower().replace(" ", "_"), "persistent": True, "format": "F3+ JSON settings", "implemented_by": "state_workbenches"}
    return None


__all__ = [
    "JavaRandom", "rng_tool", "portal_tool", "navigation", "world_seed_tool",
    "villager_tool", "safety_descriptor", "utility_descriptor", "_selected_mc",
]
