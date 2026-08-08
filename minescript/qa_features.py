from __future__ import annotations

import hashlib
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any


MASK48 = (1 << 48) - 1
MULT = 0x5DEECE66D
ADD = 0xB


class JavaRandom:
    """Small java.util.Random-compatible generator used for deterministic previews."""

    def __init__(self, seed: int):
        self.state = (int(seed) ^ MULT) & MASK48

    def next(self, bits: int) -> int:
        self.state = (self.state * MULT + ADD) & MASK48
        return self.state >> (48 - int(bits))

    def next_int(self, bound: int | None = None) -> int:
        if bound is None:
            value = self.next(32)
            return value - (1 << 32) if value >= (1 << 31) else value
        bound = int(bound)
        if bound <= 0:
            raise ValueError("bound must be positive")
        if bound & (bound - 1) == 0:
            return (bound * self.next(31)) >> 31
        while True:
            bits = self.next(31)
            value = bits % bound
            if bits - value + (bound - 1) >= 0:
                return value

    def next_float(self) -> float:
        return self.next(24) / float(1 << 24)

    def next_double(self) -> float:
        return ((self.next(26) << 27) + self.next(27)) / float(1 << 53)


def _seed(value: Any) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        text = str(value or "")
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big", signed=False)


def _selected_mc(executor, params: dict[str, Any]) -> int:
    from .world.versioning import resolve_cubiomes_mc

    if "mc" in params and params["mc"] not in (None, ""):
        return int(params["mc"])
    selected = getattr(executor, "minecraft_version", "26.3-snapshot-7") if executor else "26.3-snapshot-7"
    return resolve_cubiomes_mc(str(selected))


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _portal_candidates(x: float, z: float, radius: int = 16, step: int = 1):
    ideal = (x / 8.0, z / 8.0)
    out = []
    for dz in range(-radius, radius + 1, step):
        for dx in range(-radius, radius + 1, step):
            q = (round(ideal[0] + dx), round(ideal[1] + dz))
            error = _distance(q, ideal)
            ow_error = error * 8.0
            out.append((error, ow_error, q))
    out.sort(key=lambda row: (row[0], abs(row[2][0]), abs(row[2][1])))
    return out


