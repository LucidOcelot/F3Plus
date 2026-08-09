from __future__ import annotations

"""User-facing analysis reports for F3+ 2.0.

The legacy catalog intentionally keeps stable tool IDs, but several historical
"score" and aggregate-analysis entries exposed backend values too directly or reused
nearly identical summaries.  This layer gives those entries distinct jobs, translates
Minecraft/Cubiomes identifiers into readable labels, and keeps raw IDs only where they
are useful for technical verification.
"""

import math
from collections import Counter, deque
from typing import Any


# Cubiomes BiomeID values. Modern display names are preferred where an old numeric ID
# is retained by Mojang/Cubiomes for compatibility.
BIOME_NAMES: dict[int, str] = {
    0: "Ocean", 1: "Plains", 2: "Desert", 3: "Windswept Hills", 4: "Forest",
    5: "Taiga", 6: "Swamp", 7: "River", 8: "Nether Wastes", 9: "The End",
    10: "Frozen Ocean", 11: "Frozen River", 12: "Snowy Plains",
    13: "Snowy Mountains (legacy)", 14: "Mushroom Fields",
    15: "Mushroom Field Shore (legacy)", 16: "Beach", 17: "Desert Hills (legacy)",
    18: "Wooded Hills (legacy)", 19: "Taiga Hills (legacy)",
    20: "Mountain Edge (legacy)", 21: "Jungle", 22: "Jungle Hills (legacy)",
    23: "Sparse Jungle", 24: "Deep Ocean", 25: "Stony Shore", 26: "Snowy Beach",
    27: "Birch Forest", 28: "Birch Forest Hills (legacy)", 29: "Dark Forest",
    30: "Snowy Taiga", 31: "Snowy Taiga Hills (legacy)",
    32: "Old Growth Pine Taiga", 33: "Giant Tree Taiga Hills (legacy)",
    34: "Windswept Forest", 35: "Savanna", 36: "Savanna Plateau", 37: "Badlands",
    38: "Wooded Badlands", 39: "Badlands Plateau (legacy)", 40: "Small End Islands",
    41: "End Midlands", 42: "End Highlands", 43: "End Barrens", 44: "Warm Ocean",
    45: "Lukewarm Ocean", 46: "Cold Ocean", 47: "Deep Warm Ocean",
    48: "Deep Lukewarm Ocean", 49: "Deep Cold Ocean", 50: "Deep Frozen Ocean",
    127: "The Void", 129: "Sunflower Plains", 130: "Desert Lakes (legacy)",
    131: "Windswept Gravelly Hills", 132: "Flower Forest", 133: "Taiga Mountains (legacy)",
    134: "Swamp Hills (legacy)", 140: "Ice Spikes", 149: "Modified Jungle (legacy)",
    151: "Modified Jungle Edge (legacy)", 155: "Old Growth Birch Forest",
    156: "Tall Birch Hills (legacy)", 157: "Dark Forest Hills (legacy)",
    158: "Snowy Taiga Mountains (legacy)", 160: "Old Growth Spruce Taiga",
    161: "Giant Spruce Taiga Hills (legacy)", 162: "Modified Gravelly Mountains (legacy)",
    163: "Windswept Savanna", 164: "Shattered Savanna Plateau (legacy)",
    165: "Eroded Badlands", 166: "Modified Wooded Badlands Plateau (legacy)",
    167: "Modified Badlands Plateau (legacy)", 168: "Bamboo Jungle",
    169: "Bamboo Jungle Hills (legacy)", 170: "Soul Sand Valley", 171: "Crimson Forest",
    172: "Warped Forest", 173: "Basalt Deltas", 174: "Dripstone Caves", 175: "Lush Caves",
    177: "Meadow", 178: "Grove", 179: "Snowy Slopes", 180: "Jagged Peaks",
    181: "Frozen Peaks", 182: "Stony Peaks", 183: "Deep Dark", 184: "Mangrove Swamp",
    185: "Cherry Grove", 186: "Pale Garden",
}


def biome_name(value: Any) -> str:
    try:
        biome_id = int(value)
    except (TypeError, ValueError):
        return str(value)
    return BIOME_NAMES.get(biome_id, f"Unknown biome (ID {biome_id})")


