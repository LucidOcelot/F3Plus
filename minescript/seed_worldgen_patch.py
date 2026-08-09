from __future__ import annotations

from typing import Any

from .catalog_integrity import annotate
from .seed_worldgen import resolve_world_source

# These are the original catalog tools whose truthful answer can be obtained from
# generated block/entity state. When no save is supplied, F3+ can now materialize
# vanilla chunks from seed + exact Minecraft server version and feed those chunks
# into the same analyzers used for ordinary saves.
SEED_REGENERATABLE = {
    "Dungeon/Pig Spawner Locator", "Double Spawner Locator", "Triple Spawner Locator",
    "Quad Spawner Locator", "Spawner Cluster Ranking", "Stronghold Silverfish",
    "Trial Chamber Spawners", "Largest Ocean", "Largest Mountain Chain",
    "Largest Cave Region", "Flat Terrain Finder", "Valley Finder", "Mountain Peak Finder",
    "Terrain Base Finder", "Island Finder", "Peninsula Detector", "River Crossing Finder",
    "Lake Density", "Cliff Locator", "Ore Distribution", "Ore Exposure Estimate",
    "Cave Exposure Estimate", "Technical World Score", "Resource Score",
}

TICK_SENSITIVE = {"Largest Cave Region", "Cave Exposure Estimate", "Ore Exposure Estimate"}


def _seed_worldgen_fields(fields):
    out = list(fields)
    # Exact regeneration is intentionally bounded by default. A radius of 8 is 289
    # chunks and is practical for an interactive first run; users may knowingly raise
    # both radius and max-chunk limits for larger searches.
    for i, field in enumerate(out):
        if field[0] == "radius":
            out[i] = (field[0], field[1], 8, field[3])
    present = {f[0] for f in out}
    extra = [
        ("regenerate_from_seed", "Generate vanilla chunks from seed when no save is selected", True, "bool"),
        ("accept_minecraft_eula", "I accept the Minecraft EULA for this local server generation", False, "bool"),
        ("worldgen_max_chunks", "Maximum exact chunks to generate", 4096, "int"),
    ]
    out.extend(field for field in extra if field[0] not in present)
    return out


def install() -> None:
    from . import restored_features
    from .feature_executor import FeatureExecutor

    if getattr(restored_features, "_seed_worldgen_patch_installed", False):
        return

    previous_execute = restored_features.execute
    previous_input_fields = FeatureExecutor.input_fields

    def input_fields(self, feature):
        spec = self.spec(feature)
        fields = previous_input_fields(self, feature)
        if spec.top == "Seed Tools" and spec.name in SEED_REGENERATABLE:
            return _seed_worldgen_fields(fields)
        return fields

    def dry_run(self, feature):
        spec = self.spec(feature)
        params = self.defaults(feature)
        # Catalog integrity tests must never download/run Minecraft. Dry runs verify
        # dispatch and prerequisite honesty; the dedicated integration test verifies
        # real Mojang world generation.
        if spec.top == "Seed Tools" and spec.name in SEED_REGENERATABLE:
            params["regenerate_from_seed"] = False
            params["accept_minecraft_eula"] = False
        return self.execute(feature, params, dry_run=True)

    def execute(spec, p: dict[str, Any], executor=None):
        if spec.top == "Seed Tools" and spec.name in SEED_REGENERATABLE and not str(p.get("world_path", "")).strip():
            if bool(p.get("regenerate_from_seed", False)):
                world, source = resolve_world_source(p, executor)
                if world is None:
                    return annotate(spec, {"operation": spec.name, **source})
                q = dict(p)
                q["world_path"] = world
                result = previous_execute(spec, q, executor)
                if isinstance(result, dict):
                    result = dict(result)
                    source = dict(source)
                    if spec.name in TICK_SENSITIVE:
                        source["limitation"] = (
                            "Cave/air/exposure state is measured from a freshly generated vanilla server save. "
                            "Scheduled fluid, gravity, and other game ticks can change some air/exposure blocks after generation; "
                            "ore placement and immutable geology are separately integration-tested for exact repeatability."
                        )
                    result["worldgen_source"] = source
                return result
        return previous_execute(spec, p, executor)

    FeatureExecutor.input_fields = input_fields
    FeatureExecutor.dry_run = dry_run
    restored_features.execute = execute
    restored_features._seed_worldgen_patch_installed = True
