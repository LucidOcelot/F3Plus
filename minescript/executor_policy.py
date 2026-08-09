from __future__ import annotations

"""Explicit composition policy for historical operation compatibility.

This module contains routing only. Domain algorithms remain in their canonical services.
"""

from typing import Any

from . import operation_semantics as semantics
from . import result_quality as quality
from . import search_policy, seed_generation, spawners, supplemental_operations
from . import waypoint_semantics as waypoints


def input_fields(executor, spec):
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
        fields = supplemental_operations.input_fields(spec)
        if fields is None:
            fields = semantics._fields_for(spec)
        if fields is None:
            fields = quality._fields(spec)
        if fields is None and spec.top == "Seed Tools" and spec.submenu == "Spawners":
            fields = spawners.input_fields(spec.name)
        if fields is None:
            fields = executor._base_input_fields(spec)
    if spec.top == "Seed Tools" and spec.name in seed_generation.SEED_REGENERATABLE:
        fields = seed_generation.add_fields(fields)
    return search_policy.add_fields(spec, fields)


def dry_run(executor, spec):
    if spec.top == "Seed Tools" and spec.name in seed_generation.SEED_REGENERATABLE and spec.submenu != "Spawners":
        return executor._result(spec, "unavailable", {
            "available": False,
            "requires_generated_world": True,
            "requires_seed_worldgen": True,
            "reason": "This operation needs generated Java world data. Select a save or run it with exact Mojang reference-world generation after accepting the EULA.",
        })
    values = executor.defaults(spec)
    if spec.top == "Seed Tools" and spec.name in seed_generation.SEED_REGENERATABLE:
        values["regenerate_from_seed"] = False
        values["accept_minecraft_eula"] = False
    return execute(executor, spec, values, True)


def semantic_result(executor, spec, values):
    data = None
    if spec.top == "Navigation" and spec.submenu == "Waypoints" and spec.name in {
        "Nearest Waypoint", "Sort Waypoints by Distance", "Waypoint Route",
    }:
        data = waypoints._waypoint_report(executor, spec.name, values)
    if data is None:
        data = supplemental_operations.report(spec, values)
    if data is None and spec.top == "Navigation" and spec.submenu == "Coordinates":
        data = semantics._navigation_coordinate(spec.name, values)
    if data is None and spec.top == "Navigation" and spec.submenu == "Routes":
        data = semantics._navigation_route(spec.name, values)
    if data is None and spec.top == "Seed Tools" and spec.submenu == "Nether":
        data = semantics._portal_report(spec.name, values)
    if data is None and spec.top == "Calculators" and spec.submenu == "Build":
        data = semantics._build_report(spec.name, values)
    if data is None and spec.top == "Calculators" and spec.submenu == "Storage":
        data = semantics._storage_report(spec.name, values)
    if data is None and spec.top == "Calculators" and spec.submenu == "Technical":
        data = semantics._technical_report(spec.name, values)
    if data is None and spec.top == "Calculators" and spec.submenu == "Shapes":
        data = semantics._shape_report(spec.name, values)
    if data is None and spec.top == "Calculators" and spec.submenu == "Resource Usage":
        data = semantics._resource_usage_report(spec.name, values)
    if data is None and spec.top == "RNG Tools":
        for resolver in (
            semantics._loot_table_report,
            semantics._probability_report,
            semantics._sequence_report,
            semantics._target_event_report,
        ):
            data = resolver(spec.name, values)
            if data is not None:
                break
        if data is None and spec.submenu == "Generation RNG":
            data = semantics._generation_report(spec.name, values, executor)
    if data is None and spec.top == "Seed Tools" and spec.submenu == "Slime" and spec.name == "Farm Location Ranking":
        data = quality._farm_location_report(values)
    if data is None and spec.top == "Seed Tools" and spec.submenu == "World Analysis":
        resolvers = {
            "Spawn Chunk Optimizer": quality._spawn_site_report,
            "Chunk Loading Simulator": quality._chunk_loading_report,
            "Search Radius Optimizer": quality._search_radius_report,
        }
        resolver = resolvers.get(spec.name)
        if resolver is not None:
            data = resolver(values)
    if data is None and spec.top == "Calculators" and spec.submenu == "Build" and spec.name == "Circle Layer Export":
        data = quality._circle_export(values)
    if data is None:
        return None
    status = "unavailable" if isinstance(data, dict) and data.get("available") is False else "ok"
    return executor._result(spec, status, data)


