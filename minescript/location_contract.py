from __future__ import annotations

"""Qt-free contract for world/search center inputs."""


LOCATION_KEYS = {
    "x", "y", "z", "cx", "cz", "chunk_x", "chunk_z", "center_chunk_x",
    "center_chunk_z", "center_x", "center_z", "origin_x", "origin_z",
}

_WORLD_ANALYSIS_WITHOUT_CENTER = {
    "Spawn Analysis",          # intentionally analyzes coordinate origin / spawn context
    "Chunk Loading Simulator", # pure simulation-distance footprint geometry
    "Search Radius Optimizer", # compares scan-radius cost, not a location
}


def applies_to(spec) -> bool:
    if getattr(spec, "top", "") != "Seed Tools":
        return False
    submenu = str(getattr(spec, "submenu", ""))
    name = str(getattr(spec, "name", ""))
    if submenu in {"World Seed Recovery", "Cubiomes"}:
        return False
    if name.endswith("Status") or name in {"Compatibility Report"}:
        return False
    if submenu == "World Analysis" and name in _WORLD_ANALYSIS_WITHOUT_CENTER:
        return False
    return submenu in {
        "Slime", "Structures", "Spawners", "Biomes", "Local Area",
        "World Analysis", "Nether",
    }
