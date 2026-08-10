# F3+ 2.5.4

**A local technical Minecraft workstation for vanilla Java Edition.**

F3+ combines analysis, navigation, generated-world inspection, simulation, planning, and optional automation in one cross-platform desktop app for an unmodified Minecraft Java client.

**Release:** 2.5.4  
**Default Minecraft target:** 26.3 Snapshot 7  
**Python:** 3.11 through 3.13

## Start

- **Windows:** extract the ZIP and run `START_F3PLUS.bat`.
- **macOS:** extract the ZIP and run `START_F3PLUS.command`.
- **Linux:** run `START_F3PLUS.sh`.

The launcher prepares a project-local environment when needed. Installed copies still open when update checks are unavailable.

F3+ normally installs validated **Stable** updates before launch. Set `F3PLUS_UPDATE_CHANNEL=preview` to follow `main`, `F3PLUS_AUTO_UPDATE=0` for check-only behavior, or `F3PLUS_SKIP_UPDATE=1` to skip the network check.

## Desktop UI

The desktop shell uses a compact status bar, global context controls, a workspace rail, workbench cards, a **contextual inspector**, and a searchable `Ctrl+K` command palette. Every launch path resolves to the same workbench instead of opening different generic dialogs.

Operation panels keep the visible copy short. Detailed explanations stay in tooltips and result context rather than repeating the same information above, below, and beside every field.

## Workbenches

- **Automation** — continuous actions, travel, mining, farming, construction, parameterized routines, and Macro Studio.
- **Navigation** — live position, coordinates, waypoints, routes/surveys, and portal networks.
- **World Explorer** — structures, spawners, biomes/terrain, slime, Nether, local-area/world analysis, **Ore & Cave Explorer**, and World Profiles.
- **Build & Technical** — shapes, redstone/timing, storage/logistics, farms, technical mechanics, resources, speedrun/End tools, and Recipe & Material Explorer.
- **Simulation & RNG** — Minecraft-style Enchanting Table, Anvil, RNG/recovery/probability, loot/drop exploration, generation RNG, brewing, leather dye/cauldron mechanics, and horse breeding.
- **Villagers** — a virtualized visual Villager Explorer plus curing, hall, workstation, and breeding-food planning.
- **Utilities & Safety** — version status, profiles, bindings, diagnostics, result history/export, and automation safety.

All 457 historical feature IDs remain compatibility aliases for saved settings, favorites, recents, and scripts. They resolve into the canonical workbenches rather than appearing as hundreds of duplicate buttons.

## Search Center and world sources

Location-aware tools use one shared **Search Center**: Current position, Block coordinates, or Center chunk.

Generated-world analyzers that need actual block/entity data offer a clear **Data source** choice:

- **Seed** — F3+ creates only the bounded reference area needed for the scan with Mojang's matching Java server after EULA acceptance.
- **World save** — F3+ reads an existing Java world folder locally.

The same analysis runs after either source is prepared. A world save is therefore no longer presented as the only path for terrain, ore, cave, or supported spawner analysis.

Seed fields accept either a numeric seed or Minecraft-style text. Leaving a seed blank uses **`F3Plus`**.

Location finders use Radius search or Search until found. The advanced **Ignore maximum search / generation limit** option can continue beyond the configured maximum; exact generation can consume significant CPU, memory, disk, and time.

F3+ keeps selected Minecraft version, calculation/world-generation version, and installed local-data version separate. Placement candidates are not labeled as observed generated structures.

**World/structure-seed recovery is limited to the Nether Bedrock Cracker workflow.** Player/gameplay RNG recovery is separate.

## Results and maps

Results prioritize values that answer the selected task. Generic `Status: ok` and generic model badges are suppressed; unusual status, source, and exactness information remain visible when they matter.

Tables use human labels and add short metric definitions for ambiguous statistics such as distinct count, candidate count, attempts, scanned chunks, minimum/average/maximum, hit rate, and mean items per pull.

