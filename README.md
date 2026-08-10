# F3+ 2.5.3

**A local technical Minecraft workstation for vanilla Java Edition.**

F3+ combines technical Minecraft analysis, planning, simulation, navigation, generated-world inspection, and optional automation in one cross-platform desktop application. It is designed for an ordinary unmodified Minecraft Java client and keeps user data local whenever the selected workflow does not require an external component download.

**Release:** 2.5.3  
**Default Minecraft target:** 26.3 Snapshot 7  
**Python:** 3.11 through 3.13

## Start

- **Windows:** extract the ZIP and run `START_F3PLUS.bat`.
- **macOS:** extract the ZIP and run `START_F3PLUS.command`. Automation may require Accessibility/Input Monitoring permission.
- **Linux:** run `START_F3PLUS.sh`. Calculators and foreground workflows do not require background-input support.

The launcher prepares a project-local environment and required Python packages when needed. Installed copies continue to launch when update checks are unavailable.

F3+ normally installs validated **Stable** updates before launch. Stable does not follow rolling development commits. Set `F3PLUS_UPDATE_CHANNEL=preview` to follow `main`, `F3PLUS_AUTO_UPDATE=0` for check-only behavior, or `F3PLUS_SKIP_UPDATE=1` to skip the network check.

## 2.5.3 desktop UI

2.5.3 replaces the previous three-column catalog shell with a **professional desktop shell** built around task selection rather than catalog browsing. The permanent structure is now:

- a compact top bar for Minecraft link/input/safety state;
- a context bar for global search, dimension, version, world seed, and position capture;
- a left workspace rail;
- a responsive central grid of workbench cards;
- a **contextual inspector** that explains the selected workbench before it opens;
- a searchable `Ctrl+K` command palette for current workbenches and historical operation names.

Every launch path uses the same canonical workbench owner. Home, search, favorites, double-click, menus, and Command Palette no longer send the same tool to different generic dialogs. Dedicated workbenches such as RNG & Enchanting, Loot, Mechanics, Villagers, Macro Studio, World Profiles, Recipes, Safety, History, and Diagnostics open their purpose-built UI directly.

Field help is part of the normal interface rather than hidden documentation. Generic operation panels show what the operation does, which inputs it actually uses, inline explanations, examples/defaults, matching tooltips, and accessibility descriptions. Compatibility defaults used internally are not presented as fake user inputs.

## Workbenches

F3+ does not expose every historical command, preset, report, and compatibility ID as a separate application. Related operations live inside task-oriented workbenches:

- **Automation** — continuous actions, travel, mining, farming, construction, parameterized routines, and Macro Studio.
- **Navigation** — live position, coordinate/travel math, waypoints, routes/surveys, and portal networks.
- **World Explorer** — Structure, Spawner, Biome & Terrain, Slime, Nether, Local Area, World Analysis, **Ore & Cave Explorer**, and World Profiles/Local Saves.
- **Build & Technical** — block-layer shape/build planning, redstone/timing, storage/logistics, farms, technical mechanics, resources, speedrun/End tools, and Recipe & Material Explorer.
- **Simulation & RNG** — Minecraft-style Enchanting Table and Anvil planning, RNG/recovery/probability, loot/drop exploration, generation RNG, brewing, dye/cauldron mechanics, and animal/horse breeding.
- **Villagers** — a virtualized visual explorer for professions, levels, direction filters, all matching trades, comparison/favorites, planned uses/restocks, emerald flow, curing, breeding, workstations, and halls.
- **Utilities & Safety** — Minecraft/data version status, profiles, bindings/calibration, diagnostics, result history/export, and automation safety.

All 457 historical feature IDs remain compatibility aliases for saved favorites, recents, scripts, and settings. They resolve to the matching canonical workbench operation rather than reappearing as hundreds of duplicate buttons.

## Search Center, world data, and exactness

World/search tools use one shared **Search Center** where location actually affects the result. Choose **Current position**, **Block coordinates**, or **Center chunk**; F3+ converts that choice to the internal coordinate representation required by the calculation. Spawn-centered and location-independent operations do not display a fake center input.

Location-oriented finders use **Radius search** or **Search until found**. Search Until Found expands outward by a configurable step and normally stops at a selected maximum. Supported long-running searches remain responsive and check cooperative cancellation between safe expansion attempts.

An advanced **Ignore maximum search / generation limit** option can continue beyond the configured maximum. Exact generation can consume substantial CPU, memory, disk, and time, so the UI states that cost explicitly.

F3+ keeps three version concepts separate: selected Minecraft version, actual calculation/world-generation version, and installed local-data version. Placement candidates are not mislabeled as confirmed generated structures, and generated-world observations are not mislabeled as seed-only predictions.

Generated-terrain tools can inspect an existing Java save. Where supported, F3+ can create bounded reference chunks with Mojang's matching server JAR after explicit EULA acceptance. Bundled Cubiomes mappings remain explicitly bounded through Minecraft 1.21.3.

