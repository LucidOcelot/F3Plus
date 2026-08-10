# F3+ 2.4.2

**A local technical Minecraft workstation for vanilla Java Edition.**

F3+ combines technical Minecraft analysis, planning, simulation, navigation, generated-world inspection, and optional automation in one cross-platform desktop application. It is designed to work with an ordinary unmodified Minecraft Java client and to keep world, seed, coordinate, project, and planning data local whenever the selected workflow does not require an external component download.

**Release:** 2.4.2  
**Default Minecraft target:** 26.3 Snapshot 7  
**Python:** 3.11 through 3.13

## Start

- **Windows:** extract the ZIP and run `START_F3PLUS.bat`.
- **macOS:** extract the ZIP and run `START_F3PLUS.command`. Automation may require Accessibility/Input Monitoring permission.
- **Linux:** run `START_F3PLUS.sh`. Calculators and foreground workflows do not depend on background-input support.

The launcher prepares a project-local environment and required Python packages when needed. Installed copies continue to launch when update checks are unavailable.

F3+ normally installs validated **Stable** updates before launch. Stable does not follow rolling development commits. Set `F3PLUS_UPDATE_CHANNEL=preview` to follow `main`, `F3PLUS_AUTO_UPDATE=0` for check-only behavior, or `F3PLUS_SKIP_UPDATE=1` to skip the network check entirely.

## Workbenches

F3+ does not present every historical command, preset, report, and compatibility ID as a separate application. Related operations live inside task-oriented workbenches:

- **Automation** — continuous actions, travel, mining, farming, construction, parameterized routines, and Macro Studio for reusable sequences.
- **Navigation** — live position, coordinate/travel math, persistent waypoints and groups, coordinate history, routes/surveys, and portal networks.
- **World Explorer** — Structure, Spawner, Biome & Terrain, Slime, Nether, Local Area, World Analysis, **Ore & Cave Explorer**, and World Profiles/Local Saves.
- **Build & Technical** — block-layer shape/build planning, redstone/timing, storage/logistics, farms, technical mechanics, resource use, speedrun/End utilities, and an installed-data Recipe & Material Explorer.
- **Simulation & RNG** — Minecraft-style Enchanting Table and Anvil planning, RNG/recovery/probability tools, loot/drop exploration, generation RNG, brewing, dye/cauldron mechanics, and animal/horse breeding.
- **Villagers** — a virtualized visual explorer for professions, levels, direction filters, all matching trades, comparison/favorites, planned uses/restocks, emerald flow, curing, breeding, workstations, and halls.
- **Utilities & Safety** — Minecraft/data version status, profiles, bindings/calibration, component diagnostics, result history/export, and automation safety.

Historical feature IDs remain an internal compatibility namespace for saved favorites, recents, scripts, and settings. All 457 historical IDs resolve to the matching canonical workbench operation rather than appearing as hundreds of duplicate buttons.

## 2.4.2 interaction model

Search/world tools use one shared **Search Center** control where location actually affects the result. Choose **Current position**, **Block coordinates**, or **Center chunk**; F3+ converts that choice to the legacy coordinate fields required internally. Operations that are intentionally spawn-centered or location-independent do not show a fake center input.

The public UI is an abstraction layer over Minecraft data. Player-facing simulators do not require raw NBT or JSON. Enchanting and Anvil use item/enchantment selectors; Brewing uses bottle/ingredient/output slots; leather dyeing uses color swatches; breeding exposes only traits that influence the model.

Long operations show a visible activity indicator and remain responsive. Generic world/search operations, installed-JAR indexing, Loot simulations, RNG/enchanting data loading, and Villager trade loading use background work with cooperative cancellation where the operation can safely stop.

Minecraft artwork is recovered from the selected/local installed Java JAR when a matching texture exists. Missing semantic artwork falls back to original **recolorable F3+ SVGs** rather than reusing one generic glyph. No Mojang artwork is redistributed.

## Workbench behavior

Calculator/explorer workbenches are grouped by their real domain rather than keyword guesses. The selected operation explains what it calculates, shows only its user-facing inputs, describes each input beside the control, and states what type of result to expect before Run is pressed. Compatibility defaults required by older internal calculation code are kept internal and are not presented as fake user inputs.

World Analysis no longer leaks one broad parameter form into unrelated operations. Ore/cave inspection, seed comparison, spawn analysis, chunk-loading simulation, and search-radius planning expose only the values their active handlers actually consume.

**Live Position** returns captured coordinates, chunk, dimension, and source in the workbench. Continuous capture, distance announcement, and bearing monitoring remain dedicated live-state workflows instead of no-output calculator actions.

**Macro Studio** records or manually assembles tap/click/wait/hold/turn/slot sequences, shows a dry timeline, saves local macros, imports/exports JSON, and runs them through the same `MacroEngine` safety controls as built-in automation.

**World Profiles & Local Saves** discovers standard Java singleplayer saves and reads `level.dat` locally for world name, version, seed, spawn, and related context. Applying a profile reuses that context in F3+; the world is not modified.

**Recipe & Material Explorer** reads recipe definitions from an installed Minecraft client JAR. It can search recipes and expand a target into a recursive material bill. Alternative ingredients use the first listed choice for planning and unresolved tags remain explicitly marked instead of being guessed.

