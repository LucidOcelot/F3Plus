# F3+ 2.0 Feature Guide

F3+ is an offline-first technical companion for Minecraft Java Edition. It combines automation, navigation, known-seed analysis, RNG tools, villager planning, building/farming calculators, world inspection, guided setups, and safety controls in one desktop application.

This file describes the parts that are easier to understand outside the app. Individual tools include their own purpose, inputs, output, limitations, and version notes in the Inspector.

## Shared 2.0 interface

Every tool uses the same interaction model:

- **Tool Library** groups tools by the Minecraft task they solve rather than by implementation detail.
- **Inspector** explains what the selected tool does, when it is useful, how to use it, its inputs, output, and relevant limitations.
- **Configure Tool** dialogs use consistent labels, validation-oriented controls, path pickers, and current F3+ state where appropriate.
- **Results** use cards, metrics, tables, warnings, and detail sections instead of raw debug-style text wherever the result can be represented clearly.
- **Version notices** stay visible when a tool is using data or world-generation rules from a version other than the selected Minecraft version.
- **Favorites and recent tools** provide a smaller Home workspace without hiding the complete catalog.

## Tool identity and shared engines

F3+ keeps the historical 457-entry catalog and stable feature IDs for saved favorites, recents, and compatibility. A shared implementation engine is allowed; an unexplained duplicate tool is not.

Two differently named tools must therefore do one of the following:

- expose a genuinely different calculation, filter, route, visualization, or decision;
- present a clearly different user-oriented view over shared math; or
- identify itself as an intentional shortcut/preset into one canonical workflow.

Examples in 2.0 include separate direct/resource/structure/biome/survey route reports; separate chunk-border and chunk-line navigation; separate portal routing, reliability, reciprocity, and graph reports; separate build-stack, shulker, and chest requirements; separate planar Spiral and 3D Helix layouts; and separate RNG sequence, timeline, tree-attempt, geode-frequency, and structure-placement views.

The Villager entries are an intentional exception in navigation rather than implementation: Trade Search, Trade Comparison, Emerald Calculator, Trade Cycle Calculator, Librarian Browser, profession entries, and Trade Browser are modes/presets of the single visual Villager Trade Explorer and are labeled as such.

Guided automation shortcuts work the same way. Entries such as Branch Mine Wizard or Quarry Wizard identify the corresponding canonical Guided Setup instead of pretending the same setup engine is a second algorithm.

The regression suite dry-runs the complete catalog and performs a semantic duplicate scan after removing internal implementation metadata. Unexpected indistinguishable reports are treated as regressions.

## Minecraft version state

F3+ separates three version concepts that were previously easy to confuse:

- **Selected Minecraft version** — the version the user is playing or wants F3+ to target.
- **World-generation calculation version** — the rules actually used by Cubiomes-dependent calculations.
- **Local data version** — the installed Minecraft JAR supplying resources such as villager trade definitions or textures.

These values are not silently treated as interchangeable.

### Unsupported Cubiomes versions

The bundled Cubiomes revision has an explicit stable mapping through **Minecraft 1.21.3**. When the selected Minecraft version is newer or otherwise unsupported, F3+ keeps the selected version unchanged, displays a warning, and uses **1.21.3** as the current stable Cubiomes calculation fallback.

Fallback results are labeled as fallback results. F3+ does not claim that a 1.21.3 world-generation result is exact for a newer snapshot or release.

Tools that use generated saves or official matching-version reference generation can still report their own exact source separately.

## Minecraft linking

Minecraft linking is used only by features that need a live Java client, such as input automation or coordinate capture.

On Windows, F3+ validates that a candidate Minecraft window is owned by a Java process before linking it. A browser tab, GitHub page, documentation window, or other application containing the word “Minecraft” in its title is not considered sufficient evidence that the window is the game.

The command deck shows one authoritative link state. Detailed process/backend information remains available through Connection Status instead of being placed in the normal header.

## Villager Trade Explorer

The old spreadsheet-style villager table has been replaced by a visual explorer.

The explorer reads trade definitions from an installed Minecraft JAR and shows the actual source version in its header. If the selected version is not installed locally, the explorer clearly labels the installed stable version it is using instead.

The interface includes:

- profession navigation with workstation/item artwork;
- Minecraft item/block textures read from the local client when available;
- visual **You Give → You Receive** trade cards;
- Novice through Master level filters;
- buy/sell/exchange direction filters;
- free-text search across items, professions, trade names, and exposed definition details;
- exact max-use and villager-XP details when present in the source definition;
- planned-use emerald totals;
- persistent favorite trades;
- a comparison tray for up to three offers;
- source-definition paths for technical verification.

**Librarian Browser is no longer a separate generic popup.** It opens the same explorer prefiltered to Librarians. Trade Search, Trade Comparison, Emerald Calculator, Trade Cycle Calculator, profession entries, and the normal Trade Browser also open the same interface with the appropriate starting context.

F3+ does not invent trade data that is absent from the selected/local Minecraft resources. Experimental datapacks or server-side rule changes can still differ from local vanilla definitions.

## Workspaces

### Automation

Managed keyboard/mouse workflows for repetitive actions, travel, excavation, farming, equipment handling, construction, custom sequences, and setup-assisted macros. Automation always routes through the macro engine so Emergency Stop can release tracked input.

Examples include continuous attack/use actions, travel presets, coordinate-aware travel, tunnel/branch mining, crop/tree cycles, hotbar workflows, durability/resource guards, and repeated construction paths.

### Navigation

Coordinate capture and conversion, distance/bearing math, chunk and region geometry, waypoints, routes, surveys, breadcrumb tools, and Overworld/Nether portal planning.

