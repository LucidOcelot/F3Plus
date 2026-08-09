from __future__ import annotations

"""Canonical compatibility executor.

Historical FeatureSpec IDs remain executable for saved favorites, scripts, and regression
coverage.  Distinct jobs are explicit dispatches inside the canonical executor; aliases
may intentionally share a workbench/mode.  No module mutates this class at import time.
"""

from .feature_engine import (
    COMMON_FIELDS, MACRO_NAMES, FeatureExecutor as _BaseFeatureExecutor, FeatureResult,
)
from .version import TARGET_MINECRAFT
from . import search_policy, seed_generation, spawners
from . import semantic_cleanup_v2 as _semantics
from . import semantic_quality_v2 as _quality
from . import semantic_waypoints_v2 as _waypoints


class FeatureExecutor(_BaseFeatureExecutor):
    def __init__(self, minecraft_version=TARGET_MINECRAFT):
        super().__init__(minecraft_version)

    def input_fields(self, feature):
        spec = self.spec(feature)

        if spec.top == "Navigation" and spec.submenu == "Waypoints" and spec.name in {
            "Nearest Waypoint", "Sort Waypoints by Distance", "Waypoint Route",
        }:
            fields = [
                ("x1", "Current / origin X", 0.0, "float"),
                ("y1", "Current / origin Y", 64.0, "float"),
                ("z1", "Current / origin Z", 0.0, "float"),
            ]
            if spec.name == "Waypoint Route":
                fields.append(("return_to_start", "Return to origin", False, "bool"))
        else:
            fields = _semantics._fields_for(spec)
            if fields is None:
                fields = _quality._fields(spec)
            if fields is None and spec.top == "Seed Tools" and spec.submenu == "Spawners":
                fields = spawners.input_fields(spec.name)
            if fields is None:
                fields = super().input_fields(spec)

        if spec.top == "Seed Tools" and spec.name in seed_generation.SEED_REGENERATABLE:
            fields = seed_generation.add_fields(fields)
        return search_policy.add_fields(spec, fields)

    def dry_run(self, feature):
        spec = self.spec(feature)
        params = self.defaults(spec)
        if spec.top == "Seed Tools" and spec.name in seed_generation.SEED_REGENERATABLE:
            params["regenerate_from_seed"] = False
            params["accept_minecraft_eula"] = False
        return self.execute(spec, params, dry_run=True)

    def _semantic_result(self, spec, values):
        data = None
        if spec.top == "Navigation" and spec.submenu == "Waypoints" and spec.name in {
            "Nearest Waypoint", "Sort Waypoints by Distance", "Waypoint Route",
        }:
            data = _waypoints._waypoint_report(self, spec.name, values)
        if data is None and spec.top == "Navigation" and spec.submenu == "Coordinates":
            data = _semantics._navigation_coordinate(spec.name, values)
        if data is None and spec.top == "Navigation" and spec.submenu == "Routes":
            data = _semantics._navigation_route(spec.name, values)
        if data is None and spec.top == "Seed Tools" and spec.submenu == "Nether":
            data = _semantics._portal_report(spec.name, values)
        if data is None and spec.top == "Calculators" and spec.submenu == "Build":
            data = _semantics._build_report(spec.name, values)
        if data is None and spec.top == "Calculators" and spec.submenu == "Storage":
            data = _semantics._storage_report(spec.name, values)
        if data is None and spec.top == "Calculators" and spec.submenu == "Technical":
            data = _semantics._technical_report(spec.name, values)
        if data is None and spec.top == "Calculators" and spec.submenu == "Shapes":
            data = _semantics._shape_report(spec.name, values)
        if data is None and spec.top == "Calculators" and spec.submenu == "Resource Usage":
            data = _semantics._resource_usage_report(spec.name, values)
        if data is None and spec.top == "RNG Tools":
            data = _semantics._loot_table_report(spec.name, values)
            if data is None:
                data = _semantics._probability_report(spec.name, values)
            if data is None:
                data = _semantics._sequence_report(spec.name, values)
            if data is None:
                data = _semantics._target_event_report(spec.name, values)
            if data is None and spec.submenu == "Generation RNG":
                data = _semantics._generation_report(spec.name, values, self)

        if data is None and spec.top == "Seed Tools" and spec.submenu == "Slime" and spec.name == "Farm Location Ranking":
            data = _quality._farm_location_report(values)
        if data is None and spec.top == "Seed Tools" and spec.submenu == "World Analysis":
            if spec.name == "Spawn Chunk Optimizer":
                data = _quality._spawn_site_report(values)
            elif spec.name == "Chunk Loading Simulator":
                data = _quality._chunk_loading_report(values)
            elif spec.name == "Search Radius Optimizer":
                data = _quality._search_radius_report(values)
        if data is None and spec.top == "Calculators" and spec.submenu == "Build" and spec.name == "Circle Layer Export":
            data = _quality._circle_export(values)

        if data is None:
            return None
        status = "unavailable" if isinstance(data, dict) and data.get("available") is False else "ok"
        return self._result(spec, status, data)

    def _apply_result_semantics(self, spec, result):
        data = getattr(result, "data", None)
        if not isinstance(data, dict):
            return result
        if spec.top == "Seed Tools" and spec.submenu == "Biomes" and spec.name in {
            "Terrain Base Finder", "Lake Density", "Largest Cave Region",
        }:
            result.data = _quality._transform_terrain(spec.name, data)
        elif spec.top == "Seed Tools" and spec.submenu == "Structures" and spec.name in {
            "Structure Heatmap", "Isolated Structure Finder", "Structure Chains",
            "Structure Corridor", "Structure Cluster Finder",
        }:
            result.data = _quality._transform_structure(spec.name, data)
        elif spec.top == "Seed Tools" and spec.submenu == "Nether" and spec.name == "Portal Reliability Heatmap":
            result.data = _quality._portal_heatmap(data)
        elif spec.top == "Seed Tools" and spec.submenu == "World Analysis" and spec.name == "Seed Comparison":
            result.data = _quality._seed_comparison(data)
        return result

    def _execute_once(self, spec, values, dry_run=False):
        semantic = self._semantic_result(spec, values)
        if semantic is not None:
            return semantic

        if spec.top == "Seed Tools" and spec.submenu == "Spawners":
            data = spawners.report(spec.name, values, self, dry_run)
            status = "unavailable" if data.get("available") is False else "ok"
            return self._result(spec, status, data)

        if (
            not dry_run
            and spec.top == "Seed Tools"
            and spec.name in seed_generation.SEED_REGENERATABLE
            and not str(values.get("world_path", "")).strip()
            and bool(values.get("regenerate_from_seed", False))
        ):
            from .seed_worldgen import resolve_world_source
            world, source = resolve_world_source(values, self)
            if world is None:
                return self._result(spec, "unavailable", {"operation": spec.name, **source})
            generated_values = dict(values); generated_values["world_path"] = world
            result = super().execute(spec, generated_values, False)
            if isinstance(getattr(result, "data", None), dict):
                source = dict(source)
                if spec.name in seed_generation.TICK_SENSITIVE:
                    source["limitation"] = (
                        "Cave/air/exposure state is measured from a freshly generated vanilla server save. "
                        "Scheduled fluid, gravity, and other game ticks can change some air/exposure blocks after generation; "
                        "ore placement and immutable geology are separately integration-tested for exact repeatability."
                    )
                result.data = {**result.data, "worldgen_source": source}
            return self._apply_result_semantics(spec, result)

        return self._apply_result_semantics(spec, super().execute(spec, values, dry_run))

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        values = self.defaults(spec); values.update(params or {})
        if dry_run and spec.name in seed_generation.SEED_REGENERATABLE:
            values["regenerate_from_seed"] = False
            values["accept_minecraft_eula"] = False

        if search_policy.supports(spec) and not dry_run and str(values.get("search_mode", search_policy.SEARCH_MODES[0])) == "Search until found":
            def at_radius(radius):
                attempt = search_policy.prepare_attempt(spec, values, radius)
                return self._execute_once(spec, attempt, False)
            result, summary = search_policy.run_until_found(spec, values, at_radius)
            return search_policy.decorate(result, summary)

        result = self._execute_once(spec, values, dry_run)
        if search_policy.supports(spec) and not dry_run:
            radius = max(0, int(values.get("radius", 0)))
            search_policy.decorate(result, {
                "mode": "Radius search",
                "unit": search_policy.unit(spec),
                "radius": radius,
                "found": search_policy.has_match(spec, getattr(result, "data", {}) or {}),
                "ignore_maximum_limit": False,
            })
        return result


__all__ = ["FeatureExecutor", "FeatureResult", "MACRO_NAMES", "COMMON_FIELDS"]
