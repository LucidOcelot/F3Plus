# F3+ Workbench Guide

F3+ 2.5.4 is an offline-first technical companion for Minecraft Java Edition. The default target is **26.3 Snapshot 7**. The UI is organized by task; the 457 historical feature IDs remain compatibility aliases.

## Shared UI

The desktop shell has a connection/safety bar, global Minecraft context, a workspace rail, workbench cards, a contextual inspector, and `Ctrl+K` command search.

Operation panels show a short task description, only relevant controls, and a concrete result description. Detailed field explanations remain available as tooltips/accessibility text instead of being repeated inline everywhere.

Themes: **Chorus, Light, Cyber, Vanilla, Custom**.

## World data and Search Center

Location-aware tools share **Search Center**: Current position, Block coordinates, or Center chunk.

Generated-world analyzers that require blocks/entities can use either:

- **Seed** — generate the bounded reference area locally with the matching Mojang server after EULA acceptance.
- **World save** — scan an existing Java save.

Seed fields accept numbers or text. Blank seed = **`F3Plus`**.

Radius Search checks one area. Search Until Found expands by the chosen step. Ignore-limit mode continues past the configured maximum until a match or a real prerequisite/backend stop.

## Automation

**Automation Studio** groups continuous, periodic, equipment, travel, mining, farming, and construction routines. **Macro Studio** supports reusable step sequences, recording, editing, dry timeline review, import/export, and normal F3+ stop/safety controls.

## Navigation

**Live Position** handles F3+C capture and monitoring. **Coordinate & Travel Calculator** covers distance, bearing, midpoint, deltas, chunk/region math, snapping, and dimension conversion. **Waypoints, Routes & Surveys** handles saved locations and ordered paths. **Portal Network Planner** handles sister coordinates, link competition, and network geometry.

## World Explorer

**World Seed Recovery** is the Nether Bedrock Cracker path. Player/gameplay RNG recovery is separate.

World Explorer includes Slime, Structures, Spawners, Biomes & Terrain, Local Area, World Analysis, Nether, World Profiles, and **Ore & Cave Explorer**.

### Ore & Cave Explorer

- **Ore Distribution** — ore counts by type and Y level.
- **Ore Exposure Estimate** — generated ore blocks exposed to modeled cave/air surfaces.
- **Cave Exposure Estimate** — cave-air and cave-surface coverage.
- **Ancient City Area Analysis** — Ancient City candidate/area analysis.

Generated block-state tools can scan a selected save or generate the bounded area from a seed where supported.

## Build & Technical

**Build & Shape Planner** generates dimensions/material calculations and discrete Minecraft geometry. Shape results use a **block blueprint**; 3D shapes expose Y layers.

Other workbenches cover Redstone & Timing, Storage & Logistics, Farm Planning, Technical Minecraft, Resources, Speedrun/End, and Recipe & Material Explorer.

## Simulation & RNG

### Enchanting Table

Uses a Minecraft item dropdown, bookshelf count, and text-or-number simulation seed. Three table offers are displayed. Item registry IDs stay internal.

### Anvil

Uses base/sacrifice item dropdowns, enchantment dropdowns, prior-work counts, rename state, and level-cost/survival output. No raw item IDs, enchantment JSON, or NBT are required.

### Loot & Drop

Browse installed loot tables and reachable items, then simulate rolls. Statistics are labeled as:

- **Hit rate** — rolls containing the item ÷ total rolls.
- **Average / roll** — total copies ÷ rolls.
- **Total** — copies observed.

Loot tables that can return an enchanted book show possible enchantments from the active data source grouped as Common, Uncommon, Rare, or Very Rare according to enchantment weight.

### RNG / Recovery / Probability

Java LCG tools, probabilities, sequences, generation RNG, and EnchantmentCracker remain separate operations. Simulation/player RNG is never labeled as the Minecraft world seed.

### Mechanics Lab

Brewing and leather dye/cauldron tools use Minecraft controls. Breeding simulation is limited to the supported **horse inherited-stat** model and reports minimum/average/maximum health, movement speed, and jump strength. Cosmetic-only animal inheritance is not presented as a stats simulator.

## Villagers

**Villager Explorer** is virtualized: only visible cards are painted while every matching loaded trade remains available.

Trade details show wants → gives, level/profession, max uses, restocks, emerald flow, XP/details, favorites, and comparison. Librarian enchanted-book trades also show the active tradeable enchantment set grouped by rarity/weight and maximum level.

Planning helpers cover curing, halls, workstations, and breeding food.

## Results and visualization

Normal result views suppress successful-status boilerplate and generic model badges. Source/exactness information stays visible when it distinguishes observed/generated/reference data.

Ambiguous statistics receive short definitions. Ranked result tables prefer useful coordinates and named metrics instead of anonymous `Value 1` / `Value 2` columns.

Maps use X/Z block coordinates: +X east, +Z south. Candidate layers are points; only ordered routes receive lines. The search center is marked separately. Arbitrary number pairs are not guessed into maps.

## Artwork and themes

F3+ recovers Minecraft item/block/profession artwork from the local installed JAR when possible and uses original recolorable SVGs as fallback. It does not redistribute Mojang texture files.

## Accuracy boundaries

F3+ distinguishes:

- selected Minecraft version;
- actual calculation/world-generation version;
- installed local-data version.

Bundled Cubiomes support remains version-bounded. Generated facts are not presented as seed-only predictions, and placement candidates are not presented as confirmed saved structures.

## Validation and release channel

CI covers Windows, macOS, and Ubuntu on Python 3.11–3.13, strict Cubiomes bridge compilation, Mojang exact-world integration, historical-alias coverage, launch ownership, UI contracts, and native Windows screenshot review.

Stable updates come from the validated `stable` branch. `main` is available through the explicit Preview channel.