**Result History** keeps recent calculations locally under the F3+ user-data folder and can export an individual result as JSON. **Diagnostics** reports input-backend state, installed Minecraft versions, component readiness, configuration paths, and saved-state counts.

A **Command Palette** (`Ctrl+K`) searches canonical workbenches and historical operation names without restoring the old flat catalog UI.

## Results and explorers

Configuration fields include visible contextual help and accessibility descriptions. Search-oriented dialogs explain Radius search, Search until found, maximum radius, exact generation, EULA acceptance, and the explicit ignore-limit override; controls that do not apply to the selected search mode are disabled.

Structured results display status, source, purpose, limitations, and exactness context while hiding internal dispatch metadata. World-coordinate results can show an interactive X/Z map with zoom, pan, layer visibility, optional point labels, and copyable coordinates. Unordered candidates are rendered as points; route lines appear only for explicitly ordered paths.

Shape/build results use a separate **block blueprint** renderer. Two-dimensional layouts show Minecraft block cells directly; 3D spheres, cylinders, domes, helices and related shapes expose selectable Y layers instead of flattening every layer into a misleading X/Z map.

Declared statistical outputs can render labeled charts alongside structured tables. F3+ does not interpret arbitrary numeric arrays as maps or charts.

The **Villager Explorer** renders only visible trade cards instead of rebuilding a full widget table. A complete labeled reference dataset is available immediately; installed-version trade data is checked in the background and replaces the reference when available. Profession portraits and item textures are recovered from the installed client when possible.

The **Ore & Cave Explorer** exposes Ore Distribution, Ore Exposure Estimate, Cave Exposure Estimate, and Ancient City Area Analysis as first-class operations. Ore/exposure/cave results require generated block-state data or supported bounded Mojang reference generation; F3+ does not invent ore coordinates from a placement-only seed model.

## Search and exactness

Location-oriented finders use **Radius search** or **Search until found**. Search until found expands outward by a configurable step and normally stops at a user-selected maximum. Long-running expanding searches support cooperative cancellation between search attempts.

An advanced **Ignore maximum search / generation limit** option is available for supported searches. It can substantially increase CPU, memory, disk, and runtime use. Exact reference-world searches can also increase the generated-chunk budget as the radius grows; backend failures and an internal runaway-loop guard can still stop the process.

F3+ keeps three version concepts separate:

1. **Selected Minecraft version** — what the user is targeting.
2. **Calculation/world-generation version** — the actual rules used by the active backend.
3. **Local data version** — the installed client JAR used for data-driven definitions or artwork.

Bundled Cubiomes mappings are explicitly bounded through Minecraft 1.21.3. A newer selected version remains visible when a supported calculation fallback is used; F3+ does not label that fallback as snapshot-exact generation.

Generated-terrain tools can inspect an existing Java save. Where supported, F3+ can instead create bounded reference chunks with Mojang's matching server JAR after explicit EULA acceptance. Required Java versions and compatible runtimes are discovered before generation.

**World/structure-seed recovery is limited to the Nether Bedrock Cracker workflow.** Gameplay/player RNG recovery belongs to the RNG & Enchanting workbench and is never presented as world-seed recovery.

## Minecraft linking and automation safety

Automation links to a detected Minecraft Java process rather than trusting window-title text alone. When multiple clients are detected, F3+ asks which client to control. If the linked client disappears, managed automation is stopped, held input is released, and the stale targeted backend is discarded.

Automation can use targeted background input, focus switching, or foreground-only input depending on the platform/backend. When F3+ temporarily switches focus for a macro, it can restore the previous application when the run ends.

Runtime/action limits, delayed start, coordinate recovery attempts, hotbar restoration, stuck detection, focus-loss stop, Emergency Stop, Pause/Resume, and configurable global hotkeys are active settings rather than informational descriptors. Safe Mode is a conservative multiplayer filter; it does not replace a server's rules.

## Local data, network use, and assets

Prepared calculations, settings, world profiles, result history, saved macros, installed-data browsing, and generated-save analysis run locally. Network access may be required for dependency/component acquisition, update checks, optional upstream helpers, or Mojang reference-world acquisition.

F3+ does not bundle Minecraft client/server JARs or Mojang texture files. Minecraft artwork shown in the interface is read from the player's installed Java files at runtime when available.

Themes available under Options are **Chorus, Light, Cyber, Vanilla, and Custom**. Custom can use the recolorable F3+ SVG artwork or recovered Minecraft assets where available.

## Documentation and security

`FEATURES.md` documents the workbenches and accuracy boundaries. `SECURITY.md` documents downloads, permissions, written files, automation privileges, and responsible disclosure. `COMMUNITY_CREDITS.md` records community lineage, `THIRD_PARTY.md` covers third-party software/license boundaries, and `LICENSE.md` contains the F3+ license.

## AI-assisted development disclosure

Generative AI was used during development for code translation/porting, refactoring, integration, debugging, test construction, UI iteration, and documentation. Project direction, feature selection, testing feedback, revisions, release decisions, and final inclusion decisions remained human-directed and human-reviewed.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.