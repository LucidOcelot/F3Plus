# F3+ Workbench Guide

F3+ 2.4.1 is an offline-first technical companion for Minecraft Java Edition. The default target is **26.3 Snapshot 7**. The desktop UI is organized by user task; the 457 historical feature IDs are compatibility aliases, not separate applications.

## Shared interaction model

1. Choose a workbench or use `Ctrl+K` Command Palette.
2. Choose the operation inside it.
3. Read what the operation calculates, what each visible input means, and what output to expect.
4. Enter the user-facing values required by that operation.
5. Run it and inspect structured output, source/exactness context, limitations, and any explicitly declared map/chart.

Compatibility defaults required by older internal calculation code are not shown as user inputs. Maps and charts are operation-declared; F3+ does not infer a coordinate map or statistical graph from arbitrary numeric result shapes.

Favorites and recents store canonical workbench IDs. Historical IDs from older F3+ builds still resolve to the matching operation so existing settings/scripts are not orphaned.

Configuration fields include visible contextual help and accessibility descriptions. Search controls enable only when they affect the selected mode. **Search until found** exposes expansion step and maximum radius; the explicit ignore-limit override disables the normal maximum and warns that exact generation can consume substantial CPU, memory, disk and runtime. Long-running generic workbench jobs run off the GUI thread and can be cancelled; expanding searches check cancellation between attempts.

## Automation

**Automation Studio** is a purpose-built control surface rather than a calculator shell. It groups continuous/periodic actions and equipment routines by gameplay task, shows live link/input/Safe Mode/session state, and exposes Start, Configure & Start, and Stop controls according to the routine. **Travel & Mobility** contains walking, sprinting, swimming, vehicle, elytra, riptide, coordinate, waypoint, and Nether-assisted travel. **Mining & Excavation**, **Farm Automation**, and **Construction Automation** group related repetitive routines instead of presenting each preset as an independent application.

Previously fixed example values are configurable again: Custom Hold/Periodic Action, livestock breeding, fishing, coordinate/waypoint/Nether-assisted travel, branch/stair/area excavation, coordinate row farming, bone meal farming, Mending Grinder, and construction rectangle/filled rectangle/grid/rows/alternating/perimeter paths all use their configured parameters.

### Macro Studio

Macro Studio is a canonical workbench for reusable local automation. It supports:

- tap, click, wait, hold, turn, and hotbar-slot steps;
- built-in templates;
- manual step editing and ordering;
- optional keyboard/mouse recording through the existing pynput input layer;
- a dry timeline showing the sequence and known minimum duration;
- looped or one-pass playback;
- local save/delete plus JSON import/export;
- execution through `MacroEngine`, so global stop/pause and configured safety limits still apply.

## Automation safety and connection state

All automation uses the shared `MacroEngine`/platform-input path. The following settings are active controls, not descriptors: runtime limit, action/cycle limit, delayed start, coordinate-recovery attempts, hotbar restoration, stuck-detection window/minimum progress, and focus-loss stop.

If the linked Minecraft process/window disappears, F3+ stops managed automation, releases held input, clears the target, and returns to a non-targeted foreground backend. Automatic linking only happens without a prompt when exactly one client is available; multiple detected clients require a choice.

When a macro requires focus, F3+ can capture the previously focused application, focus the linked Minecraft client, and restore the previous application after the run when that option is enabled. Minimized-client and unlinked-client paths are surfaced before input starts.

## Navigation

**Live Position** handles F3+C capture, continuous position monitoring, distance announcements, and bearing-to-target monitoring. The configured coordinate-capture delay is applied before clipboard polling.

**Coordinate & Travel Calculator** combines distance, bearing, midpoint, XYZ delta, travel time, chunk/region geometry, snapping, offsets, and Overworld/Nether conversion. Sister-coordinate conversion explicitly rejects the End.

**Waypoints, Routes & Surveys** owns persistent waypoint state. Users can create, edit/rename, delete, group, import, and export waypoints; Save Sister Waypoint persists a unique Overworld/Nether sister coordinate. Captured coordinates are kept in a bounded local history. Nearest/sorted/route calculations read the saved waypoint set and default their origin to the currently captured player position when available.

