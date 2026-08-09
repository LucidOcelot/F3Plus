**AI Disclosure:**

F3+ was unfortunately developed with generative AI assistance. In the spirit of transparency, AI use is described below.

Approximately 35% of F3+'s original first-party work is estimated to be substantially AI-created or AI-assisted translation, porting, integration, and refactoring of existing human/community work. The remaining work originates from human-written code and designs, ports of earlier Minescript/M.A.R.T. work, or implementations based on established community tools, algorithms, and research.

Generative AI was also used extensively for integration, debugging, iterative testing in sandboxed environments, UI development, refactoring, documentation, and project organization. Project direction, feature choices, testing feedback, revisions, and release decisions remained human work.

All final inclusions were reviewed and edited by a human before being included in the project.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.

Third-party and community contributions are credited separately in `COMMUNITY_CREDITS.md` and `THIRD_PARTY.md`.

# F3+ 2.3.4

F3+ is an all-in-one offline-first companion app for Minecraft Java Edition. Built around community tools and based on Minescript/M.A.R.T by Lucid, it brings common and niche technical Minecraft workflows into one cross-platform desktop application without requiring a modified client.

**Current release:** F3+ **2.3.4**  
**Default Minecraft target:** **26.3 Snapshot 7**  
**Supported Python:** **3.11 through 3.13**  
**Update channel:** `LucidOcelot/F3Plus` `main`

F3+ combines automation, navigation, known-seed analysis, RNG utilities, generated-world inspection, technical calculators, villager planning, construction/farming tools, guided setups, and emergency controls. The historical 457 feature IDs remain stable for favorites, recents, and compatibility.

## What 2.3.4 focuses on

2.3.4 consolidates the 2.x interface and audit work into a release with consistent version metadata, clearer reports, and stronger regression coverage. The most visible changes include:

- structured player-facing results instead of raw implementation dictionaries;
- readable biome, coordinate, percentage, time, and status values instead of unexplained numeric/raw values;
- X/Z maps for spatial seed/world results and visual plans for spatial construction/layout results;
- a visual Villager Trade Explorer with named Novice–Master levels, local Minecraft artwork when available, and an explicitly labeled planning baseline when exact local trade JSON is unavailable;
- a mob-aware Spawner Locator with filters for common dungeon mobs, trial spawners, vaults, and unknown/custom spawners;
- compatible-Java discovery for exact Mojang reference-world generation instead of exposing raw class-version failures;
- catalog-wide semantic regression checks so differently named tools cannot silently collapse into identical reports unless they are explicitly documented presets/shortcuts.

## Start

### Windows

1. Extract the ZIP completely.
2. Run `START_F3PLUS.bat`.
3. Leave the setup window open during the first launch.
4. Start Minecraft Java. F3+ links automatically when one valid client is detected; if several are open, choose the intended client.

### macOS

1. Extract the ZIP.
2. Run `START_F3PLUS.command`.
3. Grant Accessibility/Input Monitoring permission when required for input automation.
4. Start Minecraft Java and allow F3+ to link the client.

### Linux

Run `START_F3PLUS.sh`.

Linux background automation uses the native Wayland/uinput path when the required local helpers and compositor integration are available. Calculators and foreground workflows remain available when targeted background input is unavailable.

## Automatic updates

F3+ checks the `main` branch of `LucidOcelot/F3Plus` on GitHub every launch.

A clean Git checkout fast-forwards from `origin/main`. Extracted ZIP installs compare their saved commit with GitHub and overlay a newer immutable commit archive after validating its paths and Python source. User settings under `~/.f3plus`, the private runtime, Git metadata, and startup logs are not replaced by archive updates.

Tracked local changes in a Git checkout are never overwritten automatically. If GitHub cannot be reached, the installed copy continues launching offline. For development or recovery, set `F3PLUS_SKIP_UPDATE=1` to skip the launch update check.

## Main interface

F3+ uses one interaction model across the catalog:

