from __future__ import annotations

"""Spawner discovery with actual spawned-mob identification and user filters."""

import math
from pathlib import Path
from typing import Any

SPAWNER_CHOICES = [
    "All mob spawners", "Zombie", "Skeleton", "Spider", "Cave Spider",
    "Blaze", "Silverfish", "Pig", "Magma Cube", "Other / Unknown",
    "Trial Spawner", "Vault", "All spawner-like blocks",
]

MOB_LABELS = {
    "minecraft:zombie": "Zombie",
    "minecraft:skeleton": "Skeleton",
    "minecraft:spider": "Spider",
    "minecraft:cave_spider": "Cave Spider",
    "minecraft:blaze": "Blaze",
    "minecraft:silverfish": "Silverfish",
    "minecraft:pig": "Pig",
    "minecraft:magma_cube": "Magma Cube",
}


def _entity_ids(block_entity: dict[str, Any]) -> list[str]:
    found: list[str] = []

    def add(value):
        text = str(value or "").strip().lower()
        if text and text not in found:
            found.append(text)

    add(block_entity.get("EntityId"))
    spawn_data = block_entity.get("SpawnData") or block_entity.get("spawn_data")
    if isinstance(spawn_data, dict):
        entity = spawn_data.get("entity") or spawn_data.get("Entity") or spawn_data
        if isinstance(entity, dict):
            add(entity.get("id"))
    potentials = block_entity.get("SpawnPotentials") or block_entity.get("spawn_potentials") or []
    if isinstance(potentials, list):
        for entry in potentials:
            if not isinstance(entry, dict):
                continue
            data = entry.get("data") or entry.get("Data") or entry
            if isinstance(data, dict):
                entity = data.get("entity") or data.get("Entity") or data
                if isinstance(entity, dict):
                    add(entity.get("id"))
    return found


def _mob_labels(entity_ids: list[str]) -> list[str]:
    labels = []
    for entity_id in entity_ids:
        label = MOB_LABELS.get(entity_id)
        if label is None:
            clean = entity_id.removeprefix("minecraft:").replace("_", " ").strip()
            label = clean.title() if clean else "Unknown"
        if label not in labels:
            labels.append(label)
    return labels


def scan_spawners_detailed(world_path: str | Path, *, dimension: str = "overworld", center_chunk=(0, 0), radius_chunks=64):
    from .world_scan import _region_chunks, _region_dir, _walk

    root = Path(world_path).expanduser()
    region = _region_dir(root, dimension)
    cx0, cz0 = map(int, center_chunk)
    radius = max(0, int(radius_chunks))
    hits: list[dict[str, Any]] = []
    files = chunks = 0
    if not region.exists():
        return {
            "available": False,
            "reason": f"No generated {dimension} region directory was found at {region}.",
            "hits": [], "chunks_scanned": 0,
        }
    for rp in sorted(region.glob("r.*.*.mca")):
        files += 1
        for _, nbt in _region_chunks(rp):
            chunks += 1
            for block_entity in _walk(nbt):
                ident = str(block_entity.get("id", "")).lower()
                if ident not in {"minecraft:mob_spawner", "mobspawner", "minecraft:trial_spawner", "minecraft:vault"}:
                    continue
                if not all(key in block_entity for key in ("x", "y", "z")):
                    continue
                x, y, z = int(block_entity["x"]), int(block_entity["y"]), int(block_entity["z"])
                chunk = [math.floor(x / 16), math.floor(z / 16)]
                if abs(chunk[0] - cx0) > radius or abs(chunk[1] - cz0) > radius:
                    continue
                entities = _entity_ids(block_entity) if ident in {"minecraft:mob_spawner", "mobspawner"} else []
                if ident == "minecraft:trial_spawner":
                    kind = "Trial Spawner"
                elif ident == "minecraft:vault":
                    kind = "Vault"
                else:
                    kind = "Mob Spawner"
                mobs = _mob_labels(entities)
                hits.append({
                    "spawner_kind": kind,
                    "mobs": mobs or (["Unknown"] if kind == "Mob Spawner" else []),
                    "position": [x, y, z],
                    "chunk": chunk,
                    "distance_from_reference_blocks": round(math.hypot(x - (cx0 * 16 + 8), z - (cz0 * 16 + 8)), 1),
                    "region_file": rp.name,
                })
    hits.sort(key=lambda row: float(row["distance_from_reference_blocks"]))
    return {
        "available": True,
        "world_path": str(root),
        "dimension": dimension.title(),
        "reference_chunk": [cx0, cz0],
        "radius_chunks": radius,
        "region_files_scanned": files,
        "chunks_scanned": chunks,
        "hits": hits,
    }