Resource Route, Structure Tour, and Biome Expedition expose their multi-stop `x,y,z,label` lists directly. Breadcrumb/Expedition Recorder exposes recorded points and sampling interval, Survey Mode exposes radius/spacing, and Loop Detection exposes path points plus revisit tolerance. These UI schemas match the values their handlers actually consume.

**Portal Network Planner** combines sister-coordinate math, competing exits, one-way/asymmetric routing, reliability geometry, bidirectional matrices, graphs, route comparison, and network planning. Portal Reliability Heatmap's normalized proximity remains explicitly a geometric planning metric, **not a probability** that Minecraft will choose an exit.

## World Explorer

**World Seed Recovery** is the Nether Bedrock Cracker path and remains the only world/structure-seed recovery workflow. Player/gameplay RNG recovery is separate.

**Slime Chunk Explorer** handles finding, adjacency, geometric clusters, ranking, and related known-seed slime analysis. **Structure Explorer** combines individual/compound placement searches, density/relationship analysis, cluster/corridor/route views, and structure-placement previews; deterministic placement candidates are not mislabeled as confirmed generated structures.

**Spawner Explorer** reads generated Anvil/NBT data, identifies mob-spawner entity IDs where encoded, distinguishes trial spawners/vaults, supports mob filters, and applies double/triple/quad/cluster grouping after filtering. Seed math alone is never presented as proof that an arbitrary dungeon spawner generated.

**Biome & Terrain Explorer**, **Local Area Analyzer**, **World Analysis**, and **Nether Explorer** retain known-seed and generated-world operations. Exact/reference-world generation remains opt-in after Minecraft EULA acceptance and keeps selected/calculation/local-data version state separate.

### World Profiles & Local Saves

World Profiles discovers standard local Java `saves` folders or accepts an explicitly selected world folder. `level.dat` is read locally for available world name, DataVersion/version name, seed, spawn, mode/hardcore state and last-played metadata. Selecting a profile can apply its known seed/version context to F3+ without modifying the world.

World-profile data is stored locally under the F3+ user-data folder. Local save inspection remains read-only by default.

## Build & Technical

**Build & Shape Planner** separates Build Calculators from Shape Layouts rather than guessing categories from operation names. The selected operation explains its purpose and expected result before running. Shape forms expose only the dimensions that the selected shape actually consumes—for example, Arch/Circle/Diamond use radius, Ellipse uses two radii, and cylinder/cone/helix families expose their required height/turn controls.

**Redstone & Timing Lab**, **Storage & Logistics**, **Farm & Breeding Planner**, **Technical Minecraft Calculator**, and **Resource, Speedrun & End Toolkit** retain their distinct calculations while sharing a smaller visible surface.

### Recipe & Material Explorer

The Recipe & Material Explorer reads installed Minecraft recipe JSON directly from the selected/available client JAR. It can search by recipe ID, result item, or recipe type, inspect ingredient slots, and recursively expand a target output into a material bill.

When a recipe slot permits alternatives, the planning expansion chooses the first listed concrete alternative rather than pretending all alternatives are interchangeable. Item tags that require a user material choice remain unresolved and visible in the BOM. This is a planning tool, not a claim that one material choice is uniquely correct.

## Simulation & RNG

### RNG & Enchanting Workbench

Enchanting Table, Anvil, sequence/timeline, general probability, Java LCG observation/recovery, enchantment planning, and player-RNG recovery share one workbench. The compatibility Java RNG uses the canonical `java.util.Random`-compatible implementation, including Java's signed 32-bit overflow behavior in bounded `nextInt`; JVM-derived truth vectors are regression-tested. Installed enchantment definitions/tags are used when available; normal table offers exclude treasure-tagged enchantments. Player RNG is never presented as world-seed recovery.

### Loot & Drop Workbench

The loot workbench reads installed vanilla loot-table JSON, item tags, nested references, conditions, and supported functions. Item-tag object members are normalized and an entry condition is evaluated once per selection attempt rather than resampled during expansion. Context-dependent branches remain labeled instead of receiving fabricated exact probabilities.

