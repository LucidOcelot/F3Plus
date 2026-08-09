# F3+ Workbench Guide

F3+ is an offline-first technical companion for Minecraft Java Edition. The default target is **26.3 Snapshot 7**. The desktop UI is organized by user task; historical feature IDs are compatibility aliases, not separate applications.

## Shared interaction model

1. Choose a workbench.
2. Choose the operation inside it.
3. Enter only the fields used by that operation.
4. Run the operation and inspect its structured result, source, and limitations.

Favorites and recents store canonical workbench IDs. Historical IDs from older F3+ builds still resolve to the matching operation so existing settings/scripts are not orphaned.

Coordinate-bearing results can open an interactive X/Z view with wheel zoom, drag panning, fit-to-data, layer visibility, optional point labels, and copyable visible coordinates.

## Automation

**Automation Studio** groups continuous/periodic actions and equipment routines. **Travel & Mobility** contains automated/planned walking, sprinting, swimming, vehicle, elytra, riptide, coordinate, waypoint, and Nether-assisted travel. **Mining & Excavation**, **Farm Automation**, and **Construction Automation** group related repetitive routines instead of presenting each macro preset as an independent program. **Sequences & Macro Workflows** covers recording and multi-step automation.

All automation uses the shared `MacroEngine`/platform-input safety path. Emergency Stop releases held input. Pause/Resume, delayed start, runtime/action limits, focus behavior, stuck detection, and configurable global hotkeys remain common controls.

## Navigation

**Live Position** handles coordinate capture/tracking. **Coordinate & Travel Calculator** combines distance, bearing, midpoint, XYZ delta, travel time, chunk/region geometry, snapping, offsets, and Overworld/Nether conversion.

**Waypoints, Routes & Surveys** keeps genuinely different tasks as modes of one route workbench: nearest waypoint, sort from origin, greedy multi-stop route, breadcrumb/expedition summaries, and survey-path generation.

**Portal Network Planner** combines sister-coordinate math, competing exits, one-way/asymmetric routing, reliability geometry, bidirectional matrices, graphs, route comparison, and network planning. A heatmap's normalized proximity is explicitly a geometric planning metric, not a probability that Minecraft will choose an exit.

## World Explorer

**World Seed Recovery** is the Nether Bedrock Cracker path and remains the only world/structure-seed recovery workflow. Player/gameplay RNG recovery is separate.

**Slime Chunk Explorer** handles finding, adjacency, geometric clusters, ranking, and related known-seed slime analysis.

**Structure Explorer** combines individual/compound structure candidate searches, density/relationship analysis, cluster/corridor/route views, and structure placement previews. Deterministic placement candidates are not mislabeled as confirmed generated structures.

**Spawner Explorer** reads generated Anvil/NBT data. It identifies mob-spawner entity IDs when encoded, distinguishes trial spawners/vaults, supports mob filters, and applies double/triple/quad/cluster grouping after filtering. Seed math alone is never presented as proof that an arbitrary dungeon spawner generated.

**Biome & Terrain Explorer** contains biome lookup/nearest/intersection/boundary operations plus generated-terrain reports such as flat terrain, valleys, peaks, islands, rivers, cliffs, caves, and larger terrain regions.

**Local Area Analyzer** provides bounded composition/highlight/site reports. **World Analysis** contains spawn/resource/ore/cave/loading/comparison/search-cost reports. **Nether Explorer** contains known-seed Nether biome and fortress/bastion analysis that depends on generation rather than ordinary portal-coordinate math.

### Search modes

Finders with a concrete found/not-found result support:

- **Radius search** — inspect one bounded radius.
- **Search until found** — expand by a configured step until a match or maximum radius.
- **Ignore maximum search / generation limit** — advanced override that can greatly increase CPU, memory, disk, and runtime use. An internal runaway-loop guard and backend errors can still stop the process.

Generated-world spawner/terrain scans use chunk units. Cubiomes biome search operations use block units where appropriate; the UI keeps these units explicit.

## Build & Technical

**Build & Shape Planner** combines dimensions, block counts, foundations, stairs, bridges, roofs, roads, grids, lighting, gradients, circles/spheres/spirals/helices, and export-ready layouts.

**Redstone & Timing Lab** includes game/redstone tick conversion, repeaters/comparators/hoppers, transport timing, crafter throughput, clocks, counters, and signal planning.

