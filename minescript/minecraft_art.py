from __future__ import annotations

"""Recover semantic UI artwork from the player's installed Minecraft Java client.

F3+ never redistributes Mojang assets. Workbench art is resolved at runtime from the
selected/local Java JAR; original recolorable F3+ SVG art remains the fallback when a
suitable installed texture is unavailable.
"""

from functools import lru_cache
from pathlib import Path
import zipfile

from .villagers import installed_versions


# Semantic UI keys -> ordered installed-JAR texture candidates. The list deliberately
# contains both modern and older resource names where Mojang has moved animated items.
_TEXTURES = {
    "home": ("assets/minecraft/textures/block/chorus_flower.png", "assets/minecraft/textures/block/chorus_flower_dead.png"),
    "chorus_flower": ("assets/minecraft/textures/block/chorus_flower.png", "assets/minecraft/textures/block/chorus_flower_dead.png"),
    "seed": ("assets/minecraft/textures/item/chorus_fruit.png", "assets/minecraft/textures/item/wheat_seeds.png"),
    "seed_recovery": ("assets/minecraft/textures/block/bedrock.png", "assets/minecraft/textures/item/ender_eye.png"),
    "chorus_fruit": ("assets/minecraft/textures/item/chorus_fruit.png",),
    "automation": ("assets/minecraft/textures/item/redstone.png", "assets/minecraft/textures/block/redstone_torch.png"),
    "actions": ("assets/minecraft/textures/item/redstone.png", "assets/minecraft/textures/item/wooden_sword.png"),
    "travel": ("assets/minecraft/textures/item/elytra.png", "assets/minecraft/textures/item/compass.png", "assets/minecraft/textures/item/leather_boots.png"),
    "mining": ("assets/minecraft/textures/item/diamond_pickaxe.png", "assets/minecraft/textures/item/iron_pickaxe.png"),
    "construction": ("assets/minecraft/textures/item/bricks.png", "assets/minecraft/textures/item/brick.png", "assets/minecraft/textures/block/stone_bricks.png"),
    "macro": ("assets/minecraft/textures/item/writable_book.png", "assets/minecraft/textures/item/book.png", "assets/minecraft/textures/item/repeater.png"),
    "shulker": ("assets/minecraft/textures/item/shulker_shell.png", "assets/minecraft/textures/item/purple_dye.png"),
    "navigation": ("assets/minecraft/textures/item/compass_00.png", "assets/minecraft/textures/item/compass.png", "assets/minecraft/textures/item/recovery_compass_00.png"),
    "position": ("assets/minecraft/textures/item/recovery_compass_00.png", "assets/minecraft/textures/item/compass_00.png", "assets/minecraft/textures/item/compass.png"),
    "coordinates": ("assets/minecraft/textures/item/compass_00.png", "assets/minecraft/textures/item/map.png", "assets/minecraft/textures/item/filled_map.png"),
    "map": ("assets/minecraft/textures/item/map.png", "assets/minecraft/textures/item/filled_map.png", "assets/minecraft/textures/item/compass.png"),
    "route": ("assets/minecraft/textures/item/recovery_compass.png", "assets/minecraft/textures/item/recovery_compass_00.png", "assets/minecraft/textures/item/compass.png", "assets/minecraft/textures/item/map.png"),
    "portal": ("assets/minecraft/textures/item/obsidian.png", "assets/minecraft/textures/block/obsidian.png", "assets/minecraft/textures/item/crying_obsidian.png"),
    "structure": ("assets/minecraft/textures/item/ender_eye.png", "assets/minecraft/textures/item/map.png"),
    "shulker_seed": ("assets/minecraft/textures/item/ender_eye.png", "assets/minecraft/textures/item/shulker_shell.png"),
    "slime": ("assets/minecraft/textures/item/slime_ball.png", "assets/minecraft/textures/block/slime_block.png"),
    "spawner": ("assets/minecraft/textures/item/trial_key.png", "assets/minecraft/textures/item/ominous_trial_key.png", "assets/minecraft/textures/block/spawner.png"),
    "biome": ("assets/minecraft/textures/block/grass_block_side.png", "assets/minecraft/textures/block/moss_block.png", "assets/minecraft/textures/item/map.png"),
    "ore": ("assets/minecraft/textures/item/raw_iron.png", "assets/minecraft/textures/item/diamond.png", "assets/minecraft/textures/block/diamond_ore.png"),
    "local_area": ("assets/minecraft/textures/item/map.png", "assets/minecraft/textures/item/filled_map.png", "assets/minecraft/textures/block/grass_block_side.png"),
    "world_analysis": ("assets/minecraft/textures/item/spyglass.png", "assets/minecraft/textures/item/map.png", "assets/minecraft/textures/item/compass.png"),
    "profiles": ("assets/minecraft/textures/item/book.png", "assets/minecraft/textures/item/writable_book.png", "assets/minecraft/textures/item/map.png"),
    "calculator": ("assets/minecraft/textures/item/redstone.png", "assets/minecraft/textures/item/clock_00.png", "assets/minecraft/textures/item/clock.png"),
    "chorus_calc": ("assets/minecraft/textures/item/redstone.png", "assets/minecraft/textures/item/clock_00.png"),
    "building": ("assets/minecraft/textures/item/iron_pickaxe.png", "assets/minecraft/textures/item/bricks.png", "assets/minecraft/textures/item/brick.png"),
    "shape": ("assets/minecraft/textures/item/stonecutter.png", "assets/minecraft/textures/item/bricks.png", "assets/minecraft/textures/block/stone_bricks.png"),
    "farm": ("assets/minecraft/textures/item/wheat.png", "assets/minecraft/textures/item/wheat_seeds.png", "assets/minecraft/textures/item/iron_hoe.png"),
    "redstone": ("assets/minecraft/textures/item/redstone.png", "assets/minecraft/textures/item/repeater.png", "assets/minecraft/textures/item/comparator.png"),
    "storage": ("assets/minecraft/textures/item/chest.png", "assets/minecraft/textures/item/shulker_box.png", "assets/minecraft/textures/item/bundle.png"),
    "technical": ("assets/minecraft/textures/item/comparator.png", "assets/minecraft/textures/item/repeater.png", "assets/minecraft/textures/item/observer.png"),
    "resources": ("assets/minecraft/textures/item/diamond.png", "assets/minecraft/textures/item/raw_iron.png", "assets/minecraft/textures/item/experience_bottle.png"),
    "recipes": ("assets/minecraft/textures/item/knowledge_book.png", "assets/minecraft/textures/item/book.png", "assets/minecraft/textures/item/crafting_table.png"),
    "rng": ("assets/minecraft/textures/item/ender_pearl.png", "assets/minecraft/textures/item/ender_eye.png"),
    "enchant": ("assets/minecraft/textures/item/enchanted_book.png", "assets/minecraft/textures/item/lapis_lazuli.png", "assets/minecraft/textures/item/book.png"),
    "anvil": ("assets/minecraft/textures/item/anvil.png", "assets/minecraft/textures/block/anvil.png", "assets/minecraft/textures/item/enchanted_book.png"),
    "loot": ("assets/minecraft/textures/item/chest.png", "assets/minecraft/textures/item/bundle.png", "assets/minecraft/textures/item/golden_apple.png"),
    "generation": ("assets/minecraft/textures/item/ender_eye.png", "assets/minecraft/textures/item/amethyst_shard.png", "assets/minecraft/textures/item/chorus_fruit.png"),
    "brewing": ("assets/minecraft/textures/item/brewing_stand.png", "assets/minecraft/textures/item/potion.png", "assets/minecraft/textures/item/blaze_powder.png"),
    "horse": ("assets/minecraft/textures/item/saddle.png", "assets/minecraft/textures/item/golden_horse_armor.png"),
    "villager": ("assets/minecraft/textures/item/emerald.png", "assets/minecraft/textures/block/emerald_block.png"),
    "trade": ("assets/minecraft/textures/item/emerald.png", "assets/minecraft/textures/item/book.png"),
    "guided": ("assets/minecraft/textures/item/book.png", "assets/minecraft/textures/item/writable_book.png"),
    "version": ("assets/minecraft/textures/item/clock_00.png", "assets/minecraft/textures/item/clock.png", "assets/minecraft/textures/item/compass.png"),
    "settings": ("assets/minecraft/textures/item/comparator.png", "assets/minecraft/textures/item/repeater.png", "assets/minecraft/textures/item/redstone.png"),
    "history": ("assets/minecraft/textures/item/clock_00.png", "assets/minecraft/textures/item/clock.png", "assets/minecraft/textures/item/book.png"),
    "diagnostics": ("assets/minecraft/textures/item/spyglass.png", "assets/minecraft/textures/item/recovery_compass_00.png", "assets/minecraft/textures/item/redstone.png"),
    "utilities": ("assets/minecraft/textures/item/recovery_compass_00.png", "assets/minecraft/textures/item/compass_00.png", "assets/minecraft/textures/item/redstone.png"),
    "safety": ("assets/minecraft/textures/item/totem_of_undying.png", "assets/minecraft/textures/item/golden_apple.png"),
    "app": ("assets/minecraft/textures/block/chorus_flower.png", "assets/minecraft/textures/item/chorus_fruit.png"),
}