World maps use Minecraft X/Z coordinates:

- +X = east;
- +Z = south;
- grid labels are blocks;
- independent candidates are points;
- lines are reserved for declared routes;
- the search-center marker is identified separately.

Shape/build results use a **block blueprint** renderer. Three-dimensional builds expose Y layers instead of flattening every layer into one X/Z picture.

## Simulation & RNG

Simulator controls use Minecraft names and artwork. Item selection is a dropdown; registry IDs such as `minecraft:diamond_pickaxe` stay internal.

### Enchanting Table and Anvil

The Minecraft-style Enchanting Table uses an item dropdown, bookshelf count, text-or-number reproducibility seed, and three offer cards. Blank simulator seeds use `F3Plus` and are never described as world seeds.

Anvil planning uses item dropdowns, enchantment dropdowns, prior-work counts, rename state, and level-cost/survival output. Users do not type item IDs, enchantment IDs, JSON, or NBT.

### Loot & Drop Workbench

Loot tables are loaded from the selected/available Minecraft data source. The browser shows reachable items and repeatable simulation statistics:

- **Hit rate** — percent of simulated rolls containing the item.
- **Average / roll** — total copies observed divided by rolls.
- **Total** — all copies observed in the simulation.

If a loot table can produce an enchanted book, F3+ lists the enchantments that the active table/data source can roll and groups them by vanilla enchantment weight: Common, Uncommon, Rare, or Very Rare.

### Minecraft Mechanics Lab

Brewing and leather dye/cauldron tools use mechanic-specific controls. Breeding simulation is limited to the supported **horse stat** model because health, movement speed, and jump strength are inherited numerical attributes. Cosmetic/variant-only animal breeding is not presented as a statistical simulator.

Horse output reports minimum, average, and maximum health/speed/jump strength for the simulated offspring sample.

## Villager Explorer

Villager Explorer renders only visible trade cards but keeps every matching loaded trade in its model. The detail panel shows wants → gives, profession/level, max uses, restocks, emerald flow, XP/details, favorites, and comparison state.

When a Librarian enchanted-book offer is selected, F3+ shows the possible enchantments from the active installed tradeable-enchantment set and groups them by rarity/weight with maximum level.

Profession portraits and item textures are recovered from the installed client when available. Fallback/reference trade data remains clearly labeled.

## Minecraft artwork and themes

F3+ first attempts to recover suitable artwork from the selected/available installed Minecraft Java JAR, including conservative semantic fallback when an item/block texture has moved. When suitable installed artwork is unavailable, F3+ uses original **recolorable F3+ SVGs**.

Themes remain **Chorus, Light, Cyber, Vanilla, and Custom**.

## Automation and safety

Automation links to a detected Minecraft Java process and releases managed input if that client disappears. Runtime/action limits, delayed start, stuck/focus-loss protection, configurable global hotkeys, Pause/Resume, and Emergency Stop remain active controls. Safe Mode is a conservative multiplayer filter, not a replacement for server rules.

## Validation

CI validates Windows, macOS, and Ubuntu on Python 3.11, 3.12, and 3.13. The Cubiomes bridge compiles with strict warnings, Mojang exact-world integration is independently checked, and the semantic audit verifies all 457 historical aliases, launch ownership, field help, themes, and artwork contracts.

Windows CI captures native screenshots for the main shell and major workbench/result surfaces so layout and DPI regressions can be reviewed before release.

## Documentation and security

`FEATURES.md` is the concise workbench/accuracy reference. `SECURITY.md` covers downloads, permissions, written files, automation privileges, and responsible disclosure. `COMMUNITY_CREDITS.md`, `THIRD_PARTY.md`, and `LICENSE.md` cover project lineage and licensing.

## AI-assisted development disclosure

Generative AI was used during development for code translation/porting, refactoring, integration, debugging, test construction, UI iteration, and documentation. Project direction, feature selection, testing feedback, revisions, release decisions, and final inclusion decisions remained human-directed and human-reviewed.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.
