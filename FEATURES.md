# F3+ Workbench Guide

F3+ 2.5.3 is an offline-first technical companion for Minecraft Java Edition. The default target is **26.3 Snapshot 7**. The desktop UI is organized by user task; the 457 historical feature IDs are compatibility aliases, not separate applications.

## 2.5 desktop interaction model

The runtime UI is a new professional desktop shell with a compact connection/safety bar, a context bar for global Minecraft state, a workspace rail, a responsive workbench-card canvas, and a contextual inspector. The inspector explains a selected workbench before it opens instead of filling half the main window with a permanent documentation wall.

`Ctrl+K` opens a searchable command palette. Home, search, favorites, double-click, menus, and historical aliases all resolve through the same canonical launch contract, so a tool does not open a different or empty UI depending on how the user reached it.

Generic operation explorers use an operation list on the left and a focused configure/results surface on the right. Each field includes inline helper text, an example/default when useful, the same information as a tooltip/accessibility description, and operation context. Internal compatibility defaults are not shown merely because older engine code accepts them.

The five current themes remain **Chorus, Light, Cyber, Vanilla, and Custom**. Chorus, Light, and Vanilla prefer installed Minecraft artwork; Custom can choose installed Minecraft assets or original recolorable SVGs; Cyber keeps its distinct treatment.

## Shared execution behavior

1. Choose a workbench or use Command Palette.
2. Choose the operation inside it when the workbench contains multiple related jobs.
3. Read what the operation calculates, which values it actually uses, and what result it will return.
4. Enter only the user-facing inputs required by that operation.
5. Run it and inspect structured output, source/exactness context, limitations, and any declared visual result.

World/search operations use one shared **Search Center** when location matters. Choose Current position, Block coordinates, or Center chunk. F3+ converts that value into the compatibility coordinate representation required internally. Spawn-centered and location-independent operations do not display a fake center control.

Long-running workbench jobs run outside the Qt event thread where practical. Visible activity indicators identify installed-JAR indexing, villager trade loading, world/search work, and simulations; supported operations expose cooperative cancellation.

## Automation

**Automation Studio** is a dedicated controller rather than a calculator shell. It groups continuous/periodic actions and equipment routines by gameplay task, shows link/input/Safe Mode/session state, and exposes Start, Configure & Start, and Stop according to the routine.

**Travel & Mobility**, **Mining & Excavation**, **Farm Automation**, and **Construction Automation** group related routines instead of presenting each preset as an independent application.

### Macro Studio

Macro Studio supports tap, click, wait, hold, turn, and hotbar-slot steps; built-in templates; manual editing/reordering; optional keyboard/mouse recording; a dry timeline; looped or one-pass playback; local save/delete; JSON import/export; and execution through `MacroEngine` so global stop/pause and configured safety limits still apply.

## Navigation

**Live Position** handles F3+C capture, current coordinate/chunk results, continuous monitoring, distance announcements, and bearing-to-target monitoring. Capture/convert/save operations return visible results instead of silent action placeholders.

**Coordinate & Travel Calculator** combines distance, bearing, midpoint, XYZ delta, travel time, chunk/region geometry, snapping, offsets, and Overworld/Nether conversion.

**Waypoints, Routes & Surveys** owns persistent waypoint state and route/survey operations. **Portal Network Planner** combines sister-coordinate math, competing exits, asymmetric routing, reliability geometry, bidirectional matrices, graphs, route comparison, and network planning.

## World Explorer

**World Seed Recovery** is the Nether Bedrock Cracker path and remains the only world/structure-seed recovery workflow. Player/gameplay RNG recovery is separate.

**Slime Chunk Explorer**, **Structure Explorer**, **Spawner Explorer**, **Biome & Terrain Explorer**, **Local Area Analyzer**, **World Analysis**, and **Nether Explorer** retain their dedicated domains. Placement candidates and observed/generated facts remain visibly distinct.

### Search Center and exact generation

