from __future__ import annotations

import math
from collections import Counter, deque
from pathlib import Path
from statistics import median
from typing import Any

from .catalog_integrity import annotate, generic_placeholder_reason


def _components(points: set[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    unseen = set(points)
    groups: list[list[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        q = deque([start])
        group = [start]
        while q:
            x, z = q.popleft()
            for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
                if n in unseen:
                    unseen.remove(n)
                    q.append(n)
                    group.append(n)
        groups.append(group)
    groups.sort(key=len, reverse=True)
    return groups


def _world_chunks(world_path: str, dimension: str, cx0: int, cz0: int, radius: int, max_chunks: int = 4096):
    from .world_analysis import _region_dir, analyze_chunk, iter_region_chunks

    root = Path(world_path).expanduser()
    region = _region_dir(root, dimension)
    if not region.is_dir():
        raise FileNotFoundError(f"No region directory found at {region}")
    rows = []
    for region_file in sorted(region.glob("r.*.*.mca")):
        for raw in iter_region_chunks(region_file):
            cx = int(raw.get("xPos", 0))
            cz = int(raw.get("zPos", 0))
            if abs(cx - cx0) <= radius and abs(cz - cz0) <= radius:
                rows.append(analyze_chunk(raw))
                if len(rows) >= max_chunks:
                    return rows
    if not rows:
        raise ValueError("No generated chunks were found in the selected scan area")
    return rows


def _terrain_tool(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    terrain_names = {
        "Largest Ocean", "Largest Mountain Chain", "Largest Cave Region", "Flat Terrain Finder",
        "Valley Finder", "Mountain Peak Finder", "Terrain Base Finder", "Island Finder",
        "Peninsula Detector", "River Crossing Finder", "Lake Density", "Cliff Locator",
    }
    if name not in terrain_names:
        return None
    world = str(p.get("world_path", "")).strip()
    if not world:
        return {
            "operation": name,
            "requires_generated_world": True,
            "reason": "This tool measures generated terrain shape. Select a Java world save; F3+ will not pretend biome IDs are terrain height/cave geometry.",
        }
    cx0 = int(p.get("cx", 0))
    cz0 = int(p.get("cz", 0))
    radius = max(1, int(p.get("radius", 64)))
    dimension = str(p.get("dimension", "Overworld"))
    rows = _world_chunks(world, dimension, cx0, cz0, radius)
    by_pos = {tuple(row["chunk"]): row for row in rows}
    heights = {pos: float(row["mean_surface_y"]) for pos, row in by_pos.items() if row["mean_surface_y"] is not None}
    water = {pos for pos, row in by_pos.items() if float(row["water_top_ratio"]) >= 0.5}
    land = set(by_pos) - water

    if name == "Mountain Peak Finder":
        ranked = sorted(((row["max_surface_y"], pos) for pos, row in by_pos.items() if row["max_surface_y"] is not None), reverse=True)
        return {"operation": name, "source": "generated-world block states", "peak": {"y": ranked[0][0], "chunk": ranked[0][1]} if ranked else None, "ranked": ranked[:64], "chunks_scanned": len(rows)}
    if name == "Valley Finder":
        ranked = sorted((row["min_surface_y"], pos) for pos, row in by_pos.items() if row["min_surface_y"] is not None)
        return {"operation": name, "source": "generated-world block states", "valley": {"y": ranked[0][0], "chunk": ranked[0][1]} if ranked else None, "ranked": ranked[:64], "chunks_scanned": len(rows)}
    if name == "Cliff Locator":
        cliffs = []
        for (x, z), h in heights.items():
            for n in ((x + 1, z), (x, z + 1)):
                if n in heights:
                    cliffs.append((abs(h - heights[n]), (x, z), n))
        cliffs.sort(reverse=True)
        return {"operation": name, "source": "generated-world block states", "largest": cliffs[0] if cliffs else None, "ranked": cliffs[:128], "chunks_scanned": len(rows), "metric": "difference in mean surface Y between adjacent generated chunks"}
    if name == "Flat Terrain Finder":
        ranked = []
        for pos, row in by_pos.items():
            lo, hi = row["min_surface_y"], row["max_surface_y"]
            if lo is not None and hi is not None:
                ranked.append((hi - lo, abs(float(row["mean_surface_y"] or 0) - 64.0), pos, row["mean_surface_y"]))
        ranked.sort()
        return {"operation": name, "source": "generated-world block states", "ranked": [{"chunk": q[2], "surface_relief": q[0], "mean_y": q[3]} for q in ranked[:128]], "chunks_scanned": len(rows)}
    if name == "Terrain Base Finder":
        ranked = []
        for pos, row in by_pos.items():
            lo, hi, mean_y = row["min_surface_y"], row["max_surface_y"], row["mean_surface_y"]
            if lo is not None and hi is not None and mean_y is not None:
                score = float(mean_y) - 2.0 * float(hi - lo)
                ranked.append((score, pos, mean_y, hi - lo))
        ranked.sort(reverse=True)
        return {"operation": name, "source": "generated-world block states", "ranked": [{"chunk": q[1], "base_score": q[0], "mean_y": q[2], "relief": q[3]} for q in ranked[:128]], "formula": "mean_surface_y - 2*within_chunk_relief", "chunks_scanned": len(rows)}
    if name == "Largest Mountain Chain":
        threshold = float(p.get("mountain_y", 96.0))
        mountains = {pos for pos, h in heights.items() if h >= threshold}
        groups = _components(mountains)
        return {"operation": name, "source": "generated-world block states", "threshold_mean_y": threshold, "largest": {"size_chunks": len(groups[0]), "chunks": groups[0][:512]} if groups else None, "component_count": len(groups), "chunks_scanned": len(rows), "note": "Mountain-chain membership is an explicit mean-surface-Y threshold, not a biome-name proxy."}
    if name == "Largest Cave Region":
        values = [int(row["cave_air_blocks"]) for row in rows]
        threshold = int(p.get("cave_air_threshold", median(values) if values else 0))
        caves = {tuple(row["chunk"]) for row in rows if int(row["cave_air_blocks"]) >= threshold and int(row["cave_air_blocks"]) > 0}
        groups = _components(caves)
        return {"operation": name, "source": "generated-world block states", "cave_air_threshold": threshold, "largest": {"size_chunks": len(groups[0]), "chunks": groups[0][:512]} if groups else None, "component_count": len(groups), "chunks_scanned": len(rows)}
    water_groups = _components(water)
    land_groups = _components(land)
    if name == "Largest Ocean":
        return {"operation": name, "source": "generated-world block states", "largest": {"size_chunks": len(water_groups[0]), "chunks": water_groups[0][:512]} if water_groups else None, "water_chunk_count": len(water), "chunks_scanned": len(rows)}
    if name == "Island Finder":
        islands = []
        for group in land_groups:
            gs = set(group)
            border = 0
            wet = 0
            for x, z in group:
                for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
                    if n not in gs:
                        border += 1
                        wet += int(n in water)
            ratio = wet / border if border else 0.0
            if ratio >= 0.75:
                islands.append({"size_chunks": len(group), "water_border_ratio": ratio, "chunks": group[:512]})
        islands.sort(key=lambda q: q["size_chunks"], reverse=True)
        return {"operation": name, "source": "generated-world block states", "islands": islands[:64], "chunks_scanned": len(rows), "definition": "connected generated land component with >=75% sampled water boundary"}
    if name == "Peninsula Detector":
        candidates = []
        for x, z in land:
            wet = sum((x + dx, z + dz) in water for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if wet >= 3:
                candidates.append({"chunk": (x, z), "water_sides": wet})
        return {"operation": name, "source": "generated-world block states", "candidates": candidates, "chunks_scanned": len(rows), "definition": "generated land chunk with water on at least three cardinal neighboring chunks"}
    if name == "River Crossing Finder":
        crossings = []
        for x, z in water:
            ns = (x, z - 1) in land and (x, z + 1) in land
            ew = (x - 1, z) in land and (x + 1, z) in land
            if ns or ew:
                crossings.append({"water_chunk": (x, z), "crossing_axis": "north-south" if ns else "east-west"})
        return {"operation": name, "source": "generated-world block states", "candidates": crossings, "chunks_scanned": len(rows), "note": "Chunk-resolution crossing candidates; inspect locally before building."}
    # Lake Density: components touching the scan boundary are treated as ocean/unknown,
    # while enclosed water components are counted as lake candidates.
    minx, maxx = cx0 - radius, cx0 + radius
    minz, maxz = cz0 - radius, cz0 + radius
    lakes = []
    for group in water_groups:
        touches = any(x in (minx, maxx) or z in (minz, maxz) for x, z in group)
        if not touches:
            lakes.append(group)
    return {"operation": name, "source": "generated-world block states", "lake_components": len(lakes), "lake_chunks": sum(map(len, lakes)), "sampled_chunks": len(rows), "density": sum(map(len, lakes)) / max(1, len(rows)), "definition": "water components fully enclosed inside the sampled generated area"}


def _cubiomes_samples(p: dict[str, Any], executor=None):
    from .seed.bundled import cubiomes_status
    from .seed.cubiomes_api import biome_at
    from .world.versioning import resolve_cubiomes_mc

    status = cubiomes_status()
    if not status.available:
        return None, {"available": False, "backend": "cubiomes", "reason": status.note}
    selected = str(getattr(executor, "minecraft_version", "26.3-snapshot-7"))
    try:
        mc = int(p.get("mc")) if p.get("mc") not in (None, "") else resolve_cubiomes_mc(selected)
    except ValueError as exc:
        return None, {"available": False, "backend": "cubiomes", "reason": str(exc), "selected_version": selected}
    seed = int(str(p.get("seed", 0)).strip())
    x0 = int(p.get("x", int(p.get("cx", 0)) * 16 + 8))
    z0 = int(p.get("z", int(p.get("cz", 0)) * 16 + 8))
    y = int(p.get("y", 64))
    radius = max(16, int(p.get("radius", 256)))
    step = max(4, int(p.get("step", max(4, radius // 16))))
    rows = []
    for z in range(z0 - radius, z0 + radius + 1, step):
        for x in range(x0 - radius, x0 + radius + 1, step):
            q = biome_at(seed, x, y, z, dimension=0, mc=mc)
            rows.append((x, z, int(q.biome_id)))
    return rows, {"backend": "cubiomes", "mc_enum": mc, "seed": seed, "center": (x0, z0), "radius": radius, "step": step}


def _biome_tool(name: str, p: dict[str, Any], executor=None) -> dict[str, Any] | None:
    terrain = _terrain_tool(name, p)
    if terrain is not None:
        return terrain
    biome_names = {
        "Current Biome", "Nearest Biome", "Rare Biome Search", "Largest Biome", "Biome Boundary",
        "Two-Way Biome Intersection", "Three-Way Biome Intersection", "Four-Way Biome Intersection",
        "Biome Diversity Finder", "Largest Continuous Region",
    }
    if name not in biome_names:
        return None
    rows, meta = _cubiomes_samples(p, executor)
    if rows is None:
        return {"operation": name, **meta}
    counts = Counter(b for _, _, b in rows)
    x0, z0 = meta["center"]
    if name == "Current Biome":
        nearest = min(rows, key=lambda q: (q[0] - x0) ** 2 + (q[1] - z0) ** 2)
        return {"operation": name, **meta, "position": nearest[:2], "biome_id": nearest[2]}
    if name == "Nearest Biome":
        target = int(p.get("target_biome", min(counts, key=counts.get)))
        hits = [q for q in rows if q[2] == target]
        hits.sort(key=lambda q: (q[0] - x0) ** 2 + (q[1] - z0) ** 2)
        return {"operation": name, **meta, "target_biome_id": target, "nearest": hits[0] if hits else None, "sample_hits": hits[:128], "note": "Nearest at the configured sample resolution; reduce step for finer search."}
    if name == "Rare Biome Search":
        rare = sorted(counts.items(), key=lambda q: (q[1], q[0]))
        return {"operation": name, **meta, "rarest_sampled": rare[:16], "counts": dict(counts)}
    if name == "Largest Biome":
        return {"operation": name, **meta, "largest_by_sample_count": max(counts.items(), key=lambda q: q[1]) if counts else None, "counts": dict(counts), "note": "Sample-count area estimate, not an unsampled exact polygon."}
    grid = {(x, z): b for x, z, b in rows}
    step = int(meta["step"])
    if name == "Biome Boundary":
        boundary = []
        for (x, z), b in grid.items():
            for n in ((x + step, z), (x, z + step)):
                if n in grid and grid[n] != b:
                    boundary.append({"a": (x, z, b), "b": (n[0], n[1], grid[n])})
        return {"operation": name, **meta, "boundary_segments": boundary[:1000], "count": len(boundary)}
    required = {"Two-Way Biome Intersection": 2, "Three-Way Biome Intersection": 3, "Four-Way Biome Intersection": 4}.get(name)
    if required:
        hits = []
        for x, z, _ in rows:
            neighborhood = {grid.get((x + dx, z + dz)) for dx, dz in ((0, 0), (step, 0), (-step, 0), (0, step), (0, -step))}
            neighborhood.discard(None)
            if len(neighborhood) >= required:
                hits.append({"position": (x, z), "biome_ids": sorted(neighborhood)})
        return {"operation": name, **meta, "required_distinct_biomes": required, "candidates": hits[:1000], "count": len(hits)}
    if name == "Biome Diversity Finder":
        window = max(step * 2, int(p.get("diversity_window", step * 4)))
        scored = []
        for x, z, _ in rows:
            ids = {b for sx, sz, b in rows if abs(sx - x) <= window and abs(sz - z) <= window}
            scored.append((len(ids), x, z, sorted(ids)))
        scored.sort(reverse=True)
        return {"operation": name, **meta, "window_blocks": window, "ranked": [{"distinct": q[0], "position": (q[1], q[2]), "biome_ids": q[3]} for q in scored[:128]]}
    # Largest Continuous Region, at sample resolution.
    positions_by_biome: dict[int, set[tuple[int, int]]] = {}
    for x, z, b in rows:
        positions_by_biome.setdefault(b, set()).add((x // step, z // step))
    regions = []
    for biome, pts in positions_by_biome.items():
        groups = _components(pts)
        if groups:
            regions.append((len(groups[0]), biome, groups[0]))
    regions.sort(reverse=True)
    return {"operation": name, **meta, "largest": {"sample_cells": regions[0][0], "biome_id": regions[0][1], "cells": regions[0][2][:512]} if regions else None, "note": "Connectivity is measured on the configured sampling grid."}


def _structure_meta(name: str, p: dict[str, Any], executor=None) -> dict[str, Any] | None:
    composite = {
        "Compound Search", "Structure Chains", "Isolated Structure Finder", "Structure Cluster Finder",
        "Structure Density", "Structure Heatmap", "Structure Corridor", "Multi-Target Locator",
        "Portal-Optimized Structure Search",
    }
    if name not in composite:
        return None
    from .restored_features import structure_candidates
    from .world.versioning import resolve_cubiomes_mc

    seed = int(str(p.get("seed", 0)).strip())
    cx, cz = int(p.get("cx", 0)), int(p.get("cz", 0))
    radius = max(1, int(p.get("radius", 64)))
    selected = str(getattr(executor, "minecraft_version", "26.3-snapshot-7"))
    try:
        mc = resolve_cubiomes_mc(selected)
    except ValueError as exc:
        return {"operation": name, "available": False, "reason": str(exc), "selected_version": selected}
    targets = ("Village", "Trial Chamber", "Ocean Monument", "Pillager Outpost", "Ancient City", "Ruined Portal")
    sets = {target: structure_candidates(target, seed, cx, cz, radius, mc=mc)["candidate_chunks"] for target in targets}
    flat = [(target, q[0], q[1]) for target, points in sets.items() for q in points]
    if name == "Structure Density":
        area = (2 * radius + 1) ** 2
        return {"operation": name, "counts": {k: len(v) for k, v in sets.items()}, "total": len(flat), "candidate_density_per_1000_chunks": len(flat) * 1000 / area, "sampled_chunk_area": area, "note": "Placement-attempt density; final biome/terrain viability is separate."}
    if name == "Structure Heatmap":
        cell = max(4, radius // 8)
        buckets: Counter[tuple[int, int]] = Counter((x // cell, z // cell) for _, x, z in flat)
        return {"operation": name, "cell_size_chunks": cell, "cells": [{"cell": k, "candidates": v} for k, v in buckets.most_common()], "note": "Heatmap of placement candidates, not confirmed generated structures."}
    if name == "Structure Cluster Finder":
        clusters = []
        for i, a in enumerate(flat):
            group = [b for b in flat if math.hypot(a[1] - b[1], a[2] - b[2]) <= max(8, radius / 8)]
            if len(group) >= 2:
                clusters.append(group)
        clusters.sort(key=len, reverse=True)
        return {"operation": name, "clusters": clusters[:64], "cluster_radius_chunks": max(8, radius / 8), "note": "Clusters use placement candidates; confirm viability in-game/generated save."}
    if name == "Isolated Structure Finder":
        rows = []
        for a in flat:
            other = [math.hypot(a[1] - b[1], a[2] - b[2]) for b in flat if b != a]
            rows.append((min(other) if other else float("inf"), a))
        rows.sort(reverse=True, key=lambda q: q[0])
        return {"operation": name, "ranked": [{"nearest_other_chunks": q[0], "candidate": q[1]} for q in rows[:128]], "note": "Isolation among sampled placement candidates."}
    if name in {"Compound Search", "Multi-Target Locator"}:
        ranked = []
        for target, points in sets.items():
            for x, z in points[:128]:
                distances = {other: min((math.hypot(x - ox, z - oz) for ox, oz in ops), default=float("inf")) for other, ops in sets.items() if other != target}
                score = sum(1 for d in distances.values() if d <= radius / 4)
                ranked.append((score, target, x, z, distances))
        ranked.sort(reverse=True, key=lambda q: q[0])
        return {"operation": name, "ranked": [{"nearby_target_count": q[0], "structure": q[1], "chunk": (q[2], q[3]), "nearest_by_type": q[4]} for q in ranked[:128]], "note": "Multi-target placement-candidate search."}
    if name == "Structure Chains":
        remaining = list(flat)
        chain = []
        if remaining:
            current = min(remaining, key=lambda q: (q[1] - cx) ** 2 + (q[2] - cz) ** 2)
            chain.append(current); remaining.remove(current)
            while remaining:
                nxt = min(remaining, key=lambda q: math.hypot(q[1] - current[1], q[2] - current[2]))
                chain.append(nxt); remaining.remove(nxt); current = nxt
        distance = sum(math.hypot(a[1] - b[1], a[2] - b[2]) for a, b in zip(chain, chain[1:]))
        return {"operation": name, "chain": chain[:256], "route_chunks": distance, "note": "Greedy route through placement candidates; not a guarantee each candidate generates."}
    if name == "Structure Corridor":
        width = max(1.0, float(p.get("corridor_width", 8.0)))
        rows = [q for q in flat if abs(q[2] - cz) <= width or abs(q[1] - cx) <= width]
        rows.sort(key=lambda q: (q[1] - cx) ** 2 + (q[2] - cz) ** 2)
        return {"operation": name, "corridor_half_width_chunks": width, "candidates": rows[:256], "count": len(rows)}
    # Portal-Optimized Structure Search
    ranked = []
    for target, x, z in flat:
        nx, nz = x * 2.0, z * 2.0  # chunk center /8: (chunk*16)/8 = chunk*2
        nether_distance = math.hypot(nx - cx * 2.0, nz - cz * 2.0)
        ranked.append((nether_distance, target, (x, z), (round(nx), round(nz))))
    ranked.sort()
    return {"operation": name, "ranked": [{"nether_route_blocks": q[0], "structure": q[1], "chunk": q[2], "nether_gate_approx": q[3]} for q in ranked[:128]], "note": "Ranks placement candidates by Nether travel distance; confirm actual structure generation and portal linking."}


def _nether_planner(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    names = {
        "Asymmetric Jump Designer", "Maximum Displacement", "Repeating Network Generator",
        "Portal-State Simulator", "Routing Table Generator", "Corridor Transport",
        "Standard Route Comparison", "Portal Radius Visualizer",
    }
    if name not in names:
        return None
    x = float(p.get("x", 800.0)); y = float(p.get("y", 64.0)); z = float(p.get("z", -800.0))
    ox = float(p.get("other_x", 100.0)); oy = float(p.get("other_y", 64.0)); oz = float(p.get("other_z", 100.0))
    ideal = (x / 8.0, y, z / 8.0)
    other = (ox, oy, oz)
    if name == "Maximum Displacement":
        d = math.dist(ideal, other)
        return {"operation": name, "ideal_nether": ideal, "other_nether": other, "nether_displacement": d, "overworld_equivalent_horizontal": math.hypot(ideal[0] - ox, ideal[2] - oz) * 8.0}
    if name == "Asymmetric Jump Designer":
        return {"operation": name, "overworld": (x, y, z), "ideal_nether": ideal, "alternate_nether": other, "horizontal_error_overworld": math.hypot(ideal[0] - ox, ideal[2] - oz) * 8.0, "vertical_offset": oy - y, "note": "Geometry planner only; portal search/link competition must be verified."}
    if name == "Repeating Network Generator":
        count = max(2, int(p.get("count", 8)))
        step = float(p.get("spacing", 128.0))
        gates = [{"index": i, "overworld": (x + i * step, z), "nether": (round((x + i * step) / 8.0), round(z / 8.0))} for i in range(count)]
        return {"operation": name, "spacing_overworld": step, "gates": gates}
    if name == "Portal-State Simulator":
        error = math.hypot(ideal[0] - ox, ideal[2] - oz)
        return {"operation": name, "ideal_nether": ideal, "candidate_nether": other, "horizontal_error_nether": error, "horizontal_error_overworld": error * 8.0, "within_16_nether_blocks": error <= 16.0, "note": "Distance state only; exact vanilla portal search also depends on dimension, Y, loaded portals, and search rules."}
    if name == "Routing Table Generator":
        destinations = [(x, z), (ox * 8.0, oz * 8.0)]
        return {"operation": name, "routes": [{"overworld": q, "nether": (q[0] / 8.0, q[1] / 8.0), "scale": "8:1"} for q in destinations]}
    if name == "Corridor Transport":
        nether_blocks = math.hypot(ideal[0] - ox, ideal[2] - oz)
        speed = max(0.01, float(p.get("speed", 8.0)))
        return {"operation": name, "nether_blocks": nether_blocks, "speed_blocks_per_second": speed, "travel_seconds": nether_blocks / speed}
    if name == "Standard Route Comparison":
        ow = math.hypot(x - ox * 8.0, z - oz * 8.0)
        nether = math.hypot(ideal[0] - ox, ideal[2] - oz)
        return {"operation": name, "overworld_walk_blocks": ow, "nether_walk_blocks": nether, "compressed_overworld_equivalent": nether * 8.0, "nether_route_ratio": nether / max(1e-9, ow)}
    r = max(1.0, float(p.get("radius", 16.0)))
    return {"operation": name, "center_nether": ideal, "radius_nether_blocks": r, "overworld_equivalent_radius": r * 8.0, "bounds": (ideal[0] - r, ideal[2] - r, ideal[0] + r, ideal[2] + r)}


def _local_area(name: str, p: dict[str, Any], executor=None) -> dict[str, Any] | None:
    names = {"32-Chunk Analysis", "Biome Composition", "Structure Counts", "Slime Distribution", "Notable Locations", "Technical Score", "Build Score", "Exploration Score"}
    if name not in names:
        return None
    from .seed.slime import nearby as slime_nearby
    from .restored_features import structure_candidates
    from .world.versioning import resolve_cubiomes_mc

    seed = int(str(p.get("seed", 0)).strip()); cx = int(p.get("cx", 0)); cz = int(p.get("cz", 0))
    radius = 16 if name == "32-Chunk Analysis" else max(1, int(p.get("radius", 32)))
    slime = slime_nearby(seed, cx, cz, min(radius, 128))
    selected = str(getattr(executor, "minecraft_version", "26.3-snapshot-7"))
    try: mc = resolve_cubiomes_mc(selected)
    except ValueError: mc = None
    structures = {}
    if mc is not None:
        for target in ("Village", "Trial Chamber", "Ocean Monument", "Pillager Outpost"):
            structures[target] = structure_candidates(target, seed, cx, cz, radius, mc=mc)["candidate_chunks"]
    biome_data = _biome_tool("Biome Diversity Finder", {**p, "x": cx * 16 + 8, "z": cz * 16 + 8, "radius": radius * 16}, executor)
    if name == "Slime Distribution":
        return {"operation": name, "center_chunk": (cx, cz), "radius_chunks": radius, "slime_chunks": slime, "count": len(slime), "density": len(slime) / max(1, (2 * radius + 1) ** 2)}
    if name == "Structure Counts":
        return {"operation": name, "candidate_counts": {k: len(v) for k, v in structures.items()}, "note": "Counts are deterministic placement candidates; terrain/biome viability may remove candidates."}
    if name == "Biome Composition":
        return {"operation": name, "biome_analysis": biome_data}
    nearest = []
    for target, points in structures.items():
        if points:
            q = min(points, key=lambda pos: (pos[0] - cx) ** 2 + (pos[1] - cz) ** 2)
            nearest.append({"type": target, "chunk": q, "distance_chunks": math.hypot(q[0] - cx, q[1] - cz)})
    nearest.sort(key=lambda q: q["distance_chunks"])
    diversity = 0
    if isinstance(biome_data, dict) and biome_data.get("ranked"):
        diversity = int(biome_data["ranked"][0].get("distinct", 0))
    struct_types = sum(bool(v) for v in structures.values())
    slime_density = len(slime) / max(1, (2 * radius + 1) ** 2)
    technical = min(100.0, struct_types * 12.5 + slime_density * 250.0 + diversity * 4.0)
    build = min(100.0, 50.0 + diversity * 3.0 - min(25.0, len(nearest) * 1.5))
    exploration = min(100.0, struct_types * 15.0 + diversity * 7.5)
    if name == "Notable Locations":
        return {"operation": name, "nearest_structure_candidates": nearest, "nearest_slime_chunks": sorted(slime, key=lambda q: (q[0] - cx) ** 2 + (q[1] - cz) ** 2)[:32], "note": "Structure entries are candidate positions until viability is confirmed."}
    if name == "Technical Score":
        return {"operation": name, "score": round(technical, 2), "components": {"structure_types": struct_types, "slime_density": slime_density, "sampled_biome_diversity": diversity}, "note": "Transparent F3+ heuristic, not a Minecraft mechanic."}
    if name == "Build Score":
        return {"operation": name, "score": round(build, 2), "components": {"sampled_biome_diversity": diversity, "nearby_structure_candidate_types": len(nearest)}, "note": "Transparent planning heuristic; terrain flatness requires a generated-world scan."}
    if name == "Exploration Score":
        return {"operation": name, "score": round(exploration, 2), "components": {"structure_types": struct_types, "sampled_biome_diversity": diversity}, "note": "Transparent F3+ heuristic."}
    return {"operation": name, "radius_chunks": radius, "slime_count": len(slime), "structure_candidate_counts": {k: len(v) for k, v in structures.items()}, "biome_analysis": biome_data}


def _world_analysis(name: str, p: dict[str, Any], executor=None) -> dict[str, Any] | None:
    from .qa_features import world_seed_tool
    existing = world_seed_tool(name, "World Analysis", p, executor)
    if existing is not None:
        return existing
    names = {"Spawn Analysis", "Seed Comparison", "Ancient City Area Analysis", "Chunk Loading Simulator", "Spawn Chunk Optimizer", "Search Radius Optimizer"}
    if name not in names:
        return None
    seed = int(str(p.get("seed", 0)).strip()); cx = int(p.get("cx", 0)); cz = int(p.get("cz", 0)); radius = max(1, int(p.get("radius", 64)))
    if name == "Chunk Loading Simulator":
        sim = max(2, int(p.get("simulation_distance", min(32, radius))))
        square = (2 * sim + 1) ** 2
        return {"operation": name, "simulation_distance_chunks": sim, "square_chunk_count": square, "square_block_side": (2 * sim + 1) * 16, "note": "Geometric loaded/simulation-distance footprint only; ticket levels and server plugins can change actual loading."}
    if name == "Search Radius Optimizer":
        targets = max(1, int(p.get("target_candidates", 8)))
        estimates = []
        for r in (8, 16, 24, 32, 48, 64, 96, 128):
            chunks = (2 * r + 1) ** 2
            estimates.append({"radius_chunks": r, "chunks": chunks, "relative_scan_cost": chunks / ((2 * 8 + 1) ** 2), "meets_requested_radius": r >= radius})
        return {"operation": name, "requested_radius": radius, "target_candidates": targets, "options": estimates, "note": "Cost model is geometric; actual Cubiomes/world-save scan time depends on backend and disk."}
    from .restored_features import structure_candidates
    from .seed.slime import nearby as slime_nearby
    from .world.versioning import resolve_cubiomes_mc
    selected = str(getattr(executor, "minecraft_version", "26.3-snapshot-7"))
    try: mc = resolve_cubiomes_mc(selected)
    except ValueError as exc:
        return {"operation": name, "available": False, "reason": str(exc), "selected_version": selected}
    if name == "Ancient City Area Analysis":
        pts = structure_candidates("Ancient City", seed, cx, cz, radius, mc=mc)["candidate_chunks"]
        return {"operation": name, "candidate_chunks": pts, "count": len(pts), "nearest": pts[0] if pts else None, "note": "Placement candidates only; Ancient City generation also depends on biome/terrain."}
    if name == "Spawn Analysis":
        structures = {target: structure_candidates(target, seed, 0, 0, radius, mc=mc)["candidate_chunks"][:16] for target in ("Village", "Ruined Portal", "Pillager Outpost", "Trial Chamber")}
        biomes = _biome_tool("Biome Diversity Finder", {**p, "x": 0, "z": 0, "radius": radius * 16}, executor)
        slime = slime_nearby(seed, 0, 0, min(radius, 64))
        return {"operation": name, "spawn_reference": (0, 0), "structure_candidates": structures, "slime_chunks": slime[:128], "biome_analysis": biomes, "note": "This analyzes the coordinate origin. Exact player spawn selection may be offset by Minecraft spawn-search rules."}
    if name == "Spawn Chunk Optimizer":
        candidates = []
        slime = set(slime_nearby(seed, cx, cz, min(radius, 64)))
        for dz in range(-8, 9, 4):
            for dx in range(-8, 9, 4):
                qx, qz = cx + dx, cz + dz
                slime_near = sum((qx + ox, qz + oz) in slime for ox in range(-4, 5) for oz in range(-4, 5))
                dist = math.hypot(dx, dz)
                score = slime_near * 2.0 - dist * 0.1
                candidates.append((score, (qx, qz), slime_near, dist))
        candidates.sort(reverse=True)
        return {"operation": name, "ranked": [{"score": q[0], "chunk": q[1], "nearby_slime_chunks": q[2], "distance_from_reference": q[3]} for q in candidates], "formula": "2*nearby_slime_chunks - 0.1*distance", "note": "Transparent technical-site heuristic; it does not alter Minecraft's actual spawn chunks."}
    second = int(str(p.get("second_seed", seed + 1)).strip())
    summaries = []
    for value in (seed, second):
        struct = {target: len(structure_candidates(target, value, cx, cz, radius, mc=mc)["candidate_chunks"]) for target in ("Village", "Trial Chamber", "Ocean Monument", "Pillager Outpost")}
        slime = len(slime_nearby(value, cx, cz, min(radius, 64)))
        summaries.append({"seed": value, "structure_candidate_counts": struct, "slime_chunks": slime})
    return {"operation": name, "radius_chunks": radius, "seeds": summaries, "note": "Compares deterministic placement/slime metrics only; terrain/resource comparison requires generated saves or supported biome generation."}


def seed_tool(spec, p: dict[str, Any], executor=None) -> dict[str, Any] | None:
    if spec.submenu == "Biomes":
        return _biome_tool(spec.name, p, executor)
    if spec.submenu == "Structures":
        return _structure_meta(spec.name, p, executor)
    if spec.submenu == "Nether":
        return _nether_planner(spec.name, p)
    if spec.submenu == "Local Area":
        return _local_area(spec.name, p, executor)
    if spec.submenu == "World Analysis":
        return _world_analysis(spec.name, p, executor)
    return None


def calculator_tool(spec, p: dict[str, Any]) -> dict[str, Any] | None:
    n = spec.name
    if n == "Material Weight":
        items = max(0, int(p.get("items", p.get("value", 0))))
        stack = max(1, int(p.get("stack_size", 64)))
        return {"operation": n, "items": items, "stacks": math.ceil(items / stack), "shulker_boxes": math.ceil(items / (stack * 27)), "double_chests": math.ceil(items / (stack * 54)), "note": "Minecraft has no item-mass mechanic. This tool therefore reports inventory/logistics burden rather than inventing physical weight."}
    if n == "Slime Farm Optimizer":
        units = max(1, int(p.get("units", 1))); spacing = max(1, int(p.get("spacing", 4)))
        return {"operation": n, "planned_slime_chunks": units, "platform_spacing": spacing, "spawnproof_radius_blocks": 128, "recommended_player_distance_from_platform": {"minimum": 24, "despawn_outer": 128}, "note": "Layout planner only; supply actual slime chunks/terrain for site-specific optimization."}
    if n == "Fortress Farm Planner":
        units = max(1, int(p.get("units", 1))); spacing = max(1, int(p.get("spacing", 4)))
        return {"operation": n, "planned_spawn_platforms": units, "vertical_spacing": spacing, "spawnproof_radius_blocks": 128, "requirements": ["generated Nether fortress bounding pieces", "biome/spawn-rule verification"], "note": "Does not fabricate fortress bounding boxes from a radius input."}
    if n == "Trial Chamber Planner":
        units = max(1, int(p.get("units", 1))); spacing = max(1, int(p.get("spacing", 4)))
        return {"operation": n, "players_or_stations": units, "station_spacing": spacing, "checklist": ["record trial spawner/vault positions", "separate normal and ominous workflow", "plan safe reset/loot route"], "note": "Planning checklist; generated chamber geometry must come from the world save or in-game survey."}
    if n == "Blaze Route Planner":
        x1, z1 = float(p.get("x1", 0)), float(p.get("z1", 0)); x2, z2 = float(p.get("x2", 100)), float(p.get("z2", 0))
        d = math.hypot(x2 - x1, z2 - z1)
        return {"operation": n, "start": (x1, z1), "target": (x2, z2), "distance_blocks": d, "bearing_degrees": (math.degrees(math.atan2(-(x2 - x1), z2 - z1)) + 360) % 360, "note": "Route geometry between supplied points; fortress/blaze-spawner discovery is not inferred from eye-throw angles."}
    return None


def rng_tool(spec, p: dict[str, Any]) -> dict[str, Any] | None:
    from .rng_tools import at_least_one
    from .calculators import technical
    n = spec.name
    probability = max(0.0, min(1.0, float(p.get("probability", 0.05))))
    attempts = max(1, int(p.get("attempts", 20)))
    if n == "Enchantment Table Layout":
        # Valid bookshelf ring cells with the one-block air gap around a table at 0,0.
        cells = [(x, z) for x in range(-2, 3) for z in range(-2, 3) if max(abs(x), abs(z)) == 2 and not (abs(x) == 2 and abs(z) == 2)]
        return {"operation": n, "table": (0, 0), "valid_bookshelf_ring": cells, "bookshelves_for_level_30": cells[:15], "required_count": 15, "note": "Layout coordinates assume unobstructed air between table and shelves; Minecraft version mechanics still govern enchanting offers."}
    if n == "XP Level Planner":
        target = max(0, attempts)
        return {"operation": n, "target_level": target, "xp_from_zero": technical.total_xp_for_level(target) if hasattr(technical, "total_xp_for_level") else _xp_for_level(target), "note": "Uses vanilla Java level-XP curve; this is not RNG."}
    if n == "Best Enchantment Search":
        targets = (0.5, 0.75, 0.9, 0.95, 0.99)
        rows = []
        for target in targets:
            if probability <= 0:
                needed = None
            elif probability >= 1:
                needed = 1
            else:
                needed = math.ceil(math.log(1 - target) / math.log(1 - probability))
            rows.append({"confidence": target, "attempts_needed": needed})
        return {"operation": n, "target_offer_probability": probability, "attempt_thresholds": rows, "note": "Probability planning only. F3+ does not claim these are exact enchantment-table offers without mechanic/version-specific observations."}
    if n == "Enchanting Simulator":
        return {"operation": n, **at_least_one(probability, attempts), "model": "independent target-offer probability", "note": "A probability-model simulator, not exact enchantment selection. Use the dedicated RNG recovery workflow for supported observed player-RNG states."}
    if n == "Enchantment Odds":
        return {"operation": n, **at_least_one(probability, attempts), "model": "independent attempts"}
    return None


def _xp_for_level(level: int) -> int:
    level = max(0, int(level))
    if level <= 16:
        return level * level + 6 * level
    if level <= 31:
        return int(2.5 * level * level - 40.5 * level + 360)
    return int(4.5 * level * level - 162.5 * level + 2220)


def install() -> None:
    """Make all 457 catalog rows resolve through an explicit implementation contract."""
    from . import restored_features
    from .feature_executor import FeatureExecutor
    from .qa_features import villager_tool

    if getattr(FeatureExecutor, "_full_catalog_integrity_installed", False):
        return

    old_result = FeatureExecutor._result
    old_villager = FeatureExecutor._villager
    old_fields = FeatureExecutor.input_fields
    old_execute = restored_features.execute

    def result(self, spec, status, data, note=""):
        enriched = annotate(spec, data)
        return old_result(self, spec, status, enriched, note)

    def villager(self, spec, p):
        if spec.name in {"Trade Search", "Trade Comparison", "Emerald Calculator", "Trade Cycle Calculator", "Librarian Browser"}:
            value = villager_tool(spec.name, self.minecraft_version, p)
            return self._result(spec, "ok" if value and value.get("available", True) else "unavailable", value or {"available": False})
        return old_villager(self, spec, p)

    def fields(self, feature):
        spec = self.spec(feature)
        if spec.top == "Seed Tools" and spec.submenu == "Biomes":
            return [
                ("seed", "World seed", 123456789, "text"), ("x", "Center X", 0, "int"), ("y", "Sample Y", 64, "int"),
                ("z", "Center Z", 0, "int"), ("radius", "Radius (blocks)", 256, "int"), ("step", "Sample step (blocks)", 16, "int"),
                ("target_biome", "Target biome numeric ID", 1, "int"), ("world_path", "Generated world path (terrain-shape tools)", "", "text"),
            ]
        if spec.top == "Seed Tools" and spec.submenu == "World Analysis":
            return [
                ("seed", "World seed", 123456789, "text"), ("second_seed", "Comparison seed", 987654321, "text"),
                ("cx", "Center chunk X", 0, "int"), ("cz", "Center chunk Z", 0, "int"), ("radius", "Radius (chunks)", 64, "int"),
                ("world_path", "Generated world path", "", "text"), ("simulation_distance", "Simulation distance", 10, "int"),
            ]
        return old_fields(self, feature)

    def execute(spec, p, executor=None):
        if spec.top == "Calculators":
            value = calculator_tool(spec, p)
            if value is not None:
                return value
        if spec.top == "Seed Tools":
            value = seed_tool(spec, p, executor)
            if value is not None:
                return value
        if spec.top == "RNG Tools":
            value = rng_tool(spec, p)
            if value is not None:
                return value
        value = old_execute(spec, p, executor)
        reason = generic_placeholder_reason(spec, annotate(spec, value))
        if reason:
            raise RuntimeError(f"{spec.id} still resolves to a non-honest generic fallback ({reason})")
        return value

    FeatureExecutor._result = result
    FeatureExecutor._villager = villager
    FeatureExecutor.input_fields = fields
    FeatureExecutor._full_catalog_integrity_installed = True
    restored_features.execute = execute
