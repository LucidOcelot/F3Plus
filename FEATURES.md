# F3+ Workbench Guide

F3+ 2.4.2 is an offline-first technical companion for Minecraft Java Edition. The default target is **26.3 Snapshot 7**. The desktop UI is organized by user task; the 457 historical feature IDs are compatibility aliases, not separate applications.

## Shared interaction model

1. Choose a workbench or use `Ctrl+K` Command Palette.
2. Choose the operation inside it.
3. Read what the operation calculates, what each visible input means, and what output to expect.
4. Enter only the user-facing values required by that operation.
5. Run it and inspect structured output, source/exactness context, limitations, and any explicitly declared visual result.

Compatibility defaults required by older calculation code are not shown as user inputs. Field explanations are operation-aware: a simulation/RNG seed is identified as a reproducibility seed rather than a world seed, and expensive search/generation limits explain their resource cost.

World/search operations use one shared **Search Center** when location matters. The user can select Current position, Block coordinates, or Center chunk. F3+ converts that value into the compatibility coordinate keys required internally. Spawn-centered and location-independent operations do not display a fake center control.

Long-running workbench jobs run outside the Qt event thread where practical. Visible indeterminate progress/activity controls identify JAR indexing, trade loading, world/search work, and simulations; supported jobs expose cooperative Cancel.

## Automation

**Automation Studio** is a purpose-built control surface rather than a calculator shell. It groups continuous/periodic actions and equipment routines by gameplay task, shows live link/input/Safe Mode/session state, and exposes Start, Configure & Start, and Stop controls according to the routine. **Travel & Mobility**, **Mining & Excavation**, **Farm Automation**, and **Construction Automation** group related routines instead of presenting each preset as an independent application.

### Macro Studio

Macro Studio supports tap, click, wait, hold, turn, and hotbar-slot steps; built-in templates; manual editing/reordering; optional keyboard/mouse recording; a dry timeline; looped or one-pass playback; local save/delete and JSON import/export; and execution through `MacroEngine` so global stop/pause and configured safety limits still apply.

## Navigation

**Live Position** handles F3+C capture, current coordinate/chunk results, continuous position monitoring, distance announcements, and bearing-to-target monitoring. Capture/convert/save operations return visible workbench results instead of silent action placeholders.

**Coordinate & Travel Calculator** combines distance, bearing, midpoint, XYZ delta, travel time, chunk/region geometry, snapping, offsets, and Overworld/Nether conversion.

**Waypoints, Routes & Surveys** owns persistent waypoint state and route/survey operations. **Portal Network Planner** combines sister-coordinate math, competing exits, asymmetric routing, reliability geometry, bidirectional matrices, graphs, route comparison, and network planning.

## World Explorer

**World Seed Recovery** is the Nether Bedrock Cracker path and remains the only world/structure-seed recovery workflow. Player/gameplay RNG recovery is separate.

**Slime Chunk Explorer**, **Structure Explorer**, **Spawner Explorer**, **Biome & Terrain Explorer**, **Local Area Analyzer**, **World Analysis**, and **Nether Explorer** retain their dedicated domains. Placement candidates and observed/generated facts remain visibly distinct.

### Search center and exact generation

Location-oriented seed/world tools can center on the current captured player position, entered block coordinates, or a center chunk. Radius search and Search until found remain separate modes. Exact/reference-world generation is opt-in after Minecraft EULA acceptance and reports selected version, calculation version, and local-data version separately.

Search Until Found can expand a reusable reference-world cache rather than creating an unrelated complete world directory for every radius. Cancellation is checked between safe expansion attempts.

### Ore & Cave Explorer

Ore-related operations are no longer hidden inside the general World Analysis list. **Ore Distribution**, **Ore Exposure Estimate**, **Cave Exposure Estimate**, and **Ancient City Area Analysis** resolve to the canonical Ore & Cave Explorer while their historical IDs remain valid.

Ore/exposure/cave operations show only fields their active handlers use: world seed, dimension, search center, radius, and generated-world source/exact-generation controls where supported. Comparison seed and simulation-distance fields are not leaked into these forms.

Observed ore/cave analysis requires generated block-state data or supported bounded Mojang reference generation. F3+ does not invent ore coordinates from a placement-only seed model.

### World Profiles & Local Saves

World Profiles discovers standard local Java `saves` folders or accepts an explicitly selected world folder. `level.dat` is read locally for available world name, DataVersion/version name, seed, spawn, mode/hardcore state and last-played metadata. Applying a profile reuses context in F3+ without modifying the world.

## Build & Technical

**Build & Shape Planner** separates Build Calculators from Shape Layouts. Shape forms expose only dimensions the selected shape consumes—for example, Arch/Circle/Diamond use radius, Ellipse uses two radii, and cylinder/cone/helix families expose their required height/turn controls.

Shape results use a dedicated **block blueprint** visualizer rather than the world map renderer. Each square is one Minecraft block in X/Z. Three-dimensional shapes expose a Y-layer selector so spheres, domes, cylinders and helices can be built slice-by-slice instead of being flattened into an incorrect-looking projection.

**Redstone & Timing Lab**, **Storage & Logistics**, **Farm & Breeding Planner**, **Technical Minecraft Calculator**, and **Resource, Speedrun & End Toolkit** retain their distinct calculations while sharing the explained panel/explorer interaction model.

### Recipe & Material Explorer

The Recipe & Material Explorer reads installed Minecraft recipe JSON directly from the selected/available client JAR. It can search by recipe ID, result item, or recipe type, inspect ingredient slots, and recursively expand a target output into a material bill.