Location-oriented seed/world tools can center on the current captured player position, entered block coordinates, or a center chunk. Radius Search and Search Until Found remain separate modes. Search Until Found expands after empty results and checks cancellation between safe attempts.

Exact/reference-world generation is opt-in after Minecraft EULA acceptance and reports selected version, calculation version, and local-data version separately. Expanding exact searches can reuse a reference-world cache rather than generating an unrelated full world for every radius.

### Ore & Cave Explorer

Ore-related operations are first-class rather than hidden inside general World Analysis. **Ore Distribution**, **Ore Exposure Estimate**, **Cave Exposure Estimate**, and **Ancient City Area Analysis** route to the canonical Ore & Cave Explorer while their historical IDs remain valid.

Ore/exposure/cave operations show only fields their active handlers use: world seed, dimension, Search Center, radius, and generated-world/exact-generation controls where supported. Comparison seed and simulation-distance fields are not leaked into these forms.

Observed ore/cave analysis requires generated block-state data or supported bounded Mojang reference generation. F3+ does not invent ore coordinates from a placement-only seed model.

### World Profiles & Local Saves

World Profiles discovers standard local Java saves or accepts an explicitly selected world folder. `level.dat` is read locally for available world name, DataVersion/version name, seed, spawn, mode/hardcore state, and last-played metadata. Applying a profile reuses that context in F3+ without modifying the world.

## Build & Technical

**Build & Shape Planner** separates Build Calculators from Shape Layouts. Shape forms expose only dimensions the selected shape consumes—for example, Arch/Circle/Diamond use radius, Ellipse uses two radii, and cylinder/cone/helix families expose their required height/turn controls.

Shape results use a dedicated **block blueprint** visualizer rather than the world map renderer. Each square is one Minecraft block in X/Z. Three-dimensional shapes expose a Y-layer selector so spheres, domes, cylinders, and helices can be built slice-by-slice instead of being flattened into an incorrect-looking projection.

**Redstone & Timing Lab**, **Storage & Logistics**, **Farm & Breeding Planner**, **Technical Minecraft Calculator**, and **Resource, Speedrun & End Toolkit** retain their distinct calculations while sharing the explained operation/result model.

### Recipe & Material Explorer

Recipe & Material Explorer reads installed Minecraft recipe JSON from the selected/available client JAR. It can search by recipe ID, result item, or recipe type, inspect ingredient slots, and recursively expand a target output into a material bill.

## Simulation & RNG

### RNG & Enchanting Workbench

The workbench paints immediately, then reads installed enchantment data in the background with a visible activity state.

**Enchanting Table** uses a visual Minecraft item picker, bookshelf control, reproducibility seed, and three offer cards. Installed enchantment definitions/tags are preferred; treasure-only enchantments are excluded from normal table rolls.

**Anvil** uses left item/sacrifice/result slots, visual item selection, add/remove enchantment controls, prior-work fields, rename option, and visible level-cost/prior-work/survival metrics. Users do not type enchantment JSON.

The RNG/Recovery/Probability panel groups Java LCG state tools, sequences, probability/odds planning, and EnchantmentCracker. Gameplay/player RNG is never presented as the world seed.

### Loot & Drop Workbench

Installed loot-table indexing happens in the background and reports activity. Large simulations execute off the GUI thread with an activity strip and Cancel button. The simulator keeps source/version/context limitations visible.

### Generation RNG Workbench

Decoration, feature-position, ore-position, tree/geode frequency, trial-chamber, and structure-placement models remain separate operations with explicit model limits. Candidate RNG positions are not presented as final generated features.

### Minecraft Mechanics Lab

The mechanics lab is a player-facing abstraction layer rather than an NBT/JSON editor.

- **Brewing Stand** presents current potion + ingredient → output and explains the modeled transition.
- **Leather Dye & Cauldron** uses selectable color swatches, visible resulting leather color, and a separate wash/water-level action.
- **Animal & Horse Breeding** exposes species-specific breeding traits and human-readable offspring distributions. UUIDs, brain memories, timers, positions, and raw parent NBT are not normal UI inputs.

