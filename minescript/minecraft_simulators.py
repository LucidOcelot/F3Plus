from __future__ import annotations

"""Canonical data-driven Minecraft simulation engines.

Minecraft JSON namespaces are decoded in one cached ZIP pass per installed-JAR
fingerprint. This avoids reopening a large client JAR for every loot table/tag while
keeping the canonical correctness policy shared by GUI and direct callers.
"""

from functools import lru_cache
import json
import random
from typing import Any, Iterable
import zipfile

from .simulator_engine import *  # noqa: F401,F403 - deliberate public compatibility surface
from .simulator_engine import (
    AnimalBreedingEngine as _BaseAnimalBreedingEngine,
    EnchantingEngine as _BaseEnchantingEngine,
    LootTableEngine as _BaseLootTableEngine,
    MinecraftJarData as _BaseMinecraftJarData,
    _provider_value,
)
from .ux_semantics25 import STAT_BREEDING_SPECIES, enchantment_possibilities


@lru_cache(maxsize=48)
def _namespace_cache(path_text: str, mtime_ns: int, size: int, prefixes: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        with zipfile.ZipFile(path_text) as jar:
            for member in jar.namelist():
                prefix = next((p for p in prefixes if member.startswith(p) and member.endswith(".json")), None)
                if prefix is None:
                    continue
                try:
                    value = json.loads(jar.read(member).decode("utf-8"))
                except (KeyError, UnicodeDecodeError, json.JSONDecodeError):
                    continue
                rel = member[len(prefix):-5]
                out[f"minecraft:{rel}"] = value
    except (OSError, zipfile.BadZipFile):
        return {}
    return out


class MinecraftJarData(_BaseMinecraftJarData):
    def json_namespace(self, prefixes: Iterable[str]) -> dict[str, Any]:
        prefixes = tuple(str(prefix) for prefix in prefixes)
        if not self.jar_path or self._stat is None:
            return {}
        return dict(_namespace_cache(
            str(self.jar_path.resolve()), int(self._stat.st_mtime_ns), int(self._stat.st_size), prefixes
        ))

    @lru_cache(maxsize=1)
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


def _has_book_enchant_function(functions: Any) -> bool:
    if not isinstance(functions, list):
        return False
    for fn in functions:
        if not isinstance(fn, dict):
            continue
        name = str(fn.get("function", fn.get("type", ""))).removeprefix("minecraft:")
        if name in {"enchant_randomly", "enchant_with_levels", "set_enchantments"}:
            return True
        if name == "set_components":
            components = fn.get("components")
            if isinstance(components, dict) and any(str(key).endswith("stored_enchantments") for key in components):
                return True
    return False


class LootTableEngine(_BaseLootTableEngine):
    def __init__(self, data: MinecraftJarData):
        self.data = data
        raw = data.json_namespace(("data/minecraft/loot_table/", "data/minecraft/loot_tables/"))
        self.using_baseline = not bool(raw)
        self.tables = {key: value for key, value in raw.items() if isinstance(value, dict)} if raw else dict(FALLBACK_LOOT_TABLES)
        self.tags = data.item_tags()

    @property
    def source(self) -> str:
        return "Bundled baseline examples" if self.using_baseline else self.data.source

    def _resolve_tag(self, tag_id: str, seen: set[str] | None = None) -> list[str]:
        return _resolve_item_tag(self.tags, tag_id, seen)

    def _apply_functions(self, stacks, functions, rng):
        out = super()._apply_functions(stacks, functions, rng)
        if _has_book_enchant_function(functions):
            for stack in out:
                if stack.item in {"book", "minecraft:book"}:
                    stack.item = "minecraft:enchanted_book"
        return out

    def possible_items(self, table_id: str):
        rows = super().possible_items(table_id)
        merged: dict[str, dict[str, Any]] = {}
        for original in rows:
            row = dict(original)
            functions = str(row.get("functions", "")).lower()
            if row.get("item") in {"book", "minecraft:book"} and any(
                token in functions for token in ("enchant randomly", "enchant with levels", "set enchantments", "stored enchantments")
            ):
                row["item"] = "minecraft:enchanted_book"
            key = str(row.get("item", ""))
            if key not in merged:
                merged[key] = row
                continue
            current = merged[key]
            try:
                current["weight"] = float(current.get("weight", 0)) + float(row.get("weight", 0))
            except (TypeError, ValueError):
                pass
            for field in ("pools", "conditions", "functions"):
                parts = [
                    part.strip()
                    for source in (current.get(field, ""), row.get(field, ""))
                    for part in str(source).split(";")
                    if part.strip()
                ]
                current[field] = "; ".join(dict.fromkeys(parts))
        return sorted(merged.values(), key=lambda row: (-float(row.get("weight", 0) or 0), str(row.get("item", ""))))

    def roll(self, table_id: str, *, rng=None, context=None, depth: int = 0):
        rng = rng or random.Random(); context = dict(context or {})
        if depth > 12: return []
        table = self.tables.get(table_id)
        if not isinstance(table, dict): return []
        stacks: list[LootStack] = []
        for pool in table.get("pools", []):
            if not isinstance(pool, dict): continue
            if not all(self._condition_passes(condition, rng, context) for condition in pool.get("conditions", [])): continue
            rolls = max(0, int(round(_provider_value(pool.get("rolls", 1), rng))))
            for _ in range(rolls):
                eligible, weights = [], []
                for entry in pool.get("entries", []):
                    if not isinstance(entry, dict): continue
                    if not all(self._condition_passes(condition, rng, context) for condition in entry.get("conditions", [])): continue
                    weight = max(0.0, float(entry.get("weight", 1) or 1))
                    if weight > 0: eligible.append(entry); weights.append(weight)
                if not eligible: continue
                chosen = dict(rng.choices(eligible, weights=weights, k=1)[0])
                chosen["conditions"] = []
                stacks.extend(self._entry_stacks(chosen, rng, context, depth + 1))
            stacks = self._apply_functions(stacks, pool.get("functions"), rng)
        stacks = self._apply_functions(stacks, table.get("functions"), rng)
        grouped: dict[tuple[str, str], int] = {}
        for stack in stacks:
            if stack.count <= 0: continue
            key = (stack.item, stack.detail); grouped[key] = grouped.get(key, 0) + stack.count
        return [LootStack(item, count, detail) for (item, detail), count in grouped.items()]


class EnchantingEngine(_BaseEnchantingEngine):
    def __init__(self, data: MinecraftJarData):
        self.data = data
        raw = data.json_namespace(("data/minecraft/enchantment/", "data/minecraft/enchantments/"))
        self.using_baseline = not bool(raw)
        self.enchantments = {key: value for key, value in raw.items() if isinstance(value, dict)} if raw else {f"minecraft:{key}": dict(value) for key, value in FALLBACK_ENCHANTMENTS.items()}
        self.tags = data.item_tags(); self.treasure_enchantments: set[str] = set()
        raw_tags = data.json_namespace(("data/minecraft/tags/enchantment/", "data/minecraft/tags/enchantments/")); treasure = raw_tags.get("minecraft:treasure", {})
        if isinstance(treasure, dict):
            for member in treasure.get("values", []):
                value = member.get("id", "") if isinstance(member, dict) else member; value = str(value)
                if value and not value.startswith("#"): self.treasure_enchantments.add(value if ":" in value else "minecraft:" + value)
        if self.using_baseline:
            self.treasure_enchantments.update(enchant_id for enchant_id, definition in self.enchantments.items() if isinstance(definition, dict) and definition.get("treasure_only"))

    @staticmethod
    def _supported_values(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, (list, tuple, set)):
            out: list[str] = []
            for child in value:
                out.extend(EnchantingEngine._supported_values(child))
            return out
        if isinstance(value, dict):
            if "id" in value:
                return EnchantingEngine._supported_values(value.get("id"))
            if "tag" in value:
                return ["#" + str(value.get("tag", "")).removeprefix("#")]
            if "values" in value:
                return EnchantingEngine._supported_values(value.get("values"))
        return []

    def _supported(self, definition: dict[str, Any], item_id: str) -> bool:
        supported = definition.get("supported_items", definition.get("primary_items"))
        if supported is None:
            return True
        item = str(item_id); item = item if ":" in item else "minecraft:" + item
        values = self._supported_values(supported); saw_tag = False
        for value in values:
            if value.startswith("#"):
                saw_tag = True
                if item in _resolve_item_tag(self.tags, value):
                    return True
            else:
                normalized = value if ":" in value else "minecraft:" + value
                if normalized == item:
                    return True
        if saw_tag and not self.tags:
            return True
        return False

    def roll_offers(self, item_id: str, bookshelves: int = 15, seed: int = 0, enchantability: int | None = None):
        offers = super().roll_offers(item_id, bookshelves, seed, enchantability)
        for offer in offers:
            offer["enchantments"] = [row for row in offer.get("enchantments", []) if row.get("id") not in self.treasure_enchantments]
            if self.using_baseline: offer["source"] = "Bundled enchanting baseline"
        return offers

    def possible_book_enchantments(self) -> list[dict[str, Any]]:
        rows = enchantment_possibilities(self.enchantments, treasure=True)
        for row in rows:
            row["treasure_only"] = row["id"] in self.treasure_enchantments or bool(row.get("treasure_only"))
        return rows


class AnimalBreedingEngine(_BaseAnimalBreedingEngine):
    """Player-facing breeding model limited to inherited gameplay statistics."""

    @staticmethod
    def stat_species() -> list[str]:
        return list(STAT_BREEDING_SPECIES)

    def species(self) -> list[str]:
        return self.stat_species()

    def profile(self, species: str) -> dict[str, Any]:
        profile = super().profile(species)
        if species in self.stat_species():
            profile["stats"] = ["Max health", "Movement speed", "Jump strength"]
        return profile

    def simulate(self, species: str, parent_a: Any, parent_b: Any, children: int = 1000, seed: int = 0) -> dict[str, Any]:
        if species not in self.stat_species():
            raise ValueError(f"Breeding statistics are only modeled for: {', '.join(self.stat_species())}")
        result = self.horses.simulate(dict(parent_a or {}), dict(parent_b or {}), children, seed)
        result["species"] = species
        result["profile"] = self.profile(species)
        result["note"] = "Minimum, average, and maximum are calculated from the simulated offspring sample for inherited health, movement speed, and jump strength."
        return result


SIMULATOR_ICON_CANDIDATES = {
    "loot": ("assets/minecraft/textures/item/chest.png", "assets/minecraft/textures/block/chest_front.png"),
    "enchant": ("assets/minecraft/textures/item/enchanted_book.png", "assets/minecraft/textures/block/enchanting_table_top.png"),
    "anvil": ("assets/minecraft/textures/block/anvil.png", "assets/minecraft/textures/item/iron_ingot.png"),
    "brewing": ("assets/minecraft/textures/item/potion.png", "assets/minecraft/textures/block/brewing_stand.png"),
    "dye": ("assets/minecraft/textures/item/leather_chestplate.png", "assets/minecraft/textures/item/red_dye.png"),
    "animal": ("assets/minecraft/textures/item/wheat.png", "assets/minecraft/textures/item/golden_carrot.png"),
}