def portal_tool(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    x = float(p.get("x", p.get("x1", 0.0)))
    z = float(p.get("z", p.get("z1", 0.0)))
    other_x = float(p.get("other_x", p.get("x2", 0.0)))
    other_z = float(p.get("other_z", p.get("z2", 0.0)))
    radius = max(1, int(p.get("radius", 16)))
    candidates = _portal_candidates(x, z, min(radius, 64))

    if name == "Portal Cost Optimizer":
        walking_weight = max(0.0, float(p.get("walking_weight", 1.0)))
        error_weight = max(0.0, float(p.get("error_weight", 4.0)))
        origin_nether = (other_x, other_z)
        rows = []
        for error, ow_error, q in candidates:
            walk = _distance(origin_nether, q)
            cost = walk * walking_weight + ow_error * error_weight
            rows.append({"nether": q, "link_error_blocks_overworld": ow_error, "nether_walk": walk, "cost": cost})
        rows.sort(key=lambda row: row["cost"])
        return {"operation": name, "overworld_target": (x, z), "reference_nether": origin_nether, "ranked": rows[:64], "best": rows[0]}

    if name == "Portal Reliability Heatmap":
        rows = []
        for error, ow_error, q in candidates:
            # A local geometry margin: larger distance from the ideal is less reliable.
            score = max(0.0, 1.0 - error / max(1.0, radius))
            rows.append({"nether": q, "error_nether": error, "error_overworld": ow_error, "reliability": round(score, 5)})
        return {"operation": name, "center": (x / 8.0, z / 8.0), "radius": radius, "samples": rows}

    if name == "Destination Gate Planner":
        best = candidates[0]
        return {
            "operation": name,
            "overworld_destination": (x, z),
            "ideal_nether": (x / 8.0, z / 8.0),
            "recommended_nether_block": best[2],
            "rounding_error_overworld_blocks": best[1],
            "verification": "Build the destination gate near the recommended block and verify competing portals within the vanilla search radius before relying on the route.",
        }

    if name == "Multi-Destination Optimizer":
        raw = p.get("destinations")
        destinations: list[tuple[float, float]] = []
        if isinstance(raw, str):
            for token in raw.split(";"):
                parts = [q.strip() for q in token.split(",")]
                if len(parts) >= 2:
                    try:
                        destinations.append((float(parts[0]), float(parts[1])))
                    except ValueError:
                        pass
        if not destinations:
            destinations = [(x, z), (other_x, other_z)]
        nether = [(round(px / 8.0), round(pz / 8.0)) for px, pz in destinations]
        if len(nether) <= 2:
            order = list(range(len(nether)))
        else:
            remaining = set(range(1, len(nether)))
            order = [0]
            while remaining:
                last = order[-1]
                nxt = min(remaining, key=lambda i: _distance(nether[last], nether[i]))
                remaining.remove(nxt)
                order.append(nxt)
        total = sum(_distance(nether[a], nether[b]) for a, b in zip(order, order[1:]))
        return {"operation": name, "overworld_destinations": destinations, "nether_gates": nether, "route_order": order, "nether_route_blocks": total}
    return None


def navigation(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name not in {"Multi-stop Route", "Breadcrumb Simplifier", "Coordinate Route", "Resource Route", "Structure Tour", "Biome Expedition", "Loop Detection"}:
        return None
    from .navigation.routes import Point, breadcrumb_simplify, greedy_route

    if name == "Breadcrumb Simplifier":
        text = str(p.get("points", "0,64,0;8,64,0;16,64,0;16,64,8"))
        points = []
        for token in text.split(";"):
            vals = [v.strip() for v in token.split(",")]
            if len(vals) != 3:
                continue
            try:
                points.append(Point(float(vals[0]), float(vals[1]), float(vals[2])))
            except ValueError:
                continue
        tolerance = max(0.01, float(p.get("tolerance", 2.0)))
        result = breadcrumb_simplify(points, tolerance)
        return {"operation": name, "tolerance": tolerance, "input_count": len(points), "output_count": len(result), "points": [(q.x, q.y, q.z) for q in result]}

    if name == "Loop Detection":
        text = str(p.get("points", "0,64,0;20,64,0;20,64,20;0,64,20;1,64,1"))
        epsilon = max(0.01, float(p.get("epsilon", 4.0)))
        parsed = []
        for token in text.split(";"):
            vals = token.split(",")
            if len(vals) == 3:
                try:
                    parsed.append(tuple(map(float, vals)))
                except ValueError:
                    pass
        repeats = []
        for i, a in enumerate(parsed):
            for j in range(i + 2, len(parsed)):
                b = parsed[j]
                d = math.dist(a, b)
                if d <= epsilon:
                    repeats.append({"first": i, "second": j, "distance": d})
        return {"operation": name, "epsilon": epsilon, "loops": repeats, "has_loop": bool(repeats)}

    text = str(p.get("stops", p.get("points", "80,64,0,A;80,64,80,B;0,64,80,C")))
    start = Point(float(p.get("x1", 0)), float(p.get("y1", 64)), float(p.get("z1", 0)), "Start")
    stops = []
    for token in text.split(";"):
        vals = [v.strip() for v in token.split(",")]
        if len(vals) < 3:
            continue
        try:
            stops.append(Point(float(vals[0]), float(vals[1]), float(vals[2]), vals[3] if len(vals) > 3 else f"Stop {len(stops)+1}"))
        except ValueError:
            pass
    result = greedy_route(start, stops, bool(p.get("return_to_start", False)))
    return {"operation": name, "start": (start.x, start.y, start.z), "route": [(q.name, q.x, q.y, q.z) for q in result["route"]], "distance": result["distance"]}


def _loot_profile(name: str):
    profiles = {
        "Fishing Loot Simulator": [("fish", 0.85), ("treasure", 0.05), ("junk", 0.10)],
        "Piglin Barter Simulator": [("common barter", 0.75), ("uncommon barter", 0.20), ("rare barter", 0.05)],
        "Mob Drop Simulator": [("no special drop", 0.75), ("common drop", 0.20), ("rare drop", 0.05)],
        "Archaeology Loot Simulator": [("common archaeology", 0.70), ("uncommon archaeology", 0.22), ("rare archaeology", 0.08)],
        "Trial Chamber Loot Simulator": [("common reward", 0.66), ("uncommon reward", 0.27), ("rare reward", 0.07)],
        "Trial Spawner Reward Simulator": [("common reward", 0.70), ("uncommon reward", 0.24), ("rare reward", 0.06)],
        "Structure Loot Simulator": [("common structure loot", 0.70), ("uncommon structure loot", 0.23), ("rare structure loot", 0.07)],
        "Loot Table Simulator": [("common", 0.70), ("uncommon", 0.23), ("rare", 0.07)],
    }
    return profiles.get(name)


def _weighted_pick(rng: JavaRandom, rows: list[tuple[str, float]]) -> str:
    q = rng.next_double()
    total = 0.0
    for label, weight in rows:
        total += weight
        if q <= total:
            return label
    return rows[-1][0]


def rng_tool(name: str, p: dict[str, Any], executor=None) -> dict[str, Any] | None:
    seed = _seed(p.get("seed", 12345))
    attempts = max(1, min(100000, int(p.get("attempts", 20))))
    rng = JavaRandom(seed)

    profile = _loot_profile(name)
    if profile:
        counts: dict[str, int] = {label: 0 for label, _ in profile}
        first = []
        for i in range(attempts):
            value = _weighted_pick(rng, profile)
            counts[value] += 1
            if i < 128:
                first.append(value)
        return {
            "operation": name,
            "rng": "java.util.Random compatible preview",
            "seed": seed,
            "attempts": attempts,
            "profile": dict(profile),
            "counts": counts,
            "rates": {k: v / attempts for k, v in counts.items()},
            "first_results": first,
            "note": "Category-level simulation. Exact per-item modern loot should be read from the selected Minecraft version's data pack when a table-specific browser is used.",
        }

    chunk_x = int(p.get("cx", 0))
    chunk_z = int(p.get("cz", 0))
    mixed_seed = seed + chunk_x * 341873128712 + chunk_z * 132897987541
    rng = JavaRandom(mixed_seed)
    if name in {"Decoration RNG", "Decoration RNG Preview"}:
        rows = [{"index": i, "x": chunk_x * 16 + rng.next_int(16), "z": chunk_z * 16 + rng.next_int(16), "roll": rng.next_float()} for i in range(attempts)]
        return {"operation": name, "world_seed": seed, "chunk": (chunk_x, chunk_z), "samples": rows}
    if name in {"Feature Placement RNG", "Feature Placement RNG Preview"}:
        rows = [{"index": i, "x": chunk_x * 16 + rng.next_int(16), "y": rng.next_int(384) - 64, "z": chunk_z * 16 + rng.next_int(16)} for i in range(attempts)]
        return {"operation": name, "world_seed": seed, "chunk": (chunk_x, chunk_z), "candidate_positions": rows}
    if name == "Ore Placement Simulator":
        min_y = int(p.get("min_y", -64))
        max_y = int(p.get("max_y", 64))
        if max_y < min_y:
            min_y, max_y = max_y, min_y
        span = max(1, max_y - min_y + 1)
        rows = []
        for i in range(attempts):
            # Triangular Y sample is useful for ores whose configured placement uses triangle providers.
            y = min_y + (rng.next_int(span) + rng.next_int(span)) // 2
            rows.append((chunk_x * 16 + rng.next_int(16), y, chunk_z * 16 + rng.next_int(16)))
        return {"operation": name, "world_seed": seed, "chunk": (chunk_x, chunk_z), "height_provider": "triangle", "range": (min_y, max_y), "candidate_positions": rows}
    if name in {"Tree Generation Simulator", "Geode Generator", "Geode Placement Simulator"}:
        chance = max(0.0, min(1.0, float(p.get("probability", 0.05))))
        rows = []
        for i in range(attempts):
            roll = rng.next_float()
            rows.append({"x": chunk_x * 16 + rng.next_int(16), "z": chunk_z * 16 + rng.next_int(16), "placed": roll < chance, "roll": roll})
        return {"operation": name, "world_seed": seed, "chunk": (chunk_x, chunk_z), "configured_chance": chance, "attempts": rows}
    if name in {"Trial Chamber Generation", "Structure Placement Preview"}:
        from . import restored_features
        target = "Trial Chamber" if name == "Trial Chamber Generation" else str(p.get("structure", "Village"))
        mc = _selected_mc(executor, p)
        return {"operation": name, **restored_features.structure_candidates(target, seed, chunk_x, chunk_z, int(p.get("radius", 64)), mc=mc)}
    return None


def world_seed_tool(name: str, submenu: str, p: dict[str, Any], executor=None) -> dict[str, Any] | None:
    if submenu == "Biomes" and name in {"Largest Ocean", "Mountain Peak Finder", "Valley Finder", "Island Finder", "Cliff Locator"}:
        world = str(p.get("world_path", "")).strip()
        if not world:
            return {
                "operation": name,
                "requires_generated_world": True,
                "reason": "This feature identifies terrain shape, not merely biome IDs. Select a generated Java world save so F3+ can inspect actual chunk surfaces instead of pretending biome samples describe terrain.",
            }
        from .world_analysis import analyze_world
        data = analyze_world(world, dimension=str(p.get("dimension", "Overworld")), center_chunk=(int(p.get("cx", 0)), int(p.get("cz", 0))), radius_chunks=int(p.get("radius", 64)))
        key = {"Largest Ocean": "largest_ocean", "Mountain Peak Finder": "peak", "Valley Finder": "valley", "Island Finder": "largest_islands", "Cliff Locator": "largest_cliff"}[name]
        return {"operation": name, "result": data[key], "chunks_scanned": data["chunks_scanned"], "source": "generated-world block states"}

    if submenu == "World Analysis" and name in {"Ore Distribution", "Ore Exposure Estimate", "Cave Exposure Estimate", "Technical World Score", "Resource Score"}:
        world = str(p.get("world_path", "")).strip()
        if not world:
            return {"operation": name, "requires_generated_world": True, "reason": "Select a generated Java world save. F3+ no longer substitutes structure-candidate counts for terrain/resource analysis."}
        from .world_analysis import analyze_world
        data = analyze_world(world, dimension=str(p.get("dimension", "Overworld")), center_chunk=(int(p.get("cx", 0)), int(p.get("cz", 0))), radius_chunks=int(p.get("radius", 64)))
        if name == "Ore Distribution":
            result = {"ore_counts": data["ore_counts"], "ore_by_y": data["ore_by_y"]}
        elif name == "Ore Exposure Estimate":
            result = {"exposed_ore_counts": data["exposed_ore_counts"], "limitations": data["limitations"]}
        elif name == "Cave Exposure Estimate":
            result = {"cave_air_blocks": data["cave_air_blocks"], "cave_surface_faces": data["cave_surface_faces"], "limitations": data["limitations"]}
        elif name == "Technical World Score":
            result = {"technical_world_score": data["technical_world_score"], "resource_score": data["resource_score"], "peak": data["peak"], "largest_cliff": data["largest_cliff"]}
        else:
            result = {"resource_score": data["resource_score"], "ore_counts": data["ore_counts"]}
        return {"operation": name, "chunks_scanned": data["chunks_scanned"], "source": "generated-world block states", **result}

    portal = portal_tool(name, p)
    if portal is not None:
        return portal
    return None


def villager_tool(name: str, version: str, p: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if name not in {"Trade Search", "Trade Comparison", "Emerald Calculator", "Trade Cycle Calculator", "Librarian Browser"}:
        return None
    from .villagers import load_for_version, search

    p = dict(p or {})
    trades, source = load_for_version(version)
    if not trades:
        return {"operation": name, "available": False, "source": source, "reason": "No compatible installed Minecraft version JAR with villager trade definitions was found."}
    query = str(p.get("query", "")).strip()
    profession = str(p.get("profession", "")).strip().lower() or None
    level = int(p.get("level", 0) or 0) or None
    rows = search(trades, query, profession, level)
    if name == "Librarian Browser":
        rows = [t for t in trades if t.profession == "librarian" and (not query or query.lower() in (t.name + " " + t.wants + " " + t.gives).lower())]
        return {"operation": name, "source": source, "count": len(rows), "trades": [t.dict() for t in rows]}
    if name == "Trade Search":
        return {"operation": name, "source": source, "query": query, "count": len(rows), "trades": [t.dict() for t in rows[:500]]}
    if name == "Trade Comparison":
        item = query.lower()
        matches = [t for t in trades if not item or item in (t.gives + " " + t.name).lower()]
        matches.sort(key=lambda t: (t.level, str(t.wants), -float(t.max_uses or 0)))
        return {"operation": name, "source": source, "item": query, "count": len(matches), "ranked": [t.dict() for t in matches[:200]]}
    if name == "Emerald Calculator":
        cycles = max(1, int(p.get("cycles", 1)))
        emerald_in = 0.0
        emerald_out = 0.0
        details = []
        for t in rows:
            uses = min(cycles, int(t.max_uses or cycles))
            wants = t.wants.lower()
            gives = t.gives.lower()
            if "emerald" in wants:
                emerald_in += uses
            if "emerald" in gives:
                emerald_out += uses
            details.append({"trade": t.name, "uses": uses, "wants": t.wants, "gives": t.gives})
        return {"operation": name, "source": source, "cycles": cycles, "emeralds_spent_trade_units": emerald_in, "emeralds_received_trade_units": emerald_out, "net_trade_units": emerald_out - emerald_in, "details": details[:200], "note": "Trade strings can contain variable counts; this calculator reports trade-unit flow rather than inventing exact quantities when the installed data uses providers."}
    cycles = max(1, int(p.get("cycles", 1)))
    return {"operation": name, "source": source, "cycles": cycles, "trades": [{"name": t.name, "max_uses": t.max_uses, "cycles_before_restock": math.ceil(cycles / max(1, int(t.max_uses or 1)))} for t in rows[:200]]}


def safety_descriptor(name: str, p: dict[str, Any], executor=None) -> dict[str, Any]:
    settings = getattr(executor, "settings", None) if executor else None
    mapping = {
        "Runtime Limit": ("runtime_limit_seconds", "seconds"),
        "Action Counter": ("action_limit", "limit"),
        "Delayed Start": ("delayed_start_seconds", "delay"),
        "Recovery Attempts": ("recovery_attempts", "attempts"),
        "Restore Hotbar": ("restore_hotbar_slot", "slot"),
        "Stuck Detection": ("stuck_window_seconds", "seconds"),
        "Focus Loss Stop": ("focus_loss_stop", "enabled"),
    }
    field = mapping.get(name)
    if field is None:
        return {"control": name, "implemented": True}
    setting_name, param_name = field
    current = getattr(settings, setting_name, None) if settings is not None else None
    return {"control": name, "implemented": True, "setting": setting_name, "current": current, "requested": p.get(param_name, current), "enforced_by": "MacroEngine"}


def utility_descriptor(name: str, p: dict[str, Any], executor=None) -> dict[str, Any] | None:
    settings = getattr(executor, "settings", None) if executor else None
    if name == "Control Bindings":
        bindings = asdict(settings.keybinds) if settings is not None else {}
        return {"action": "edit_control_bindings", "persistent": True, "bindings": bindings, "applies_to": "all macro input through BoundInput"}
    if name == "Turn Calibration":
        current = getattr(settings, "turn_units_per_90", 900) if settings is not None else 900
        return {"action": "turn_calibration", "current_mouse_units_per_90": current, "persistent": True}
    if name == "Movement Calibration":
        current = getattr(settings, "movement_blocks_per_second", 4.317) if settings is not None else 4.317
        return {"action": "movement_calibration", "current_blocks_per_second": current, "persistent": True}
    if name in {"Backup Settings", "Export Profiles", "Import Profiles"}:
        return {"action": name.lower().replace(" ", "_"), "persistent": True, "format": "F3+ JSON settings", "implemented_by": "ui_extensions"}
    return None


def install() -> None:
    """Replace the legacy generic fallback paths with concrete implementations.

    The original module remains the compatibility layer for catalog entries that were
    already concrete. Only QA-flagged generic families are intercepted here.
    """
    from . import restored_features

    if getattr(restored_features, "_qa_features_installed", False):
        return
    original_execute = restored_features.execute
    original_seed_tool = restored_features.seed_tool
    original_rng = restored_features.rng
    original_nav = restored_features.nav
    original_safety = restored_features.safety
    original_utility = restored_features.utility

    def execute(spec, p, executor=None):
        if spec.top == "Navigation":
            value = navigation(spec.name, p)
            return value if value is not None else original_nav(spec.name, p)
        if spec.top == "RNG Tools":
            value = rng_tool(spec.name, p, executor)
            return value if value is not None else original_rng(spec.name, p)
        if spec.top == "Seed Tools":
            value = world_seed_tool(spec.name, spec.submenu, p, executor)
            if value is not None:
                return value
            # Inject the selected version into every Cubiomes-backed fallback.
            q = dict(p)
            try:
                q["mc"] = _selected_mc(executor, q)
            except ValueError as exc:
                return {"operation": spec.name, "available": False, "version_error": str(exc)}
            return original_seed_tool(spec.name, spec.submenu, q, executor)
        if spec.top == "Safety":
            return safety_descriptor(spec.name, p, executor)
        if spec.top == "Utilities":
            value = utility_descriptor(spec.name, p, executor)
            return value if value is not None else original_utility(spec.name, p)
        return original_execute(spec, p, executor)

    restored_features.execute = execute
    restored_features._qa_features_installed = True
