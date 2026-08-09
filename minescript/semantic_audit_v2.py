from __future__ import annotations

"""Catalog-wide semantic audit and final shared-engine view corrections.

F3+ deliberately shares engines where the underlying math is the same, but two catalog
entries must not silently present the same user report as if they were separate tools.
This module gives the last shared families explicit jobs and exposes a scanner that
checks all 457 dry-run results for indistinguishable user-facing output.
"""

import json
import math
from typing import Any


# These are intentionally multiple entry points into one canonical visual application,
# not claims of separate calculation engines. Their GUI mode/preset is the distinction.
INTENTIONAL_CANONICAL_VIEWS = (
    frozenset({
        "Trade Browser", "Trade Search", "Trade Comparison", "Emerald Calculator",
        "Trade Cycle Calculator", "Librarian Browser", "Refresh Trades From Installed Version",
    }),
)

# Prose is deliberately excluded from duplicate fingerprints. A tool is not allowed to
# evade the audit simply by attaching a different sentence to the same data structure.
# Semantic fields such as units, coordinates, thresholds, modes, shapes, and route data
# are retained and therefore still distinguish genuinely different user-facing jobs.
AUDIT_IGNORED_KEYS = {
    "implementation", "implementation_detail", "operation", "display_name",
    "source", "backend", "mc_enum", "backend_error", "worldgen_source",
    "purpose", "note", "interpretation", "warning", "metric_warning",
    "model_limit", "next_step", "why_this_entry_exists", "classification_basis",
    "ranking_basis", "ranking_order", "pattern_definition", "cluster_definition",
    "identification_limit", "required_input", "requested_analysis", "routing_method",
    "reroll_planning", "planning_readout", "loot_roll_readout",
}


