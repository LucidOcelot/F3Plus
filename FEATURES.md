# F3+ 2.3.4 Feature Guide

F3+ is an offline-first technical companion for Minecraft Java Edition. Release 2.3.4 targets Minecraft Java **26.3 Snapshot 7** by default and combines automation, navigation, known-seed analysis, generated-world inspection, RNG utilities, villagers, construction/farming planners, calculators, guided setups, and safety controls without requiring a modified Minecraft client.

## Common interface

The 457 historical feature IDs remain stable for favorites, recents, and compatibility, but shared code is not allowed to masquerade as different tools. Different entries must perform a different calculation, filter, visualization, or decision, or clearly identify themselves as a shortcut/preset into one canonical workflow. CI dry-runs the complete catalog and fails on unexplained duplicate reports.

Normal results are translated for players before display. Internal implementation metadata stays out of the primary result view; booleans become labels such as **Ready**, **Unavailable**, **Required**, or **Enabled**; fractions that represent densities/shares become percentages; time values receive usable units; and coordinate arrays are labeled as block, chunk, or region coordinates instead of generic `Value 1` / `Value 2` columns.

Spatial Seed Tools display a theme-aware X/Z map beside the result when location data is available. Structure candidates, slime chunks, biome samples, routes, ranked sites, and generated spawner hits use the same block-coordinate frame so the user can see relationships instead of interpreting raw tuples.

Construction, shape, farm, and related planning tools use focused inputs rather than one generic dimension form. Tools that produce layouts or footprints also receive a visual plan when their result contains enough spatial information.

## Minecraft version state

F3+ keeps these sources separate:

- **Selected Minecraft version** — the version the user is playing or targeting.
- **World-generation calculation version** — the Cubiomes rules actually used by a calculation.
- **Local data version** — the installed Minecraft JAR used for textures or data-driven resources.

The bundled Cubiomes mapping is explicitly version-bounded. When the selected version is unsupported, F3+ keeps the selected version visible and labels the supported calculation fallback rather than pretending the fallback is snapshot-exact.

Generated-world tools can instead inspect an existing Java save or, with explicit EULA acceptance, generate bounded vanilla reference chunks from the selected seed using Mojang's matching server JAR. F3+ reads Mojang's required Java major version and searches the configured Java runtime, `JAVA_HOME`, PATH, and Minecraft Launcher's installed runtimes for a compatible executable. An incompatible Java installation therefore produces an actionable runtime message instead of a raw `UnsupportedClassVersionError` wall of text.

## Minecraft linking

Live-client features use one authoritative Java-client link state. On Windows, a window title containing “Minecraft” is not enough: the owning executable must resolve to a Java process. Browser tabs, GitHub pages, documentation, and other title matches are rejected. If the target disappears, F3+ drops the link rather than continuing to send targeted input to a stale process.

## Villager Trade Explorer

Villager browsing is one visual application with profession navigation, workstation/item artwork, level filters, trade-direction filters, search, favorites, comparison, planned uses, source information, and **You Give → You Receive** trade cards. Librarian Browser, Trade Search, Trade Comparison, Emerald Calculator, Trade Cycle Calculator, profession entries, and Trade Browser open this same explorer with the appropriate preset rather than maintaining separate spreadsheet-style windows.

F3+ first attempts to read data-driven villager trade definitions from the exact selected installed JAR. If that JAR has no usable trade JSON, it searches newer useful installed release data. Older Minecraft versions may hard-code offers rather than expose the modern JSON path; if no installed JAR yields data-driven offers, F3+ shows a non-empty **baseline planning reference** instead of a broken zero-row explorer. That fallback is visibly labeled **baseline reference** and is not claimed exact for the selected version. Item/workstation textures can still be recovered from an installed client independently of the trade-data source.

The explorer shows level names such as **Novice**, **Apprentice**, **Journeyman**, **Expert**, and **Master**, with the numeric level only as secondary context. Exact max uses, villager XP, enchantment/detail data, and source paths are shown when the source definition provides them.

## World & Seed

Known-seed tools include slime analysis, Nether/portal analysis, local-area reports, structure candidates, biome analysis, world reports, and generated-world inspection. Local Area tools deliberately separate biome composition, structure candidates, slime distribution, build context, technical-site context, and exploration context rather than recombining the same values into arbitrary scores.

Structure candidate output distinguishes placement attempts from final generated structures. Candidate tables use **Chunk X / Chunk Z** and corresponding block centers, and spatial results are plotted on the result map.

**Nether Bedrock Cracker remains the only F3+ world/structure-seed recovery path.** Gameplay/player RNG recovery is a separate system and is never presented as world-seed recovery.

### Generated spawners

The historical `Dungeon/Pig Spawner Locator` ID is displayed as **Spawner Locator**. It scans generated Anvil/NBT data and can filter for:

- all mob spawners;
- Zombie;
- Skeleton;
- Spider;
- Cave Spider;
- Blaze;
- Silverfish;
- Pig;
- Magma Cube;
- other/unknown mob spawners;
- Trial Spawners;
- Vaults; or
- all spawner-like block entities.

When mob identity is encoded in `EntityId`, `SpawnData`, or `SpawnPotentials`, F3+ translates that NBT into the mob name instead of reporting every block only as `minecraft:mob_spawner`. Double, triple, quad, and cluster-ranking tools apply their own minimum/grouping rules to the selected spawner type. Spawner hits include block position, chunk, distance from the reference, and map-ready coordinates.

