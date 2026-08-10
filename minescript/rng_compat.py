from __future__ import annotations

"""Compatibility RNG models built on the canonical Java RNG implementation.

Historical operation names still resolve here when no newer domain model handles them.
The module intentionally contains no installer or monkey-patching entry point.
"""

import hashlib
from collections import Counter
from typing import Any

from .seed.java_rng import JavaRandom


def _seed(value: Any) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        text = str(value or "")
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big", signed=False)


def _selected_mc(executor, params: dict[str, Any]) -> int:
    from .world.versioning import resolve_cubiomes_mc

    if "mc" in params and params["mc"] not in (None, ""):
        return int(params["mc"])
    selected = getattr(executor, "minecraft_version", "26.3-snapshot-7") if executor else "26.3-snapshot-7"
    return resolve_cubiomes_mc(str(selected))


def _parse_weights(text: Any) -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    for token in str(text or "").split(";"):
        if ":" not in token:
            continue
        label, raw = token.split(":", 1)
        try:
            weight = float(raw.strip())
        except ValueError:
            continue
        if label.strip() and weight > 0:
            rows.append((label.strip(), weight))
    return rows


def _loot_profile(name: str):
    profiles = {
        "Fishing Loot Simulator": [("fish", 0.85), ("treasure", 0.05), ("junk", 0.10)],
        "Piglin Barter Simulator": [("common barter", 0.75), ("uncommon barter", 0.20), ("rare barter", 0.05)],
        "Mob Drop Simulator": [("no special drop", 0.75), ("common drop", 0.20), ("rare drop", 0.05)],
        "Archaeology Loot Simulator": [("common archaeology", 0.70), ("uncommon archaeology", 0.22), ("rare archaeology", 0.08)],
        "Trial Chamber Loot Simulator": [("common reward", 0.66), ("uncommon reward", 0.27), ("rare reward", 0.07)],
        "Trial Spawner Reward Simulator": [("common reward", 0.70), ("uncommon reward", 0.24), ("rare reward", 0.06)],
        "Structure Loot Simulator": [("common structure loot", 0.70), ("uncommon structure loot", 0.23), ("rare structure loot", 0.07)],
    }
    return profiles.get(name)


def _weighted_pick(rng: JavaRandom, rows: list[tuple[str, float]]) -> str:
    roll = rng.next_double() * sum(weight for _, weight in rows)
    total = 0.0
    for label, weight in rows:
        total += weight
        if roll <= total:
            return label
    return rows[-1][0]


def _weighted_table(name: str, p: dict[str, Any], seed: int, attempts: int):
    rows = _parse_weights(p.get("entries", "common:70;uncommon:23;rare:7"))
    if not rows:
        return {"available": False, "reason": "Enter weighted entries as label:weight separated by semicolons."}
    rng = JavaRandom(seed); counts = Counter({label: 0 for label, _ in rows}); first = []
    total = sum(weight for _, weight in rows)
    for index in range(attempts):
        value = _weighted_pick(rng, rows); counts[value] += 1
        if index < 50: first.append(value)
    return {
        "operation": name,
        "purpose": "Simulate a user-supplied weighted table rather than a hidden generic rarity profile",
        "rng": "java.util.Random compatible preview",
        "seed": seed,
        "entries": [{"label": label, "weight": weight, "normalized_percent": round(weight / total * 100, 4)} for label, weight in rows],
        "rolls": attempts,
        "results": [{"label": label, "count": counts[label], "observed_percent": round(counts[label] / attempts * 100, 4)} for label, _ in rows],
        "first_results": first,
        "note": "Weights are supplied by the user. Use the installed-table Loot Explorer when exact selected-version loot behavior is required.",
    }


