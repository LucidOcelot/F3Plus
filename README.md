# F3+ 2.4.0

**A local technical Minecraft workstation for vanilla Java Edition.**

F3+ combines technical Minecraft analysis, planning, simulation, navigation, generated-world inspection, and optional automation in one cross-platform desktop application. It is designed to work with an ordinary unmodified Minecraft Java client and to keep world, seed, coordinate, project, and planning data local whenever the selected workflow does not require an external component download.

**Release:** 2.4.0  
**Default Minecraft target:** 26.3 Snapshot 7  
**Python:** 3.11 through 3.13

## Start

- **Windows:** extract the ZIP and run `START_F3PLUS.bat`.
- **macOS:** extract the ZIP and run `START_F3PLUS.command`. Automation may require Accessibility/Input Monitoring permission.
- **Linux:** run `START_F3PLUS.sh`. Calculators and foreground workflows do not depend on background-input support.

The launcher prepares a project-local environment and required Python packages when needed. Installed copies continue to launch when update checks are unavailable. Launch-time updates are check-only by default; installation requires explicit opt-in.

## Workbenches

F3+ does not present every historical command, preset, report, and compatibility ID as a separate application. Related operations live inside task-oriented workbenches:

- **Automation** — continuous actions, travel, mining, farming, construction, parameterized routines, and Macro Studio for reusable sequences.
- **Navigation** — live position, coordinate/travel math, persistent waypoints and groups, coordinate history, routes/surveys, and portal networks.
- **World Explorer** — known-seed structure/biome/slime analysis, generated spawners, Nether analysis, local-area reports, generated-world inspection, and World Profiles for local Java saves.
- **Build & Technical** — shapes/build planning, redstone/timing, storage/logistics, farms, technical mechanics, resource use, speedrun/End utilities, and an installed-data Recipe & Material Explorer.
- **Simulation & RNG** — enchanting/anvil/RNG recovery and timelines, loot/drop exploration, generation RNG models, brewing/dye/cauldron mechanics, and animal/horse breeding.
- **Villagers** — one visual explorer for professions, levels, direction filters, trade search/comparison/favorites, librarians, planned uses/restocks, emerald flow, curing, breeding, workstations, and halls.
- **Utilities & Safety** — Minecraft/data version status, profiles, bindings/calibration, component diagnostics, result history/export, and automation safety.

Historical feature IDs remain an internal compatibility namespace for saved favorites, recents, scripts, and settings. All 457 historical IDs resolve to the matching canonical workbench operation rather than appearing as hundreds of duplicate buttons.

## Project workbenches

**Macro Studio** records or manually assembles tap/click/wait/hold/turn/slot sequences, shows a dry timeline, saves local macros, imports/exports JSON, and runs them through the same `MacroEngine` safety controls as built-in automation.

**World Profiles & Local Saves** discovers standard Java singleplayer saves and reads `level.dat` locally for world name, version, seed, spawn, and related context. Applying a profile reuses that context in F3+; the world is not modified.

**Recipe & Material Explorer** reads recipe definitions from an installed Minecraft client JAR. It can search recipes and expand a target into a recursive material bill. Alternative ingredients use the first listed choice for planning and unresolved tags remain explicitly marked instead of being guessed.

**Result History** keeps recent calculations locally under the F3+ user-data folder and can export an individual result as JSON. **Diagnostics** reports input-backend state, installed Minecraft versions, component readiness, configuration paths, and saved-state counts.

A **Command Palette** (`Ctrl+K`) searches canonical workbenches and historical operation names without restoring the old flat catalog UI.

## Results and explorers

Configuration fields include contextual help and accessibility descriptions. Search-oriented dialogs explain Radius search, Search until found, maximum radius, exact generation, EULA acceptance, and the explicit ignore-limit override; controls that do not apply to the selected search mode are disabled.

Structured results display status, source and exactness context while hiding internal dispatch metadata. Coordinate-bearing world, route, structure, and planning results can open an interactive X/Z view with wheel zoom, drag panning, fit-to-data, layer visibility, optional point labels, and copyable visible coordinates.

The Villager Explorer uses villager entity/type/profession skin layers and item textures recovered from an installed Java client when available. Trade data and artwork are independent: installed trade definitions are preferred, while a clearly labeled planning baseline keeps the explorer usable when exact local trade data is unavailable.

Simulation workbenches read installed loot tables, enchantment definitions, tags, recipes, and textures where Minecraft exposes them. Fallback datasets are labeled as baseline/reference data rather than being presented as exact selected-version results.

## Search and exactness

Location-oriented finders use **Radius search** or **Search until found**. Search until found expands outward by a configurable step and normally stops at a user-selected maximum.

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

Themes available under Options are **Chorus, Light, Cyber, Vanilla, and Custom**. Custom can use the recolorable F3+ artwork or recovered Minecraft assets where available.

## Documentation and security

`FEATURES.md` documents the workbenches and accuracy boundaries. `SECURITY.md` documents downloads, permissions, written files, automation privileges, and responsible disclosure. `COMMUNITY_CREDITS.md` records community lineage, `THIRD_PARTY.md` covers third-party software/license boundaries, and `LICENSE.md` contains the F3+ license.

## AI-assisted development disclosure

Generative AI was used during development for code translation/porting, refactoring, integration, debugging, test construction, UI iteration, and documentation. Project direction, feature selection, testing feedback, revisions, release decisions, and final inclusion decisions remained human-directed and human-reviewed.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.