### Finder search modes

Location-oriented search tools expose **Radius search** and **Search until found** when a concrete match/non-match result exists. Radius search evaluates exactly one user-selected radius. Search until found begins at that radius and expands by a configurable step until the first matching result appears or the configured maximum radius is reached. Results include the mode, search units, number of attempts, last radius checked, and the radius that first produced a match.

This policy applies to the Spawner Locator family, structure candidate finders, selected biome/boundary/intersection finders, generated-terrain locators, Nether fortress/bastion finders, and slime-cluster searches. Reports whose job is analysis rather than locating a first target—such as Structure Density, Rare Biome Search, and Search Radius Optimizer—do not receive an artificial until-found mode.

Spawner searches against an existing generated save skip Anvil region files that cannot intersect the requested radius. Exact seed-regenerated spawner searches remain bounded by the user's **Maximum exact chunks to generate** setting; if that budget prevents the requested expansion, the result explains the effective radius limit instead of silently exceeding the generation budget.

Generated-terrain locators use **chunk X/Z and chunk radius** because they inspect generated chunks. Cubiomes biome target searches use **block X/Z and block radius**. The UI keeps those units separate.

## Navigation

Navigation includes coordinate capture/conversion, bearings, block/chunk/region geometry, waypoints, routes, surveys, breadcrumbs, and Overworld/Nether planning. Similar-looking entries answer different questions: Nearest Waypoint returns one saved location; Sort Waypoints measures every saved waypoint from the same origin; Waypoint Route creates a nearest-next route with per-leg distances. Coordinate Route, Resource Route, Structure Tour, Biome Expedition, Survey Mode, and recording tools likewise keep separate output semantics.

## Calculators, building, and farming

Coordinate/travel, storage/logistics, redstone, mob/loading, farm, speedrun, durability/resource, End, building, and shape tools use task-specific labels and units. Storage Capacity answers how much chosen storage holds, while Shulker/Chest Requirement answers how many containers a target needs. Render Distance and Simulation Distance are presented as different concepts.

Construction inputs are purpose-specific: a Bridge Span asks for span/support spacing; a Roof Pitch asks for run/rise; a Stair Calculator asks for rise and run per step; grids ask for footprint and spacing; shape tools ask only for the dimensions relevant to that shape. Layout-producing tools expose coordinates or footprints and use visual plan previews rather than only returning a scalar count.

Construction Grid is a regular spacing grid; Lighting Grid includes far edges for boundary coverage. Planar Spiral stays in X/Z while 3D Helix rises along Y. Circle Layer Export produces copy-ready coordinate text rather than duplicating the Circle preview.

## RNG

Gameplay RNG recovery is separate from world-seed recovery. The two Java LCG recovery entries expose their actual observations: **2 nextInt** records the two consecutive `nextInt()` observations, while **nextLong** records the one observed `nextLong()` and the derived pair of 32-bit outputs. They therefore cannot collapse into the same empty-candidate report.

RNG Sequence Viewer, RNG Timeline, enchantment planning, generation previews, loot simulations, tree attempts, geode frequency, and structure placement previews remain separate views/models. Generic probability tools state their attempt unit and model instead of presenting unrelated mechanics as one universal loot calculation.

## Guided setups and automation

Automation uses the shared MacroEngine/BoundInput safety layer. Guided setups combine related planning values for mining, farming, portals, and construction. Automation-menu wizard entries that share a planning engine are explicitly shortcuts into the canonical setup rather than duplicate algorithms.

## Safety

Emergency Stop, Pause/Resume, held-input release, delayed start, runtime/action limits, stuck detection, recovery limits, focus-loss behavior, and hotbar restoration remain available across automation. Safe Mode is a conservative multiplayer filter, not a substitute for a server's rules.

## Themes

Appearance choices are available under **Options → Appearance**:

- **Chorus** — default End-inspired purple/gold/black presentation.
- **Light** — bright blue/gold/white desktop presentation.
- **Cyber** — high-contrast neon technical presentation.
- **Vanilla** — Minecraft-oriented green/earth presentation.
- **Aether** — bright cartographic teal/coral presentation with softer geometry.
- **Foundry** — dark industrial furnace/brass presentation with sharper geometry.
- **Custom** — editable palette with the option to use locally recovered Minecraft artwork.

Minecraft artwork is read from the player's installed Java files at runtime where available; F3+ does not redistribute Mojang textures.

## Automatic updates and offline behavior

F3+ 2.3.4 checks `LucidOcelot/F3Plus` `main` on GitHub at launch. Clean Git checkouts fast-forward; extracted ZIP installs compare their stored commit with GitHub and apply a validated newer commit archive. User configuration under `~/.f3plus` is preserved. Tracked local Git changes are not overwritten. Update/network failure does not stop an already installed copy from launching, and `F3PLUS_SKIP_UPDATE=1` disables the check for development/recovery.

Normal calculations, local data browsing, settings, prepared components, and generated-save analysis run locally. Network access is used for the launch update check, dependency/component acquisition, or exact Mojang reference-world generation when those workflows are requested.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider. Community lineage and third-party software are documented in `COMMUNITY_CREDITS.md` and `THIRD_PARTY.md`.
