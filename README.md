# F3+

**A local technical Minecraft workstation for Java Edition.**

F3+ combines technical calculations, navigation, world inspection, build planning, simulation, villager tools, and optional bounded automation in one desktop application.

**Release:** 2.5.3  
**Default Minecraft target:** 26.3 Snapshot 7  
**Python:** 3.11 through 3.13

## Start

- **Windows:** extract the ZIP and run `START_F3PLUS.bat`.
- **macOS:** extract the ZIP and run `START_F3PLUS.command`. Automation may require Accessibility/Input Monitoring permission.
- **Linux:** run `START_F3PLUS.sh`. Calculators and foreground workflows do not require background-input support.

The launcher prepares a project-local Python environment and required packages when needed. Installed copies continue to launch when update checks are unavailable.

F3+ normally installs validated Stable updates before launch. Set `F3PLUS_UPDATE_CHANNEL=preview` to follow `main`, `F3PLUS_AUTO_UPDATE=0` for check-only behavior, or `F3PLUS_SKIP_UPDATE=1` to skip the update check.

## Interface

The desktop is organized by player task instead of implementation category or feature count.

### Home

Favorites, recent tools, and common starting points. Global search and `Ctrl+K` can open a workbench or a specific operation by mechanic or task name.

### Play & Travel

- repeated actions and bounded automation;
- travel automation;
- mining, farming, and construction automation;
- macros and recorded sequences;
- live position and coordinate calculations;
- routes, waypoints, surveys, and portal planning.

### Explore Worlds

- structure, biome, Nether, and slime searches;
- generated-world spawner, ore, cave, and area scans;
- broader world analysis;
- seed-recovery tooling;
- local Java saves and reusable world profiles.

Search tools can use current position, block coordinates, or a center chunk where location matters. Generated-world operations can read an existing Java save and supported workflows can create bounded reference chunks with the matching Minecraft server after EULA acceptance.

### Plan & Build

- block shapes and build layouts;
- redstone and timing;
- storage and logistics;
- farms and breeding plans;
- technical spacing, loading, and perimeter calculations;
- resource, XP, speedrun, and End utilities;
- recipes and recursive material lists.

Two-dimensional layouts render as block cells. Three-dimensional shapes expose selectable Y layers instead of flattening every layer into one X/Z image.

### Mechanics & Trading

- enchanting and anvil planning;
- Java/gameplay RNG tools;
- loot and drop simulation;
- generation mechanics;
- brewing, dye/cauldron behavior, and horse/donkey breeding stats;
- villager profession, trade, curing, breeding, workstation, and hall planning.

Simulator controls use readable Minecraft items and mechanic-specific inputs rather than requiring users to edit registry JSON or NBT.

### App & Safety

- Minecraft/data versions;
- controls and calibration;
- automation safety settings;
- result history and export;
- diagnostics.

## Inputs and outputs

Input controls expose tooltips and accessibility descriptions that explain the value, unit, direction, format, and default where applicable. Generic operation panels show only the fields used by the selected operation.

Results lead with concrete values such as locations found, chunks scanned, radius searched, material totals, timing, probability, or min/average/max statistics. Coordinate results can render maps; statistical results can render charts; build shapes can render block-layer previews. Raw structured output remains available for users who need the complete result.

## World data

F3+ can use:

- a known Java world seed;
- generated data from an existing Java save;
- installed Minecraft Java JAR data such as loot tables, tags, recipes, enchantments, villager resources, and textures;
- bounded locally generated reference chunks for supported workflows;
- the bundled/native Cubiomes integration where the selected operation supports it.

The UI identifies the data source when that information matters to interpreting the result.

## Minecraft artwork and themes

F3+ first attempts to recover suitable artwork from an installed Minecraft Java JAR. When matching installed artwork is unavailable, the application uses recolorable F3+ SVG/icon artwork.

Themes: **Chorus, Light, Cyber, Vanilla, and Custom**.

## Automation and safety

Automation links to a detected Minecraft Java process and can use targeted background input, focus switching, or foreground-only input depending on the operating system and available backend.

Available controls include runtime/action limits, delayed start, coordinate recovery attempts, hotbar restoration, stuck detection, focus-loss stop, configurable hotkeys, Pause/Resume, and Emergency Stop. Safe Mode provides conservative multiplayer restrictions; server rules remain authoritative.

## Validation

CI runs on Windows, macOS, and Ubuntu using Python 3.11, 3.12, and 3.13. It validates Python sources, regression tests, native Cubiomes compilation, release consistency, workbench routing, field help, Mojang world-generation integration, and Windows UI screenshot generation.

## Documentation and security

- `FEATURES.md` contains feature and calculation details.
- `SECURITY.md` documents downloads, permissions, local files, automation privileges, and responsible disclosure.
- `COMMUNITY_CREDITS.md` records community lineage.
- `THIRD_PARTY.md` covers third-party software and licenses.
- `LICENSE.md` contains the F3+ license.

## AI-assisted development disclosure

Generative AI has been used during development for code translation/porting, refactoring, integration, debugging, test construction, UI iteration, and documentation. Project direction, testing feedback, revisions, release decisions, and inclusion decisions remain human-directed and human-reviewed.

F3+ does not use generative AI during normal operation and does not transmit Minecraft worlds, seeds, coordinates, account information, or other user data to an AI provider.
