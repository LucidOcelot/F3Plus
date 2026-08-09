# F3+ 2.3.4 Feature Guide

F3+ is an offline-first technical companion for Minecraft Java Edition. It targets **26.3 Snapshot 7** by default and keeps the historical 457 feature IDs stable while presenting them through task-oriented workspaces.

## Shared tool interface

Every catalog entry uses the same basic workflow: choose a tool, read its Inspector explanation, configure only the inputs that matter to that operation, then inspect a structured result. Player-facing output translates implementation values into named biomes, block/chunk/region coordinates, percentages, time units, statuses, tables, warnings, and visual layers where appropriate.

Tool cards use task-specific icon families for maps/routes, biome and terrain searches, generated spawners, portals, construction/shapes, farming, redstone, storage, villagers, RNG, utilities, automation, and safety instead of relying on one generic symbol. The selected tool also carries its family icon into the Run control.

Configuration fields include contextual tooltips. Search-oriented dialogs explain how radius mode, until-found expansion, maximum radius, exact world generation, EULA acceptance, and the explicit ignore-limit override interact before the search is started.

The Inspector describes what the tool does, when to use it, how to run it, inputs, output semantics, version limits, and additional search/visual behavior when those systems apply.

## Interactive visual results

Spatial Seed Tools and spatial construction/planning tools use a shared interactive X/Z view when enough coordinate data exists. The visual layer supports:

- mouse-wheel zoom;
- drag panning;
- Fit to restore the full plotted extent;
- per-layer visibility controls;
- grid visibility;
- optional point-coordinate labels;
- live cursor X/Z coordinates;
- copyable visible coordinate layers.

Seed/world visuals normalize plotted data into block X/Z coordinates so chunk candidates, spawner hits, routes, slime chunks, biome samples, and reference centers can be compared in one frame. Construction/shape/farm visuals use a local block-coordinate frame for footprints, paths, spans, and generated layouts.

Visual output supplements the structured numeric result; it does not replace the underlying coordinates or exactness/version notices.

## Minecraft version state

F3+ keeps three version concepts separate:

- **Selected Minecraft version** — what the user is targeting.
- **World-generation calculation version** — the rules actually used by the active generation backend.
- **Local data version** — the installed Minecraft JAR used for artwork or data-driven resources.

The bundled Cubiomes mapping is explicitly bounded through **1.21.3**. When a newer selected version is unsupported, F3+ keeps that version visible and labels the supported fallback rather than claiming snapshot-exact generation.

Generated-world tools can inspect an existing Java save. Where supported, they can instead run Mojang's matching server JAR locally after explicit EULA acceptance to materialize exact reference chunks. F3+ reads Mojang's required Java major version and checks configured Java, `JAVA_HOME`, PATH, and Minecraft Launcher runtimes for a compatible executable.

## Finder search modes

Location-oriented tools expose **Radius search** and **Search until found** only when a concrete match/non-match result exists.

**Radius search** evaluates one bounded area around the reference point. **Search until found** begins at the configured radius and expands outward by the chosen step after each empty result. The normal mode stops at the configured maximum radius and reports the attempted radii plus the radius where the first match was found.

Every tool that exposes Search until found also exposes **Ignore maximum search / generation limit**. When enabled, the configured maximum radius is ignored. If the operation needs exact Mojang reference-world generation, F3+ also raises the per-attempt exact-generation chunk budget as the radius grows. This override can use substantial CPU, memory, disk space, and time; backend errors and an internal runaway-loop guard can still end the process.

The shared search policy applies where appropriate to generated spawners, structure candidate finders, selected biome/boundary/intersection searches, generated-terrain locators, Nether fortress/bastion finders, and slime-cluster searches. Analysis reports such as Structure Density or Rare Biome Search remain bounded analyses because “first match” is not their job.

Generated-terrain locators use **chunk X/Z and chunk radius**. Cubiomes biome searches use **block X/Z and block radius**. These units stay separate in the UI.

## Villager Trade Explorer

Villager browsing is one visual explorer used by Trade Browser, Trade Search, Trade Comparison, Emerald Calculator, Trade Cycle Calculator, Librarian Browser, and profession entries.

Profession navigation uses **villager entity/type/profession skin layers** read from the player's installed Java client when available. It no longer represents professions with workstation blocks. Item/output cards still use relevant item textures.

The explorer supports profession navigation, named **Novice / Apprentice / Journeyman / Expert / Master** levels, trade direction, search, favorites, comparison, planned uses, max-use context, villager XP, definition details, and source information.

Trade data and artwork are independent. F3+ first tries exact installed data-driven trade JSON, then another usable installed release. If no installed JAR exposes usable trade JSON, the explorer shows a non-empty **baseline planning reference** and labels it as non-exact rather than showing an empty/broken table.

