from __future__ import annotations

"""Canonical data-driven Minecraft simulation engines.

The mechanics implementation lives in :mod:`simulator_engine`; this module owns the
current source/data normalization and correctness policy.  It replaces the former
release-specific hardening layer, so direct callers and the desktop workbenches use the
same behavior without import-time mutation.
"""

import random
from typing import Any

from .simulator_engine import *  # noqa: F401,F403 - deliberate public compatibility surface
from .simulator_engine import (
    EnchantingEngine as _BaseEnchantingEngine,
    LootTableEngine as _BaseLootTableEngine,
    MinecraftJarData as _BaseMinecraftJarData,
    _provider_value,
)


class MinecraftJarData(_BaseMinecraftJarData):
    def item_tags(self) -> dict[str, list[str]]:
        raw = self.json_namespace(("data/minecraft/tags/item/", "data/minecraft/tags/items/"))
        out: dict[str, list[str]] = {}
        for key, value in raw.items():
            if not isinstance(value, dict) or not isinstance(value.get("values"), list):
                continue
            members: list[str] = []
            for member in value["values"]:
                item_id = member.get("id", "") if isinstance(member, dict) else member
                item_id = str(item_id)
                if item_id:
                    members.append(item_id)
            out[key] = members
        return out


def _resolve_item_tag(tags: dict[str, list[str]], tag_id: str, seen: set[str] | None = None) -> list[str]:
    tag_id = str(tag_id).removeprefix("#")
    if ":" not in tag_id:
        tag_id = "minecraft:" + tag_id
    seen = set() if seen is None else seen
    if tag_id in seen:
        return []
    seen.add(tag_id)
    out: list[str] = []
    for raw in tags.get(tag_id, []):
        value = str(raw)
        if value.startswith("#"):
            out.extend(_resolve_item_tag(tags, value, seen))
        elif value:
            out.append(value if ":" in value else "minecraft:" + value)
    return list(dict.fromkeys(out))


class LootTableEngine(_BaseLootTableEngine):
    def __init__(self, data: MinecraftJarData):
        self.data = data
        raw = data.json_namespace(("data/minecraft/loot_table/", "data/minecraft/loot_tables/"))
        self.using_baseline = not bool(raw)
        self.tables = (
            {key: value for key, value in raw.items() if isinstance(value, dict)}
            if raw else dict(FALLBACK_LOOT_TABLES)
        )
        self.tags = data.item_tags()

    @property
    def source(self) -> str:
        return "Bundled baseline examples" if self.using_baseline else self.data.source

    def _resolve_tag(self, tag_id: str, seen: set[str] | None = None) -> list[str]:
        return _resolve_item_tag(self.tags, tag_id, seen)

    def roll(self, table_id: str, *, rng=None, context=None, depth: int = 0):
        rng = rng or random.Random()
        context = dict(context or {})
        if depth > 12:
            return []
        table = self.tables.get(table_id)
        if not isinstance(table, dict):
            return []
        stacks: list[LootStack] = []
        for pool in table.get("pools", []):
            if not isinstance(pool, dict):
                continue
            if not all(self._condition_passes(condition, rng, context) for condition in pool.get("conditions", [])):
                continue
            rolls = max(0, int(round(_provider_value(pool.get("rolls", 1), rng))))
            for _ in range(rolls):
                eligible, weights = [], []
                for entry in pool.get("entries", []):
                    if not isinstance(entry, dict):
                        continue
                    if not all(self._condition_passes(condition, rng, context) for condition in entry.get("conditions", [])):
                        continue
                    weight = max(0.0, float(entry.get("weight", 1) or 1))
                    if weight > 0:
                        eligible.append(entry); weights.append(weight)
                if not eligible:
                    continue
                chosen = dict(rng.choices(eligible, weights=weights, k=1)[0])
                # Conditions determined entry eligibility above.  Removing them here is
                # deliberate: a random_chance predicate must not be sampled twice.
                chosen["conditions"] = []
                stacks.extend(self._entry_stacks(chosen, rng, context, depth + 1))
            stacks = self._apply_functions(stacks, pool.get("functions"), rng)
        stacks = self._apply_functions(stacks, table.get("functions"), rng)
        grouped: dict[tuple[str, str], int] = {}
        for stack in stacks:
            if stack.count <= 0:
                continue
            key = (stack.item, stack.detail)
            grouped[key] = grouped.get(key, 0) + stack.count
        return [LootStack(item, count, detail) for (item, detail), count in grouped.items()]


class EnchantingEngine(_BaseEnchantingEngine):
    def __init__(self, data: MinecraftJarData):
        self.data = data
        raw = data.json_namespace(("data/minecraft/enchantment/", "data/minecraft/enchantments/"))
        self.using_baseline = not bool(raw)
        self.enchantments = (
            {key: value for key, value in raw.items() if isinstance(value, dict)}
            if raw else {f"minecraft:{key}": dict(value) for key, value in FALLBACK_ENCHANTMENTS.items()}
        )
        self.tags = data.item_tags()
        self.treasure_enchantments: set[str] = set()
        raw_tags = data.json_namespace(("data/minecraft/tags/enchantment/", "data/minecraft/tags/enchantments/"))
        treasure = raw_tags.get("minecraft:treasure", {})
        if isinstance(treasure, dict):
            for member in treasure.get("values", []):
                value = member.get("id", "") if isinstance(member, dict) else member
                value = str(value)
                if value and not value.startswith("#"):
                    self.treasure_enchantments.add(value if ":" in value else "minecraft:" + value)
        if self.using_baseline:
            self.treasure_enchantments.update(
                enchant_id for enchant_id, definition in self.enchantments.items()
                if isinstance(definition, dict) and definition.get("treasure_only")
            )

    def roll_offers(self, item_id: str, bookshelves: int = 15, seed: int = 0, enchantability: int | None = None):
        offers = super().roll_offers(item_id, bookshelves, seed, enchantability)
        for offer in offers:
            offer["enchantments"] = [
                row for row in offer.get("enchantments", [])
                if row.get("id") not in self.treasure_enchantments
            ]
            if self.using_baseline:
                offer["source"] = "Bundled enchanting baseline"
        return offers


SIMULATOR_ICON_CANDIDATES = {
    "loot": ("assets/minecraft/textures/item/chest.png", "assets/minecraft/textures/block/chest_front.png"),
    "enchant": ("assets/minecraft/textures/item/enchanted_book.png", "assets/minecraft/textures/block/enchanting_table_top.png"),
    "anvil": ("assets/minecraft/textures/block/anvil.png", "assets/minecraft/textures/item/iron_ingot.png"),
    "brewing": ("assets/minecraft/textures/item/potion.png", "assets/minecraft/textures/block/brewing_stand.png"),
    "dye": ("assets/minecraft/textures/item/leather_chestplate.png", "assets/minecraft/textures/item/red_dye.png"),
    "animal": ("assets/minecraft/textures/item/wheat.png", "assets/minecraft/textures/item/golden_carrot.png"),
}
