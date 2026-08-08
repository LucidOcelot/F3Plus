"""Seed-recovery policy for F3+.

Known world seeds may be used for deterministic locators and calculators.
World/structure seed recovery is restricted to Nether bedrock observations.
Independent gameplay RNG analysis does not count as world-seed recovery.
"""
from __future__ import annotations

ALLOWED_WORLD_SEED_RECOVERY = frozenset({
    "Nether Bedrock Cracker",
})

# Terms which indicate a world/structure-seed recovery feature when used outside
# the explicitly allowed Nether-bedrock workflow.
RECOVERY_TERMS = (
    "seed cracker", "seed cracking", "seed recovery", "recover seed",
    "structure seed crack", "world seed crack", "biome seed crack",
    "dungeon seed crack", "terrain seed crack",
)


def is_world_seed_recovery(name: str) -> bool:
    text = name.strip().lower()
    return any(term in text for term in RECOVERY_TERMS) or text in {
        "seed candidate search", "seed verification"
    }


def validate_feature(name: str, submenu: str = "", top: str = "") -> None:
    """Raise if a catalog feature violates the world-seed recovery scope.

    Gameplay RNG recovery is explicitly separate and is permitted under RNG Tools.
    """
    if top == "RNG Tools":
        return
    if name in ALLOWED_WORLD_SEED_RECOVERY:
        if submenu and submenu != "World Seed Recovery":
            raise ValueError(f"{name} must remain under Seed Tools > World Seed Recovery.")
        return
    if is_world_seed_recovery(name):
        raise ValueError(
            f"World/structure seed recovery is restricted to Nether bedrock: {name}"
        )