def _normalized(value: str | None) -> str:
    return (value or "").strip().lower().replace(" ", "-")


def _version_order(version_hint: str | None) -> list[tuple[str, Path]]:
    versions = installed_versions()
    if not versions: return []
    hint = _normalized(version_hint); items = list(versions.items())

    def modified(item):
        try: return int(item[1].stat().st_mtime_ns)
        except OSError: return 0

    items.sort(key=lambda item: (modified(item), item[0].lower()), reverse=True)
    exact, related, rest = [], [], []
    for item in items:
        name = _normalized(item[0])
        if hint and name == hint: exact.append(item)
        elif hint and (hint in name or name in hint): related.append(item)
        else: rest.append(item)
    return exact + related + rest


@lru_cache(maxsize=256)
def _read_from_jar(jar_text: str, mtime_ns: int, size: int, kind: str) -> tuple[bytes | None, str | None]:
    paths = _TEXTURES.get(kind, ())
    if not paths: return None, None
    try:
        with zipfile.ZipFile(jar_text) as jar:
            names = set(jar.namelist())
            for member in paths:
                if member in names: return jar.read(member), member
    except (OSError, zipfile.BadZipFile, KeyError): pass
    return None, None


def texture_bytes(kind: str, version_hint: str = "") -> tuple[bytes | None, str | None, str | None]:
    """Return ``(PNG bytes, path in JAR, version)`` for an installed texture."""
    key = str(kind or "").lower()
    if key not in _TEXTURES: return None, None, None
    for version, jar in _version_order(version_hint):
        try: st = jar.stat()
        except OSError: continue
        data, member = _read_from_jar(str(jar.resolve()), int(st.st_mtime_ns), int(st.st_size), key)
        if data: return data, member, version
    return None, None, None


def clear_texture_cache() -> None:
    _read_from_jar.cache_clear()