def apply_result_semantics(spec, result):
    data = getattr(result, "data", None)
    if not isinstance(data, dict):
        return result
    if spec.top == "Seed Tools" and spec.submenu == "Biomes" and spec.name in {
        "Terrain Base Finder", "Lake Density", "Largest Cave Region",
    }:
        result.data = quality._transform_terrain(spec.name, data)
    elif spec.top == "Seed Tools" and spec.submenu == "Structures" and spec.name in {
        "Structure Heatmap", "Isolated Structure Finder", "Structure Chains",
        "Structure Corridor", "Structure Cluster Finder",
    }:
        result.data = quality._transform_structure(spec.name, data)
    elif spec.top == "Seed Tools" and spec.submenu == "Nether" and spec.name == "Portal Reliability Heatmap":
        result.data = quality._portal_heatmap(data)
    elif spec.top == "Seed Tools" and spec.submenu == "World Analysis" and spec.name == "Seed Comparison":
        result.data = quality._seed_comparison(data)
    return result


def execute_once(executor, spec, values, dry_run=False):
    semantic = semantic_result(executor, spec, values)
    if semantic is not None:
        return semantic
    if spec.top == "Seed Tools" and spec.submenu == "Spawners":
        data = spawners.report(spec.name, values, executor, dry_run)
        status = "unavailable" if data.get("available") is False else "ok"
        return executor._result(spec, status, data)
    if (
        not dry_run
        and spec.top == "Seed Tools"
        and spec.name in seed_generation.SEED_REGENERATABLE
        and not str(values.get("world_path", "")).strip()
        and bool(values.get("regenerate_from_seed", False))
    ):
        from .seed_worldgen import resolve_world_source
        world, source = resolve_world_source(values, executor)
        if world is None:
            return executor._result(spec, "unavailable", {"operation": spec.name, **source})
        generated = dict(values); generated["world_path"] = world
        result = executor._base_execute(spec, generated, False)
        if isinstance(getattr(result, "data", None), dict):
            source = dict(source)
            if spec.name in seed_generation.TICK_SENSITIVE:
                source["limitation"] = (
                    "Cave/air/exposure state is measured from a freshly generated vanilla server save. "
                    "Scheduled fluid, gravity, and other game ticks can change some air/exposure blocks after generation; "
                    "ore placement and immutable geology are separately integration-tested for exact repeatability."
                )
            result.data = {**result.data, "worldgen_source": source}
        return apply_result_semantics(spec, result)
    return apply_result_semantics(spec, executor._base_execute(spec, values, dry_run))


def execute(executor, spec, params: dict[str, Any] | None = None, dry_run=False):
    values = executor.defaults(spec); values.update(params or {})
    if dry_run and spec.name in seed_generation.SEED_REGENERATABLE:
        values["regenerate_from_seed"] = False
        values["accept_minecraft_eula"] = False
    if search_policy.supports(spec) and not dry_run and str(values.get("search_mode", search_policy.SEARCH_MODES[0])) == "Search until found":
        def at_radius(radius):
            return execute_once(executor, spec, search_policy.prepare_attempt(spec, values, radius), False)
        result, summary = search_policy.run_until_found(spec, values, at_radius)
        return search_policy.decorate(result, summary)
    result = execute_once(executor, spec, values, dry_run)
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