**World/structure-seed recovery is limited to the Nether Bedrock Cracker workflow.** Gameplay/player RNG recovery belongs to Simulation & RNG and is never presented as world-seed recovery.

## Ore & Cave Explorer

Ore Distribution, Ore Exposure Estimate, Cave Exposure Estimate, and Ancient City Area Analysis are first-class World Explorer operations instead of being buried inside a broad World Analysis list.

Ore/exposure/cave operations request only the values their active handlers use. Observed ore/cave analysis requires generated block-state data or supported bounded Mojang reference generation; F3+ does not invent ore coordinates from a placement-only seed model.

## Simulation & RNG

The public simulator UI is an abstraction layer over Minecraft data rather than an NBT/JSON editor.

**Minecraft-style Enchanting Table** uses a visual item picker, bookshelf control, reproducibility seed, and three offer cards. Installed enchantment definitions/tags are preferred and treasure-only enchantments are excluded from normal table rolls.

**Anvil** uses left item, sacrifice/book, result, visual enchantment editors, prior-work fields, rename option, and level-cost/prior-work/survival metrics. Users do not type enchantment JSON.

**Loot & Drop Workbench** indexes installed loot data in the background. Simulations run outside the UI thread, show a visible activity strip, retain their inputs, and expose cooperative cancellation. Source/version/context limitations remain visible.

**Minecraft Mechanics Lab** presents brewing, leather dye/cauldron behavior, and animal/horse breeding through mechanic-specific controls rather than raw parent NBT.

## Villager Explorer

Villager Explorer is a virtualized explorer rather than a full `QTableWidget` rebuild. It paints only visible trade cards, retains every matching loaded trade, and makes a complete labeled reference dataset available immediately while installed-version trade data loads in the background.

The detail panel represents the actual wants → gives transaction with item artwork, profession/level/source, max uses, planned restocks, emerald flow, XP/details, favorites, and comparison state. Profession portraits and item textures are recovered from the installed client when possible.

## Results and visualization

Structured results display status, source, purpose, limitations, and exactness context while hiding internal dispatch metadata. World-coordinate results can show an interactive X/Z map with zoom, pan, layers, optional labels, and copyable coordinates.

Unordered structure/slime/search candidates render as scatter points. Lines appear only for declared ordered routes. Statistical charts include category labels rather than unlabeled bars.

Shape/build results use a separate **block blueprint** renderer. Two-dimensional layouts show Minecraft block cells directly; 3D spheres, cylinders, domes, helices, and related shapes expose selectable Y layers instead of flattening every layer into a misleading X/Z map.

## Minecraft artwork and themes

F3+ first attempts to recover suitable artwork from the selected/available installed Minecraft Java JAR. 2.5.3 adds a conservative semantic fallback search for cases where Mojang has moved or renamed a texture while retaining the same recognizable item/block concept.

When suitable installed artwork is unavailable, F3+ uses original **recolorable F3+ SVGs** rather than recycling one generic glyph. Minecraft client/server JARs and Mojang texture files are not redistributed.

The existing themes remain **Chorus, Light, Cyber, Vanilla, and Custom**. Chorus, Light, and Vanilla prefer locally recovered Minecraft art. Custom can choose recovered Minecraft assets or original recolorable art. Cyber retains its distinct non-Vanilla visual treatment.

## Automation and safety

Automation links to a detected Minecraft Java process rather than trusting only a window title. If the linked client disappears, managed automation stops and held input is released. Depending on the platform/backend, automation can use targeted background input, focus switching, or foreground-only input.

Runtime/action limits, delayed start, coordinate recovery attempts, hotbar restoration, stuck detection, focus-loss stop, configurable global hotkeys, Pause/Resume, and Emergency Stop are active controls. Safe Mode is a conservative multiplayer filter; it does not replace server rules.

## Validation

CI validates Windows, macOS, and Ubuntu on Python 3.11, 3.12, and 3.13. The native Cubiomes bridge compiles with strict warnings, Mojang exact-world integration is independently checked, and a full semantic audit verifies all 457 historical aliases, workbench launch ownership, public field explanations, theme availability, and artwork recovery contracts.

Windows CI also captures native screenshots for all five themes and the major workbench/result surfaces, including Search Center, Ore & Cave, Automation, Villagers, Enchanting, Anvil, RNG, Mechanics, Loot, structure scatter maps, labeled ore charts, and layered block blueprints.

## Documentation and security

`FEATURES.md` documents the workbenches and accuracy boundaries. `SECURITY.md` documents downloads, permissions, written files, automation privileges, and responsible disclosure. `COMMUNITY_CREDITS.md` records community lineage, `THIRD_PARTY.md` covers third-party software/license boundaries, and `LICENSE.md` contains the F3+ license.

## AI-assisted development disclosure

Generative AI was used during development for code translation/porting, refactoring, integration, debugging, test construction, UI iteration, and documentation. Project direction, feature selection, testing feedback, revisions, release decisions, and final inclusion decisions remained human-directed and human-reviewed.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.
