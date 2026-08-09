from __future__ import annotations

"""Explicit composition policy for historical operation compatibility.

The order here replaces the old import-time installer stack. New/canonical semantics
win first; older domain models only fill an operation that has no newer implementation.
"""

from typing import Any

from . import full_catalog as catalog_models
from . import operation_semantics as semantics
from . import qa_features as qa_models
from . import result_quality as quality
from . import search_policy, seed_generation, spawners, supplemental_operations
from . import waypoint_semantics as waypoints


def _legacy_catalog_fields(spec):
    if spec.top == "Seed Tools" and spec.submenu == "Biomes":
        return [
            ("seed", "World seed", 123456789, "text"),
            ("x", "Center X", 0, "int"),
            ("y", "Sample Y", 64, "int"),
            ("z", "Center Z", 0, "int"),
            ("radius", "Radius (blocks)", 256, "int"),
            ("step", "Sample step (blocks)", 16, "int"),
            ("target_biome", "Target biome numeric ID", 1, "int"),
            ("world_path", "Generated world path (terrain-shape tools)", "", "text"),
        ]
    if spec.top == "Seed Tools" and spec.submenu == "World Analysis":
        return [
            ("seed", "World seed", 123456789, "text"),
            ("second_seed", "Comparison seed", 987654321, "text"),
            ("cx", "Center chunk X", 0, "int"),
            ("cz", "Center chunk Z", 0, "int"),
            ("radius", "Radius (chunks)", 64, "int"),
            ("world_path", "Generated world path", "", "text"),
            ("simulation_distance", "Simulation distance", 10, "int"),
        ]
    return None


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
            fields = _legacy_catalog_fields(spec)
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


def _current_semantic_result(executor, spec, values):
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
        resolver = {
            "Spawn Chunk Optimizer": quality._spawn_site_report,
            "Chunk Loading Simulator": quality._chunk_loading_report,
            "Search Radius Optimizer": quality._search_radius_report,
        }.get(spec.name)
        if resolver is not None:
            data = resolver(values)
    if data is None and spec.top == "Calculators" and spec.submenu == "Build" and spec.name == "Circle Layer Export":
        data = quality._circle_export(values)
    return data


def _legacy_model_result(executor, spec, values):
    """Run pre-rewrite models as ordinary fallbacks, never as installers."""
    data = None
    if spec.top == "Calculators":
        data = catalog_models.calculator_tool(spec, values)
    elif spec.top == "Seed Tools":
        data = catalog_models.seed_tool(spec, values, executor)
    elif spec.top == "RNG Tools":
        data = catalog_models.rng_tool(spec, values)
    if data is not None:
        return data
    if spec.top == "Navigation":
        return qa_models.navigation(spec.name, values)
    if spec.top == "RNG Tools":
        return qa_models.rng_tool(spec.name, values, executor)
    if spec.top == "Seed Tools":
        return qa_models.world_seed_tool(spec.name, spec.submenu, values, executor)
    if spec.top == "Villager Explorer":
        return qa_models.villager_tool(spec.name, executor.minecraft_version, values)
    if spec.top == "Safety":
        return qa_models.safety_descriptor(spec.name, values, executor)
    if spec.top == "Utilities":
        return qa_models.utility_descriptor(spec.name, values, executor)
    return None


def semantic_result(executor, spec, values):
    data = _current_semantic_result(executor, spec, values)
    waiting_for_exact_world = (
        spec.top == "Seed Tools"
        and spec.name in seed_generation.SEED_REGENERATABLE
        and not str(values.get("world_path", "")).strip()
        and bool(values.get("regenerate_from_seed", False))
    )
    if data is None and not waiting_for_exact_world:
        data = _legacy_model_result(executor, spec, values)
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


def _seed_values_for_base(executor, spec, values):
    if spec.top != "Seed Tools" or "mc" in values:
        return values, None
    normalized = dict(values)
    try:
        normalized["mc"] = qa_models._selected_mc(executor, normalized)
    except ValueError as exc:
        return normalized, executor._result(spec, "unavailable", {"available": False, "version_error": str(exc)})
    return normalized, None


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
        generated_semantic = semantic_result(executor, spec, generated)
        if generated_semantic is not None:
            if isinstance(getattr(generated_semantic, "data", None), dict):
                generated_semantic.data = {**generated_semantic.data, "worldgen_source": dict(source)}
            return apply_result_semantics(spec, generated_semantic)
        generated, version_error = _seed_values_for_base(executor, spec, generated)
        if version_error is not None:
            return version_error
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
    base_values, version_error = _seed_values_for_base(executor, spec, values)
    if version_error is not None:
        return version_error
    return apply_result_semantics(spec, executor._base_execute(spec, base_values, dry_run))


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