Loot table browsing is cached per installed JAR. Large simulations execute off the GUI thread and provide cooperative cancellation during the pull loop rather than freezing the explorer.

### Generation RNG Workbench

Decoration, feature-position, ore-position, tree/geode frequency, trial-chamber, and structure-placement models remain separate modes with explicit model limits. Candidate RNG positions are not presented as final generated features.

### Minecraft Mechanics Lab

Brewing, leather dye/cauldron behavior, and animal/horse breeding share a mechanics workbench. Brewing transitions that are code-defined in Java are labeled as an internal vanilla rule model. Java leather-dye mixing uses brightness-preserving RGB behavior; cauldron washing remains separate. Breeding exposes species-specific fields instead of copying unrelated runtime NBT into offspring.

## Villagers

**Villager Explorer** is a full visual explorer rather than a flat trade table. It includes:

- profession/level/item search and direction filtering;
- installed villager profession/type skin layers and item icons when available;
- trade favorites and Favorites-only filtering;
- planned-use count, max-use/restock context, villager XP, source definition, and approximate emerald flow;
- a trade comparison list;
- librarian-focused workflows and explicit installed/reference source labeling;
- Zombie Cure, Villager Hall, Workstation Count, and Breeding Food helpers through the canonical executor.

Trade data and artwork are independent. Exact installed definitions are preferred; otherwise the planning reference is labeled as non-exact.

## Profiles, controls and calibration

The Profiles, Controls & Calibration workbench edits the canonical Minecraft action bindings used by `BoundInput`, coordinate-capture delay, turn units per 90 degrees, and movement planning speed. Full settings can be backed up/exported/imported as JSON. Import creates a local pre-import backup before applying recognized settings and keybindings.

Global Emergency Stop, Pause/Resume, and Copy Sister Coordinates hotkeys remain configurable under Options.

## Results and visualization

Normal result presentation removes private/internal dispatch keys and shows readable labels plus status, purpose, source/exactness context, warnings/notes, and structured tables. Maps and charts use explicit operation contracts instead of guessing meaning from numeric values. Declared X/Z viewers support wheel zoom, drag panning, fit-to-data, layer visibility, point labels, cursor coordinates, and copying visible coordinate layers.

**Result History** stores a bounded local record of recent calculations including timestamp, workbench, operation, selected Minecraft version, note, and data. Individual entries can be inspected or exported as JSON; history can be cleared without affecting settings/world data.

## Diagnostics

Diagnostics reports the linked client, active input backend/session and background/minimized capability labels, installed Minecraft versions, Cubiomes/Nether Bedrock component readiness, configuration path, and local saved-state counts. It is intended to make platform/component failures diagnosable without exposing world data externally.

## Appearance

The user-selectable themes are **Chorus, Light, Cyber, Vanilla, and Custom**. Custom exposes the F3+ palette and can optionally use recovered Minecraft artwork. Minecraft client/server JARs and Mojang assets are not redistributed.

## Version and source accuracy

F3+ keeps three concepts separate:

- **Selected Minecraft version** — what the user targets.
- **Calculation/world-generation version** — the actual rules used by the active backend.
- **Local data version** — the installed client JAR supplying definitions or artwork.

Bundled Cubiomes mappings are explicitly bounded through Minecraft 1.21.3. Unsupported newer selections remain visible while the actual supported calculation fallback is labeled.

Generated-terrain operations can inspect a Java save or, where supported, create bounded Mojang reference chunks after explicit EULA acceptance. Exact-generation integration tests compare F3+ predictions with an independently generated Mojang server world. Tick-sensitive cave/air/fluid state is labeled separately from immutable generation facts.

## Updates and release channel

Automatic updates follow the validated **Stable** branch by default. Development `main` is available only through the explicit Preview channel (`F3PLUS_UPDATE_CHANNEL=preview`). Update failures never prevent the installed build from opening offline.

## Architecture boundary

The visible workbench registry is canonical. The 457 historical IDs remain compatibility aliases. Importing `minescript` does not install patches or rewrite classes. New behavior is composed through explicit executor/services and public workbench owners. Legacy model libraries that still contain valid calculations remain compatibility fallbacks until those algorithms are migrated; dormant installer functions are not invoked at runtime.