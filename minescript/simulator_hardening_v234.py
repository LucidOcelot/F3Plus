from __future__ import annotations

"""Correctness hardening for data-driven Simulation Lab engines.

Kept separate from Qt so direct/library callers and unit tests receive the same source
labels, tag expansion, condition handling, and treasure-enchantment exclusions.
"""

import random
from typing import Any


def install() -> None:
    from .minecraft_simulators_v234 import (
        EnchantingEngine, FALLBACK_ENCHANTMENTS, FALLBACK_LOOT_TABLES,
        LootTableEngine, MinecraftJarData,
    )

    if getattr(LootTableEngine, "_hardening_v234_installed", False):
        return

    def normalized_item_tags(data: MinecraftJarData) -> dict[str, list[Any]]:
        raw_tags = data.json_namespace(("data/minecraft/tags/item/", "data/minecraft/tags/items/"))
        out: dict[str, list[Any]] = {}
        for tag_id, payload in raw_tags.items():
            if not isinstance(payload, dict) or not isinstance(payload.get("values"), list):
                continue
            values = []
            for raw in payload["values"]:
                if isinstance(raw, dict):
                    value = raw.get("id", "")
                else:
                    value = raw
                value = str(value)
                if value:
                    values.append(value)
            out[tag_id] = values
        return out

    # ---- source identity -------------------------------------------------
    def loot_init(self, data: MinecraftJarData):
        self.data = data
        raw = data.json_namespace(("data/minecraft/loot_table/", "data/minecraft/loot_tables/"))
        self.using_baseline = not bool(raw)
        self.tables = {key: value for key, value in raw.items() if isinstance(value, dict)} if raw else dict(FALLBACK_LOOT_TABLES)
        self.tags = normalized_item_tags(data)

    LootTableEngine.__init__ = loot_init
    LootTableEngine.source = property(lambda self: "Bundled baseline examples" if self.using_baseline else self.data.source)

    # Resolve nested tags and object-form tag members without ever exposing serialized
    # object text as a Minecraft identifier.
    def resolve_tag(self, tag_id: str, seen: set[str] | None = None) -> list[str]:
        tag_id = str(tag_id)
        if tag_id.startswith("#"):
            tag_id = tag_id[1:]
        if ":" not in tag_id:
            tag_id = "minecraft:" + tag_id
        seen = set() if seen is None else seen
        if tag_id in seen:
            return []
        seen.add(tag_id)
        out = []
        for raw in self.tags.get(tag_id, []):
            value = raw.get("id", "") if isinstance(raw, dict) else raw
            value = str(value)
            if not value:
                continue
            if value.startswith("#"):
                out.extend(resolve_tag(self, value, seen))
            else:
                out.append(value if ":" in value else "minecraft:" + value)
        return list(dict.fromkeys(out))

    LootTableEngine._resolve_tag = resolve_tag

    # Evaluate an entry's conditions once when deciding pool eligibility. The original
    # explorer then expanded the chosen entry and accidentally checked those same
    # random conditions a second time, squaring random-chance predicates.
    original_entry_stacks = LootTableEngine._entry_stacks

    def entry_stacks_without_recheck(self, entry: Any, rng: random.Random, context: dict[str, Any], depth: int = 0):
        if isinstance(entry, dict) and entry.pop("__f3plus_conditions_already_checked", False):
            entry = dict(entry)
            entry["conditions"] = []
        return original_entry_stacks(self, entry, rng, context, depth)

    LootTableEngine._entry_stacks = entry_stacks_without_recheck

    def roll(self, table_id: str, *, rng=None, context=None, depth: int = 0):
        # Reimplement only the top-level pool selection so the chosen entry can be
        # marked as already checked. Nested entry conditions remain evaluated by the
        # normal recursive expander exactly once.
        from .minecraft_simulators_v234 import _provider_value
        rng = rng or random.Random()
        context = dict(context or {})
        if depth > 12:
            return []
        table = self.tables.get(table_id)
        if not isinstance(table, dict):
            return []
        stacks = []
        for pool in table.get("pools", []):
            if not isinstance(pool, dict):
                continue
            if not all(self._condition_passes(cond, rng, context) for cond in pool.get("conditions", [])):
                continue
            rolls = max(0, int(round(_provider_value(pool.get("rolls", 1), rng))))
            for _ in range(rolls):
                eligible, weights = [], []
                for entry in pool.get("entries", []):
                    if not isinstance(entry, dict):
                        continue
                    if not all(self._condition_passes(cond, rng, context) for cond in entry.get("conditions", [])):
                        continue
                    weight = max(0.0, float(entry.get("weight", 1) or 1))
                    if weight > 0:
                        eligible.append(entry); weights.append(weight)
                if not eligible:
                    continue
                chosen = dict(rng.choices(eligible, weights=weights, k=1)[0])
                chosen["__f3plus_conditions_already_checked"] = True
                stacks.extend(self._entry_stacks(chosen, rng, context, depth + 1))
            stacks = self._apply_functions(stacks, pool.get("functions"), rng)
        stacks = self._apply_functions(stacks, table.get("functions"), rng)
        grouped = {}
        for stack in stacks:
            if stack.count <= 0:
                continue
            key = (stack.item, stack.detail)
            grouped[key] = grouped.get(key, 0) + stack.count
        stack_type = None
        for stack in stacks:
            stack_type = type(stack); break
        if stack_type is None:
            from .minecraft_simulators_v234 import LootStack
            stack_type = LootStack
        return [stack_type(item, count, detail) for (item, detail), count in grouped.items()]

    LootTableEngine.roll = roll

    # ---- enchanting registry ---------------------------------------------
    def enchantment_tag_values(data: MinecraftJarData, tag_name: str) -> set[str]:
        tags = data.json_namespace(("data/minecraft/tags/enchantment/", "data/minecraft/tags/enchantments/"))
        target = tags.get("minecraft:" + tag_name, {})
        values = target.get("values", []) if isinstance(target, dict) else []
        out = set()
        for raw in values:
            value = raw.get("id", "") if isinstance(raw, dict) else raw
            value = str(value)
            if value and not value.startswith("#"):
                out.add(value if ":" in value else "minecraft:" + value)
        return out

    def enchanting_init(self, data: MinecraftJarData):
        self.data = data
        raw = data.json_namespace(("data/minecraft/enchantment/", "data/minecraft/enchantments/"))
        self.using_baseline = not bool(raw)
        self.enchantments = {key: value for key, value in raw.items() if isinstance(value, dict)} if raw else {f"minecraft:{key}": dict(value) for key, value in FALLBACK_ENCHANTMENTS.items()}
        self.tags = normalized_item_tags(data)
        self.treasure_enchantments = enchantment_tag_values(data, "treasure")
        if self.using_baseline:
            self.treasure_enchantments.update(
                enchant_id for enchant_id, definition in self.enchantments.items()
                if isinstance(definition, dict) and definition.get("treasure_only")
            )

    EnchantingEngine.__init__ = enchanting_init
    original_roll_offers = EnchantingEngine.roll_offers

    def roll_offers(self, item_id: str, bookshelves: int = 15, seed: int = 0, enchantability: int | None = None):
        offers = original_roll_offers(self, item_id, bookshelves, seed, enchantability)
        # The base implementation already excludes fallback treasure_only definitions.
        # Installed registries encode treasure status in an enchantment tag, so remove
        # any such offer and leave the slot otherwise unchanged rather than ever
        # suggesting Mending/other treasure enchants from a normal table.
        for offer in offers:
            offer["enchantments"] = [row for row in offer.get("enchantments", []) if row.get("id") not in self.treasure_enchantments]
            if self.using_baseline:
                offer["source"] = "Bundled enchanting baseline"
        return offers

    EnchantingEngine.roll_offers = roll_offers

    LootTableEngine._hardening_v234_installed = True
    EnchantingEngine._hardening_v234_installed = True
