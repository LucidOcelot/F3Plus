from __future__ import annotations

"""Exact Mojang reference-world generation policy for seed-backed analyzers."""

from typing import Any

from .seed_worldgen_reuse import resolve_world_source

SEED_REGENERATABLE = {
    "Dungeon/Pig Spawner Locator", "Double Spawner Locator", "Triple Spawner Locator",
    "Quad Spawner Locator", "Spawner Cluster Ranking", "Stronghold Silverfish",
    "Trial Chamber Spawners", "Largest Ocean", "Largest Mountain Chain",
    "Largest Cave Region", "Flat Terrain Finder", "Valley Finder", "Mountain Peak Finder",
    "Terrain Base Finder", "Island Finder", "Peninsula Detector", "River Crossing Finder",
    "Lake Density", "Cliff Locator", "Ore Distribution", "Ore Exposure Estimate",
    "Cave Exposure Estimate", "Technical World Score", "Resource Score",
}
TICK_SENSITIVE = {"Largest Cave Region", "Cave Exposure Estimate", "Ore Exposure Estimate"}


def add_fields(fields):
    out = list(fields)
    for index, field in enumerate(out):
        if field[0] == "radius": out[index] = (field[0], field[1], 8, field[3])
    present = {field[0] for field in out}
    additions = [
        ("seed", "World seed", "", "text"),
        ("regenerate_from_seed", "Generate vanilla chunks from seed when no save is selected", True, "bool"),
        ("accept_minecraft_eula", "I accept the Minecraft EULA for this local server generation", False, "bool"),
        ("worldgen_max_chunks", "Maximum exact chunks to generate", 4096, "int"),
    ]
    out.extend(field for field in additions if field[0] not in present)
    return out


def execute_with_world(spec, params: dict[str, Any], executor, base_execute):
    if spec.top != "Seed Tools" or spec.name not in SEED_REGENERATABLE or str(params.get("world_path", "")).strip() or not bool(params.get("regenerate_from_seed", False)):
        return base_execute(spec, params)
    world, source = resolve_world_source(params, executor)
    if world is None:
        return executor._result(spec, "unavailable", {"operation": spec.name, **source})
    values = dict(params); values["world_path"] = world
    result = base_execute(spec, values)
    if isinstance(getattr(result, "data", None), dict):
        source = dict(source)
        if spec.name in TICK_SENSITIVE:
            source["limitation"] = (
                "Cave/air/exposure state is measured from a freshly generated vanilla server save. "
                "Scheduled fluid, gravity, and other game ticks can change some air/exposure blocks after generation; "
                "ore placement and immutable geology are separately integration-tested for exact repeatability."
            )
        result.data = {**result.data, "worldgen_source": source}
    return result