## Villagers

**Villager Explorer** is a virtualized three-panel browser rather than a `QTableWidget` trade dump.

- A profession rail can use recovered installed villager type/profession skin layers.
- The center panel paints only visible trade cards, so filtering does not rebuild widgets for every offer.
- Every matching loaded trade remains in the model; results are not truncated to an arbitrary first 25 rows.
- The detail panel shows the actual wants → gives transaction with item artwork, level/profession/source, max uses, planned restocks, emerald flow, XP/details, favorites, and comparison state.
- A complete labeled reference dataset appears immediately. Installed-version trade data is checked in the background and replaces the reference when available.
- Zombie Cure, Villager Hall, Workstation Count, and Breeding Food helpers remain adjacent planning workflows.

## Results and visualization

Normal results display status, purpose, source/exactness context, warnings/notes, and structured tables. Internal dispatch metadata is hidden from the normal presentation layer; raw structured data is collapsed under an advanced disclosure.

Visuals use explicit semantic contracts:

- unordered structure/slime/search candidates render as scatter points;
- lines appear only for declared ordered routes/paths;
- build shapes use block blueprints/layers rather than world maps;
- statistical charts show category labels;
- arbitrary number pairs/dictionaries do not become invented maps/charts.

Interactive X/Z maps support wheel zoom, drag panning, fit-to-data, layer visibility, optional point labels, cursor coordinates, and copying visible coordinates.

## Artwork and themes

F3+ first tries exact semantic artwork paths in the selected/available installed Minecraft Java JAR. 2.5.3 adds a conservative installed-JAR fallback search by recognizable item/block concept for Mojang texture moves/renames. The fallback is restricted to local `assets/minecraft/textures/item` and `block` resources and does not download or redistribute assets.

When a suitable Minecraft texture is unavailable—or when Custom is configured to use original artwork—the UI uses original recolorable F3+ SVGs instead of reusing one generic glyph.

The user-selectable themes remain **Chorus, Light, Cyber, Vanilla, and Custom**.

## Version and source accuracy

F3+ keeps three concepts separate:

- **Selected Minecraft version** — what the user targets.
- **Calculation/world-generation version** — the actual rules used by the active backend.
- **Local data version** — the installed client JAR supplying definitions or artwork.

Bundled Cubiomes mappings are explicitly bounded through Minecraft 1.21.3. Unsupported newer selections remain visible while the actual supported calculation fallback is labeled.

Generated-terrain operations can inspect a Java save or, where supported, create bounded Mojang reference chunks after explicit EULA acceptance. Exact-generation integration tests compare F3+ predictions with an independently generated Mojang server world.

## Validation and release channel

CI validates Windows, macOS, and Ubuntu on Python 3.11, 3.12, and 3.13. The native C Cubiomes bridge compiles with strict warnings, Mojang exact-world integration is independently checked, and the 2.5.3 full audit verifies all 457 historical aliases, launch ownership, field help, themes, and artwork contracts.

Windows CI captures a native-platform review artifact covering the new main shell in all five themes plus Search Center, Ore & Cave, Automation, Villagers, Enchanting, Anvil, RNG, Mechanics, Loot, structure scatter maps, labeled ore charts, and layered block blueprints.

Automatic updates follow the validated **Stable** branch by default. Development `main` is available only through the explicit Preview channel (`F3PLUS_UPDATE_CHANNEL=preview`). Update failures never prevent the installed build from opening offline.

## Architecture boundary

The visible workbench registry is canonical. The 457 historical IDs remain compatibility aliases. Importing `minescript` does not install patches or rewrite classes. 2.5 adds a new presentation shell and explicit launch/art/help services without adding a runtime monkeypatch layer. Existing domain engines remain behind their canonical executor/service boundary.