- **Command deck** — verified Minecraft link state, active input capabilities, Relink, Safe Mode, Options, Pause/Resume, and Emergency Stop.
- **Context deck** — global search, dimension, selected Minecraft version, world seed, live coordinate capture, and visible world-generation fallback state when applicable.
- **Workspace rail** — Automation, Navigation, World & Seed, Structures & Biomes, Calculators, Building & Farming, RNG, Villagers, Guided Setups, Utilities, and Safety.
- **Tool Library** — task-oriented groups with searchable tool cards.
- **Inspector** — what the selected tool does, when to use it, how to use it, required inputs, expected output, and version/implementation limitations.
- **Configure Tool** — task-specific parameter controls and path pickers instead of unrelated one-off dialogs.
- **Results** — compact metrics, translated tables, warnings, maps, and visual plan previews instead of raw diagnostic-style dumps.

Spatial seed/world results use readable chunk/block coordinates and an X/Z map when location data is present. Construction/shape/farm tools use focused inputs and show a plan or footprint preview when their result contains spatial information.

Browsing the catalog does not execute seed searches or other heavy calculations.

## Minecraft versions and fallback behavior

F3+ keeps **selected Minecraft version**, **world-generation calculation version**, and **local data version** separate.

The bundled Cubiomes revision has an explicit stable mapping through Minecraft **1.21.3**. If the selected Minecraft version is newer or otherwise unsupported, F3+ keeps that selected version visible, warns the user, and uses 1.21.3 only for Cubiomes-dependent calculations. Those results are labeled as fallback results and are not presented as exact results for the newer version.

Exact generated-world tools can instead inspect an existing save or run Mojang's matching server JAR after explicit EULA acceptance. F3+ reads the server metadata's required Java major version and checks configured Java, `JAVA_HOME`, PATH, and Minecraft Launcher runtimes for a compatible executable before starting reference generation.

## Villager Trade Explorer

The old spreadsheet-style trade window has been replaced by a visual explorer. It uses Minecraft item/block textures read from the installed client when available and presents trades as **You Give → You Receive** cards.

The explorer includes profession navigation, named Novice–Master level filters, trade-direction filters, search, definition details, max uses, villager XP, planned emerald totals, persistent favorites, and a comparison tray. The selected Minecraft version and actual trade-data source are displayed independently.

F3+ prefers data-driven villager trade JSON from the exact selected installed JAR, then tries usable installed release data. If no installed JAR exposes modern trade JSON, the explorer shows a visibly labeled **baseline reference** instead of an empty zero-trade window. That reference is for planning only and is not claimed exact for the selected version.

`Librarian Browser`, profession entries, Trade Search, Trade Comparison, Emerald Calculator, and Trade Cycle Calculator all use the same explorer with an appropriate starting preset rather than separate generic popups.

## Generated spawners

The user-facing **Spawner Locator** can filter generated spawner NBT for all mob spawners or specific Zombie, Skeleton, Spider, Cave Spider, Blaze, Silverfish, Pig, Magma Cube, unknown/custom, Trial Spawner, or Vault entries. Where the NBT provides mob identity, F3+ translates it to a readable mob name and reports block/chunk coordinates plus a map-ready hit list. Double/triple/quad and cluster-ranking entries apply their own grouping rules to the selected type.

## World, seed, and spatial reports

Local-area and world-analysis tools are intentionally separated by user question. Biome composition, structure candidate summaries, slime distribution, technical-site context, build-site context, exploration context, generated terrain, caves, and resources are not combined into several renamed copies of the same generic report.

Coordinates in normal results identify whether they are blocks, chunks, or regions. Structure placement candidates are distinguished from final generated structures. Spatial candidate sets, slime chunks, biome samples, routes, spawner hits, and similar data can be plotted on the result map.

## Construction and planning

Construction tools use inputs appropriate to the operation: bridge tools ask for span/support spacing, roof pitch asks for run/rise, stairs ask for rise/run, grids ask for footprint and spacing, and shape tools request only their relevant dimensions. Layout-producing operations return coordinates or footprints and can display a visual plan rather than only a scalar total.

Planar Spiral remains an X/Z layout while 3D Helix rises along Y. Construction Grid and Lighting Grid use different edge-coverage rules. Storage-capacity tools and container-requirement tools answer opposite questions rather than sharing one output under different names.

## Appearance

Themes are selected only under **Options → Appearance**:

- **Chorus** — default End-inspired purple/gold theme.
- **Light** — bright blue/gold/white desktop theme.
- **Cyber** — high-contrast neon technical theme.
- **Vanilla** — Minecraft-oriented green/earth presentation.
- **Aether** — bright cartographic teal/coral presentation with spacious rounded geometry.
- **Foundry** — dark industrial furnace/brass presentation with sharper geometry.
- **Custom** — editable F3+ palette with optional locally recovered Minecraft artwork.