def _matches(hit: dict[str, Any], selected: str) -> bool:
    if selected == "All spawner-like blocks":
        return True
    if selected == "Trial Spawner":
        return hit.get("spawner_kind") == "Trial Spawner"
    if selected == "Vault":
        return hit.get("spawner_kind") == "Vault"
    if hit.get("spawner_kind") != "Mob Spawner":
        return False
    if selected == "All mob spawners":
        return True
    mobs = set(hit.get("mobs") or [])
    if selected == "Other / Unknown":
        return not mobs or "Unknown" in mobs or any(mob not in set(MOB_LABELS.values()) for mob in mobs)
    return selected in mobs


def _clusters(hits: list[dict[str, Any]], minimum: int, distance: float) -> list[dict[str, Any]]:
    groups: dict[tuple[tuple[int, int, int], ...], list[dict[str, Any]]] = {}
    for anchor in hits:
        ax, ay, az = anchor["position"]
        group = [
            row for row in hits
            if math.dist((ax, ay, az), tuple(row["position"])) <= distance
        ]
        if len(group) < minimum:
            continue
        key = tuple(sorted(tuple(map(int, row["position"])) for row in group))
        groups[key] = group
    rows = []
    for group in groups.values():
        center = [sum(row["position"][axis] for row in group) / len(group) for axis in range(3)]
        rows.append({
            "spawners": len(group),
            "approx_center": [round(center[0], 1), round(center[1], 1), round(center[2], 1)],
            "mob_types": sorted({mob for row in group for mob in row.get("mobs", [])}),
            "positions": [row["position"] for row in group],
        })
    rows.sort(key=lambda row: (-int(row["spawners"]), row["approx_center"]))
    return rows