def rng_tool(name: str, p: dict[str, Any], executor=None) -> dict[str, Any] | None:
    seed = _seed(p.get("seed", 12345))
    attempts = max(1, min(100000, int(p.get("attempts", 20))))

    if name == "Loot Table Simulator":
        return _weighted_table(name, p, seed, attempts)

    profile = _loot_profile(name)
    if profile:
        rng = JavaRandom(seed); counts: dict[str, int] = {label: 0 for label, _ in profile}; first = []
        for index in range(attempts):
            value = _weighted_pick(rng, profile); counts[value] += 1
            if index < 128: first.append(value)
        return {
            "operation": name,
            "rng": "java.util.Random compatible preview",
            "seed": seed,
            "attempts": attempts,
            "profile": dict(profile),
            "counts": counts,
            "rates": {key: value / attempts for key, value in counts.items()},
            "first_results": first,
            "note": "Category-level probability preview. Use the installed-table explorer for exact per-item selected-version loot.",
        }

    chunk_x = int(p.get("cx", 0)); chunk_z = int(p.get("cz", 0)); mixed_seed = seed + chunk_x * 341873128712 + chunk_z * 132897987541; rng = JavaRandom(mixed_seed)

    if name in {"Decoration RNG", "Decoration RNG Preview"}:
        rows = [{"index": index, "roll": rng.next_float()} for index in range(attempts)]
        return {"operation": name, "purpose": "Inspect deterministic decoration-stage random draws", "world_seed": seed, "chunk": (chunk_x, chunk_z), "draws": rows}

    if name in {"Feature Placement RNG", "Feature Placement RNG Preview"}:
        min_y = int(p.get("min_y", -64)); max_y = int(p.get("max_y", 319))
        if max_y < min_y: min_y, max_y = max_y, min_y
        span = max(1, max_y - min_y + 1)
        rows = [{"index": index, "x": chunk_x * 16 + rng.next_int(16), "y": min_y + rng.next_int(span), "z": chunk_z * 16 + rng.next_int(16)} for index in range(attempts)]
        return {"operation": name, "purpose": "Preview raw deterministic candidate positions", "world_seed": seed, "chunk": (chunk_x, chunk_z), "candidate_positions": rows, "note": "Candidate RNG positions do not guarantee final feature placement."}

    if name == "Ore Placement Simulator":
        min_y = int(p.get("min_y", -64)); max_y = int(p.get("max_y", 64))
        if max_y < min_y: min_y, max_y = max_y, min_y
        span = max(1, max_y - min_y + 1); rows = []
        for _ in range(attempts):
            y = min_y + (rng.next_int(span) + rng.next_int(span)) // 2
            rows.append((chunk_x * 16 + rng.next_int(16), y, chunk_z * 16 + rng.next_int(16)))
        return {"operation": name, "world_seed": seed, "chunk": (chunk_x, chunk_z), "height_provider": "triangle", "range": (min_y, max_y), "candidate_positions": rows, "note": "This is a candidate-position RNG model, not an exact ore-vein reconstruction."}

    if name in {"Tree Generation Simulator", "Geode Generator", "Geode Placement Simulator"}:
        chance = max(0.0, min(1.0, float(p.get("probability", 0.05)))); rows = []
        for _ in range(attempts):
            roll = rng.next_float(); rows.append({"x": chunk_x * 16 + rng.next_int(16), "z": chunk_z * 16 + rng.next_int(16), "placed": roll < chance, "roll": roll})
        return {"operation": name, "world_seed": seed, "chunk": (chunk_x, chunk_z), "configured_chance": chance, "attempts": rows, "note": "This models a supplied placement chance; final vanilla placement may have additional configured predicates."}

    if name in {"Trial Chamber Generation", "Structure Placement Preview"}:
        from . import restored_features
        target = "Trial Chamber" if name == "Trial Chamber Generation" else str(p.get("structure", "Village")); mc = _selected_mc(executor, p)
        return {"operation": name, **restored_features.structure_candidates(target, seed, chunk_x, chunk_z, int(p.get("radius", 64)), mc=mc)}
    return None
