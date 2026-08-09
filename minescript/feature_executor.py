from __future__ import annotations

"""Canonical compatibility executor.

The historical FeatureSpec API remains available for saved IDs, scripts, and regression
coverage, but behavior is composed through normal inheritance and domain services.
Nothing in this module mutates another class at import time.
"""

from .feature_engine import (
    COMMON_FIELDS, MACRO_NAMES, FeatureExecutor as _BaseFeatureExecutor, FeatureResult,
)
from .version import TARGET_MINECRAFT
from . import search_policy, seed_generation, spawners


class FeatureExecutor(_BaseFeatureExecutor):
    def __init__(self, minecraft_version=TARGET_MINECRAFT):
        super().__init__(minecraft_version)

    def input_fields(self, feature):
        spec = self.spec(feature)
        if spec.top == "Seed Tools" and spec.submenu == "Spawners":
            fields = spawners.input_fields(spec.name)
        else:
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

    def _execute_once(self, spec, values, dry_run=False):
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
            return result

        return super().execute(spec, values, dry_run)

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