def _report(name: str, params: dict[str, Any], executor, dry_run: bool) -> dict[str, Any]:
    selected = str(params.get("spawner_type", "All mob spawners"))
    if name == "Stronghold Silverfish":
        selected = "Silverfish"
    elif name == "Trial Chamber Spawners":
        selected = "Trial Spawner"

    if dry_run:
        return {
            "available": False,
            "requires_generated_world": True,
            "selected_spawner_type": selected,
            "reason": "Run against a generated Java save, or enable exact seed regeneration.",
        }

    from .seed_worldgen import resolve_world_source
    world, source = resolve_world_source(params, executor, default_radius=8)
    if world is None:
        return {**source, "selected_spawner_type": selected}

    data = scan_spawners_detailed(
        world,
        dimension=str(params.get("dimension", "overworld")).lower(),
        center_chunk=(int(params.get("cx", 0)), int(params.get("cz", 0))),
        radius_chunks=int(params.get("radius", 8)),
    )
    if not data.get("available"):
        return data
    filtered = [row for row in data["hits"] if _matches(row, selected)]
    result = {
        "purpose": "Find generated spawner block entities and identify the mob encoded in their NBT when available.",
        "selected_spawner_type": selected,
        "matches_found": len(filtered),
        "reference_chunk": data["reference_chunk"],
        "radius_chunks": data["radius_chunks"],
        "hits": filtered,
        "scan_summary": {
            "chunks_scanned": data["chunks_scanned"],
            "region_files_scanned": data["region_files_scanned"],
            "world_source": source.get("source", "generated save"),
        },
    }
    if name == "Double Spawner Locator":
        result["clusters"] = _clusters(filtered, 2, 32.0)
        result["cluster_rule"] = "At least two selected spawners within 32 blocks of one anchor; verify one-player activation overlap in-game."
    elif name == "Triple Spawner Locator":
        result["clusters"] = _clusters(filtered, 3, 32.0)
        result["cluster_rule"] = "At least three selected spawners within 32 blocks of one anchor; verify one-player activation overlap in-game."
    elif name == "Quad Spawner Locator":
        result["clusters"] = _clusters(filtered, 4, 32.0)
        result["cluster_rule"] = "At least four selected spawners within 32 blocks of one anchor; verify one-player activation overlap in-game."
    elif name == "Spawner Cluster Ranking":
        result["clusters"] = _clusters(filtered, 2, 48.0)[:100]
        result["cluster_rule"] = "Ranks selected spawner neighborhoods within 48 blocks; this is a scouting radius, not a claim that all can activate at once."
    elif name == "Stronghold Silverfish":
        result["purpose"] = "Find generated mob spawners whose NBT identifies Silverfish."
    elif name == "Trial Chamber Spawners":
        result["purpose"] = "Find generated trial-spawner block entities in the scanned area."
    return result


def install() -> None:
    from . import descriptions, tool_guides
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_spawner_v3_installed", False):
        return
    previous_execute = FeatureExecutor.execute
    previous_fields = FeatureExecutor.input_fields

    tool_guides.DISPLAY_NAMES[("Seed Tools", "Spawners", "Dungeon/Pig Spawner Locator")] = "Spawner Locator"
    descriptions.SPECIAL["Dungeon/Pig Spawner Locator"] = (
        "Scans generated chunk NBT for mob spawners and lets you filter by Zombie, Skeleton, Spider, Cave Spider, Blaze, Silverfish, Pig, Magma Cube, or unknown/custom spawners."
    )
    tool_guides._OUTPUT_EXACT["Dungeon/Pig Spawner Locator"] = (
        "Returns selected spawner type, mob identity when encoded in NBT, block position, chunk, distance from the reference, and a map-ready hit list."
    )

    def input_fields(self, feature):
        spec = self.spec(feature)
        if spec.top == "Seed Tools" and spec.submenu == "Spawners":
            fields = [
                ("world_path", "Generated world save (optional)", "", "text"),
                ("spawner_type", "Spawner / mob type", SPAWNER_CHOICES, "choice"),
                ("seed", "World seed (for exact regeneration)", 123456789, "text"),
                ("cx", "Reference chunk X", 0, "int"),
                ("cz", "Reference chunk Z", 0, "int"),
                ("radius", "Scan radius (chunks)", 8, "int"),
                ("regenerate_from_seed", "Generate exact vanilla chunks when no save is selected", True, "bool"),
                ("accept_minecraft_eula", "Accept Minecraft EULA for local reference generation", False, "bool"),
                ("worldgen_max_chunks", "Maximum exact chunks to generate", 4096, "int"),
            ]
            if spec.name in {"Stronghold Silverfish", "Trial Chamber Spawners"}:
                fields = [field for field in fields if field[0] != "spawner_type"]
            return fields
        return previous_fields(self, feature)

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        if spec.top == "Seed Tools" and spec.submenu == "Spawners":
            values = self.defaults(spec)
            values.update(params or {})
            data = _report(spec.name, values, self, dry_run)
            status = "unavailable" if data.get("available") is False else "ok"
            return self._result(spec, status, data)
        return previous_execute(self, spec, params, dry_run)

    FeatureExecutor.input_fields = input_fields
    FeatureExecutor.execute = execute
    FeatureExecutor._spawner_v3_installed = True
