from __future__ import annotations

"""Resilient semantic artwork recovery for the 2.5 desktop UI.

The normal exact-path lookup remains first choice.  Mojang occasionally moves or
renames texture files, so the UI also has a conservative keyword fallback scoped to
item/block textures.  Nothing is bundled or downloaded: bytes are read only from an
installed Java client JAR and cached for the current process.
"""

from functools import lru_cache
from pathlib import Path
import zipfile

from .minecraft_art import texture_bytes as exact_texture_bytes
from .villagers import installed_versions


FUZZY_TERMS: dict[str, tuple[str, ...]] = {
    "home": ("chorus_flower", "chorus"),
    "app": ("chorus_flower", "chorus_fruit"),
    "actions": ("redstone", "wooden_sword"),
    "automation": ("redstone", "repeater"),
    "travel": ("elytra", "compass", "boots"),
    "mining": ("diamond_pickaxe", "iron_pickaxe", "pickaxe"),
    "construction": ("bricks", "stone_bricks", "brick"),
    "macro": ("writable_book", "book", "repeater"),
    "position": ("recovery_compass", "compass"),
    "coordinates": ("compass", "filled_map", "map"),
    "map": ("filled_map", "map", "compass"),
    "route": ("recovery_compass", "compass", "map"),
    "portal": ("obsidian", "crying_obsidian"),
    "seed": ("chorus_fruit", "wheat_seeds"),
    "seed_recovery": ("bedrock", "ender_eye"),
    "slime": ("slime_ball", "slime_block"),
    "structure": ("ender_eye", "filled_map", "map"),
    "spawner": ("trial_key", "ominous_trial_key", "spawner"),
    "biome": ("grass_block", "moss_block", "map"),
    "ore": ("raw_iron", "diamond", "diamond_ore"),
    "local_area": ("filled_map", "map", "grass_block"),
    "world_analysis": ("spyglass", "map", "compass"),
    "profiles": ("writable_book", "book", "map"),
    "building": ("iron_pickaxe", "bricks", "stone_bricks"),
    "shape": ("stonecutter", "bricks", "stone_bricks"),
    "farm": ("wheat", "wheat_seeds", "iron_hoe"),
    "redstone": ("redstone", "repeater", "comparator"),
    "storage": ("shulker_box", "chest", "bundle"),
    "technical": ("observer", "comparator", "repeater"),
    "resources": ("diamond", "raw_iron", "experience_bottle"),
    "recipes": ("knowledge_book", "crafting_table", "book"),
    "rng": ("ender_pearl", "ender_eye"),
    "enchant": ("enchanted_book", "lapis_lazuli", "book"),
    "anvil": ("anvil", "enchanted_book"),
    "loot": ("chest", "bundle", "golden_apple"),
    "generation": ("amethyst_shard", "ender_eye", "chorus_fruit"),
    "brewing": ("brewing_stand", "potion", "blaze_powder"),
    "horse": ("saddle", "horse_armor"),
    "villager": ("emerald", "emerald_block"),
    "trade": ("emerald", "book"),
    "version": ("clock", "compass"),
    "settings": ("comparator", "repeater", "redstone"),
    "history": ("clock", "book"),
    "diagnostics": ("spyglass", "recovery_compass", "redstone"),
    "utilities": ("recovery_compass", "compass", "redstone"),
    "safety": ("totem_of_undying", "golden_apple"),
}


def _ordered_versions(version_hint: str) -> list[tuple[str, Path]]:
    rows = list(installed_versions().items())
    hint = str(version_hint or "").strip().lower().replace(" ", "-")
    def score(row):
        name, path = row
        normalized = str(name).lower().replace(" ", "-")
        exact = 2 if hint and normalized == hint else (1 if hint and (hint in normalized or normalized in hint) else 0)
        try: modified = int(path.stat().st_mtime_ns)
        except OSError: modified = 0
        return exact, modified, normalized
    rows.sort(key=score, reverse=True)
    return rows


@lru_cache(maxsize=256)
def _fuzzy_from_jar(path_text: str, mtime_ns: int, size: int, key: str):
    terms = FUZZY_TERMS.get(key, ())
    if not terms:
        return None, None
    try:
        with zipfile.ZipFile(path_text) as jar:
            names = [
                name for name in jar.namelist()
                if name.startswith("assets/minecraft/textures/")
                and ("/item/" in name or "/block/" in name)
                and name.endswith(".png")
            ]
            lower = [(name, name.lower()) for name in names]
            for term in terms:
                token = str(term).lower()
                matches = [name for name, low in lower if token in low]
                if not matches:
                    continue
                # Prefer the shortest direct-looking resource name over animation/frame
                # companions or unusually deep resource-pack variants.
                matches.sort(key=lambda name: (name.count("/"), len(name), name))
                member = matches[0]
                return jar.read(member), member
    except (OSError, zipfile.BadZipFile, KeyError):
        pass
    return None, None


def semantic_texture_bytes(kind: str, version_hint: str = ""):
    """Return ``(bytes, member, version)`` using exact then conservative fuzzy lookup."""
    data, member, version = exact_texture_bytes(kind, version_hint)
    if data:
        return data, member, version
    key = str(kind or "").lower()
    for version, jar in _ordered_versions(version_hint):
        try:
            stat = jar.stat()
            data, member = _fuzzy_from_jar(str(jar.resolve()), int(stat.st_mtime_ns), int(stat.st_size), key)
        except OSError:
            continue
        if data:
            return data, member, version
    return None, None, None


def clear_semantic_texture_cache() -> None:
    _fuzzy_from_jar.cache_clear()
