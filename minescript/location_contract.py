from __future__ import annotations

"""Qt-free contract for world/search center inputs."""


LOCATION_KEYS = {
    "x", "y", "z", "cx", "cz", "chunk_x", "chunk_z", "center_chunk_x",
    "center_chunk_z", "center_x", "center_z", "origin_x", "origin_z",
}


def applies_to(spec) -> bool:
    if getattr(spec, "top", "") != "Seed Tools":
        return False
    if getattr(spec, "submenu", "") in {"World Seed Recovery", "Cubiomes"}:
        return False
    name = str(getattr(spec, "name", ""))
    if name.endswith("Status") or name in {"Compatibility Report"}:
        return False
    return getattr(spec, "submenu", "") in {
        "Slime", "Structures", "Spawners", "Biomes", "Local Area",
        "World Analysis", "Nether",
    }
