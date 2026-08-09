# F3+ 2.3.4

**A local technical Minecraft workstation for vanilla Java Edition.**

F3+ combines technical Minecraft analysis, planning, simulation, navigation, generated-world inspection, and optional automation in one cross-platform desktop application. It is designed to work with an ordinary unmodified Minecraft Java client and to keep world, seed, coordinate, and planning data local whenever the selected workflow does not require an external component download.

**Release:** 2.3.4  
**Default Minecraft target:** 26.3 Snapshot 7  
**Python:** 3.11 through 3.13

## Start

- **Windows:** extract the ZIP and run `START_F3PLUS.bat`.
- **macOS:** extract the ZIP and run `START_F3PLUS.command`. Automation may require Accessibility/Input Monitoring permission.
- **Linux:** run `START_F3PLUS.sh`. Calculators and foreground workflows do not depend on background-input support.

The launcher prepares a project-local environment and required Python packages when needed. Installed copies continue to launch when update checks are unavailable.

## Workbenches

F3+ no longer presents every historical command, preset, report, and compatibility ID as a separate application. Related operations live inside a small set of task-oriented workbenches:

- **Automation** — continuous actions, travel, mining, farming, construction, and multi-step sequences.
- **Navigation** — live position, coordinate/travel math, waypoints/routes/surveys, and portal networks.
- **World Explorer** — known-seed structure/biome/slime analysis, generated spawners, Nether analysis, local-area reports, and generated-world inspection.
- **Build & Technical** — shapes/build planning, redstone/timing, storage/logistics, farms, technical mechanics, resource use, speedrun, and End utilities.
- **Simulation & RNG** — enchanting/anvil/RNG recovery and timelines, loot/drop exploration, generation RNG models, brewing/dye/cauldron mechanics, and animal/horse breeding.
- **Villagers** — one visual explorer for professions, levels, trades, search/comparison, librarians, emerald/use planning, curing, breeding, workstations, and halls.
- **Utilities & Safety** — Minecraft/data version status, profiles, controls/calibration, component state, and automation safety.

Historical feature IDs remain an internal compatibility namespace for saved favorites, recents, scripts, and settings. They resolve to the matching workbench operation rather than appearing as hundreds of duplicate buttons.

## Results and explorers

Tools request only the values used by the selected operation. Structured results use readable units and labels instead of exposing internal dictionaries as the primary UI. Coordinate-bearing world, route, structure, and planning results can open an interactive X/Z view with wheel zoom, drag panning, fit-to-data, layer visibility, optional point labels, and copyable visible coordinates.

The Villager Explorer uses villager entity/type/profession skin layers and item textures recovered from an installed Java client when available. Trade data and artwork are independent: installed trade definitions are preferred, while a clearly labeled planning baseline keeps the explorer usable when exact local trade data is unavailable.

Simulation workbenches read installed loot tables, enchantment definitions, tags, and textures where Minecraft exposes them. Fallback datasets are labeled as baseline/reference data rather than being presented as exact selected-version results.

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

Automation links to a detected Minecraft Java process rather than trusting window-title text alone. F3+ reports whether the current platform/backend can deliver targeted background input, requires focus switching, or is foreground-only.

Emergency Stop releases tracked held input. Pause/Resume and the main global hotkeys are configurable under **Options → Automation**. Safe Mode is a conservative multiplayer filter; it does not replace a server's rules.

## Local data, network use, and assets

Prepared calculations, settings, installed-data browsing, and generated-save analysis run locally. Network access may be required for dependency/component acquisition, update checks, optional upstream helpers, or Mojang reference-world acquisition.

F3+ does not bundle Minecraft client/server JARs or Mojang texture files. Minecraft artwork shown in the interface is read from the player's installed Java files at runtime when available.

## Documentation and security

`FEATURES.md` documents the workbenches and accuracy boundaries. `SECURITY.md` documents downloads, permissions, written files, automation privileges, and responsible disclosure. `COMMUNITY_CREDITS.md` records community lineage, `THIRD_PARTY.md` covers third-party software/license boundaries, and `LICENSE.md` contains the F3+ license.

## AI-assisted development disclosure

Generative AI was used during development for code translation/porting, refactoring, integration, debugging, test construction, UI iteration, and documentation. Project direction, feature selection, testing feedback, revisions, release decisions, and final inclusion decisions remained human-directed and human-reviewed.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.
