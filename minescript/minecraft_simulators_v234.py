from __future__ import annotations

"""Data-driven/offline simulation engines for F3+ mechanic explorers.

The preferred source is the player's installed Minecraft Java JAR. Loot tables, item
item-tags, enchantment definitions, and textures are read at runtime and are never
redistributed. Small first-party baseline datasets keep every simulator usable when a
client JAR is unavailable; every result exposes its source/exactness so a baseline is
never mistaken for selected-version game data.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
import json
import math
import random
from pathlib import Path
from typing import Any, Iterable
import zipfile

from .villagers import installed_versions


# ---------------------------------------------------------------------------
# Installed Java data access
# ---------------------------------------------------------------------------


def _norm(value: str | None) -> str:
    return str(value or "").strip().lower().replace(" ", "-")


def _jar_candidates(version_hint: str = "") -> list[tuple[str, Path]]:
    hint = _norm(version_hint)
    rows = list(installed_versions().items())

    def modified(row):
        try:
            return row[1].stat().st_mtime_ns
        except OSError:
            return 0

    rows.sort(key=lambda row: (modified(row), row[0].lower()), reverse=True)
    exact, related, rest = [], [], []
    for row in rows:
        name = _norm(row[0])
        if hint and name == hint:
            exact.append(row)
        elif hint and (hint in name or name in hint):
            related.append(row)
        else:
            rest.append(row)
    return exact + related + rest


@lru_cache(maxsize=12)
def _jar_index(path_text: str, mtime_ns: int, size: int) -> tuple[str, ...]:
    try:
        with zipfile.ZipFile(path_text) as jar:
            return tuple(jar.namelist())
    except (OSError, zipfile.BadZipFile):
        return ()


@lru_cache(maxsize=4096)
def _jar_member(path_text: str, mtime_ns: int, size: int, member: str) -> bytes | None:
    try:
        with zipfile.ZipFile(path_text) as jar:
            return jar.read(member)
    except (OSError, zipfile.BadZipFile, KeyError):
        return None


class MinecraftJarData:
    def __init__(self, version_hint: str = ""):
        self.version_hint = str(version_hint or "")
        candidates = _jar_candidates(self.version_hint)
        self.version = candidates[0][0] if candidates else ""
        self.jar_path = candidates[0][1] if candidates else None
        self._stat = None
        if self.jar_path is not None:
            try:
                self._stat = self.jar_path.stat()
            except OSError:
                self.jar_path = None
        self.source = f"Installed Minecraft {self.version}" if self.jar_path else "Bundled baseline reference"
        self.exact_local_data = bool(self.jar_path and _norm(self.version) == _norm(self.version_hint))

    def _members(self) -> tuple[str, ...]:
        if not self.jar_path or self._stat is None:
            return ()
        return _jar_index(str(self.jar_path.resolve()), int(self._stat.st_mtime_ns), int(self._stat.st_size))

    def read_bytes(self, member: str) -> bytes | None:
        if not self.jar_path or self._stat is None:
            return None
        return _jar_member(
            str(self.jar_path.resolve()), int(self._stat.st_mtime_ns), int(self._stat.st_size), str(member)
        )

    def read_json(self, member: str) -> Any:
        raw = self.read_bytes(member)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    def json_namespace(self, prefixes: Iterable[str]) -> dict[str, Any]:
        prefixes = tuple(str(prefix) for prefix in prefixes)
        out: dict[str, Any] = {}
        for member in self._members():
            prefix = next((p for p in prefixes if member.startswith(p) and member.endswith(".json")), None)
            if prefix is None:
                continue
            value = self.read_json(member)
            if value is None:
                continue
            rel = member[len(prefix):-5]
            out[f"minecraft:{rel}"] = value
        return out

    def loot_tables(self) -> dict[str, dict[str, Any]]:
        tables = self.json_namespace(("data/minecraft/loot_table/", "data/minecraft/loot_tables/"))
        return {key: value for key, value in tables.items() if isinstance(value, dict)} or dict(FALLBACK_LOOT_TABLES)

    def item_tags(self) -> dict[str, list[str]]:
        raw = self.json_namespace(("data/minecraft/tags/item/", "data/minecraft/tags/items/"))
        out = {}
        for key, value in raw.items():
            if isinstance(value, dict) and isinstance(value.get("values"), list):
                out[key] = [str(item) for item in value["values"]]
        return out

    def enchantments(self) -> dict[str, dict[str, Any]]:
        rows = self.json_namespace(("data/minecraft/enchantment/", "data/minecraft/enchantments/"))
        clean = {key: value for key, value in rows.items() if isinstance(value, dict)}
        return clean or {f"minecraft:{key}": dict(value) for key, value in FALLBACK_ENCHANTMENTS.items()}

    def texture_bytes(self, candidates: Iterable[str]) -> tuple[bytes | None, str | None]:
        names = set(self._members())
        for member in candidates:
            if member not in names:
                continue
            data = self.read_bytes(member)
            if data:
                return data, member
        return None, None


# ---------------------------------------------------------------------------
# Loot tables
# ---------------------------------------------------------------------------


def _item(name: str, weight: int = 1, count: Any = 1, **extra) -> dict[str, Any]:
    row: dict[str, Any] = {"type": "minecraft:item", "name": f"minecraft:{name}", "weight": weight}
    if count != 1:
        row["functions"] = [{"function": "minecraft:set_count", "count": count}]
    row.update(extra)
    return row


FALLBACK_LOOT_TABLES: dict[str, dict[str, Any]] = {
    "minecraft:chests/simple_dungeon": {
        "pools": [
            {"rolls": {"min": 1, "max": 3}, "entries": [_item("saddle", 20), _item("golden_apple", 15), _item("enchanted_golden_apple", 2), _item("music_disc_13", 15), _item("music_disc_cat", 15), _item("name_tag", 20)]},
            {"rolls": 3, "entries": [_item("iron_ingot", 10, {"min": 1, "max": 4}), _item("gold_ingot", 5, {"min": 1, "max": 4}), _item("bread", 20), _item("wheat", 20, {"min": 1, "max": 4}), _item("gunpowder", 20, {"min": 1, "max": 4}), _item("string", 20, {"min": 1, "max": 4}), _item("bucket", 10), _item("redstone", 15, {"min": 1, "max": 4})]},
        ]
    },
    "minecraft:entities/zombie": {
        "pools": [
            {"rolls": 1, "entries": [_item("rotten_flesh", 1, {"min": 0, "max": 2})]},
            {"rolls": 1, "entries": [_item("iron_ingot", 1), _item("carrot", 1), _item("potato", 1), {"type": "minecraft:empty", "weight": 97}]},
        ]
    },
    "minecraft:gameplay/fishing": {
        "pools": [{"rolls": 1, "entries": [
            {"type": "minecraft:loot_table", "value": "minecraft:gameplay/fishing/fish", "weight": 85},
            {"type": "minecraft:loot_table", "value": "minecraft:gameplay/fishing/junk", "weight": 10},
            {"type": "minecraft:loot_table", "value": "minecraft:gameplay/fishing/treasure", "weight": 5},
        ]}]
    },
    "minecraft:gameplay/fishing/fish": {"pools": [{"rolls": 1, "entries": [_item("cod", 60), _item("salmon", 25), _item("pufferfish", 13), _item("tropical_fish", 2)]}]},
    "minecraft:gameplay/fishing/junk": {"pools": [{"rolls": 1, "entries": [_item("lily_pad", 17), _item("bowl", 10), _item("fishing_rod", 2), _item("leather", 10), _item("leather_boots", 10), _item("rotten_flesh", 10), _item("stick", 5), _item("string", 5), _item("potion", 10), _item("bone", 10), _item("ink_sac", 1, 10), _item("tripwire_hook", 10)]}]},
    "minecraft:gameplay/fishing/treasure": {"pools": [{"rolls": 1, "entries": [_item("name_tag"), _item("saddle"), _item("bow"), _item("fishing_rod"), _item("enchanted_book"), _item("nautilus_shell")]}]},
    "minecraft:gameplay/piglin_bartering": {"pools": [{"rolls": 1, "entries": [
        _item("enchanted_book", 5), _item("iron_boots", 8), _item("potion", 8), _item("splash_potion", 8), _item("water_bottle", 10), _item("iron_nugget", 10, {"min": 10, "max": 36}), _item("ender_pearl", 10, {"min": 2, "max": 4}), _item("string", 20, {"min": 3, "max": 9}), _item("quartz", 20, {"min": 5, "max": 12}), _item("obsidian", 40), _item("crying_obsidian", 40, {"min": 1, "max": 3}), _item("fire_charge", 40), _item("leather", 40, {"min": 2, "max": 4}), _item("soul_sand", 40, {"min": 2, "max": 8}), _item("nether_brick", 40, {"min": 2, "max": 8}), _item("spectral_arrow", 40, {"min": 6, "max": 12}), _item("gravel", 40, {"min": 8, "max": 16}), _item("blackstone", 40, {"min": 8, "max": 16}),
    ]}]},
    "minecraft:archaeology/desert_well": {"pools": [{"rolls": 1, "entries": [_item("arms_up_pottery_sherd", 1), _item("brewer_pottery_sherd", 1), _item("brick", 2), _item("emerald", 2), _item("stick", 2), _item("suspicious_stew", 1)]}]},
    "minecraft:spawners/trial_chamber/reward": {"pools": [{"rolls": 1, "entries": [_item("trial_key", 5), _item("emerald", 20, {"min": 1, "max": 4}), _item("diamond", 5), _item("golden_carrot", 10, {"min": 1, "max": 3}), _item("arrow", 20, {"min": 2, "max": 8}), _item("iron_ingot", 20, {"min": 1, "max": 4})]}]},
    "minecraft:blocks/diamond_ore": {"pools": [{"rolls": 1, "entries": [_item("diamond", 1)]}]},
}


def loot_category(table_id: str) -> str:
    path = str(table_id).split(":", 1)[-1]
    if path.startswith("chests/"):
        return "Chests"
    if path.startswith("entities/"):
        return "Entity drops"
    if path.startswith("blocks/"):
        return "Block drops"
    if "fishing" in path:
        return "Fishing"
    if "piglin" in path or "barter" in path:
        return "Piglin bartering"
    if path.startswith("archaeology/"):
        return "Archaeology"
    if "trial" in path or path.startswith("spawners/"):
        return "Trial / spawner rewards"
    if path.startswith("equipment/"):
        return "Equipment"
    return path.split("/", 1)[0].replace("_", " ").title()


def _provider_value(value: Any, rng: random.Random, default: float = 1.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        if isinstance(value.get("value"), (int, float)):
            return float(value["value"])
        low = value.get("min", value.get("min_inclusive", value.get("min_value")))
        high = value.get("max", value.get("max_inclusive", value.get("max_value")))
        if isinstance(low, (int, float)) and isinstance(high, (int, float)):
            return rng.uniform(float(low), float(high))
        if str(value.get("type", "")).endswith("constant"):
            raw = value.get("value", value.get("constant", default))
            if isinstance(raw, (int, float)):
                return float(raw)
    return float(default)


def _provider_range(value: Any) -> tuple[float, float]:
    if isinstance(value, (int, float)):
        return float(value), float(value)
    if isinstance(value, dict):
        if isinstance(value.get("value"), (int, float)):
            v = float(value["value"])
            return v, v
        low = value.get("min", value.get("min_inclusive", value.get("min_value")))
        high = value.get("max", value.get("max_inclusive", value.get("max_value")))
        if isinstance(low, (int, float)) and isinstance(high, (int, float)):
            return float(low), float(high)
    return 1.0, 1.0


def _condition_label(condition: Any) -> str:
    if not isinstance(condition, dict):
        return str(condition)
    kind = str(condition.get("condition", condition.get("type", "condition"))).removeprefix("minecraft:")
    if kind == "random_chance":
        return f"random chance {condition.get('chance', '?')}"
    if kind == "killed_by_player":
        return "killed by player"
    return kind.replace("_", " ")


def _functions_label(functions: Any) -> str:
    if not isinstance(functions, list):
        return ""
    labels = []
    for fn in functions:
        if not isinstance(fn, dict):
            continue
        kind = str(fn.get("function", "function")).removeprefix("minecraft:").replace("_", " ")
        if kind == "set count":
            lo, hi = _provider_range(fn.get("count", 1))
            labels.append(f"count {lo:g}–{hi:g}" if lo != hi else f"count {lo:g}")
        elif kind in {"set potion", "set components", "set custom data", "enchant randomly", "enchant with levels"}:
            labels.append(kind)
        else:
            labels.append(kind)
    return ", ".join(labels)


@dataclass
class LootStack:
    item: str
    count: int = 1
    detail: str = ""


class LootTableEngine:
    def __init__(self, data: MinecraftJarData):
        self.data = data
        self.tables = data.loot_tables()
        self.tags = data.item_tags()

    @property
    def source(self) -> str:
        return self.data.source if self.data.jar_path else "Bundled baseline examples"

    def table_ids(self, category: str = "", query: str = "") -> list[str]:
        query = str(query or "").lower().strip()
        rows = []
        for table_id in sorted(self.tables):
            if category and category != "All" and loot_category(table_id) != category:
                continue
            if query and query not in table_id.lower() and query not in loot_category(table_id).lower():
                continue
            rows.append(table_id)
        return rows

    def categories(self) -> list[str]:
        return ["All"] + sorted({loot_category(table_id) for table_id in self.tables})

    def _resolve_tag(self, tag_id: str, seen: set[str] | None = None) -> list[str]:
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
        for value in self.tags.get(tag_id, []):
            value = str(value)
            if value.startswith("#"):
                out.extend(self._resolve_tag(value, seen))
            else:
                out.append(value if ":" in value else "minecraft:" + value)
        return list(dict.fromkeys(out))

    def possible_items(self, table_id: str) -> list[dict[str, Any]]:
        aggregate: dict[str, dict[str, Any]] = {}
        visiting: set[str] = set()

        def record(item_id: str, weight: float, pool_index: int, entry: dict[str, Any], count_value: Any = 1):
            key = str(item_id)
            row = aggregate.setdefault(key, {
                "item": key,
                "weight": 0.0,
                "pools": set(),
                "count_min": math.inf,
                "count_max": -math.inf,
                "conditions": set(),
                "functions": set(),
            })
            row["weight"] += max(0.0, float(weight))
            row["pools"].add(pool_index + 1)
            lo, hi = _provider_range(count_value)
            row["count_min"] = min(row["count_min"], lo)
            row["count_max"] = max(row["count_max"], hi)
            for condition in entry.get("conditions", []) if isinstance(entry, dict) else []:
                row["conditions"].add(_condition_label(condition))
            label = _functions_label(entry.get("functions", [])) if isinstance(entry, dict) else ""
            if label:
                row["functions"].add(label)

        def count_from(entry: dict[str, Any]):
            for fn in entry.get("functions", []) if isinstance(entry, dict) else []:
                if isinstance(fn, dict) and str(fn.get("function", "")).endswith("set_count"):
                    return fn.get("count", 1)
            return 1

        def walk_entry(entry: Any, pool_index: int, inherited_weight: float = 1.0):
            if not isinstance(entry, dict):
                return
            kind = str(entry.get("type", "minecraft:item")).removeprefix("minecraft:")
            weight = inherited_weight * float(entry.get("weight", 1) or 1)
            if kind == "item":
                item_id = str(entry.get("name", entry.get("item", "minecraft:unknown")))
                record(item_id, weight, pool_index, entry, count_from(entry))
                return
            if kind == "tag":
                tag_id = str(entry.get("name", entry.get("tag", "")))
                items = self._resolve_tag(tag_id)
                each = weight / max(1, len(items))
                for item_id in items or [f"#{tag_id.removeprefix('#')}"]:
                    record(item_id, each, pool_index, entry, count_from(entry))
                return
            if kind == "loot_table":
                value = entry.get("value", entry.get("name", ""))
                ref = str(value.get("id", "")) if isinstance(value, dict) else str(value)
                if ref and ref not in visiting:
                    walk_table(ref if ":" in ref else "minecraft:" + ref, inherited_weight=weight)
                return
            if kind == "dynamic":
                record(f"dynamic:{entry.get('name', 'loot')}", weight, pool_index, entry, count_from(entry))
                return
            children = entry.get("children", entry.get("entries", []))
            if isinstance(children, list):
                for child in children:
                    walk_entry(child, pool_index, weight)

        def walk_table(ref: str, inherited_weight: float = 1.0):
            if ref in visiting:
                return
            table = self.tables.get(ref)
            if not isinstance(table, dict):
                return
            visiting.add(ref)
            for pool_index, pool in enumerate(table.get("pools", [])):
                if not isinstance(pool, dict):
                    continue
                for entry in pool.get("entries", []):
                    walk_entry(entry, pool_index, inherited_weight)
            visiting.remove(ref)

        walk_table(table_id)
        rows = []
        for row in aggregate.values():
            lo = 1 if row["count_min"] is math.inf else row["count_min"]
            hi = 1 if row["count_max"] is -math.inf else row["count_max"]
            rows.append({
                "item": row["item"],
                "weight": row["weight"],
                "pools": ", ".join(map(str, sorted(row["pools"]))),
                "count": f"{lo:g}" if lo == hi else f"{lo:g}–{hi:g}",
                "conditions": "; ".join(sorted(row["conditions"])) or "None/entry-context",
                "functions": "; ".join(sorted(row["functions"])) or "None",
            })
        rows.sort(key=lambda row: (-row["weight"], row["item"]))
        return rows

    def _condition_passes(self, condition: Any, rng: random.Random, context: dict[str, Any]) -> bool:
        if not isinstance(condition, dict):
            return True
        kind = str(condition.get("condition", condition.get("type", ""))).removeprefix("minecraft:")
        if kind == "random_chance":
            return rng.random() < float(condition.get("chance", 1.0))
        if kind == "killed_by_player":
            return bool(context.get("killed_by_player", True))
        if kind == "inverted":
            return not self._condition_passes(condition.get("term"), rng, context)
        if kind in {"all_of", "any_of"}:
            terms = condition.get("terms", [])
            checks = [self._condition_passes(term, rng, context) for term in terms]
            return all(checks) if kind == "all_of" else any(checks)
        # Loot contexts such as location, entity equipment, tool predicates, luck,
        # weather, scores, and datapack predicates cannot be reconstructed from a
        # table alone. The explorer's default inclusive context keeps such branches
        # visible; users can still see the condition in the possible-loot table.
        return bool(context.get("include_contextual_entries", True))

    def _apply_functions(self, stacks: list[LootStack], functions: Any, rng: random.Random) -> list[LootStack]:
        if not isinstance(functions, list):
            return stacks
        out = [LootStack(stack.item, stack.count, stack.detail) for stack in stacks]
        for fn in functions:
            if not isinstance(fn, dict):
                continue
            kind = str(fn.get("function", "")).removeprefix("minecraft:")
            if kind == "set_count":
                count = max(0, int(round(_provider_value(fn.get("count", 1), rng))))
                for stack in out:
                    stack.count = count
            elif kind == "limit_count":
                limit = fn.get("limit", {})
                low = limit.get("min", limit.get("min_inclusive")) if isinstance(limit, dict) else None
                high = limit.get("max", limit.get("max_inclusive")) if isinstance(limit, dict) else None
                for stack in out:
                    if isinstance(low, (int, float)):
                        stack.count = max(stack.count, int(low))
                    if isinstance(high, (int, float)):
                        stack.count = min(stack.count, int(high))
            elif kind == "set_potion":
                potion = fn.get("id", fn.get("potion", "potion"))
                for stack in out:
                    stack.detail = (stack.detail + f"; potion={potion}").strip("; ")
            elif kind in {"enchant_randomly", "enchant_with_levels"}:
                for stack in out:
                    stack.detail = (stack.detail + f"; {kind.replace('_', ' ')}").strip("; ")
            elif kind in {"set_components", "set_custom_data", "set_name"}:
                for stack in out:
                    stack.detail = (stack.detail + f"; {kind.replace('_', ' ')}").strip("; ")
        return out

    def _entry_stacks(self, entry: Any, rng: random.Random, context: dict[str, Any], depth: int = 0) -> list[LootStack]:
        if depth > 12 or not isinstance(entry, dict):
            return []
        if not all(self._condition_passes(cond, rng, context) for cond in entry.get("conditions", [])):
            return []
        kind = str(entry.get("type", "minecraft:item")).removeprefix("minecraft:")
        stacks: list[LootStack]
        if kind == "item":
            stacks = [LootStack(str(entry.get("name", entry.get("item", "minecraft:unknown"))), 1)]
        elif kind == "empty":
            stacks = []
        elif kind == "tag":
            choices = self._resolve_tag(str(entry.get("name", entry.get("tag", ""))))
            stacks = [LootStack(rng.choice(choices), 1)] if choices else []
        elif kind == "loot_table":
            value = entry.get("value", entry.get("name", ""))
            ref = str(value.get("id", "")) if isinstance(value, dict) else str(value)
            stacks = self.roll(ref if ":" in ref else "minecraft:" + ref, rng=rng, context=context, depth=depth + 1)
        elif kind == "alternatives":
            stacks = []
            for child in entry.get("children", []):
                candidate = self._entry_stacks(child, rng, context, depth + 1)
                if candidate:
                    stacks = candidate
                    break
        elif kind in {"group", "sequence"}:
            stacks = []
            for child in entry.get("children", []):
                stacks.extend(self._entry_stacks(child, rng, context, depth + 1))
        elif kind == "dynamic":
            stacks = [LootStack(f"dynamic:{entry.get('name', 'loot')}", 1, "runtime dynamic drop")]
        else:
            stacks = []
            for child in entry.get("children", entry.get("entries", [])):
                stacks.extend(self._entry_stacks(child, rng, context, depth + 1))
        return self._apply_functions(stacks, entry.get("functions"), rng)

    def roll(self, table_id: str, *, rng: random.Random | None = None, context: dict[str, Any] | None = None, depth: int = 0) -> list[LootStack]:
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
            if not all(self._condition_passes(cond, rng, context) for cond in pool.get("conditions", [])):
                continue
            rolls = max(0, int(round(_provider_value(pool.get("rolls", 1), rng))))
            for _ in range(rolls):
                eligible = []
                weights = []
                for entry in pool.get("entries", []):
                    if not isinstance(entry, dict):
                        continue
                    if not all(self._condition_passes(cond, rng, context) for cond in entry.get("conditions", [])):
                        continue
                    weight = max(0.0, float(entry.get("weight", 1) or 1))
                    if weight > 0:
                        eligible.append(entry)
                        weights.append(weight)
                if not eligible:
                    continue
                chosen = rng.choices(eligible, weights=weights, k=1)[0]
                stacks.extend(self._entry_stacks(chosen, rng, context, depth + 1))
            stacks = self._apply_functions(stacks, pool.get("functions"), rng)
        stacks = self._apply_functions(stacks, table.get("functions"), rng)
        grouped: dict[tuple[str, str], int] = defaultdict(int)
        for stack in stacks:
            if stack.count > 0:
                grouped[(stack.item, stack.detail)] += stack.count
        return [LootStack(item, count, detail) for (item, detail), count in grouped.items()]

    def simulate(self, table_id: str, pulls: int = 1000, seed: int = 0, context: dict[str, Any] | None = None) -> dict[str, Any]:
        pulls = max(1, min(1_000_000, int(pulls)))
        rng = random.Random(int(seed))
        hits = Counter()
        totals = Counter()
        examples = []
        for index in range(pulls):
            stacks = self.roll(table_id, rng=rng, context=context)
            seen = set()
            for stack in stacks:
                totals[stack.item] += stack.count
                seen.add(stack.item)
            hits.update(seen)
            if index < 30:
                examples.append([{"item": stack.item, "count": stack.count, "detail": stack.detail} for stack in stacks])
        possible = {row["item"] for row in self.possible_items(table_id)}
        possible.update(totals)
        stats = []
        for item_id in sorted(possible, key=lambda item: (-hits[item], item)):
            stats.append({
                "item": item_id,
                "pulls_with_item": hits[item_id],
                "observed_hit_rate": hits[item_id] / pulls,
                "total_items": totals[item_id],
                "mean_items_per_pull": totals[item_id] / pulls,
            })
        return {
            "table": table_id,
            "source": self.source,
            "pulls": pulls,
            "seed": int(seed),
            "stats": stats,
            "examples": examples,
            "context_note": "Unknown/context-only loot predicates are treated as eligible so every possible branch remains explorable; random_chance and killed_by_player predicates are simulated directly.",
        }


# ---------------------------------------------------------------------------
# Enchanting + anvil
# ---------------------------------------------------------------------------


FALLBACK_ENCHANTMENTS: dict[str, dict[str, Any]] = {
    "protection": {"weight": 10, "max_level": 4, "min_cost": {"base": 1, "per_level_above_first": 11}, "max_cost": {"base": 12, "per_level_above_first": 11}, "anvil_cost": 1, "supported_items": "#minecraft:enchantable/armor"},
    "feather_falling": {"weight": 5, "max_level": 4, "min_cost": {"base": 5, "per_level_above_first": 6}, "max_cost": {"base": 11, "per_level_above_first": 6}, "anvil_cost": 2, "supported_items": "#minecraft:enchantable/foot_armor"},
    "sharpness": {"weight": 10, "max_level": 5, "min_cost": {"base": 1, "per_level_above_first": 11}, "max_cost": {"base": 21, "per_level_above_first": 11}, "anvil_cost": 1, "supported_items": "#minecraft:enchantable/sharp_weapon"},
    "efficiency": {"weight": 10, "max_level": 5, "min_cost": {"base": 1, "per_level_above_first": 10}, "max_cost": {"base": 51, "per_level_above_first": 10}, "anvil_cost": 1, "supported_items": "#minecraft:enchantable/mining"},
    "unbreaking": {"weight": 5, "max_level": 3, "min_cost": {"base": 5, "per_level_above_first": 8}, "max_cost": {"base": 55, "per_level_above_first": 8}, "anvil_cost": 2, "supported_items": "#minecraft:enchantable/durability"},
    "fortune": {"weight": 2, "max_level": 3, "min_cost": {"base": 15, "per_level_above_first": 9}, "max_cost": {"base": 65, "per_level_above_first": 9}, "anvil_cost": 4, "supported_items": "#minecraft:enchantable/mining_loot"},
    "silk_touch": {"weight": 1, "max_level": 1, "min_cost": {"base": 15, "per_level_above_first": 0}, "max_cost": {"base": 65, "per_level_above_first": 0}, "anvil_cost": 8, "supported_items": "#minecraft:enchantable/mining_loot"},
    "mending": {"weight": 2, "max_level": 1, "min_cost": {"base": 25, "per_level_above_first": 0}, "max_cost": {"base": 75, "per_level_above_first": 0}, "anvil_cost": 4, "supported_items": "#minecraft:enchantable/durability", "treasure_only": True},
    "power": {"weight": 10, "max_level": 5, "min_cost": {"base": 1, "per_level_above_first": 10}, "max_cost": {"base": 16, "per_level_above_first": 10}, "anvil_cost": 1, "supported_items": "#minecraft:enchantable/bow"},
    "infinity": {"weight": 1, "max_level": 1, "min_cost": {"base": 20, "per_level_above_first": 0}, "max_cost": {"base": 50, "per_level_above_first": 0}, "anvil_cost": 8, "supported_items": "#minecraft:enchantable/bow"},
    "looting": {"weight": 2, "max_level": 3, "min_cost": {"base": 15, "per_level_above_first": 9}, "max_cost": {"base": 65, "per_level_above_first": 9}, "anvil_cost": 4, "supported_items": "#minecraft:enchantable/sword"},
}


def _cost_component(value: Any, level: int) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, dict):
        base = value.get("base", value.get("base_cost", 1))
        per = value.get("per_level_above_first", value.get("per_level", 0))
        if isinstance(base, (int, float)) and isinstance(per, (int, float)):
            return int(base + max(0, level - 1) * per)
    return 1


def _enchantability(item_id: str) -> int:
    item = str(item_id).removeprefix("minecraft:")
    if item == "book":
        return 1
    if item.startswith("golden_"):
        return 22 if any(token in item for token in ("helmet", "chestplate", "leggings", "boots")) else 22
    if item.startswith("wooden_"):
        return 15
    if item.startswith("stone_"):
        return 5
    if item.startswith("iron_"):
        return 9 if any(token in item for token in ("pickaxe", "axe", "shovel", "hoe", "sword")) else 9
    if item.startswith("diamond_"):
        return 10
    if item.startswith("netherite_"):
        return 15
    if item.startswith("leather_"):
        return 15
    if item.startswith("chainmail_"):
        return 12
    if item in {"bow", "crossbow", "fishing_rod", "trident"}:
        return 1
    return 10


class EnchantingEngine:
    def __init__(self, data: MinecraftJarData):
        self.data = data
        self.enchantments = data.enchantments()
        self.tags = data.item_tags()

    def _supported(self, definition: dict[str, Any], item_id: str) -> bool:
        supported = definition.get("supported_items", definition.get("primary_items"))
        if supported is None:
            return True
        item_id = item_id if ":" in item_id else "minecraft:" + item_id
        values = supported if isinstance(supported, list) else [supported]
        for value in values:
            if not isinstance(value, str):
                continue
            if value.startswith("#"):
                tag_id = value[1:]
                if ":" not in tag_id:
                    tag_id = "minecraft:" + tag_id
                if item_id in self.tags.get(tag_id, []):
                    return True
                # Baseline/fallback tags are not expanded without local tag data.
                if not self.tags:
                    return True
            else:
                normalized = value if ":" in value else "minecraft:" + value
                if normalized == item_id:
                    return True
        return False

    def _candidate_level(self, definition: dict[str, Any], power: int) -> int:
        max_level = max(1, int(definition.get("max_level", 1)))
        min_cost = definition.get("min_cost", 1)
        max_cost = definition.get("max_cost", 1000)
        for level in range(max_level, 0, -1):
            if _cost_component(min_cost, level) <= power <= _cost_component(max_cost, level):
                return level
        return 0

    @staticmethod
    def slot_costs(bookshelves: int, seed: int) -> list[int]:
        shelves = max(0, min(15, int(bookshelves)))
        rng = random.Random(int(seed))
        base = rng.randint(1, 8) + shelves // 2 + rng.randint(0, shelves)
        return [max(base // 3, 1), base * 2 // 3 + 1, max(base, shelves * 2)]

    def roll_offers(self, item_id: str, bookshelves: int = 15, seed: int = 0, enchantability: int | None = None) -> list[dict[str, Any]]:
        enchantability = _enchantability(item_id) if enchantability is None else max(1, int(enchantability))
        costs = self.slot_costs(bookshelves, seed)
        offers = []
        for slot, cost in enumerate(costs, start=1):
            rng = random.Random((int(seed) << 3) ^ slot ^ 0x5DEECE66D)
            bonus = rng.randint(0, max(0, enchantability // 4)) + rng.randint(0, max(0, enchantability // 4)) + 1
            power = cost + bonus
            power = max(1, int(round(power * (1.0 + (rng.random() + rng.random() - 1.0) * 0.15))))
            candidates = []
            for enchant_id, definition in self.enchantments.items():
                if not isinstance(definition, dict) or definition.get("treasure_only"):
                    continue
                if not self._supported(definition, item_id):
                    continue
                level = self._candidate_level(definition, power)
                if level <= 0:
                    continue
                candidates.append((enchant_id, level, max(1, int(definition.get("weight", 1)))))
            selected = []
            working = list(candidates)
            current_power = power
            while working:
                choice = rng.choices(working, weights=[row[2] for row in working], k=1)[0]
                selected.append({"id": choice[0], "level": choice[1]})
                working = [row for row in working if row[0] != choice[0]]
                current_power //= 2
                if not working or rng.randrange(50) > current_power:
                    break
            offers.append({
                "slot": slot,
                "displayed_cost": cost,
                "lapis_cost": slot,
                "levels_spent": slot,
                "modified_power": power,
                "enchantability": enchantability,
                "enchantments": selected,
                "source": self.data.source if self.data.jar_path else "Bundled enchanting baseline",
            })
        return offers

    def enchantment_rows(self, item_id: str = "") -> list[dict[str, Any]]:
        rows = []
        for enchant_id, definition in sorted(self.enchantments.items()):
            if not isinstance(definition, dict):
                continue
            if item_id and not self._supported(definition, item_id):
                continue
            rows.append({
                "id": enchant_id,
                "weight": definition.get("weight", 1),
                "max_level": definition.get("max_level", 1),
                "anvil_cost": definition.get("anvil_cost", "?"),
                "supported_items": definition.get("supported_items", definition.get("primary_items", "data-defined")),
                "treasure_only": bool(definition.get("treasure_only", False)),
            })
        return rows


class AnvilEngine:
    def __init__(self, enchanting: EnchantingEngine):
        self.enchanting = enchanting

    @staticmethod
    def prior_work_penalty(operations: int) -> int:
        operations = max(0, int(operations))
        return (1 << operations) - 1 if operations else 0

    def combine(
        self,
        item_id: str,
        left_enchants: dict[str, int] | None,
        right_enchants: dict[str, int] | None,
        left_prior_operations: int = 0,
        right_prior_operations: int = 0,
        rename: bool = False,
    ) -> dict[str, Any]:
        left = dict(left_enchants or {})
        right = dict(right_enchants or {})
        result = dict(left)
        enchant_cost = 0
        changes = []
        for enchant_id, incoming_level in right.items():
            definition = self.enchanting.enchantments.get(enchant_id, self.enchanting.enchantments.get("minecraft:" + enchant_id, {}))
            definition = definition if isinstance(definition, dict) else {}
            key = enchant_id if enchant_id in self.enchanting.enchantments else ("minecraft:" + enchant_id if "minecraft:" + enchant_id in self.enchanting.enchantments else enchant_id)
            current = int(result.get(key, result.get(enchant_id, 0)))
            incoming = max(1, int(incoming_level))
            max_level = max(1, int(definition.get("max_level", max(current, incoming, 1))))
            merged = min(max_level, current + 1 if current == incoming else max(current, incoming))
            result.pop(enchant_id, None)
            result[key] = merged
            multiplier = max(1, int(definition.get("anvil_cost", 1)))
            delta = max(1, merged - current)
            enchant_cost += multiplier * delta
            changes.append({"enchantment": key, "from": current, "incoming": incoming, "result": merged, "anvil_multiplier": multiplier})
        left_penalty = self.prior_work_penalty(left_prior_operations)
        right_penalty = self.prior_work_penalty(right_prior_operations)
        rename_cost = 1 if rename else 0
        total = left_penalty + right_penalty + enchant_cost + rename_cost
        new_prior_operations = max(int(left_prior_operations), int(right_prior_operations)) + 1
        return {
            "item": item_id,
            "result_enchantments": result,
            "changes": changes,
            "left_prior_penalty": left_penalty,
            "right_prior_penalty": right_penalty,
            "enchantment_cost": enchant_cost,
            "rename_cost": rename_cost,
            "total_level_cost": total,
            "survival_too_expensive": total >= 40,
            "new_prior_operations": new_prior_operations,
            "new_prior_work_penalty": self.prior_work_penalty(new_prior_operations),
            "source": self.enchanting.data.source if self.enchanting.data.jar_path else "Bundled anvil-cost baseline",
            "note": "Anvil enchantment weights use the installed enchantment definition's anvil_cost when available. Item repair-material and durability-merging costs are outside this planner unless explicitly entered as enchantment/rename work.",
        }


# ---------------------------------------------------------------------------
# Brewing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PotionState:
    potion: str
    effect: str
    duration_seconds: int | None
    amplifier: int = 0
    bottle: str = "potion"


BASE_POTIONS: dict[str, PotionState] = {
    "water": PotionState("water", "None", None),
    "awkward": PotionState("awkward", "None — brewing base", None),
    "mundane": PotionState("mundane", "None", None),
    "thick": PotionState("thick", "None", None),
    "swiftness": PotionState("swiftness", "Speed", 180),
    "leaping": PotionState("leaping", "Jump Boost", 180),
    "healing": PotionState("healing", "Instant Health", 0),
    "poison": PotionState("poison", "Poison", 45),
    "water_breathing": PotionState("water_breathing", "Water Breathing", 180),
    "fire_resistance": PotionState("fire_resistance", "Fire Resistance", 180),
    "night_vision": PotionState("night_vision", "Night Vision", 180),
    "strength": PotionState("strength", "Strength", 180),
    "regeneration": PotionState("regeneration", "Regeneration", 45),
    "turtle_master": PotionState("turtle_master", "Slowness IV + Resistance III", 20),
    "slow_falling": PotionState("slow_falling", "Slow Falling", 90),
    "weakness": PotionState("weakness", "Weakness", 90),
    "invisibility": PotionState("invisibility", "Invisibility", 180),
    "slowness": PotionState("slowness", "Slowness", 90),
    "harming": PotionState("harming", "Instant Damage", 0),
    "wind_charged": PotionState("wind_charged", "Wind Charged", 180),
    "weaving": PotionState("weaving", "Weaving", 180),
    "oozing": PotionState("oozing", "Oozing", 180),
    "infested": PotionState("infested", "Infested", 180),
}

AWKWARD_RECIPES = {
    "sugar": "swiftness", "rabbit_foot": "leaping", "glistering_melon_slice": "healing",
    "spider_eye": "poison", "pufferfish": "water_breathing", "magma_cream": "fire_resistance",
    "golden_carrot": "night_vision", "blaze_powder": "strength", "ghast_tear": "regeneration",
    "turtle_helmet": "turtle_master", "phantom_membrane": "slow_falling", "breeze_rod": "wind_charged",
    "cobweb": "weaving", "slime_block": "oozing", "stone": "infested",
}
CORRUPT_RECIPES = {"night_vision": "invisibility", "swiftness": "slowness", "leaping": "slowness", "healing": "harming", "poison": "harming"}
EXTENDABLE = {"swiftness", "leaping", "poison", "water_breathing", "fire_resistance", "night_vision", "strength", "regeneration", "slow_falling", "weakness", "invisibility", "slowness", "wind_charged", "weaving", "oozing", "infested"}
STRONG = {"swiftness", "leaping", "healing", "poison", "strength", "regeneration", "harming", "turtle_master"}


class BrewingEngine:
    def ingredients(self) -> list[str]:
        return sorted(set(AWKWARD_RECIPES) | {"nether_wart", "fermented_spider_eye", "redstone", "glowstone_dust", "gunpowder", "dragon_breath"})

    def brew(self, input_state: PotionState | str, ingredient: str) -> dict[str, Any]:
        state = BASE_POTIONS.get(input_state, PotionState(str(input_state), str(input_state), None)) if isinstance(input_state, str) else input_state
        ingredient = str(ingredient).removeprefix("minecraft:")
        result = state
        note = "No valid vanilla transition for this combination."
        if state.potion == "water" and ingredient == "nether_wart":
            result = BASE_POTIONS["awkward"]
            note = "Water Bottle + Nether Wart → Awkward Potion."
        elif state.potion == "water" and ingredient == "fermented_spider_eye":
            result = BASE_POTIONS["weakness"]
            note = "Water Bottle can brew directly into Weakness with Fermented Spider Eye."
        elif state.potion == "awkward" and ingredient in AWKWARD_RECIPES:
            result = BASE_POTIONS[AWKWARD_RECIPES[ingredient]]
            note = f"Awkward Potion + {ingredient.replace('_', ' ').title()} → {result.potion.replace('_', ' ').title()}."
        elif ingredient == "fermented_spider_eye" and state.potion in CORRUPT_RECIPES:
            result = BASE_POTIONS[CORRUPT_RECIPES[state.potion]]
            note = f"Fermented Spider Eye corrupts {state.potion.replace('_', ' ')} into {result.potion.replace('_', ' ')}."
        elif ingredient == "redstone" and state.potion in EXTENDABLE and state.duration_seconds:
            result = PotionState(state.potion, state.effect, max(state.duration_seconds + 1, int(round(state.duration_seconds * 8 / 3))), state.amplifier, state.bottle)
            note = "Redstone extends the potion duration."
        elif ingredient == "glowstone_dust" and state.potion in STRONG:
            duration = 0 if state.duration_seconds == 0 else (max(1, int(round((state.duration_seconds or 1) / 2))))
            result = PotionState(state.potion, state.effect, duration, state.amplifier + 1, state.bottle)
            note = "Glowstone increases effect strength and shortens timed effects."
        elif ingredient == "gunpowder" and state.bottle == "potion":
            result = PotionState(state.potion, state.effect, state.duration_seconds, state.amplifier, "splash_potion")
            note = "Gunpowder converts the potion to a splash potion."
        elif ingredient == "dragon_breath" and state.bottle == "splash_potion":
            result = PotionState(state.potion, state.effect, state.duration_seconds, state.amplifier, "lingering_potion")
            note = "Dragon's Breath converts a splash potion to a lingering potion."
        return {"input": state, "ingredient": ingredient, "output": result, "changed": result != state, "note": note, "source": "F3+ vanilla brewing-rule baseline (brewing recipes are code-defined rather than normal datapack recipes)."}


# ---------------------------------------------------------------------------
# Leather dye + cauldron
# ---------------------------------------------------------------------------


DYE_COLORS = {
    "white": 0xF9FFFE, "orange": 0xF9801D, "magenta": 0xC74EBD, "light_blue": 0x3AB3DA,
    "yellow": 0xFED83D, "lime": 0x80C71F, "pink": 0xF38BAA, "gray": 0x474F52,
    "light_gray": 0x9D9D97, "cyan": 0x169C9C, "purple": 0x8932B8, "blue": 0x3C44AA,
    "brown": 0x835432, "green": 0x5E7C16, "red": 0xB02E26, "black": 0x1D1D21,
}
LEATHER_DEFAULT = 0xA06540


def mix_leather_colors(colors: Iterable[int]) -> int:
    values = [int(value) & 0xFFFFFF for value in colors]
    if not values:
        return LEATHER_DEFAULT
    r_total = g_total = b_total = max_total = 0
    for color in values:
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        r_total += r; g_total += g; b_total += b
        max_total += max(r, g, b)
    count = len(values)
    r = r_total // count; g = g_total // count; b = b_total // count
    average_max = max_total / count
    current_max = max(1, r, g, b)
    scale = average_max / current_max
    r = min(255, int(r * scale)); g = min(255, int(g * scale)); b = min(255, int(b * scale))
    return (r << 16) | (g << 8) | b


def dye_mix(existing_color: int | None, dyes: Iterable[str]) -> dict[str, Any]:
    colors = []
    if existing_color is not None:
        colors.append(int(existing_color) & 0xFFFFFF)
    valid = []
    for dye in dyes:
        key = str(dye).removeprefix("minecraft:").removesuffix("_dye")
        if key in DYE_COLORS:
            valid.append(key)
            colors.append(DYE_COLORS[key])
    result = mix_leather_colors(colors)
    return {"dyes": valid, "rgb": ((result >> 16) & 0xFF, (result >> 8) & 0xFF, result & 0xFF), "hex": f"#{result:06X}", "decimal": result}


def cauldron_wash(water_level: int, dyed: bool = True) -> dict[str, Any]:
    level = max(0, min(3, int(water_level)))
    if not dyed:
        return {"water_before": level, "water_after": level, "washed": False, "reason": "The leather item is not dyed."}
    if level <= 0:
        return {"water_before": 0, "water_after": 0, "washed": False, "reason": "A water cauldron level is required."}
    return {"water_before": level, "water_after": level - 1, "washed": True, "result_color": f"#{LEATHER_DEFAULT:06X}", "reason": "Java Edition cauldrons wash dyed leather and consume one water level; dye mixing itself is performed through leather dyeing/crafting, not colored cauldron water."}


# ---------------------------------------------------------------------------
# Animal / horse breeding + NBT planning
# ---------------------------------------------------------------------------


BREEDABLE_ANIMALS: dict[str, dict[str, Any]] = {
    "Horse": {"food": "Golden Carrot / Golden Apple", "nbt": "Variant, Health, attributes", "mode": "horse"},
    "Donkey": {"food": "Golden Carrot / Golden Apple", "nbt": "Health, attributes, ChestedHorse", "mode": "horse"},
    "Cow": {"food": "Wheat", "nbt": "Age", "mode": "parent_variant"},
    "Mooshroom": {"food": "Wheat", "nbt": "Type, Age", "mode": "parent_variant"},
    "Sheep": {"food": "Wheat", "nbt": "Color, Sheared, Age", "mode": "sheep"},
    "Pig": {"food": "Carrot / Potato / Beetroot", "nbt": "Age", "mode": "parent_variant"},
    "Chicken": {"food": "Seeds", "nbt": "Age, EggLayTime", "mode": "parent_variant"},
    "Rabbit": {"food": "Carrot / Golden Carrot / Dandelion", "nbt": "RabbitType, Age", "mode": "rabbit"},
    "Wolf": {"food": "Meat", "nbt": "variant, CollarColor, Age", "mode": "parent_variant"},
    "Cat": {"food": "Raw Cod / Raw Salmon", "nbt": "variant, CollarColor, Age", "mode": "parent_variant"},
    "Ocelot": {"food": "Raw Cod / Raw Salmon", "nbt": "Age", "mode": "parent_variant"},
    "Fox": {"food": "Sweet Berries / Glow Berries", "nbt": "Type, Trusted, Age", "mode": "parent_variant"},
    "Panda": {"food": "Bamboo", "nbt": "MainGene, HiddenGene, Age", "mode": "panda"},
    "Bee": {"food": "Flowers", "nbt": "HasNectar, HasStung, Age", "mode": "parent_variant"},
    "Goat": {"food": "Wheat", "nbt": "IsScreamingGoat, HasLeftHorn, HasRightHorn, Age", "mode": "parent_variant"},
    "Hoglin": {"food": "Crimson Fungus", "nbt": "CannotBeHunted, Age", "mode": "parent_variant"},
    "Strider": {"food": "Warped Fungus", "nbt": "Saddle, Age", "mode": "parent_variant"},
    "Llama": {"food": "Hay Bale", "nbt": "Variant, Strength, Age", "mode": "parent_variant"},
    "Trader Llama": {"food": "Hay Bale", "nbt": "Variant, Strength, Age", "mode": "parent_variant"},
    "Axolotl": {"food": "Bucket of Tropical Fish", "nbt": "Variant, Age", "mode": "axolotl"},
    "Frog": {"food": "Slimeball", "nbt": "variant, Age", "mode": "environment"},
    "Camel": {"food": "Cactus", "nbt": "LastPoseTick, Age", "mode": "parent_variant"},
    "Armadillo": {"food": "Spider Eye", "nbt": "state, Age", "mode": "parent_variant"},
    "Sniffer": {"food": "Torchflower Seeds", "nbt": "Age; breeding produces an egg", "mode": "egg"},
    "Turtle": {"food": "Seagrass", "nbt": "HomePosX/Y/Z; breeding produces eggs", "mode": "egg"},
}

SHEEP_MIX = {
    frozenset((0, 14)): 6,   # white + red -> pink
    frozenset((14, 11)): 10, # red + blue -> purple
    frozenset((14, 4)): 1,   # red + yellow -> orange
    frozenset((11, 15)): 7,  # blue + white -> light gray is not a recipe; fallback parent if absent
    frozenset((4, 11)): 13,  # yellow + blue -> green
}


def _json_parent(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not str(value or "").strip():
        return {}
    parsed = json.loads(str(value))
    if not isinstance(parsed, dict):
        raise ValueError("Parent NBT must be a JSON object")
    return parsed


def _parent_pick(a: dict[str, Any], b: dict[str, Any], key: str, rng: random.Random, default=None):
    choices = [parent.get(key) for parent in (a, b) if key in parent]
    return rng.choice(choices) if choices else default


def modern_horse_attribute(parent_a: float, parent_b: float, minimum: float, maximum: float, rng: random.Random) -> float:
    """Modern vanilla-style reflected triangular offspring attribute formula.

    Minecraft moved away from the old unrelated-third-parent average. The current
    family of implementations centers the roll on the parents, widens it by their
    difference plus 15% boundary padding, averages three random samples, and reflects
    out-of-range values back into the legal range.
    """
    a = max(minimum, min(maximum, float(parent_a)))
    b = max(minimum, min(maximum, float(parent_b)))
    padding = 0.15 * (maximum - minimum)
    spread = abs(a - b) + 2.0 * padding
    center = (a + b) / 2.0
    offset = ((rng.random() + rng.random() + rng.random()) / 3.0) - 0.5
    value = center + spread * offset
    if value > maximum:
        value = maximum - (value - maximum)
    if value < minimum:
        value = minimum + (minimum - value)
    return max(minimum, min(maximum, value))


class HorseBreedingEngine:
    LIMITS = {
        "max_health": (15.0, 30.0),
        "movement_speed": (0.1125, 0.3375),
        "jump_strength": (0.4, 1.0),
    }

    def child(self, parent_a: dict[str, Any], parent_b: dict[str, Any], rng: random.Random) -> dict[str, Any]:
        attrs = {}
        for key, (minimum, maximum) in self.LIMITS.items():
            a = float(parent_a.get(key, (minimum + maximum) / 2.0))
            b = float(parent_b.get(key, (minimum + maximum) / 2.0))
            attrs[key] = modern_horse_attribute(a, b, minimum, maximum, rng)
        color_a = int(parent_a.get("color", 0)) % 7
        color_b = int(parent_b.get("color", 0)) % 7
        mark_a = int(parent_a.get("markings", 0)) % 5
        mark_b = int(parent_b.get("markings", 0)) % 5
        color_roll = rng.randrange(9)
        color = color_a if color_roll < 4 else color_b if color_roll < 8 else rng.randrange(7)
        mark_roll = rng.randrange(5)
        markings = mark_a if mark_roll < 2 else mark_b if mark_roll < 4 else rng.randrange(5)
        variant = color | (markings << 8)
        return {
            **attrs,
            "color": color,
            "markings": markings,
            "Variant": variant,
            "Age": -24000,
            "Health": attrs["max_health"],
            "Attributes": [
                {"Name": "minecraft:generic.max_health", "Base": attrs["max_health"]},
                {"Name": "minecraft:generic.movement_speed", "Base": attrs["movement_speed"]},
                {"Name": "minecraft:horse.jump_strength", "Base": attrs["jump_strength"]},
            ],
        }

    def simulate(self, parent_a: dict[str, Any], parent_b: dict[str, Any], children: int = 1000, seed: int = 0) -> dict[str, Any]:
        children = max(1, min(100_000, int(children)))
        rng = random.Random(int(seed))
        rows = [self.child(parent_a, parent_b, rng) for _ in range(children)]
        stats = {}
        for key in self.LIMITS:
            values = [row[key] for row in rows]
            stats[key] = {"minimum": min(values), "mean": sum(values) / len(values), "maximum": max(values)}
        variants = Counter(row["Variant"] for row in rows)
        return {"children": children, "seed": int(seed), "stats": stats, "variant_counts": dict(variants.most_common()), "examples": rows[:25], "model": "Modern vanilla-style parent-centered reflected triangular attribute roll; coat/markings use parent-biased inheritance with mutation rolls."}


class AnimalBreedingEngine:
    def __init__(self):
        self.horses = HorseBreedingEngine()

    def species(self) -> list[str]:
        return list(BREEDABLE_ANIMALS)

    def profile(self, species: str) -> dict[str, Any]:
        return dict(BREEDABLE_ANIMALS.get(species, {}))

    def child(self, species: str, parent_a: Any, parent_b: Any, seed: int = 0) -> dict[str, Any]:
        a = _json_parent(parent_a); b = _json_parent(parent_b)
        rng = random.Random(int(seed))
        profile = BREEDABLE_ANIMALS.get(species)
        if profile is None:
            raise ValueError(f"Unknown breedable animal: {species}")
        mode = profile.get("mode")
        if mode == "horse":
            # Accept either compact simulator fields or NBT-ish attribute aliases.
            def compact(parent):
                out = dict(parent)
                attrs = parent.get("Attributes", [])
                if isinstance(attrs, list):
                    for row in attrs:
                        if not isinstance(row, dict):
                            continue
                        name = str(row.get("Name", row.get("id", "")))
                        base = row.get("Base", row.get("base"))
                        if not isinstance(base, (int, float)):
                            continue
                        if "max_health" in name: out.setdefault("max_health", base)
                        elif "movement_speed" in name: out.setdefault("movement_speed", base)
                        elif "jump_strength" in name: out.setdefault("jump_strength", base)
                variant = int(parent.get("Variant", 0))
                out.setdefault("color", variant & 0xFF)
                out.setdefault("markings", (variant >> 8) & 0xFF)
                return out
            return self.horses.child(compact(a), compact(b), rng)
        if mode == "egg":
            return {"breeding_result": "Egg", "Age": None, "Parents": [a, b], "note": f"{species} breeding produces egg placement/hatching rather than an immediate baby entity."}
        child: dict[str, Any] = {"Age": -24000, "InLove": 0}
        if mode == "sheep":
            color_a = int(a.get("Color", 0)); color_b = int(b.get("Color", 0))
            child["Color"] = SHEEP_MIX.get(frozenset((color_a, color_b)), rng.choice([color_a, color_b]))
            child["Sheared"] = False
        elif mode == "axolotl":
            if rng.randrange(1200) == 0:
                child["Variant"] = 4
            else:
                child["Variant"] = int(rng.choice([a.get("Variant", 0), b.get("Variant", 0)]))
        elif mode == "rabbit":
            child["RabbitType"] = int(rng.choice([a.get("RabbitType", 0), b.get("RabbitType", 0)]))
        elif mode == "panda":
            genes_a = [a.get("MainGene", "normal"), a.get("HiddenGene", "normal")]
            genes_b = [b.get("MainGene", "normal"), b.get("HiddenGene", "normal")]
            child["MainGene"] = rng.choice(genes_a)
            child["HiddenGene"] = rng.choice(genes_b)
            if rng.randrange(32) == 0:
                child[rng.choice(["MainGene", "HiddenGene"])] = rng.choice(["normal", "lazy", "worried", "playful", "brown", "weak", "aggressive"])
        elif mode == "environment":
            child["variant"] = _parent_pick(a, b, "variant", rng, "environment-determined")
            child["note"] = "Frog variant can be determined by the temperature where the tadpole matures; parent NBT alone cannot fully determine it."
        else:
            for key in ("Variant", "variant", "Type", "CollarColor", "IsScreamingGoat", "Strength"):
                value = _parent_pick(a, b, key, rng, None)
                if value is not None:
                    child[key] = value
        child["simulation_profile"] = species
        return child

    def simulate(self, species: str, parent_a: Any, parent_b: Any, children: int = 100, seed: int = 0) -> dict[str, Any]:
        children = max(1, min(100_000, int(children)))
        rows = [self.child(species, parent_a, parent_b, seed + index * 7919) for index in range(children)]
        fingerprints = Counter(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows)
        return {
            "species": species,
            "profile": self.profile(species),
            "children": children,
            "unique_outcomes": len(fingerprints),
            "most_common_outcomes": [{"count": count, "nbt": json.loads(raw)} for raw, count in fingerprints.most_common(20)],
            "examples": rows[:25],
            "note": "NBT fields shown are the breeding-relevant subset F3+ models. Runtime-only UUIDs, positions, brain memories, timers, and unrelated entity state are intentionally omitted.",
        }