def biome_id(value: Any) -> int:
    if isinstance(value, int):
        return value
    text = str(value or "").strip()
    try:
        return int(text)
    except ValueError:
        pass
    normalized = text.lower().replace("minecraft:", "").replace("_", " ").replace("-", " ")
    for key, label in BIOME_NAMES.items():
        simple = label.lower().replace(" (legacy)", "")
        if normalized == simple:
            return key
    aliases = {
        "mountains": 3, "snowy tundra": 12, "mushroom island": 14,
        "stone shore": 25, "jungle edge": 23, "wooded mountains": 34,
        "giant tree taiga": 32, "tall birch forest": 155,
    }
    if normalized in aliases:
        return aliases[normalized]
    raise ValueError(f"Unknown biome name or ID: {value!r}")


def _human_id(value: str) -> str:
    text = str(value or "").removeprefix("minecraft:").replace("_", " ").strip()
    return " ".join(word.capitalize() for word in text.split()) or "Unknown"


def _cardinal(dx: float, dz: float) -> str:
    if dx == 0 and dz == 0:
        return "at the center"
    angle = (math.degrees(math.atan2(dx, -dz)) + 360.0) % 360.0
    names = ("north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest")
    return names[int((angle + 22.5) // 45.0) % 8]


def _components(points: set[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    unseen = set(points)
    groups: list[list[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        queue = deque([start])
        group = [start]
        while queue:
            x, z = queue.popleft()
            for neighbor in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
                    group.append(neighbor)
        groups.append(group)
    groups.sort(key=len, reverse=True)
    return groups


def _nearest_row(kind: str, points: list[tuple[int, int]], cx: int, cz: int) -> dict[str, Any] | None:
    if not points:
        return None
    x, z = min(points, key=lambda q: (q[0] - cx) ** 2 + (q[1] - cz) ** 2)
    dx, dz = x - cx, z - cz
    distance_chunks = math.hypot(dx, dz)
    return {
        "type": kind,
        "candidate_chunk": [x, z],
        "candidate_block_center": [x * 16 + 8, z * 16 + 8],
        "distance_chunks": round(distance_chunks, 2),
        "approx_distance_blocks": round(distance_chunks * 16.0),
        "direction": _cardinal(dx, dz),
    }


def _collect_local_context(name: str, p: dict[str, Any], executor) -> dict[str, Any]:
    from .full_catalog import _cubiomes_samples
    from .restored_features import structure_candidates
    from .seed.slime import nearby as slime_nearby
    from .world.versioning import cubiomes_resolution, resolve_cubiomes_mc

    seed = int(str(p.get("seed", 0)).strip())
    cx, cz = int(p.get("cx", 0)), int(p.get("cz", 0))
    requested_radius = 16 if name == "32-Chunk Analysis" else max(1, int(p.get("radius", 32)))
    radius = min(requested_radius, 128)
    width = radius * 2 + 1
    total_chunks = width * width
    min_cx, max_cx = cx - radius, cx + radius
    min_cz, max_cz = cz - radius, cz + radius

    slime_points = list(slime_nearby(seed, cx, cz, radius))
    slime_set = set(slime_points)
    slime_groups = _components(slime_set)
    slime_count = len(slime_points)
    slime_percent = 100.0 * slime_count / max(1, total_chunks)
    nearest_slime = _nearest_row("Slime chunk", slime_points, cx, cz)

    selected = str(getattr(executor, "minecraft_version", ""))
    resolution = cubiomes_resolution(selected)
    structures: list[dict[str, Any]] = []
    structure_error = ""
    try:
        mc = resolve_cubiomes_mc(selected)
        targets = ("Village", "Trial Chamber", "Ocean Monument", "Pillager Outpost", "Ancient City", "Ruined Portal")
        for target in targets:
            result = structure_candidates(target, seed, cx, cz, radius, mc=mc)
            points = [tuple(map(int, q)) for q in result.get("candidate_chunks", [])]
            nearest = _nearest_row(target, points, cx, cz)
            row = {
                "type": target,
                "candidate_count": len(points),
                "candidates_per_1000_chunks": round(len(points) * 1000.0 / max(1, total_chunks), 3),
            }
            if nearest:
                row.update({key: value for key, value in nearest.items() if key != "type"})
            structures.append(row)
    except Exception as exc:
        structure_error = str(exc)

    # Keep local biome reports useful at large radii without making one Python call per
    # chunk across an arbitrarily huge square. Up to ~65 samples per axis are enough
    # for a composition/variety overview and the step is reported explicitly.
    sample_stride_chunks = max(1, math.ceil(width / 65))
    sample_step = sample_stride_chunks * 16
    sample_params = dict(p)
    sample_params.update({
        "seed": seed,
        "x": cx * 16 + 8,
        "z": cz * 16 + 8,
        "radius": radius * 16,
        "step": sample_step,
    })
    biome_rows, biome_meta = _cubiomes_samples(sample_params, executor)
    biome_info: dict[str, Any]
    if biome_rows is None:
        biome_info = {
            "available": False,
            "reason": str(biome_meta.get("reason", "Biome backend unavailable")),
            "mix": [],
            "distinct_count": 0,
            "dominant": None,
        }
    else:
        counts = Counter(int(row[2]) for row in biome_rows)
        samples = max(1, sum(counts.values()))
        mix = [
            {
                "biome": biome_name(bid),
                "biome_id": bid,
                "sample_count": count,
                "estimated_share_percent": round(100.0 * count / samples, 2),
            }
            for bid, count in sorted(counts.items(), key=lambda q: (-q[1], biome_name(q[0])))
        ]
        biome_info = {
            "available": True,
            "sample_count": samples,
            "sample_step_blocks": int(biome_meta.get("step", sample_step)),
            "distinct_count": len(counts),
            "dominant": mix[0] if mix else None,
            "mix": mix,
        }

    return {
        "seed": seed,
        "center_chunk": [cx, cz],
        "center_block": [cx * 16 + 8, cz * 16 + 8],
        "requested_radius_chunks": requested_radius,
        "radius_chunks": radius,
        "area": {
            "width_chunks": width,
            "height_chunks": width,
            "total_chunks": total_chunks,
            "chunk_bounds": {"min_x": min_cx, "max_x": max_cx, "min_z": min_cz, "max_z": max_cz},
            "block_bounds": {
                "min_x": min_cx * 16, "max_x": (max_cx + 1) * 16 - 1,
                "min_z": min_cz * 16, "max_z": (max_cz + 1) * 16 - 1,
            },
        },
        "slime": {
            "count": slime_count,
            "density_percent": round(slime_percent, 2),
            "difference_from_10_percent_points": round(slime_percent - 10.0, 2),
            "largest_connected_cluster_chunks": len(slime_groups[0]) if slime_groups else 0,
            "nearest": nearest_slime,
            "chunks": [list(q) for q in slime_points[:1024]],
        },
        "structures": structures,
        "structure_error": structure_error,
        "biomes": biome_info,
        "worldgen": {
            "selected_version": selected,
            "calculation_version": resolution.get("calculation_version"),
            "exact_for_selected_version": bool(resolution.get("exact")),
            "version_note": str(resolution.get("reason", "")),
        },
        "radius_was_limited": requested_radius != radius,
    }


def _local_summary(ctx: dict[str, Any]) -> list[str]:
    biome = ctx["biomes"]
    slime = ctx["slime"]
    structures = ctx["structures"]
    out = [
        f"Scanned {ctx['area']['total_chunks']:,} chunks in a {ctx['area']['width_chunks']}×{ctx['area']['height_chunks']} square centered on chunk {tuple(ctx['center_chunk'])}."
    ]
    if biome.get("available") and biome.get("dominant"):
        dominant = biome["dominant"]
        out.append(
            f"Biome samples found {biome['distinct_count']} biome types; {dominant['biome']} was most common at about {dominant['estimated_share_percent']:.1f}% of samples."
        )
    out.append(
        f"Found {slime['count']:,} slime chunks ({slime['density_percent']:.2f}% of the square); the largest cardinally connected cluster contains {slime['largest_connected_cluster_chunks']} chunks."
    )
    present = [row for row in structures if row.get("candidate_count", 0)]
    out.append(f"{len(present)} of {len(structures)} tracked structure types have placement candidates inside the radius.")
    return out


def _render_local_report(name: str, ctx: dict[str, Any]) -> dict[str, Any]:
    area = ctx["area"]
    biome = ctx["biomes"]
    slime = ctx["slime"]
    structures = ctx["structures"]
    common = {
        "operation": name,
        "center_chunk": ctx["center_chunk"],
        "radius_chunks": ctx["radius_chunks"],
        "scan_area": area,
        "worldgen": ctx["worldgen"],
    }
    if ctx.get("radius_was_limited"):
        common["warning"] = (
            f"Requested radius {ctx['requested_radius_chunks']} chunks was limited to 128 chunks for an interactive local report."
        )

    if name == "32-Chunk Analysis":
        return {
            **common,
            "display_name": "Local 33×33 Chunk Analysis",
            "summary": _local_summary(ctx),
            "biome_overview": {
                "distinct_biomes": biome.get("distinct_count", 0),
                "dominant_biome": biome.get("dominant"),
                "top_biomes": biome.get("mix", [])[:8],
                "sampling": f"One biome sample every {biome.get('sample_step_blocks', 'unknown')} blocks" if biome.get("available") else biome.get("reason"),
            },
            "structure_overview": structures,
            "slime_overview": {key: value for key, value in slime.items() if key != "chunks"},
            "slime_chunks": slime.get("chunks", []),
            "what_this_is_for": "A compact seed-level overview of the immediate area. Open the dedicated reports below when you need detail about biomes, structures, slime chunks, building context, or exploration.",
        }

    if name == "Biome Composition":
        return {
            **common,
            "distinct_biomes_sampled": biome.get("distinct_count", 0),
            "dominant_biome": biome.get("dominant"),
            "biome_mix": biome.get("mix", []),
            "sample_count": biome.get("sample_count", 0),
            "sample_step_blocks": biome.get("sample_step_blocks"),
            "interpretation": (
                "Percentages are the share of sampled positions, not exact polygon area. Smaller sample steps improve local detail."
                if biome.get("available") else biome.get("reason", "Biome data unavailable")
            ),
        }

    if name == "Structure Counts":
        return {
            **common,
            "tracked_structure_types": len(structures),
            "types_with_candidates": sum(bool(row.get("candidate_count")) for row in structures),
            "structures": structures,
            "interpretation": "These are deterministic placement candidates. Biome, terrain, and version-specific viability can still prevent a candidate from becoming a generated structure.",
            "backend_error": ctx.get("structure_error") or None,
        }

    if name == "Slime Distribution":
        delta = float(slime.get("difference_from_10_percent_points", 0.0))
        comparison = "about average"
        if delta >= 1.0:
            comparison = f"{delta:.2f} percentage points above the usual 10% expectation"
        elif delta <= -1.0:
            comparison = f"{abs(delta):.2f} percentage points below the usual 10% expectation"
        return {
            **common,
            "slime_chunk_count": slime.get("count", 0),
            "slime_chunk_density_percent": slime.get("density_percent", 0.0),
            "density_context": comparison,
            "largest_connected_cluster_chunks": slime.get("largest_connected_cluster_chunks", 0),
            "nearest_slime_chunk": slime.get("nearest"),
            "slime_chunks": slime.get("chunks", []),
            "interpretation": "Connected clusters use cardinal chunk adjacency. The coordinate list is retained for map/visual preview use.",
        }

    nearest_structures = [row for row in structures if row.get("candidate_count") and row.get("candidate_chunk")]
    nearest_structures.sort(key=lambda row: float(row.get("distance_chunks", float("inf"))))
    if name == "Notable Locations":
        highlights = []
        for row in nearest_structures:
            highlights.append(
                f"Nearest {row['type']} candidate: chunk {tuple(row['candidate_chunk'])}, about {row['approx_distance_blocks']} blocks {row['direction']}."
            )
        if slime.get("nearest"):
            q = slime["nearest"]
            highlights.append(
                f"Nearest slime chunk: chunk {tuple(q['candidate_chunk'])}, about {q['approx_distance_blocks']} blocks {q['direction']}."
            )
        if biome.get("dominant"):
            highlights.append(
                f"Most common sampled biome: {biome['dominant']['biome']} ({biome['dominant']['estimated_share_percent']:.1f}% of samples)."
            )
        return {
            **common,
            "highlights": highlights,
            "nearest_structure_candidates": nearest_structures,
            "nearest_slime_chunk": slime.get("nearest"),
            "biome_context": {
                "distinct_biomes": biome.get("distinct_count", 0),
                "dominant_biome": biome.get("dominant"),
            },
            "interpretation": "Structure coordinates are placement candidates until generated-world viability is confirmed.",
        }

    candidate_types = sum(bool(row.get("candidate_count")) for row in structures)
    diversity = int(biome.get("distinct_count", 0))
    cluster = int(slime.get("largest_connected_cluster_chunks", 0))

    if name == "Technical Score":
        if cluster >= 4 and candidate_types >= 3:
            classification = "Strong seed-level technical access"
        elif cluster >= 2 or candidate_types >= 2:
            classification = "Mixed seed-level technical access"
        else:
            classification = "Limited seed-level technical access"
        factors = [
            {
                "factor": "Slime farm siting",
                "finding": f"Largest connected slime cluster: {cluster} chunks; local density {slime['density_percent']:.2f}%.",
            },
            {
                "factor": "Structure access",
                "finding": f"{candidate_types} tracked structure types have placement candidates in the scan radius.",
            },
            {
                "factor": "Worldgen certainty",
                "finding": "Exact for the selected version." if ctx["worldgen"]["exact_for_selected_version"] else f"Uses {ctx['worldgen']['calculation_version']} fallback rules; verify candidates in the selected Minecraft version.",
            },
        ]
        return {
            **common,
            "display_name": "Technical Site Report",
            "assessment": classification,
            "factors": factors,
            "nearest_structure_candidates": nearest_structures,
            "next_step": "For perimeter difficulty, terrain, cave volume, spawnproofing, or farm geometry, analyze a generated world save. Those questions cannot be answered reliably from seed placement candidates alone.",
            "classification_basis": "The label above uses only connected slime-cluster size and the number of tracked structure types represented in the requested radius; it is not a hidden 0–100 score.",
        }

    if name == "Build Score":
        return {
            **common,
            "display_name": "Build Site Context",
            "assessment": "Seed-only context; terrain quality is not rated without generated chunks.",
            "biome_context": {
                "distinct_biomes_sampled": diversity,
                "dominant_biome": biome.get("dominant"),
                "biome_mix": biome.get("mix", [])[:12],
            },
            "nearby_structure_candidates": nearest_structures,
            "known_from_seed": [
                "Approximate biome mix from version-aware samples",
                "Slime-chunk locations",
                "Tracked structure placement candidates",
            ],
            "not_known_from_seed": [
                "Flatness and slope", "Cliffs and valleys", "Actual water coverage", "Cave openings",
                "Trees/vegetation and block-level obstacles", "Whether terrain-sensitive structure candidates survive final generation",
            ],
            "next_step": "Use Flat Terrain Finder, Cliff Locator, Valley Finder, or generated-world analysis on an existing save before choosing a large build footprint.",
        }

    # Exploration Score
    if diversity >= 6 and candidate_types >= 3:
        classification = "High variety within the sampled radius"
    elif diversity >= 3 or candidate_types >= 2:
        classification = "Moderate variety within the sampled radius"
    else:
        classification = "Focused / low-variety sampled area"
    route = [
        {
            "stop": index + 1,
            "type": row["type"],
            "candidate_chunk": row["candidate_chunk"],
            "candidate_block_center": row["candidate_block_center"],
            "distance_from_center_blocks": row["approx_distance_blocks"],
            "direction_from_center": row["direction"],
        }
        for index, row in enumerate(nearest_structures)
    ]
    return {
        **common,
        "display_name": "Exploration Report",
        "assessment": classification,
        "biome_variety": {
            "distinct_biomes_sampled": diversity,
            "dominant_biome": biome.get("dominant"),
            "top_biomes": biome.get("mix", [])[:10],
        },
        "structure_variety": {
            "candidate_types_present": candidate_types,
            "nearest_by_type": nearest_structures,
        },
        "suggested_first_stops": route,
        "classification_basis": "Variety is based on sampled biome count plus the number of tracked structure types with placement candidates; it is not a game mechanic or hidden score.",
    }


def _humanize_biome_result(name: str, data: dict[str, Any]) -> None:
    if "biome_id" in data:
        data["biome_name"] = biome_name(data["biome_id"])
    if "target_biome_id" in data:
        data["target_biome_name"] = biome_name(data["target_biome_id"])

    if name == "Nearest Biome" and isinstance(data.get("nearest"), (list, tuple)) and len(data["nearest"]) >= 3:
        x, z, bid = data["nearest"][:3]
        center = data.get("center", (x, z))
        distance = math.hypot(float(x) - float(center[0]), float(z) - float(center[1]))
        data["nearest"] = {
            "position": [x, z], "biome": biome_name(bid), "biome_id": int(bid),
            "distance_blocks": round(distance, 1),
        }
    if name == "Rare Biome Search" and isinstance(data.get("rarest_sampled"), list):
        total = sum(int(value) for value in (data.get("counts") or {}).values()) or 1
        data["rarest_sampled"] = [
            {"biome": biome_name(row[0]), "biome_id": int(row[0]), "samples": int(row[1]), "sample_share_percent": round(100.0 * int(row[1]) / total, 2)}
            for row in data["rarest_sampled"] if isinstance(row, (list, tuple)) and len(row) >= 2
        ]
    if name == "Largest Biome" and isinstance(data.get("largest_by_sample_count"), (list, tuple)):
        bid, count = data["largest_by_sample_count"][:2]
        total = sum(int(value) for value in (data.get("counts") or {}).values()) or 1
        data["largest_by_sample_count"] = {
            "biome": biome_name(bid), "biome_id": int(bid), "samples": int(count),
            "estimated_share_percent": round(100.0 * int(count) / total, 2),
        }
    if isinstance(data.get("counts"), dict) and name in {"Rare Biome Search", "Largest Biome"}:
        total = sum(int(value) for value in data["counts"].values()) or 1
        data["biome_counts"] = [
            {"biome": biome_name(bid), "biome_id": int(bid), "samples": int(count), "sample_share_percent": round(100.0 * int(count) / total, 2)}
            for bid, count in sorted(data["counts"].items(), key=lambda q: -int(q[1]))
        ]
        data.pop("counts", None)
    for row in data.get("candidates", []) if isinstance(data.get("candidates"), list) else []:
        if isinstance(row, dict) and isinstance(row.get("biome_ids"), list):
            row["biomes"] = [biome_name(value) for value in row["biome_ids"]]
    for row in data.get("ranked", []) if isinstance(data.get("ranked"), list) else []:
        if isinstance(row, dict) and isinstance(row.get("biome_ids"), list):
            row["biomes"] = [biome_name(value) for value in row["biome_ids"]]
    if isinstance(data.get("largest"), dict) and "biome_id" in data["largest"]:
        data["largest"]["biome"] = biome_name(data["largest"]["biome_id"])
    if name == "Biome Boundary" and isinstance(data.get("boundary_segments"), list):
        translated = []
        for row in data["boundary_segments"]:
            if not isinstance(row, dict):
                continue
            a, b = row.get("a"), row.get("b")
            if isinstance(a, (list, tuple)) and len(a) >= 3 and isinstance(b, (list, tuple)) and len(b) >= 3:
                translated.append({
                    "from": {"position": [a[0], a[1]], "biome": biome_name(a[2]), "biome_id": int(a[2])},
                    "to": {"position": [b[0], b[1]], "biome": biome_name(b[2]), "biome_id": int(b[2])},
                })
        data["boundary_segments"] = translated


def _structure_special(name: str, p: dict[str, Any], executor) -> dict[str, Any] | None:
    if name not in {"Compound Search", "Multi-Target Locator"}:
        return None
    from .restored_features import structure_candidates
    from .world.versioning import resolve_cubiomes_mc

    seed = int(str(p.get("seed", 0)).strip())
    cx, cz = int(p.get("cx", 0)), int(p.get("cz", 0))
    radius = max(1, min(256, int(p.get("radius", 64))))
    mc = resolve_cubiomes_mc(str(getattr(executor, "minecraft_version", "")))
    targets = ("Village", "Trial Chamber", "Ocean Monument", "Pillager Outpost", "Ancient City", "Ruined Portal")
    sets: dict[str, list[tuple[int, int]]] = {}
    for target in targets:
        value = structure_candidates(target, seed, cx, cz, radius, mc=mc)
        sets[target] = [tuple(map(int, q)) for q in value.get("candidate_chunks", [])]

    if name == "Multi-Target Locator":
        rows = []
        for target in targets:
            nearest = _nearest_row(target, sets[target], cx, cz)
            if nearest:
                nearest["candidate_count_in_radius"] = len(sets[target])
                rows.append(nearest)
            else:
                rows.append({"type": target, "candidate_count_in_radius": 0, "nearest": "No candidate in radius"})
        rows.sort(key=lambda row: float(row.get("distance_chunks", float("inf"))))
        return {
            "operation": name,
            "goal": "Find the nearest placement candidate for each tracked structure type from one center point.",
            "center_chunk": [cx, cz], "radius_chunks": radius,
            "targets": rows,
            "types_found": sum("candidate_chunk" in row for row in rows),
            "interpretation": "Each row answers a different target-location question. Candidates still require final biome/terrain viability checks.",
        }

    separation = max(1, int(p.get("compound_radius", max(8, radius // 4))))
    anchors = []
    flat = [(kind, point) for kind, points in sets.items() for point in points]
    for kind, (x, z) in flat:
        nearby = []
        for other, points in sets.items():
            if other == kind or not points:
                continue
            ox, oz = min(points, key=lambda q: (q[0] - x) ** 2 + (q[1] - z) ** 2)
            distance = math.hypot(ox - x, oz - z)
            if distance <= separation:
                nearby.append({"type": other, "chunk": [ox, oz], "distance_chunks": round(distance, 2)})
        if nearby:
            anchors.append({
                "anchor_type": kind,
                "anchor_chunk": [x, z],
                "anchor_block_center": [x * 16 + 8, z * 16 + 8],
                "distinct_structure_types": 1 + len(nearby),
                "nearby": sorted(nearby, key=lambda row: row["distance_chunks"]),
            })
    anchors.sort(key=lambda row: (-row["distinct_structure_types"], sum(q["distance_chunks"] for q in row["nearby"])))
    return {
        "operation": name,
        "goal": "Find candidate neighborhoods where different structure types occur near one another.",
        "center_chunk": [cx, cz], "search_radius_chunks": radius,
        "max_candidate_separation_chunks": separation,
        "compound_candidates": anchors[:128],
        "count": len(anchors),
        "interpretation": "Unlike Multi-Target Locator, this ranks close multi-structure neighborhoods rather than independently finding one nearest candidate per type.",
    }


def _ore_summary(data: dict[str, Any]) -> list[dict[str, Any]]:
    ore_counts = data.get("ore_counts") or {}
    exposed = data.get("exposed_ore_counts") or {}
    ore_by_y = data.get("ore_by_y") or {}
    chunks = max(1, int(data.get("chunks_scanned", 1)))
    families: dict[str, dict[str, Any]] = {}
    for raw, count_value in ore_counts.items():
        clean = str(raw).removeprefix("minecraft:")
        family_key = clean.removeprefix("deepslate_")
        label = _human_id(family_key)
        row = families.setdefault(label, {"resource": label, "blocks_counted": 0, "exposed_blocks_counted": 0, "y_counts": Counter()})
        row["blocks_counted"] += int(count_value)
        row["exposed_blocks_counted"] += int(exposed.get(raw, 0))
        y_rows = ore_by_y.get(raw, {})
        if isinstance(y_rows, dict):
            row["y_counts"].update({int(y): int(n) for y, n in y_rows.items()})
    out = []
    for label, row in families.items():
        y_counts: Counter[int] = row.pop("y_counts")
        peak_y = max(y_counts.items(), key=lambda q: q[1])[0] if y_counts else None
        count = int(row["blocks_counted"])
        out.append({
            **row,
            "blocks_per_scanned_chunk": round(count / chunks, 3),
            "most_common_counted_y": peak_y,
        })
    out.sort(key=lambda row: -int(row["blocks_counted"]))
    return out


def _world_report(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name not in {"Technical World Score", "Resource Score"}:
        return None
    world = str(p.get("world_path", "")).strip()
    if not world:
        return {
            "operation": name,
            "requires_generated_world": True,
            "reason": "Select a generated Java world save. This report uses actual generated chunk/block data and does not substitute seed-level structure counts.",
        }
    from .world_analysis import analyze_world

    data = analyze_world(
        world,
        dimension=str(p.get("dimension", "Overworld")),
        center_chunk=(int(p.get("cx", 0)), int(p.get("cz", 0))),
        radius_chunks=int(p.get("radius", 64)),
    )
    resources = _ore_summary(data)
    if name == "Resource Score":
        total = sum(int(row["blocks_counted"]) for row in resources)
        return {
            "operation": name,
            "display_name": "Resource Survey",
            "source": "generated-world block states",
            "chunks_scanned": data["chunks_scanned"],
            "recognized_ore_blocks_counted": total,
            "resources": resources,
            "interpretation": "Counts describe already-generated chunks in the selected save. Blocks per chunk make differently sized scans easier to compare; the most-common Y is the mode of counted ore blocks, not a guaranteed best mining level.",
            "limitations": data.get("limitations", []),
        }

    peak = data.get("peak") or {}
    valley = data.get("valley") or {}
    relief = None
    if peak.get("y") is not None and valley.get("y") is not None:
        relief = float(peak["y"]) - float(valley["y"])
    chunks = max(1, int(data["chunks_scanned"]))
    total_ore = sum(int(row["blocks_counted"]) for row in resources)
    return {
        "operation": name,
        "display_name": "Technical World Report",
        "source": "generated-world block states",
        "chunks_scanned": data["chunks_scanned"],
        "terrain": {
            "peak": peak or None,
            "valley": valley or None,
            "vertical_relief_blocks": round(relief, 2) if relief is not None else None,
            "largest_adjacent_chunk_mean_height_change": data.get("largest_cliff"),
        },
        "caves": {
            "air_blocks_below_y64_counted": data.get("cave_air_blocks", 0),
            "air_blocks_per_scanned_chunk": round(float(data.get("cave_air_blocks", 0)) / chunks, 2),
            "solid_faces_adjacent_to_cave_air": data.get("cave_surface_faces", 0),
            "cave_faces_per_scanned_chunk": round(float(data.get("cave_surface_faces", 0)) / chunks, 2),
        },
        "resources": {
            "recognized_ore_blocks_counted": total_ore,
            "ore_blocks_per_scanned_chunk": round(total_ore / chunks, 3),
            "top_resources": resources[:8],
        },
        "interpretation": [
            "Terrain, cave, and resource measurements are shown separately instead of being collapsed into an opaque 0–100 score.",
            "Use the individual terrain and resource tools when one factor matters more than the others.",
        ],
        "limitations": data.get("limitations", []),
    }


def install() -> None:
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_analysis_reports_v2_installed", False):
        return

    original_execute = FeatureExecutor.execute
    original_fields = FeatureExecutor.input_fields

    def input_fields(self, feature):
        spec = self.spec(feature)
        if spec.top == "Seed Tools" and spec.submenu == "Local Area":
            fields = [
                ("seed", "World seed", 123456789, "text"),
                ("cx", "Center chunk X", 0, "int"),
                ("cz", "Center chunk Z", 0, "int"),
            ]
            if spec.name != "32-Chunk Analysis":
                fields.append(("radius", "Search radius (chunks)", 32, "int"))
            return fields
        if spec.top == "Seed Tools" and spec.submenu == "Structures" and spec.name in {"Compound Search", "Multi-Target Locator"}:
            fields = [
                ("seed", "World seed", 123456789, "text"),
                ("cx", "Center chunk X", 0, "int"), ("cz", "Center chunk Z", 0, "int"),
                ("radius", "Search radius (chunks)", 64, "int"),
            ]
            if spec.name == "Compound Search":
                fields.append(("compound_radius", "Maximum separation (chunks)", 16, "int"))
            return fields
        if spec.top == "Seed Tools" and spec.submenu == "Biomes" and spec.name == "Nearest Biome":
            return [
                ("seed", "World seed", 123456789, "text"),
                ("x", "Center block X", 0, "int"), ("y", "Sample Y", 64, "int"), ("z", "Center block Z", 0, "int"),
                ("radius", "Search radius (blocks)", 2048, "int"),
                ("step", "Sample step (blocks)", 16, "int"),
                ("target_biome", "Target biome (name or numeric ID)", "plains", "text"),
            ]
        return original_fields(self, feature)

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        values = dict(params or {})

        if spec.top == "Seed Tools" and spec.submenu == "Local Area":
            try:
                context = _collect_local_context(spec.name, values, self)
                data = _render_local_report(spec.name, context)
                note = "Local seed reports intentionally keep placement candidates, sampled biomes, and generated-world facts separate."
                return self._result(spec, "ok", data, note)
            except Exception as exc:
                return self._result(spec, "unavailable", {"operation": spec.name, "available": False, "reason": str(exc)})

        if spec.top == "Seed Tools" and spec.submenu == "Structures":
            try:
                special = _structure_special(spec.name, values, self)
            except Exception as exc:
                special = {"operation": spec.name, "available": False, "reason": str(exc)} if spec.name in {"Compound Search", "Multi-Target Locator"} else None
            if special is not None:
                return self._result(spec, "ok" if special.get("available", True) else "unavailable", special)

        if spec.top == "Seed Tools" and spec.submenu == "World Analysis" and spec.name in {"Technical World Score", "Resource Score"}:
            try:
                data = _world_report(spec.name, values)
                return self._result(spec, "ok" if data and not data.get("requires_generated_world") else "unavailable", data or {"available": False})
            except Exception as exc:
                return self._result(spec, "unavailable", {"operation": spec.name, "available": False, "reason": str(exc)})

        if spec.top == "Seed Tools" and spec.submenu == "Biomes" and spec.name == "Nearest Biome" and "target_biome" in values:
            try:
                values["target_biome"] = biome_id(values["target_biome"])
            except ValueError as exc:
                return self._result(spec, "unavailable", {"operation": spec.name, "available": False, "reason": str(exc)})

        result = original_execute(self, spec, values, dry_run)
        if spec.top == "Seed Tools" and spec.submenu in {"Biomes", "Cubiomes"} and isinstance(getattr(result, "data", None), dict):
            _humanize_biome_result(spec.name, result.data)
        return result

    FeatureExecutor.input_fields = input_fields
    FeatureExecutor.execute = execute
    FeatureExecutor._analysis_reports_v2_installed = True