Minecraft artwork is read from the player's installed Java files at runtime where applicable. F3+ does not bundle or redistribute Mojang texture assets.

## Minecraft linking and input

F3+ links a live client only when a feature needs one. On Windows, title text alone is not sufficient to identify Minecraft: candidate windows are validated against their owning Java process so browser tabs or documentation pages containing the word “Minecraft” are rejected.

- **Windows:** targeted linked-window keyboard/mouse-button input, with focus switching when relative camera input requires it.
- **macOS:** process-targeted Quartz input where permitted, with focus switching and operating-system permission handling when required.
- **Linux:** native Wayland/uinput workflow when supported by the local environment.

When a macro cannot run reliably in the current window state, F3+ explains the limitation before sending input.

## Safe Mode

Safe Mode is a conservative strict-SMP filter. It stops active automation when enabled and blocks tools commonly restricted on strict multiplayer servers while leaving them visible so their purpose can still be read.

Safe Mode does not replace a server's rules. The server's actual policy takes precedence.

## Seed and RNG boundaries

- A known Java world seed may be entered for deterministic calculations.
- Gameplay/player RNG is separate from the world seed and can be analyzed only where the observed mechanic uses a supported generator/workflow.
- World/structure-seed recovery has one route: **Nether Bedrock Cracker** using Nether bedrock observations.

F3+ does not present gameplay RNG recovery as world-seed recovery.

## Setup and offline behavior

F3+ supports Python **3.11 through 3.13**. The launcher creates a project-local `.venv` and installs required packages when needed. Dependency setup, launch update checks, optional upstream helpers, and exact Mojang reference-world acquisition may require network access; normal prepared calculations and local-data workflows run locally.

Before package installation, F3+ checks available disk space. Disk, network, permission, and compatibility failures are reported separately.

## Emergency controls

Default Emergency Stop: `Ctrl + Alt + S`

Default Pause / Resume: `Ctrl + Alt + Space`

Default Copy Sister Coordinates: `Ctrl + Alt + C`

All three global hotkeys are configurable under **Options → Automation**. Emergency Stop releases tracked keyboard and mouse state through the active input backend.

## Troubleshooting

**The program does not open:** run the platform launcher from a fully extracted folder and read `F3Plus_startup.log` if setup fails.

**An update cannot be downloaded:** F3+ continues with the installed build. Check network access to GitHub; use `F3PLUS_SKIP_UPDATE=1` only when you intentionally want to skip the update check.

**Minecraft is not linked:** start Minecraft Java, reach the game window, then use **Relink**. F3+ intentionally ignores unrelated windows that only mention Minecraft in their title.

**Background input is unavailable:** open **Connection Status** to see the active capability path. Relative camera movement can require focus even when buttons/keys can be targeted in the background.

**Exact generated-world analysis reports an incompatible Java runtime:** start the selected Minecraft version once through the official launcher so its matching runtime is installed, or configure `F3PLUS_JAVA` / `JAVA_HOME` to a compatible Java executable.

**Villager Explorer says baseline reference:** no usable installed JAR exposed the data-driven trade definitions expected by the explorer. The displayed baseline is a planning reference, not a claim about exact offers for the selected version.

**macOS input does not work:** confirm Accessibility and Input Monitoring permission for the terminal/Python process used to launch F3+.

**Linux background input does not work:** confirm the supported Wayland/uinput helper path and local permissions.

## Validation and documentation

The GitHub Actions suite compiles the project, runs the complete regression suite on Windows, macOS, and Ubuntu with Python 3.11 and 3.13, dry-runs the 457-entry feature catalog, checks semantic report uniqueness, and performs an independent Mojang reference-world integration test.

- `FEATURES.md` — feature families, version behavior, explorer details, and implementation boundaries.
- `LICENSE.md` — F3+ license.
- `THIRD_PARTY.md` — third-party software and license boundaries.
- `COMMUNITY_CREDITS.md` — community contributors and technical lineage.

F3+ does not include Minecraft client/server JARs, Minecraft texture files, or Microsoft/Mojang assets.