## Simulation & RNG

### RNG & Enchanting Workbench

The workbench paints immediately, then reads installed enchantment data in the background with visible activity state.

**Enchanting Table** uses a visual Minecraft-item picker, bookshelf control, reproducibility seed, and three offer cards. Installed enchantment definitions/tags are preferred and treasure-only enchantments are excluded from normal table rolls.

**Anvil** uses left item/sacrifice/result slots, visual item selection, add/remove enchantment controls, prior-work fields, rename option, and visible level-cost/prior-work/survival metrics. Users do not type enchantment JSON.

The RNG/Recovery/Probability panel groups Java LCG state tools, sequences, probability/odds planning, and EnchantmentCracker. Gameplay/player RNG is never presented as the world seed.

### Loot & Drop Workbench

Installed loot-table indexing happens in the background and reports activity. Large simulations execute off the GUI thread with an explicit progress strip and Cancel button. The simulator keeps source/version/context limitations visible.

### Generation RNG Workbench

Decoration, feature-position, ore-position, tree/geode frequency, trial-chamber, and structure-placement models remain separate modes with explicit model limits. Candidate RNG positions are not presented as final generated features.

### Minecraft Mechanics Lab

The mechanics lab is a player-facing abstraction layer rather than an NBT/JSON editor.

- **Brewing Stand** presents current potion + ingredient → output and explains the modeled transition.
- **Leather Dye & Cauldron** uses selectable color swatches, visible resulting leather color, and a separate wash/water-level action.
- **Animal & Horse Breeding** exposes only species-specific breeding traits and shows human-readable offspring outcome distributions. UUIDs, brain memories, timers, positions, and raw parent NBT are not normal UI inputs.

## Villagers

**Villager Explorer** is a virtualized three-panel browser, not a `QTableWidget` trade dump.

- A profession rail can use recovered installed villager type/profession skin layers.
- The center panel paints only visible trade cards, so filtering does not rebuild widgets for every offer.
- Every matching loaded trade remains in the model; results are not truncated to an arbitrary first 25 rows.
- The detail panel shows the actual wants → gives transaction with item artwork, level/profession/source, max uses, planned restocks, emerald flow, XP/details, favorites, and comparison state.
- A complete labeled reference dataset appears immediately. Installed-version trade data is checked in the background and replaces the reference when available.
- Zombie Cure, Villager Hall, Workstation Count, and Breeding Food helpers remain adjacent planning workflows.

## Results and visualization

Normal results display status, purpose, source/exactness context, warnings/notes, and structured tables. Internal dispatch metadata is hidden behind the normal presentation layer; raw structured data is collapsed under an advanced disclosure.

Visuals use explicit semantic contracts:

- unordered structure/slime/search candidates render as scatter points;
- lines appear only for declared ordered routes/paths;
- build shapes use block blueprints/layers rather than world maps;
- statistical charts show category labels;
- arbitrary number pairs/dictionaries never become invented maps/charts.

Interactive X/Z maps support wheel zoom, drag panning, fit-to-data, layer visibility, optional point labels, cursor coordinates, and copying visible coordinates.

## Artwork and themes

F3+ first tries to recover suitable artwork from the selected/available installed Minecraft Java JAR. Semantic recovery includes navigation/map/route, portal, structure, spawner, biome, ore, build/shape, farm, redstone, storage, RNG/enchanting/anvil, loot, brewing, horse, villager/trade, utilities and safety roles.

When a matching Mojang texture is unavailable—or when Custom is configured to use original artwork—the UI falls back to a larger set of original recolorable F3+ SVGs instead of reusing one generic glyph.

The user-selectable themes are **Chorus, Light, Cyber, Vanilla, and Custom**. Minecraft JARs and Mojang assets are not redistributed.

## Version and source accuracy

F3+ keeps three concepts separate:

- **Selected Minecraft version** — what the user targets.
- **Calculation/world-generation version** — the actual rules used by the active backend.
- **Local data version** — the installed client JAR supplying definitions or artwork.

Bundled Cubiomes mappings are explicitly bounded through Minecraft 1.21.3. Unsupported newer selections remain visible while the actual supported calculation fallback is labeled.

Generated-terrain operations can inspect a Java save or, where supported, create bounded Mojang reference chunks after explicit EULA acceptance. Exact-generation integration tests compare F3+ predictions with an independently generated Mojang server world.

## Validation and release channel

CI validates Windows, macOS, and Ubuntu on Python 3.11, 3.12, and 3.13. The native C Cubiomes bridge compiles with strict warnings, and Mojang exact-world integration is independently checked.

Windows CI also captures a native-platform UI artifact covering the main/options themes, search center, Ore & Cave, Automation, Villagers, Enchanting, Anvil, RNG, Mechanics, Loot, structure scatter maps, labeled ore charts, and layered block blueprints. This catches layout/visual regressions that widget-existence assertions cannot.

Automatic updates follow the validated **Stable** branch by default. Development `main` is available only through the explicit Preview channel (`F3PLUS_UPDATE_CHANNEL=preview`). Update failures never prevent the installed build from opening offline.

## Architecture boundary

The visible workbench registry is canonical. The 457 historical IDs remain compatibility aliases. Importing `minescript` does not install patches or rewrite classes. New behavior is composed through explicit executor/services and public workbench owners. Legacy model libraries that still contain valid calculations remain compatibility fallbacks until those algorithms are migrated; dormant installer functions are not invoked at runtime.