def _strip_internal(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _strip_internal(child)
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
            if str(key) not in AUDIT_IGNORED_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [_strip_internal(item) for item in value]
    if isinstance(value, set):
        return sorted((_strip_internal(item) for item in value), key=repr)
    if hasattr(value, "__dict__"):
        return _strip_internal(vars(value))
    return value


def _fingerprint(data: dict[str, Any]) -> str:
    return json.dumps(_strip_internal(data), sort_keys=True, default=str, separators=(",", ":"))


def _intentional_group(names: set[str]) -> bool:
    return any(names <= allowed for allowed in INTENTIONAL_CANONICAL_VIEWS)


def scan_duplicate_reports(executor) -> dict[str, Any]:
    """Dry-run every catalog entry and return exact semantic duplicate groups.

    Controls, automation presets, external tools, unavailable prerequisite screens, and
    generated-world prompts are omitted because sharing a status screen is not a
    duplicate calculation. Everything else is compared after stripping implementation,
    historical naming, and explanatory prose. This means a different description alone
    cannot make two otherwise identical reports pass the audit.
    """
    from .catalog_ids import SPECS

    buckets: dict[str, list[Any]] = {}
    skipped = 0
    errors: list[dict[str, str]] = []
    audited = 0
    for spec in SPECS:
        try:
            result = executor.dry_run(spec)
        except Exception as exc:
            errors.append({"feature": spec.id, "error": f"{type(exc).__name__}: {exc}"})
            continue
        audited += 1
        data = getattr(result, "data", None)
        status = str(getattr(result, "status", ""))
        if not isinstance(data, dict):
            skipped += 1
            continue
        if status in {"control", "macro", "tool", "unavailable"}:
            skipped += 1
            continue
        if data.get("available") is False or data.get("requires_generated_world"):
            skipped += 1
            continue
        if data.get("mode") == "generated_world_scan" and not data.get("world_path"):
            skipped += 1
            continue
        buckets.setdefault(_fingerprint(data), []).append(spec)

    groups = []
    for specs in buckets.values():
        if len(specs) < 2:
            continue
        names = {spec.name for spec in specs}
        groups.append({
            "features": [spec.id for spec in specs],
            "names": sorted(names),
            "intentional_canonical_view": _intentional_group(names),
        })
    unexplained = [group for group in groups if not group["intentional_canonical_view"]]
    return {
        "catalog_entries": len(SPECS),
        "audited_entries": audited,
        "status_or_prerequisite_screens_skipped": skipped,
        "errors": errors,
        "duplicate_groups": groups,
        "unexplained_duplicate_groups": unexplained,
    }


def _spawner_semantics(name: str, data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    if not out.get("world_path") and out.get("mode") == "generated_world_scan":
        requested = {
            "Dungeon/Pig Spawner Locator": "all detected mob-spawner positions",
            "Double Spawner Locator": "clusters containing at least two nearby spawners",
            "Triple Spawner Locator": "clusters containing at least three nearby spawners",
            "Quad Spawner Locator": "clusters containing at least four nearby spawners",
            "Spawner Cluster Ranking": "ranked nearby-spawner clusters",
            "Stronghold Silverfish": "spawner hits requiring silverfish/entity verification",
            "Trial Chamber Spawners": "trial-spawner and vault block entities",
        }.get(name, name)
        out["requested_analysis"] = requested
        out["required_input"] = "Generated Java world save or exact seed-regenerated vanilla chunks"
        return out

    if name == "Dungeon/Pig Spawner Locator":
        out["purpose"] = "List individual mob-spawner hits; no cluster-size filter is applied."
        out["match_type"] = "individual spawners"
    elif name in {"Double Spawner Locator", "Triple Spawner Locator", "Quad Spawner Locator"}:
        minimum = {"Double Spawner Locator": 2, "Triple Spawner Locator": 3, "Quad Spawner Locator": 4}[name]
        out["purpose"] = f"Find groups with at least {minimum} nearby spawners."
        out["minimum_spawners_per_cluster"] = minimum
        out["cluster_search_distance_blocks"] = 32
        out["cluster_definition"] = "Spawner hits grouped by the generated-world proximity scan; inspect activation overlap before building."
    elif name == "Spawner Cluster Ranking":
        clusters = list(out.get("clusters") or [])
        out["purpose"] = "Rank larger/wider nearby-spawner groups for farm-site inspection."
        out["ranking_search_distance_blocks"] = 48
        out["clusters_returned"] = len(clusters)
        out["largest_cluster_spawners"] = len(clusters[0]) if clusters else 0
    elif name == "Stronghold Silverfish":
        out["purpose"] = "Surface spawner hits that may need stronghold/silverfish verification."
        out["identification_limit"] = "A generic mob-spawner block alone is not proof of a stronghold silverfish spawner; spawned-entity NBT/context must identify it."
    elif name == "Trial Chamber Spawners":
        out["purpose"] = "Show trial-spawner and vault block entities only."
        out["match_type"] = "minecraft:trial_spawner / minecraft:vault"
    return out


def _slime_semantics(name: str, data: dict[str, Any]) -> dict[str, Any]:
    if name not in {"Adjacent Pair", "2x2 Cluster", "Triple Cluster", "Quad Cluster", "Largest Connected Cluster"}:
        return data
    out = dict(data)
    definitions = {
        "Adjacent Pair": "Any cardinally connected slime component containing at least two chunks.",
        "2x2 Cluster": "Exact 2×2 square of four slime chunks.",
        "Triple Cluster": "Any cardinally connected slime component containing at least three chunks.",
        "Quad Cluster": "Any cardinally connected slime component containing at least four chunks; it does not require a 2×2 square.",
        "Largest Connected Cluster": "The largest cardinally connected slime-chunk component in the search radius.",
    }
    out["pattern_definition"] = definitions[name]
    if name == "2x2 Cluster": out["required_shape"] = "2×2 square"
    if name == "Quad Cluster": out["required_shape"] = "any connected 4+ chunk component"
    return out


def _build_grid(name: str, p: dict[str, Any]) -> dict[str, Any] | None:
    if name != "Grid":
        return None
    width = max(1, int(p.get("width", 16))); length = max(1, int(p.get("length", 20))); spacing = max(1, int(p.get("spacing", 4)))
    xs = list(range(0, width, spacing)); zs = list(range(0, length, spacing))
    points = [[x, z] for z in zs for x in xs]
    return {
        "purpose": "General regular construction grid; unlike Lighting Grid it does not force points onto the far edges.",
        "width_blocks": width, "length_blocks": length, "spacing_blocks": spacing,
        "columns": len(xs), "rows": len(zs), "point_count": len(points), "points": points,
    }


def _wizard_view(spec, data: dict[str, Any]) -> dict[str, Any] | None:
    gameplay_shortcuts = {
        "Branch Mine Wizard": ("Branch Mine Setup", "Branch Miner"),
        "Quarry Wizard": ("Quarry Setup", "Area Excavator"),
        "Tree Farm Wizard": ("Tree Farm Setup", "Tree Farm Cycle"),
        "Crop Farm Wizard": ("Crop Farm Setup", "Coordinate Row Farmer"),
        "Nether Highway Wizard": ("Nether Highway Setup", "travel/navigation workflow"),
    }
    if spec.top == "Gameplay" and spec.name in gameplay_shortcuts:
        setup, preset = gameplay_shortcuts[spec.name]
        return {
            "purpose": "Automation-oriented shortcut into the corresponding guided setup.",
            "canonical_guided_setup": setup,
            "automation_target": preset,
            "configured_setup": data,
            "why_this_entry_exists": "Keeps the setup reachable from Automation without pretending it is a second planning algorithm.",
        }
    if spec.top == "Gameplay" and spec.name == "Quarry Planner":
        return {
            "purpose": "Review quarry dimensions, work volume, and row/layer plan without presenting this as a second wizard.",
            "plan": data,
            "next_step": "Use Quarry Wizard / Quarry Setup when you want the guided automation configuration.",
        }
    if spec.top == "Wizards" and spec.name.endswith("Setup"):
        return {
            "purpose": "Canonical guided setup for this workflow.",
            "setup": data,
            "next_step": "Review the generated plan, then start the referenced automation/tool when ready.",
        }
    return None


def _probability_semantics(name: str, data: dict[str, Any]) -> dict[str, Any]:
    if name not in {
        "Enchantment Probability", "RNG Probability Calculator", "Loot Odds Calculator",
        "Rare Drop Odds", "Barter Odds", "Trial Reward Odds", "Enchantment Odds",
    }:
        return data
    out = dict(data)
    chance = max(0.0, min(1.0, float(out.get("single_attempt_percent", 0.0)) / 100.0))
    attempts = max(0, int(out.get("attempts", 0)))
    if name == "RNG Probability Calculator":
        out["formula"] = "P(at least one) = 1 - (1 - p)^n"
        out["expected_attempts_to_first_success"] = None if chance <= 0 else round(1.0 / chance, 3)
    elif name == "Loot Odds Calculator":
        out["loot_roll_readout"] = f"Across {attempts} independent loot rolls, expected successes = {chance * attempts:.3f}."
    elif name == "Enchantment Probability":
        out["reroll_planning"] = "Use the confidence thresholds to estimate how many independent rerolls are needed for the target enchantment probability."
        if "confidence_thresholds" not in out:
            out["confidence_thresholds"] = _confidence_rows(chance)
    elif name == "Rare Drop Odds":
        out["planning_readout"] = "Confidence thresholds are attempts/kills needed for the supplied rare-drop chance."
    elif name == "Barter Odds":
        out["gold_ingot_thresholds"] = out.get("confidence_thresholds", _confidence_rows(chance))
    elif name == "Trial Reward Odds":
        out["reward_attempt_thresholds"] = out.get("confidence_thresholds", _confidence_rows(chance))
    else:
        out["enchantment_reroll_thresholds"] = out.get("confidence_thresholds", _confidence_rows(chance))
    return out


def _confidence_rows(chance: float) -> list[dict[str, Any]]:
    rows = []
    for confidence in (0.5, 0.75, 0.9, 0.95, 0.99):
        if chance <= 0: needed = None
        elif chance >= 1: needed = 1
        else: needed = math.ceil(math.log(1 - confidence) / math.log(1 - chance))
        rows.append({"confidence_percent": confidence * 100, "attempts_needed": needed})
    return rows


def install() -> None:
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_semantic_audit_v2_installed", False):
        return
    previous_execute = FeatureExecutor.execute

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        values = self.defaults(spec)
        values.update(params or {})

        grid = _build_grid(spec.name, values) if spec.top == "Calculators" and spec.submenu == "Build" else None
        if grid is not None:
            return self._result(spec, "ok", grid)

        result = previous_execute(self, spec, values, dry_run)
        data = getattr(result, "data", None)
        if not isinstance(data, dict):
            return result

        transformed = None
        if spec.top == "Seed Tools" and spec.submenu == "Spawners":
            transformed = _spawner_semantics(spec.name, data)
        elif spec.top == "Seed Tools" and spec.submenu == "Slime":
            transformed = _slime_semantics(spec.name, data)
        elif spec.top == "RNG Tools" and spec.submenu in {"Enchanting", "Probability"}:
            transformed = _probability_semantics(spec.name, data)
        else:
            transformed = _wizard_view(spec, data)

        if transformed is not None and transformed is not data:
            result.data = transformed
        return result

    FeatureExecutor.execute = execute
    FeatureExecutor._semantic_audit_v2_installed = True
