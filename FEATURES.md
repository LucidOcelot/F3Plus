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

## Simulation Lab

Simulation Lab is a dedicated visual workspace for mechanics that need more than a scalar calculator. It is available from the main menu and relevant historical catalog entries route into the same canonical simulators instead of opening small generic parameter dialogs.

All simulator artwork prefers Minecraft textures from the player's installed Java JAR. Missing textures fall back to original F3+ pixel-art motifs, so a simulator never becomes iconless when an asset name changes or no matching client is installed.

### Loot Table Explorer

The Loot Table Explorer reads every vanilla loot table exposed by an installed client under the Minecraft loot-table data namespace. Tables are grouped as chest loot, entity drops, block drops, fishing, piglin bartering, archaeology, trial/spawner rewards, equipment, and any additional namespaces present in the selected JAR.

Selecting a table shows **all recursively reachable loot** rather than one example roll. Nested loot-table references and item tags are expanded, and each item row shows structural weight, source pool, count range, entry conditions, and loot functions. This keeps context-sensitive entries visible without inventing a false exact probability from incomplete context.

The simulator can roll one pull, ten pulls, one thousand pulls, or a custom sample up to one million pulls using a repeatable seed. Results report observed hit rate, mean item count per pull, total items, and example pulls. `random_chance`, `killed_by_player`, inversion, and all/any condition logic are simulated directly; conditions that require an actual entity/location/tool/score context remain explicitly identified and can be included as potentially eligible branches.

Historical Loot Table Simulator, Structure Loot Simulator, Trial Chamber Loot Simulator, Trial Spawner Reward Simulator, Archaeology Loot Simulator, Fishing Loot Simulator, Piglin Barter Simulator, and Mob Drop Simulator entries open this explorer with an appropriate starting category.

When no usable installed loot-table data exists, F3+ supplies clearly labeled first-party baseline examples covering chest loot, entity drops, fishing/fish/junk/treasure, piglin bartering, archaeology, trial/spawner rewards, and block drops. Those examples are never presented as exact selected-version data.

### Enchanting Table + Anvil Simulator

The enchanting simulator reads the installed enchantment registry where the client exposes data-driven enchantment definitions. It uses enchantment weight, maximum level, minimum/maximum cost curves, supported-item tags, and anvil cost values where available.

The Enchanting Table tab accepts an item, bookshelf count, seed, and optional enchantability override. It renders all three table slots with displayed level cost, lapis cost, modified enchantment power, and the rolled enchantment set. The reference table beside it shows the enchantments that can apply to the selected item under the loaded data.

The Anvil tab accepts left/right enchantment maps, prior-work operation counts, and optional renaming. It reports each merged enchantment, installed-data anvil multiplier, prior-work penalties, total level cost, resulting prior-work penalty, and whether the operation reaches the normal survival **Too Expensive** threshold. Repair-material and durability-merging costs are not silently guessed when they were not entered.

Existing Enchanting Simulator, Enchantment Sequence Simulator, Best Enchantment Search, Enchantment Table Layout, and Anvil Prior-Work Planner entries route to the appropriate simulator tab.

### Brewing Stand Simulator

The Brewing Stand Simulator models potion-state transitions, effect duration/strength modifiers, corruption with Fermented Spider Eye, Redstone extension, Glowstone strengthening, Gunpowder splash conversion, and Dragon's Breath lingering conversion. It also includes modern Awkward-potion effects such as Wind Charged, Weaving, Oozing, and Infested in its fallback rules.

Java brewing transitions are code-defined rather than ordinary datapack recipe JSON, so F3+ labels the internal vanilla brewing-rule set instead of claiming it was extracted from a nonexistent recipe table. Invalid ingredient/state combinations remain unchanged and are explained rather than producing a fabricated potion.

### Cauldron + Leather Dye Mixer

The leather dye mixer implements Java Edition's brightness-preserving RGB mix. Users can add any number of the sixteen dyes, repeat dyes, optionally include an existing leather color, and see the resulting hex/RGB/decimal color with a large visual swatch.

The Cauldron tab is kept separate from dye mixing because Java Edition water cauldrons wash dyed leather rather than storing a persistent mixed dye color. Washing reports the water level before/after and restores the default leather color when the water requirement is met.

### Animal + Horse Breeding Simulator

The Horse Breeding tab models max-health, movement-speed, and jump-strength inheritance within vanilla horse attribute bounds using the modern parent-centered reflected triangular roll family. Coat color and markings use parent-biased inheritance with a smaller random/mutation outcome. Large batches report minimum/mean/maximum attributes, variant distribution, and example offspring NBT.

The All Animals / NBT tab covers the Java breedable-animal roster used by F3+, including horses/donkeys, cows/mooshrooms, sheep, pigs, chickens, rabbits, wolves, cats, ocelots, foxes, pandas, bees, goats, hoglins, striders, llamas, axolotls, frogs, camels, armadillos, sniffers, and turtles. Each profile shows breeding food and the breeding-relevant NBT fields F3+ models. Parent NBT is entered as JSON and the simulator returns child/egg outcomes without copying runtime UUIDs, positions, brain memories, or unrelated entity state into a fictional offspring record.

Species-specific behavior is surfaced where it materially differs: sheep color, axolotl variants including the rare blue mutation roll, panda genes, environment-dependent frog variants, and turtle/sniffer egg-producing workflows are not collapsed into a generic parent average.

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