Route tools are purpose-specific: a direct Coordinate Route is not the same report as a Resource Route, Structure Tour, Biome Expedition, recorded breadcrumb/expedition summary, or generated Survey Grid Route.

Live-position features can use F3+C capture. Pure coordinate calculators do not require a linked client.

### World & Seed

Known-seed slime tools, Nether analysis, local-area reports, broader world reports, generation components, and the permitted world-seed recovery workflow.

Local-area tools separate biome sampling, structure placement candidates, slime-chunk facts, technical-site context, build-site context, and exploration context rather than recombining the same inputs into several opaque scores.

**Nether Bedrock Cracker remains the only F3+ world/structure-seed recovery path.** Gameplay RNG recovery is a separate system and is never presented as world-seed recovery.

### Structures & Biomes

Structure candidate searches, multi-structure relationships, generated-world spawner inspection, biome lookup/intersection tools, and terrain-region analysis.

Placement candidates are not automatically equivalent to final generated structures. Where biome/terrain viability or generated chunk data is required, the result explains that boundary.

Spawner cluster tools explicitly distinguish two-, three-, four-spawner minimums, exact 2×2 slime layouts versus generic four-chunk slime components, ranking radii, and individual-spawner scans.

Terrain-shape tools that need actual generated block states use generated-world data rather than pretending a biome ID is terrain geometry.

### Calculators

Coordinate/travel math, redstone timing, storage/logistics, technical farm geometry, mob/loading calculations, speedrun planning, resource/durability estimates, and End travel helpers.

Similar calculators now expose their actual question rather than one shared data dump. For example, Storage Capacity asks how much chosen containers hold, while Shulker/Chest Requirement asks how many containers a target item count needs; Render Distance and Simulation Distance are also reported as different concepts.

These are deterministic local calculators unless a tool explicitly identifies a simulation or version-sensitive game mechanic.

### Building & Farming

Material counts, dimensions, storage requirements, stairs/bridges/roads/grids, shape layouts, crop and animal planning, furnace/fuel systems, villager halls, and technical farm layouts.

Construction Grid is a regular spacing grid; Lighting Grid deliberately includes far edges for boundary coverage. Planar Spiral stays on X/Z while 3D Helix rises along Y.

Shape tools return block-coordinate layouts or layers rather than only a nominal radius/diameter.

### RNG

Gameplay/player RNG recovery, enchanting helpers, repeated probability calculations, weighted/user-supplied loot models, and generation-RNG previews.

RNG Sequence Viewer exposes indexed raw Java values; RNG Timeline adds normalized progression/deltas; Enchantment Sequence Simulator groups progression into attempt-sized bundles without claiming exact modern offers. Tree and geode entries are no longer the same Bernoulli report: the tree model reports successful attempt positions, while the geode model reports chunk-level frequency across a sample grid. Structure placement previews use structure placement candidates rather than generic random coordinates.

Probability/loot presets identify their attempt unit and model. The generic Loot Table Simulator accepts user-supplied weighted entries rather than silently applying one fabricated rarity table to every loot source.

RNG tools do not automatically imply exact current-version Minecraft behavior. The Inspector identifies when a workflow is an exact supported recovery method, a deterministic Java-RNG calculation, or a planning/simulation model.

### Villagers

The visual Trade Explorer plus curing, breeding, workstation, and hall-planning tools.

### Guided Setups

Higher-level workflows that combine related measurements for common mining, farming, portal, and building tasks. They are intended to reduce the need to open several calculators manually.

Automation-menu wizard entries are shortcuts to these canonical setups when they share the same planning engine.

### Utilities

Minecraft version/data status, component status, input/calibration controls, profile import/export, settings backups, and control bindings.

### Safety

Emergency Stop, Pause/Resume, held-input release, delayed starts, runtime/action limits, stuck detection, recovery limits, focus-loss behavior, and hotbar restoration.

Safe Mode applies a conservative multiplayer filter to categories that are commonly restricted on strict SMP servers. It does not replace the rules of the server being played.

## Themes

F3+ 2.0 includes seven appearance choices under **Options → Appearance**:

- **Chorus** — default End-inspired dark purple/gold presentation.
- **Light** — conventional bright desktop presentation.
- **Cyber** — high-contrast neon technical presentation.
- **Vanilla** — Minecraft-oriented green/earth palette with local Minecraft artwork where available.
- **Aether** — bright, spacious cartographic teal/coral presentation with softer geometry.
- **Foundry** — dark industrial presentation using furnace orange, brass, oxidized metal tones, and sharper geometry.
- **Custom** — fully editable F3+ palette with an option to use locally recovered Minecraft artwork.

Minecraft artwork is read from the player’s own installed Java files at runtime when the active theme allows it. F3+ does not redistribute Mojang textures.

## Automatic updates

F3+ checks **LucidOcelot/F3Plus `main`** on GitHub at launch.

- A clean Git checkout fast-forwards from `origin/main`.
- An extracted ZIP install compares its saved commit with GitHub and overlays the newer immutable commit archive when one is available.
- User settings in `~/.f3plus` are outside the application tree and are not replaced by updates.
- A Git checkout with tracked local changes is not overwritten automatically.
- Network/update failures do not prevent an already installed copy from launching offline.
- `F3PLUS_SKIP_UPDATE=1` can temporarily disable the launch update check for development or recovery.

After an update, F3+ restarts the launcher so dependency checks and the application both run from the new files.

## Offline and optional network behavior

Normal calculations, browsing, saved settings, locally available Minecraft data, and prepared components run locally. Network access is used only when a feature explicitly needs an upstream component/download, when exact reference-world generation needs Mojang metadata/server files, during dependency setup, or for the launch update check.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.

Third-party software, community lineage, and attribution are documented in `THIRD_PARTY.md` and `COMMUNITY_CREDITS.md`.
