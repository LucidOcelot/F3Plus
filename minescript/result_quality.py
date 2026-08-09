from __future__ import annotations

"""Human-readable corrections for remaining opaque heuristic/value reports."""

import math
from typing import Any


def _direction(dx: float, dz: float) -> str:
    if dx == 0 and dz == 0:
        return "at the reference chunk"
    angle = (math.degrees(math.atan2(dx, -dz)) + 360.0) % 360.0
    names = ("north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest")
    return names[int((angle + 22.5) // 45.0) % 8]


def _farm_location_report(p: dict[str, Any]) -> dict[str, Any]:
    from .seed.slime import clusters, nearby

    seed = int(str(p.get("seed", 0)).strip())
    cx, cz = int(p.get("cx", 0)), int(p.get("cz", 0))
    radius = max(1, min(256, int(p.get("radius", 32))))
    points = list(nearby(seed, cx, cz, radius))
    point_set = set(points)
    components = clusters(point_set)
    component_size = {point: len(group) for group in components for point in group}
    rows = []
    for x, z in points:
        local = sum((x + dx, z + dz) in point_set for dx in (-1, 0, 1) for dz in (-1, 0, 1))
        distance = math.hypot(x - cx, z - cz)
        rows.append({
            "chunk": [x, z],
            "block_center": [x * 16 + 8, z * 16 + 8],
            "slime_chunks_in_centered_3x3": local,
            "cardinal_cluster_size": component_size.get((x, z), 1),
            "distance_from_reference_chunks": round(distance, 2),
            "approx_distance_from_reference_blocks": round(distance * 16),
            "direction": _direction(x - cx, z - cz),
        })
    rows.sort(key=lambda row: (
        -int(row["slime_chunks_in_centered_3x3"]),
        -int(row["cardinal_cluster_size"]),
        float(row["distance_from_reference_chunks"]),
    ))
    return {
        "purpose": "Rank slime-farm candidate chunks by nearby slime concentration without an unexplained score.",
        "reference_chunk": [cx, cz], "radius_chunks": radius,
        "slime_chunks_found": len(points),
        "ranked_sites": rows[:100],
        "ranking_order": [
            "more slime chunks in the centered 3×3 chunk neighborhood",
            "larger cardinally connected slime cluster",
            "shorter distance from the reference chunk",
        ],
        "note": "This ranks slime-chunk geometry only. Actual farm throughput also depends on terrain excavation, spawning spaces, player position, mob cap, collection, and version/server rules.",
    }


def _spawn_site_report(p: dict[str, Any]) -> dict[str, Any]:
    from .seed.slime import nearby

    seed = int(str(p.get("seed", 0)).strip())
    cx, cz = int(p.get("cx", 0)), int(p.get("cz", 0))
    radius = max(8, min(128, int(p.get("radius", 64))))
    slime = set(nearby(seed, cx, cz, min(radius, 64)))
    rows = []
    for dz in range(-8, 9, 4):
        for dx in range(-8, 9, 4):
            qx, qz = cx + dx, cz + dz
            slime_near = sum((qx + ox, qz + oz) in slime for ox in range(-4, 5) for oz in range(-4, 5))
            distance = math.hypot(dx, dz)
            rows.append({
                "candidate_chunk": [qx, qz],
                "candidate_block_center": [qx * 16 + 8, qz * 16 + 8],
                "slime_chunks_within_4_chunks": slime_near,
                "distance_from_reference_chunks": round(distance, 2),
                "approx_distance_from_reference_blocks": round(distance * 16),
                "direction": _direction(dx, dz),
            })
    rows.sort(key=lambda row: (-int(row["slime_chunks_within_4_chunks"]), float(row["distance_from_reference_chunks"])))
    return {
        "purpose": "Rank nearby seed-level technical sites around a spawn/reference area without inventing a composite score.",
        "reference_chunk": [cx, cz],
        "ranked_sites": rows,
        "ranking_order": ["more slime chunks within four chunks", "shorter distance from the reference"],
        "does_not_change_spawn_chunks": True,
        "note": "Minecraft chooses spawn independently. This report ranks nearby technical-site geometry only; generated terrain and actual player spawn still need verification.",
    }


def _chunk_loading_report(p: dict[str, Any]) -> dict[str, Any]:
    cx, cz = int(p.get("cx", 0)), int(p.get("cz", 0))
    sim = max(2, min(64, int(p.get("simulation_distance", 10))))
    side = 2 * sim + 1
    min_cx, max_cx = cx - sim, cx + sim
    min_cz, max_cz = cz - sim, cz + sim
    edge = []
    for x in range(min_cx, max_cx + 1):
        edge.append([x, min_cz]); edge.append([x, max_cz])
    for z in range(min_cz + 1, max_cz):
        edge.append([min_cx, z]); edge.append([max_cx, z])
    return {
        "purpose": "Visualize the geometric simulation-distance footprint around a chosen center chunk.",
        "center_chunk": [cx, cz], "simulation_distance_chunks": sim,
        "side_chunks": side, "chunks_in_square": side * side,
        "chunk_bounds": {"x": [min_cx, max_cx], "z": [min_cz, max_cz]},
        "block_bounds": {
            "x": [min_cx * 16, (max_cx + 1) * 16 - 1],
            "z": [min_cz * 16, (max_cz + 1) * 16 - 1],
        },
        "outer_ring_chunks": edge,
        "outer_ring_chunk_count": len(edge),
        "note": "This is a geometric simulation-distance footprint. Ticket levels, spawn chunks, portals, mods/plugins, and server rules can load/tick chunks differently.",
    }


def _search_radius_report(p: dict[str, Any]) -> dict[str, Any]:
    requested = max(1, int(p.get("radius", 64)))
    options = []
    base_chunks = (2 * 8 + 1) ** 2
    radii = (8, 16, 24, 32, 48, 64, 96, 128, 192, 256)
    for radius in radii:
        side = 2 * radius + 1
        chunks = side * side
        options.append({
            "radius_chunks": radius, "side_chunks": side, "chunks_in_square": chunks,
            "relative_chunk_work_vs_radius_8": round(chunks / base_chunks, 2),
            "covers_requested_radius": radius >= requested,
        })
    recommendation = next((row for row in options if row["covers_requested_radius"]), options[-1])
    return {
        "purpose": "Compare geometric scan size/cost before running a large seed or generated-world search.",
        "requested_radius_chunks": requested,
        "smallest_listed_radius_covering_request": recommendation,
        "options": options,
        "interpretation": "Doubling radius increases square-area work by roughly four times. F3+ does not claim it can predict how many target structures a radius will contain without a target-specific density model.",
    }


def _circle_export(p: dict[str, Any]) -> dict[str, Any]:
    from .calculators.core import circle

    radius = max(1, int(p.get("radius", 8)))
    fmt = str(p.get("export_format", "CSV"))
    points = list(circle(radius, False))
    if fmt == "Semicolon list":
        text = ";".join(f"{x},{z}" for x, z in points)
    elif fmt == "Minecraft relative":
        text = "\n".join(f"~{x} ~ ~{z}" for x, z in points)
    else:
        text = "x,z\n" + "\n".join(f"{x},{z}" for x, z in points)
    return {
        "purpose": "Produce copy/export-ready coordinates for one circle layer rather than another circle preview.",
        "radius_blocks": radius, "point_count": len(points),
        "format": fmt, "coordinates": [list(point) for point in points],
        "export_text": text,
    }


def _transform_terrain(name: str, data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    if name == "Terrain Base Finder" and isinstance(out.get("ranked"), list):
        rows = []
        for index, row in enumerate(out["ranked"]):
            if not isinstance(row, dict):
                continue
            relief = row.get("relief")
            mean_y = row.get("mean_y")
            rows.append({
                "rank": index + 1,
                "chunk": row.get("chunk"),
                "mean_surface_y": mean_y,
                "within_chunk_relief_blocks": relief,
                "reading": (
                    f"Mean surface Y {float(mean_y):.1f} with {float(relief):.1f} blocks of local relief"
                    if mean_y is not None and relief is not None else "Incomplete surface data"
                ),
            })
        out.pop("formula", None)
        out["ranked"] = rows
        out["purpose"] = "Rank elevated, relatively flat generated chunks as possible base sites."
        out["ranking_basis"] = "Higher mean surface elevation is preferred, while within-chunk relief is penalized. The old opaque numeric base score is not shown as a meaningful game statistic."
    elif name == "Lake Density" and "density" in out:
        density = float(out.get("density", 0.0))
        out["enclosed_water_share_percent"] = round(density * 100.0, 2)
        out["interpretation"] = f"About {density * 100.0:.2f}% of scanned generated chunks belong to enclosed sampled water components under this tool's lake definition."
    elif name == "Largest Cave Region" and "cave_air_threshold" in out:
        out["threshold_explanation"] = "A chunk joins the cave-region map when its counted below-Y64 cave/air blocks meet or exceed this threshold; adjacent qualifying chunks are then connected cardinally."
    return out


def _transform_structure(name: str, data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    if name == "Structure Heatmap" and isinstance(out.get("cells"), list):
        cell_size = max(1, int(out.get("cell_size_chunks", 1)))
        cells = []
        for row in out["cells"]:
            if not isinstance(row, dict) or not isinstance(row.get("cell"), (list, tuple)):
                continue
            gx, gz = map(int, row["cell"][:2])
            cells.append({
                "grid_cell": [gx, gz],
                "chunk_bounds": {"x": [gx * cell_size, gx * cell_size + cell_size - 1], "z": [gz * cell_size, gz * cell_size + cell_size - 1]},
                "placement_candidates": int(row.get("candidates", 0)),
            })
        out["cells"] = cells
        out["interpretation"] = "Each row is a chunk-grid cell, not a biome/terrain heat value. Counts are structure placement candidates inside that cell."
    elif name == "Isolated Structure Finder" and isinstance(out.get("ranked"), list):
        rows = []
        for index, row in enumerate(out["ranked"]):
            if not isinstance(row, dict): continue
            candidate = row.get("candidate")
            if not isinstance(candidate, (list, tuple)) or len(candidate) < 3: continue
            kind, x, z = candidate[0], int(candidate[1]), int(candidate[2])
            distance = float(row.get("nearest_other_chunks", 0.0))
            rows.append({
                "rank": index + 1, "structure": kind, "candidate_chunk": [x, z],
                "candidate_block_center": [x * 16 + 8, z * 16 + 8],
                "nearest_other_candidate_distance_chunks": round(distance, 2),
                "approx_nearest_other_distance_blocks": round(distance * 16),
            })
        out["ranked"] = rows
        out["purpose"] = "Find placement candidates that are farthest from any other tracked placement candidate."
    elif name == "Structure Chains" and isinstance(out.get("chain"), list):
        stops = []
        for index, candidate in enumerate(out["chain"]):
            if isinstance(candidate, (list, tuple)) and len(candidate) >= 3:
                kind, x, z = candidate[0], int(candidate[1]), int(candidate[2])
                stops.append({"stop": index + 1, "structure": kind, "chunk": [x, z], "block_center": [x * 16 + 8, z * 16 + 8]})
        out["chain"] = stops
        out["approx_route_blocks"] = round(float(out.get("route_chunks", 0.0)) * 16.0)
        out["purpose"] = "Greedy nearest-next route through tracked structure placement candidates."
    elif name == "Structure Corridor" and isinstance(out.get("candidates"), list):
        rows = []
        for candidate in out["candidates"]:
            if isinstance(candidate, (list, tuple)) and len(candidate) >= 3:
                kind, x, z = candidate[0], int(candidate[1]), int(candidate[2])
                rows.append({"structure": kind, "chunk": [x, z], "block_center": [x * 16 + 8, z * 16 + 8]})
        out["candidates"] = rows
        out["purpose"] = "Find placement candidates inside the configured horizontal/vertical chunk corridor through the reference point."
    elif name == "Structure Cluster Finder" and isinstance(out.get("clusters"), list):
        unique = []
        seen = set()
        for group in out["clusters"]:
            if not isinstance(group, list): continue
            members = []
            for candidate in group:
                if isinstance(candidate, (list, tuple)) and len(candidate) >= 3:
                    members.append((str(candidate[0]), int(candidate[1]), int(candidate[2])))
            key = tuple(sorted(members))
            if not members or key in seen: continue
            seen.add(key)
            unique.append({
                "candidate_count": len(members),
                "structure_types": sorted({row[0] for row in members}),
                "members": [{"structure": kind, "chunk": [x, z], "block_center": [x * 16 + 8, z * 16 + 8]} for kind, x, z in members],
            })
        out["clusters"] = unique
        out["cluster_count"] = len(unique)
        out["purpose"] = "Find local groups of placement candidates, de-duplicated by exact member set."
    return out


def _portal_heatmap(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    rows = []
    for row in out.get("samples", []) if isinstance(out.get("samples"), list) else []:
        if not isinstance(row, dict): continue
        value = float(row.get("reliability", 0.0))
        rows.append({
            "nether": row.get("nether"),
            "distance_from_ideal_nether_blocks": round(float(row.get("error_nether", 0.0)), 3),
            "overworld_equivalent_error_blocks": round(float(row.get("error_overworld", 0.0)), 3),
            "normalized_proximity_to_ideal": round(value, 5),
            "proximity_band": "near" if value >= 0.67 else "middle" if value >= 0.34 else "far",
        })
    out["samples"] = rows
    out["purpose"] = "Visualize geometric proximity to an ideal sister coordinate across candidate Nether blocks."
    out["metric_warning"] = "Normalized proximity is a planning visualization, not a probability that Minecraft will link a portal. Exact linking also depends on vanilla search rules, Y, active competing portals, and dimension state."
    return out


def _seed_comparison(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    seeds = out.get("seeds")
    if not isinstance(seeds, list) or len(seeds) != 2:
        return out
    a, b = seeds
    if not isinstance(a, dict) or not isinstance(b, dict):
        return out
    ac = a.get("structure_candidate_counts") or {}; bc = b.get("structure_candidate_counts") or {}
    keys = sorted(set(ac) | set(bc))
    out["differences"] = {
        "slime_chunks": int(b.get("slime_chunks", 0)) - int(a.get("slime_chunks", 0)),
        "structure_candidate_count_delta_second_minus_first": {key: int(bc.get(key, 0)) - int(ac.get(key, 0)) for key in keys},
    }
    out["interpretation"] = "Positive deltas mean the second seed has more candidates/slime chunks in the same sampled radius; negative values favor the first. Terrain/resources are not inferred here."
    return out


def _fields(spec):
    if spec.top == "Calculators" and spec.submenu == "Build" and spec.name == "Circle Layer Export":
        return [("radius", "Circle radius (blocks)", 8, "int"), ("export_format", "Export text format", ["CSV", "Semicolon list", "Minecraft relative"], "choice")]
    if spec.top == "Seed Tools" and spec.submenu == "World Analysis" and spec.name == "Chunk Loading Simulator":
        return [("cx", "Center chunk X", 0, "int"), ("cz", "Center chunk Z", 0, "int"), ("simulation_distance", "Simulation distance (chunks)", 10, "int")]
    if spec.top == "Seed Tools" and spec.submenu == "World Analysis" and spec.name in {"Spawn Chunk Optimizer", "Search Radius Optimizer"}:
        return [("seed", "World seed", 123456789, "text"), ("cx", "Reference chunk X", 0, "int"), ("cz", "Reference chunk Z", 0, "int"), ("radius", "Search radius (chunks)", 64, "int")]
    return None


def install() -> None:
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_semantic_quality_v2_installed", False):
        return
    previous_execute = FeatureExecutor.execute
    previous_fields = FeatureExecutor.input_fields

    def input_fields(self, feature):
        spec = self.spec(feature)
        fields = _fields(spec)
        return fields if fields is not None else previous_fields(self, feature)

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        values = self.defaults(spec)
        values.update(params or {})

        if spec.top == "Seed Tools" and spec.submenu == "Slime" and spec.name == "Farm Location Ranking":
            return self._result(spec, "ok", _farm_location_report(values))
        if spec.top == "Seed Tools" and spec.submenu == "World Analysis":
            if spec.name == "Spawn Chunk Optimizer": return self._result(spec, "ok", _spawn_site_report(values))
            if spec.name == "Chunk Loading Simulator": return self._result(spec, "ok", _chunk_loading_report(values))
            if spec.name == "Search Radius Optimizer": return self._result(spec, "ok", _search_radius_report(values))
        if spec.top == "Calculators" and spec.submenu == "Build" and spec.name == "Circle Layer Export":
            return self._result(spec, "ok", _circle_export(values))

        result = previous_execute(self, spec, values, dry_run)
        data = getattr(result, "data", None)
        if not isinstance(data, dict): return result

        if spec.top == "Seed Tools" and spec.submenu == "Biomes" and spec.name in {"Terrain Base Finder", "Lake Density", "Largest Cave Region"}:
            result.data = _transform_terrain(spec.name, data)
        elif spec.top == "Seed Tools" and spec.submenu == "Structures" and spec.name in {"Structure Heatmap", "Isolated Structure Finder", "Structure Chains", "Structure Corridor", "Structure Cluster Finder"}:
            result.data = _transform_structure(spec.name, data)
        elif spec.top == "Seed Tools" and spec.submenu == "Nether" and spec.name == "Portal Reliability Heatmap":
            result.data = _portal_heatmap(data)
        elif spec.top == "Seed Tools" and spec.submenu == "World Analysis" and spec.name == "Seed Comparison":
            result.data = _seed_comparison(data)
        return result

    FeatureExecutor.input_fields = input_fields
    FeatureExecutor.execute = execute
    FeatureExecutor._semantic_quality_v2_installed = True