## Generated spawners

The historical `Dungeon/Pig Spawner Locator` ID is displayed as **Spawner Locator**. It reads generated Anvil/NBT data and can filter all mob spawners or specific Zombie, Skeleton, Spider, Cave Spider, Blaze, Silverfish, Pig, Magma Cube, unknown/custom, Trial Spawner, Vault, or all spawner-like block entities.

Mob identity is read from `EntityId`, `SpawnData`, and `SpawnPotentials` where available. Hits include block position, chunk, distance from the reference, and visual coordinates. Double, triple, quad, and cluster-ranking tools apply their minimum/grouping rule after the selected mob filter; one matching spawner is not treated as a successful double/triple/quad result.

Spawner radius scans skip Anvil region files that cannot intersect the requested search area. Existing-world searches inspect only generated data. Exact seed-regenerated searches use Mojang reference chunks and honor the normal generation budget unless the user explicitly enables the ignore-limit override.

## World & Seed

Known-seed tools include slime analysis, Nether/portal analysis, structure placement candidates, biome searches, Local Area reports, world evaluation, and generated-world inspection.

Local Area tools deliberately answer different questions: biome composition, structure candidate summary, slime distribution, nearby highlights, technical-site context, build-site context, and exploration context are not several renamed copies of one aggregate score.

Structure candidate output distinguishes deterministic placement candidates from confirmed final generated structures. Candidate tables label Chunk X/Z and block centers, and spatial candidates can be shown in the interactive map.

**Nether Bedrock Cracker remains the only F3+ world/structure-seed recovery path.** Gameplay/player RNG recovery is separate.

## Navigation and portals

Navigation covers live coordinates, coordinate/chunk/region conversion, bearings, waypoints, routes, surveys, breadcrumbs, and Overworld/Nether portal planning. Similar entries preserve separate semantics: Nearest Waypoint returns one location, Sort Waypoints measures every saved location from one origin, and Waypoint Route builds a nearest-next multi-stop route.

Portal tools separate coordinate conversion, exit competition, one-way/asymmetric routing, link matrices, reliability geometry, route comparison, and network planning rather than returning the same portal pair under multiple names.

## Calculators, building, and farming

Technical calculators cover coordinate/travel math, redstone/timing, storage/logistics, mob/loading mechanics, technical planning, speedrun planning, resources/durability, and End travel.

Building/farming configuration is operation-specific. Bridge Span asks for span/support spacing; Roof Pitch asks for run/rise; Stair Calculator asks for rise/run; grids ask for footprint/spacing; shape tools request only relevant dimensions. Layout-producing operations expose coordinates or footprints to the visual planner.

Storage Capacity answers how much selected storage can hold; Shulker/Chest Requirement answers how many containers a target amount needs. Construction Grid and Lighting Grid use different boundary behavior. Planar Spiral remains an X/Z shape while 3D Helix rises along Y.

## RNG

Gameplay RNG recovery is separate from world-seed recovery. Java LCG recovery tools state the actual observation form they expect, and general probability/simulation tools state when their results are estimates or model-based rather than exact mechanic reconstruction.

RNG Sequence Viewer, RNG Timeline, enchantment planning, loot simulations, tree/geode generation previews, decoration RNG, feature placement, ore placement, and structure placement remain separate views/models rather than duplicate reports.

## Automation, linking, and safety

Automation uses the shared MacroEngine/BoundInput safety layer. The live Minecraft target is verified as a Java client; window-title text alone is not considered sufficient identification on Windows. If the linked client disappears, the targeted link is dropped rather than silently retaining a stale window.

Emergency Stop, Pause/Resume, held-input release, delayed start, runtime/action limits, stuck detection, recovery limits, focus-loss behavior, and hotbar restoration remain available across automation. Safe Mode is a conservative multiplayer filter and does not replace server rules.

## Appearance and local assets

Themes remain available under **Options → Appearance**: Chorus, Light, Cyber, Vanilla, Aether, Foundry, and Custom. Minecraft artwork is read from the player's installed Java files at runtime where applicable; F3+ does not redistribute Mojang textures.

## Updates and offline behavior

F3+ checks `LucidOcelot/F3Plus` `main` at launch. Clean Git checkouts fast-forward, while extracted ZIP installs apply validated immutable commit archives. User configuration under `~/.f3plus` is preserved, tracked local Git changes are not overwritten, and update failure does not prevent an installed copy from launching offline.

Normal prepared calculations, settings, local-data browsing, and generated-save analysis run locally. Network access is used for update checks, dependency/component acquisition, optional upstream helpers, or exact Mojang reference-world acquisition when requested.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider. Community lineage and third-party software are documented in `COMMUNITY_CREDITS.md` and `THIRD_PARTY.md`.