**Storage & Logistics** distinguishes capacity questions from requirement questions while sharing one workbench. **Farm & Breeding Planner** combines yield, layout, furnace/fuel, crop/apiary/pen/villager-hall/beacon/farm planning. **Technical Minecraft Calculator** groups loading/mob/spacing/chunk/perimeter/sorter/technical geometry. **Resource, Speedrun & End Toolkit** groups resource-use, durability, XP/Mending, speedrun coordinate, and End-travel planning.

## Simulation & RNG

### RNG & Enchanting Workbench

Enchanting Table, Anvil, sequence/timeline, general probability, Java LCG observation/recovery, enchantment planning, and player-RNG recovery share one workbench instead of independent small dialogs.

Installed enchantment definitions and tags are used when available. Normal enchanting-table offers exclude treasure-tagged enchantments. Anvil results expose prior-work penalties, merge costs, rename cost, resulting enchantments, and the normal survival Too Expensive threshold where modeled.

### Loot & Drop Workbench

The loot workbench reads installed vanilla loot-table JSON, item tags, nested table references, conditions, and supported functions. Item-tag object members are normalized, and an entry condition is evaluated exactly once during one selection attempt rather than being resampled during expansion.

Possible-loot views show reachable entries without fabricating an exact probability when required entity/location/tool/score context is unavailable. Statistical simulation uses repeatable seeds and reports observed hit rates/counts. When no usable installed data exists, F3+ uses clearly labeled first-party baseline examples.

### Generation RNG Workbench

Decoration, feature-position, ore-position, tree/geode frequency, trial-chamber, and structure-placement models remain separate modes with explicit model limits. Candidate RNG positions are not presented as final generated features.

### Minecraft Mechanics Lab

Brewing, leather dye/cauldron behavior, and animal/horse breeding share a mechanics workbench. Brewing transitions that are code-defined in Java are labeled as an internal vanilla rule model rather than falsely attributed to datapack recipe JSON. Java leather dye mixing uses brightness-preserving RGB behavior; cauldron washing remains separate. Breeding exposes species-specific fields instead of copying unrelated runtime NBT into offspring.

## Villagers

**Villager Explorer** is the single villager surface. It includes professions, Novice/Apprentice/Journeyman/Expert/Master levels, trade directions, search, comparison, librarian workflows, emerald/use-cycle planning, curing, breeding, workstation, and hall planning.

Artwork and trade data are independent. Villager entity/type/profession skin layers and item textures are read from an installed Java client when available. Exact installed trade definitions are preferred; otherwise a non-empty planning baseline is visibly labeled as non-exact.

## Utilities & Safety

**Version & Data** reports selected Minecraft version, installed/local data, compatibility, and component state. **Profiles, Controls & Calibration** handles settings, bindings, import/export/backups, and movement/turn/capture calibration. **Automation Safety** contains emergency stop, pause/resume, held-input release, focus-loss behavior, runtime/action limits, delayed start, stuck detection, and recovery policy.

Safe Mode is a conservative multiplayer filter. It disables automation, hidden-world/seed analysis, and predictive RNG/loot/generation workbenches while keeping ordinary calculators, villager reference tools, mechanics references, and local configuration available. Server rules remain authoritative.

## Version and source accuracy

F3+ keeps three concepts separate:

- **Selected Minecraft version** — what the user targets.
- **Calculation/world-generation version** — the actual rules used by the active backend.
- **Local data version** — the installed client JAR supplying definitions or artwork.

Bundled Cubiomes mappings are explicitly bounded through Minecraft 1.21.3. Unsupported newer selections remain visible while the actual supported calculation fallback is labeled.

Generated-terrain operations can inspect a Java save or, where supported, create bounded Mojang reference chunks after explicit EULA acceptance. Exact-generation integration tests compare F3+ predictions with an independently generated Mojang server world. Tick-sensitive cave/air/fluid state is labeled separately from immutable generation facts.

## Architecture boundary

The visible workbench registry is canonical. The 457 historical IDs are retained only as compatibility aliases. Importing `minescript` does not install patches or rewrite classes. Domain behavior is composed through explicit executor/services, and simulator correctness policy is part of the canonical simulator engine rather than a release-specific hardening module.
