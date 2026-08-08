**AI Disclosure:**

F3+ was unfortunately developed with generative AI assistance.
In the spirit of transparency, AI use is described below. 

Approximately 35% of F3+'s original first-party work is estimated to be substantially AI-created or AI-assisted translation, porting, integration, and refactoring of existing human/community work. The remaining work originates from human-written code and designs, ports of earlier Minescript/M.A.R.T. work, or implementations based on established community tools, algorithms, and research. 

Generative AI was also used extensively for integration, debugging, iterative testing in sandboxed environments, UI development, refactoring, documentation, and project organization. Project, features, testing feedback, revisions, and release decisions remained human work. 

All final inclusions were reviewed and edited by a human before being included in the project.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.

Third-party and community contributions are credited separately in COMMUNITY_CREDITS.md and THIRD_PARTY.md.




# F3+ Feature Guide

F3+ is an all-in-one offline companion app for Minecraft. It combines automation helpers, navigation utilities, known-seed tools, calculators, RNG tools, villager references, guided setup tools, and safety controls in one desktop application.

## Important context

- **Offline-first:** F3+ works locally. Some optional upstream helpers are prepared only when a specific feature requests them.
- **Known-seed tools:** Many world, biome, structure, and Nether-generation tools require a Java world seed that you supply.
- **World-seed recovery boundary:** F3+ exposes exactly one world-seed recovery workflow: **Nether Bedrock Cracker**. RNG tools and player/enchantment RNG tools do not recover world seeds.
- **Automation boundary:** Macro and input tools are convenience helpers, not hacked clients. They use normal desktop input delivery and include emergency-stop/safety controls.
- **Minecraft artwork:** Chorus, Light, and Vanilla can read selected textures from the player's own installed Minecraft files at runtime. F3+ never redistributes Mojang artwork.
- **Safe Mode:** Safe Mode hides or blocks tools that should not be used casually, especially automation and sensitive recovery utilities.

## Workspaces

### Automation (63 tools)

#### Continuous Action (6)

- **Generator Miner** — Holds mining input continuously for generator-style block breaking while preserving emergency-stop input release.
- **Hold Attack** — Holds the attack button until stopped.
- **Hold Use** — Holds the use/place button until stopped.
- **Concrete Converter** — Holds attack and use together for stationary concrete-conversion workflows.
- **Auto Walk** — Holds forward movement until stopped.
- **Custom Hold** — Runs the configurable continuous held-input macro template.

#### Periodic Interaction (4)

- **Auto Attack** — Performs repeated attack actions at a fixed interval.
- **AFK Mob Grinder** — Performs repeated attack/use interaction for stationary mob-grinder operation.
- **Livestock Breeder** — Continuously holds feed and performs the configured breeding interaction cycle for livestock.
- **Custom Periodic Action** — Runs the configurable periodic interaction macro template.

#### Fishing (1)

- **Auto Fishing** — Runs an automatic fishing interaction cycle with configurable timing through the macro engine.

#### Travel (13)

- **Basic Travel** — Holds forward movement for continuous travel.
- **Sprint Travel** — Holds forward and sprint for continuous travel.
- **Sprint-Jump Travel** — Combines forward movement, sprinting, and repeated jumping.
- **Swim Travel** — Holds forward, sprint, and swim/jump input for continuous swimming.
- **Boat Travel** — Maintains forward vehicle input for boat travel.
- **Horse/Camel Travel** — Maintains forward mount movement until stopped.
- **Elytra Launch** — Performs the configured elytra launch input sequence.
- **Elytra Cruise** — Maintains the elytra cruise input sequence for a configured duration.
- **Riptide Travel** — Cycles use/charge timing for repeated Riptide propulsion.
- **Spear Dash Travel** — Runs the configured multi-slot spear/dash travel sequence.
- **Coordinate Travel** — Moves toward a coordinate target using captured-position feedback and the configured movement input backend.
- **Waypoint Travel** — Moves toward a saved waypoint using captured-position feedback.
- **Nether-Assisted Travel** — Uses coordinate-target travel with Overworld/Nether scaling to support long-distance routing.

#### Mining (7)

- **Tunnel Miner** — Combines forward travel and mining input for continuous tunnel excavation.
- **Branch Miner** — Runs a coordinate-aware branch-mining pattern with turns and branch spacing.
- **Stair Excavator** — Runs a coordinate-aware staircase excavation pattern.
- **Area Excavator** — Runs a coordinate-aware multi-row excavation pattern.
- **Strip Mine Optimizer** — Calculates planning values for strip mine optimizer rather than directly controlling Minecraft.
- **Beacon Mining Planner** — Calculates planning values for beacon mining planner rather than directly controlling Minecraft.
- **Quarry Planner** — Calculates planning values for quarry planner rather than directly controlling Minecraft.

#### Farming (7)

- **Crop Farmer** — Moves and interacts through a repeating crop-harvest/replant cycle.
- **Coordinate Row Farmer** — Farms a row while using coordinate feedback to control row length and turns.
- **Multi-Row Farmer** — Runs repeated coordinate-aware farming rows with turns between rows.
- **Bone Meal Farmer** — Cycles use/harvest inputs for bone-meal-driven farming.
- **Stationary Grow/Harvest** — Repeats stationary growth and harvest interactions.
- **Tree Farm Cycle** — Runs the configured stationary tree-farm interaction cycle.
- **Farm Station Controller** — Runs the reusable farm-station interaction sequence.

#### Equipment (8)

- **Mending Grinder** — Cycles combat/tool slots for an XP-based mending workflow.
- **Crossbow Volley** — Cycles configured hotbar slots while charging and firing crossbows.
- **Hotbar Workflow** — Executes a repeated sequence across selected hotbar slots.
- **Tool Rotation** — Rotates through selected hotbar tools on a configured cadence.
- **Durability Guard** — Runs held mining input with a bounded cycle guard to reduce unattended overrun.
- **Resource Guard** — Runs held use input with a bounded cycle guard to reduce unattended resource consumption.
- **Food Manager** — Periodically selects and uses the configured food slot during automation.
- **Offhand Workflow** — Periodically performs the configured offhand-swap workflow.

#### Construction (8)

- **Straight-Line Builder** — Places blocks while moving through a repeating straight-line construction pattern.
- **Rectangle Perimeter Builder** — Executes four placement/movement sides with quarter turns to build a rectangle perimeter.
- **Filled Rectangle Builder** — Repeats rows and turns to fill a rectangular construction area.
- **Construction Grid Builder** — Builds a repeating row-and-turn placement grid.
- **Parallel Row Builder** — Builds repeated parallel placement rows.
- **Alternating Row Builder** — Runs the reusable alternating row construction sequence.
- **Perimeter Builder** — Runs a four-sided placement sequence around a perimeter.
- **Repeating Segment Builder** — Repeats a short placement/movement construction segment.

#### Automation (9)

- **Action Sequencer** — Runs a reusable ordered sequence of taps, waits, holds, turns, and other macro actions.
- **Route Runner** — Executes a repeating movement-and-turn route sequence.
- **Macro Recorder** — Defines the recording/template workflow for capturing a repeatable action sequence and turning it into a reusable F3+ automation plan.
- **Macro Template** — Shows the reusable action-template format used to assemble taps, waits, held inputs, turns, and repeated steps before running them as automation.
- **Branch Mine Wizard** — Opens or calculates the branch mine planning workflow used to configure a related gameplay routine.
- **Quarry Wizard** — Opens or calculates the quarry planning workflow used to configure a related gameplay routine.
- **Tree Farm Wizard** — Opens or calculates the tree farm planning workflow used to configure a related gameplay routine.
- **Crop Farm Wizard** — Opens or calculates the crop farm planning workflow used to configure a related gameplay routine.
- **Nether Highway Wizard** — Opens or calculates the nether highway planning workflow used to configure a related gameplay routine.

### Navigation (50 tools)

#### Position (7)

- **Capture Position** — Captures the player coordinates from Minecraft using the configured coordinate-capture method.
- **Copy Sister Coordinates** — Converts the current Overworld/Nether position to its 8:1 sister coordinates and copies the result.
- **Save Sister Waypoint** — Converts the current Overworld/Nether position to sister coordinates and stores them as a waypoint.
- **Current Position** — Uses captured player position data to provide current position behavior.
- **Continuous Capture** — Uses captured player position data to provide continuous capture behavior.
- **Distance Announcer** — Uses captured player position data to provide distance announcer behavior.
- **Bearing Lock** — Uses captured player position data to provide bearing lock behavior.

#### Coordinates (17)

- **3D Coordinate Distance** — Measures horizontal and full 3D distance between two Minecraft positions.
- **Coordinate Bearing** — Reports Minecraft yaw and cardinal direction from one position to another on the X/Z plane.
- **Coordinate Midpoint** — Finds the X/Y/Z position halfway between two coordinates.
- **Coordinate Delta XYZ** — Reports signed coordinate change from the first position to the second.
- **Travel Time from Distance** — Calculates travel time from entered Minecraft coordinates without modifying the world.
- **Block-to-Chunk Converter** — Converts a block X/Z position into its Java Edition chunk coordinates and block bounds.
- **Block-to-Region Converter** — Converts a block position into its Anvil region and reports the region chunk/block bounds.
- **Chunk Center** — Returns the center block coordinate of the chunk containing the entered position.
- **Chunk Border** — Reports the containing chunk and the nearest chunk-line coordinates around the entered block position.
- **Chunk Corner** — Returns all four X/Z block corners of the chunk containing the entered position.
- **Region Border** — Returns the 32×32-chunk Anvil region bounds containing the entered position.
- **Axis Distance** — Reports the absolute X, Y, and Z separation between two positions so you can see which axis dominates the trip or build.
- **Cardinal Snap** — Maps an arbitrary Minecraft yaw to the nearest cardinal facing and its exact snapped yaw.
- **Chunk Line Navigator** — Calculates chunk line navigator from entered Minecraft coordinates without modifying the world.
- **OW/Nether Conversion** — Converts X/Z coordinates between Overworld and Nether travel space using the 8:1 horizontal scale.
- **Coordinate Offset** — Calculates coordinate offset from entered Minecraft coordinates without modifying the world.
- **Coordinate History** — Calculates coordinate history from entered Minecraft coordinates without modifying the world.

#### Waypoints (7)

- **Create Waypoint** — Creates and saves a named waypoint from entered or captured coordinates.
- **Rename Waypoint** — Renames a saved waypoint without changing its coordinates.
- **Delete Waypoint** — Removes a saved waypoint.
- **Nearest Waypoint** — Ranks saved waypoints from the current position and returns the nearest destination.
- **Sort Waypoints by Distance** — Sorts saved waypoints by travel distance from the current position.
- **Waypoint Route** — Builds a greedy travel route through saved waypoints from the current position.
- **Waypoint Groups** — Manages or analyzes saved waypoint data for waypoint groups.

#### Routes (10)

- **Multi-stop Route** — Builds or analyzes a route using multi-stop route logic and supplied/saved positions.
- **Breadcrumb Simplifier** — Builds or analyzes a route using breadcrumb simplifier logic and supplied/saved positions.
- **Coordinate Route** — Builds or analyzes a route using coordinate route logic and supplied/saved positions.
- **Resource Route** — Builds or analyzes a route using resource route logic and supplied/saved positions.
- **Structure Tour** — Builds or analyzes a route using structure tour logic and supplied/saved positions.
- **Biome Expedition** — Builds or analyzes a route using biome expedition logic and supplied/saved positions.
- **Breadcrumb Recorder** — Builds or analyzes a route using breadcrumb recorder logic and supplied/saved positions.
- **Expedition Recorder** — Builds or analyzes a route using expedition recorder logic and supplied/saved positions.
- **Survey Mode** — Builds or analyzes a route using survey mode logic and supplied/saved positions.
- **Loop Detection** — Builds or analyzes a route using loop detection logic and supplied/saved positions.

#### Portal Helpers (9)

- **Ideal Sister Portal Coordinates** — Converts an Overworld position to its ideal Nether X/Z sister position using the 8:1 horizontal scale while preserving the entered Y as a reference.
- **Portal Exit Selection Calculator** — Compares the ideal scaled Nether exit with another candidate portal and ranks which exit is geometrically closer to the Overworld portal target.
- **Competing Portal Link Analysis** — Shows which candidate exit an Overworld portal would select and how close the competing exit is, exposing links likely to steal or redirect a portal connection.
- **Best Candidate Portal Placement** — Chooses the better of the entered candidate Nether portals for the Overworld entry and reports its routing distance and margin over the alternative.
- **Portal Link Network Summary** — Builds an entry-to-exit link summary for the entered Overworld portal, its ideal Nether counterpart, and a competing Nether portal, including detected link cycles.
- **Nether Highway Distance Planner** — Estimates Nether-highway travel measurements for the entered Overworld distance so a long trip can be laid out at Nether scale.
- **Portal Exit Separation Check** — Measures the 3D separation between the ideal scaled Nether exit and another candidate exit so you can judge how strongly they compete for the same link.
- **Portal Coverage Radius Calculator** — Calculates the diameter and horizontal area represented by the entered portal-planning radius.
- **Two-Portal Nether Shortcut** — Converts two Overworld endpoints to Nether coordinates and reports the Nether leg between them, showing the distance saved by a two-portal shortcut.

### World & Seed (56 tools)

#### World Seed Recovery (1)

- **Nether Bedrock Cracker** — Recovers a Java Edition world seed from observed Nether bedrock positions through the bundled/upstream Nether Bedrock Cracker workflow; this is F3+'s only world-seed recovery route.

#### Slime (9)

- **Nearest Slime Chunk** — Uses the Java Edition slime-chunk formula with a known world seed to calculate nearest slime chunk.
- **Slime Chunks in Radius** — Uses the Java Edition slime-chunk formula with a known world seed to calculate slime radius.
- **Adjacent Slime Chunk Pair** — Uses the Java Edition slime-chunk formula with a known world seed to calculate adjacent pair.
- **2×2 Slime Chunk Cluster** — Uses the Java Edition slime-chunk formula with a known world seed to calculate 2x2 cluster.
- **Triple Slime Chunk Cluster** — Uses the Java Edition slime-chunk formula with a known world seed to calculate triple cluster.
- **Quad Slime Chunk Cluster** — Uses the Java Edition slime-chunk formula with a known world seed to calculate quad cluster.
- **Largest Connected Cluster** — Uses the Java Edition slime-chunk formula with a known world seed to calculate largest connected cluster.
- **Slime Chunk Density** — Uses the Java Edition slime-chunk formula with a known world seed to calculate slime density.
- **Farm Location Ranking** — Uses the Java Edition slime-chunk formula with a known world seed to calculate farm location ranking.

#### Cubiomes (2)

- **Cubiomes Status** — Reports whether the bundled Cubiomes source and its compiled local library are available.
- **Cubiomes Biome Query** — Queries the bundled Cubiomes generator for the biome at a known-seed coordinate on Minecraft versions supported by that Cubiomes revision.

#### Nether (25)

- **Asymmetric (One-Way) Portal Linking** — Generates a candidate chain of alternating low/high Nether portal pairs and evaluates the resulting links. It is intended for asymmetric or one-way portal-link layouts where the return portal can resolve differently from the arrival portal.
- **Portal Y-Level Isolation Check** — Examines Y separation between same-dimension portals in a generated asymmetric layout so vertically separated candidates can be checked before relying on them for link isolation.
- **Portal Link Reliability Margin** — Reports each generated portal link and its margin over the next-best candidate; larger margins mean the selected exit is less likely to be displaced by a nearby competing portal.
- **Two-Way Portal Link Matrix** — Lists the selected exit, routing distance, and competing-link margin for every portal in the generated Overworld/Nether test layout.
- **Nether Portal Link Graph** — Summarizes the directed portal-link network produced by the generated test layout, including portal counts, selected exits, and any routing cycles.
- **Portal Link Loop Detector** — Finds cycles in the directed portal-link graph, such as entering through one portal and returning through a different chain instead of the intended pair.
- **Nether Shortcut Compression Ratio** — Compares effective Overworld distance gained with the physical Nether and Overworld walking required, reporting travel gained per walked block and reduction versus a conventional Nether route.
- **Nether Biome Composition Scan** — Samples the Nether around the entered seed/chunk center with the bundled supported Cubiomes backend and reports biome-ID composition plus representative sampled chunks.
- **Fortress Finder** — Returns nearby Nether Fortress placement-candidate chunks for the entered known world seed and search radius. Final generation still depends on supported version rules and viability checks.
- **Bastion Finder** — Returns nearby Bastion Remnant placement-candidate chunks for the entered known world seed and search radius. Final generation still depends on supported version rules and viability checks.
- **Fortress+Bastion Finder** — Returns both Nether Fortress and Bastion Remnant placement-candidate chunks around the same known-seed search center so their proximity can be compared.
- **Nether Fortress + Bastion Candidate Density** — Counts Nether Fortress and Bastion placement candidates in the entered chunk radius and reports total candidates plus candidates per 1,000 sampled chunks.
- **Nether Bedrock Recovery Helper** — Hands world-seed recovery off to the permitted Nether Bedrock Cracker workflow; F3+ does not provide a second independent bedrock seed-cracking implementation.
- **Asymmetric Portal Jump Layout** — inputs and planning context for an asymmetric portal-jump layout; use the dedicated asymmetric link analysis tools to validate actual entry-to-exit routing before building.
- **Maximum Portal Link Offset** — Provides portal-network planning values for testing how far a candidate exit can be displaced from its scaled target; validate the final link with the reliability/link-matrix tools.
- **Repeated Asymmetric Portal Network** — Provides planning parameters for repeating portal-network layouts. Use the generated link matrix/graph tools to verify each repeated stage before construction.
- **Portal Destination Gate Plan** — Provides planning values for a destination-gated portal network where only selected exits should remain active for a destination.
- **Active/Inactive Portal Link Simulator** — Provides planning values for evaluating how enabling or disabling candidate portals can change the selected entry-to-exit link.
- **Portal Entry-to-Exit Routing Table** — Provides portal-network planning values intended to be turned into an entry-to-exit routing table; pair it with the link-matrix result for concrete link selection.
- **Nether Corridor Travel Comparison** — Provides planning values for comparing portal-assisted travel with a conventional Nether corridor route.
- **Standard vs. Asymmetric Portal Route** — Provides planning values for comparing conventional paired portals against asymmetric portal-routing layouts.
- **Multi-Destination Portal Link Optimizer** — Provides planning values for a portal network serving several destinations; final link choices must be checked with the link matrix rather than assumed from the title.
- **Portal Link Reliability Heatmap** — Provides portal-network planning values intended for comparing link stability over an area; reliability is represented by routing margin between the best and next-best exits.
- **Portal Search-Radius Visualizer** — Provides portal-network planning values for visualizing candidate search/separation radius around a portal target.
- **Portal Network Travel-Cost Optimizer** — Provides planning values for comparing portal-network travel cost; it does not alter Minecraft portal mechanics or guarantee an automatically optimal build.

#### Local Area (8)

- **32-Chunk Analysis** — Reports the selected center/radius, sampled-chunk count, and local slime-chunk count as the current data behind the 32-chunk analysis view.
- **Biome Composition** — Reports the selected center/radius, sampled-chunk count, and local slime-chunk count as the current data behind the biome composition view.
- **Local Structure Counts** — Reports the selected center/radius, sampled-chunk count, and local slime-chunk count as the current data behind the structure counts view.
- **Local Slime Chunk Distribution** — Reports the selected center/radius, sampled-chunk count, and local slime-chunk count as the current data behind the slime distribution view.
- **Notable Locations** — Reports the selected center/radius, sampled-chunk count, and local slime-chunk count as the current data behind the notable locations view.
- **Local Technical Build Score** — Reports the selected center/radius, sampled-chunk count, and local slime-chunk count as the current data behind the technical score view.
- **Build Score** — Reports the selected center/radius, sampled-chunk count, and local slime-chunk count as the current data behind the build score view.
- **Exploration Score** — Reports the selected center/radius, sampled-chunk count, and local slime-chunk count as the current data behind the exploration score view.

#### World Analysis (11)

- **Spawn Analysis** — Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind spawn analysis; it does not fabricate a numeric score that is not actually calculated.
- **Technical World Score** — Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind technical world score; it does not fabricate a numeric score that is not actually calculated.
- **Resource Score** — Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind resource score; it does not fabricate a numeric score that is not actually calculated.
- **Seed Comparison** — Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind seed comparison; it does not fabricate a numeric score that is not actually calculated.
- **Ore Distribution** — Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind ore distribution; it does not fabricate a numeric score that is not actually calculated.
- **Ore Exposure Estimate** — Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind ore exposure estimate; it does not fabricate a numeric score that is not actually calculated.
- **Ancient City Area Analysis** — Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind ancient city area analysis; it does not fabricate a numeric score that is not actually calculated.
- **Cave Exposure Estimate** — Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind cave exposure estimate; it does not fabricate a numeric score that is not actually calculated.
- **Chunk Loading Simulator** — Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind chunk loading simulator; it does not fabricate a numeric score that is not actually calculated.
- **Spawn Chunk Optimizer** — Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind spawn chunk optimizer; it does not fabricate a numeric score that is not actually calculated.
- **Search Radius Optimizer** — Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind search radius optimizer; it does not fabricate a numeric score that is not actually calculated.

### Structures & Biomes (58 tools)

#### Structures (29)

- **Structure Candidate Search** — Returns nearby placement-candidate sets for Village, Trial Chamber, Ocean Monument, and Pillager Outpost around the entered seed/chunk center.
- **Village Candidate Finder** — Finds known-seed village placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Stronghold Candidate Finder** — Finds known-seed stronghold placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Trial Chamber Candidate Finder** — Finds known-seed trial chamber placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Ancient City Candidate Finder** — Finds known-seed ancient city placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Woodland Mansion Candidate Finder** — Finds known-seed woodland mansion placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Ocean Monument Candidate Finder** — Finds known-seed ocean monument placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Desert Pyramid Candidate Finder** — Finds known-seed desert pyramid placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Jungle Temple Candidate Finder** — Finds known-seed jungle temple placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Swamp Hut Candidate Finder** — Finds known-seed swamp hut placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Igloo Candidate Finder** — Finds known-seed igloo placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Pillager Outpost Candidate Finder** — Finds known-seed pillager outpost placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Ruined Portal Candidate Finder** — Finds known-seed ruined portal placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Shipwreck Candidate Finder** — Finds known-seed shipwreck placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Ocean Ruin Candidate Finder** — Finds known-seed ocean ruin placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Buried Treasure Candidate Finder** — Finds known-seed buried treasure placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Mineshaft Candidate Finder** — Finds known-seed mineshaft placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Nether Fortress Candidate Finder** — Finds known-seed nether fortress placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Bastion Candidate Finder** — Finds known-seed bastion placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **End City Candidate Finder** — Finds known-seed end city placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.
- **Multi-Structure Candidate Search** — Returns candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as planning data for compound search. It does not claim a specialized compound search solver when the current backend only supplies those candidate counts.
- **Structure Chains** — Returns candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as planning data for structure chains. It does not claim a specialized structure chains solver when the current backend only supplies those candidate counts.
- **Isolated Structure Finder** — Returns candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as planning data for isolated structure finder. It does not claim a specialized isolated structure finder solver when the current backend only supplies those candidate counts.
- **Structure Cluster Finder** — Returns candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as planning data for structure cluster finder. It does not claim a specialized structure cluster finder solver when the current backend only supplies those candidate counts.
- **Structure Candidate Density** — Returns candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as planning data for structure density. It does not claim a specialized structure density solver when the current backend only supplies those candidate counts.
- **Structure Candidate Heatmap** — Returns candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as planning data for structure heatmap. It does not claim a specialized structure heatmap solver when the current backend only supplies those candidate counts.
- **Structure Corridor** — Returns candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as planning data for structure corridor. It does not claim a specialized structure corridor solver when the current backend only supplies those candidate counts.
- **Multi-Target Locator** — Returns candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as planning data for multi-target locator. It does not claim a specialized multi-target locator solver when the current backend only supplies those candidate counts.
- **Portal-Optimized Structure Search** — Returns candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as planning data for portal-optimized structure search. It does not claim a specialized portal-optimized structure search solver when the current backend only supplies those candidate counts.

#### Spawners (7)

- **Dungeon/Pig Spawner Locator** — Inspects generated Java Edition Anvil/NBT world-save data to locate or rank dungeon/pig spawner locator rather than pretending all spawners are seed-predictable.
- **Double Spawner Locator** — Inspects generated Java Edition Anvil/NBT world-save data to locate or rank double spawner locator rather than pretending all spawners are seed-predictable.
- **Triple Spawner Locator** — Inspects generated Java Edition Anvil/NBT world-save data to locate or rank triple spawner locator rather than pretending all spawners are seed-predictable.
- **Quad Spawner Locator** — Inspects generated Java Edition Anvil/NBT world-save data to locate or rank quad spawner locator rather than pretending all spawners are seed-predictable.
- **Spawner Cluster Ranking** — Inspects generated Java Edition Anvil/NBT world-save data to locate or rank spawner cluster ranking rather than pretending all spawners are seed-predictable.
- **Stronghold Silverfish** — Inspects generated Java Edition Anvil/NBT world-save data to locate or rank stronghold silverfish rather than pretending all spawners are seed-predictable.
- **Trial Chamber Spawners** — Inspects generated Java Edition Anvil/NBT world-save data to locate or rank trial chamber spawners rather than pretending all spawners are seed-predictable.

#### Biomes (22)

- **Biome at Coordinate** — Reports the biome for the requested known-seed/world location when a supported biome-generation backend is available.
- **Nearest Biome Search** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the nearest biome view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Rare Biome Search** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the rare biome search view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Largest Biome Region Search** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the largest biome view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Largest Ocean** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the largest ocean view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Largest Mountain Chain** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the largest mountain chain view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Largest Cave Region** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the largest cave region view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Flat Terrain Finder** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the flat terrain finder view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Valley Finder** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the valley finder view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Mountain Peak Finder** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the mountain peak finder view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Terrain Base Finder** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the terrain base finder view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Island Finder** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the island finder view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Peninsula Detector** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the peninsula detector view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **River Crossing Finder** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the river crossing finder view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Local Lake Density** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the lake density view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Cliff Locator** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the cliff locator view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Biome Boundary Search** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the biome boundary view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Two-Way Biome Intersection** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the two-way biome intersection view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Three-Way Biome Intersection** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the three-way biome intersection view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Four-Way Biome Intersection** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the four-way biome intersection view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Biome Diversity Finder** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the biome diversity finder view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.
- **Largest Continuous Region** — Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the largest continuous region view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.

### Calculators (76 tools)

#### Coordinate (7)

- **Distance Calculator** — Measures the straight-line 3D distance and the horizontal X/Z distance between two Minecraft positions.
- **Bearing Calculator** — Calculates Minecraft yaw from one X/Z position to another. The result follows Minecraft orientation: 0° south, -90° east, 90° west, and ±180° north.
- **Midpoint Calculator** — Finds the exact X/Y/Z point halfway between two entered positions.
- **Travel Time Calculator** — Estimates travel time by dividing the entered distance by movement speed in blocks per second.
- **Nether Conversion Calculator** — Converts X/Z coordinates between Overworld and Nether space using the standard 8:1 horizontal scale.
- **Coordinate Snap** — Rounds a position to a whole block and reports the center of the chunk containing that position.
- **Delta XYZ Calculator** — Reports the signed X, Y, and Z displacement from the first coordinate to the second.

#### Redstone (13)

- **Tick Converter** — Converts game ticks into seconds, minutes, and hours using Minecraft’s 20 game ticks per second.
- **Hopper Timer** — Estimates hopper-transfer timer duration from item count using one transfer every 8 game ticks while the hopper can transfer normally.
- **Comparator Strength** — Calculates comparator output strength from how full a container is relative to its slot and stack capacity.
- **Repeater Delay** — Adds the selected repeater settings and returns total redstone ticks, game ticks, and seconds.
- **Observer Delay** — Uses the entered timing values to plan the combined game/redstone delay for an observer-driven timing chain.
- **Minecart Timing** — Estimates rail travel time from distance using the planner’s assumed 8 blocks/second minecart speed.
- **Water Stream Timing** — Estimates item/water-stream travel time from distance using a planning speed; real layouts can change the result.
- **Ice Boat Timing** — Estimates boat travel time from distance and the speed value you provide.
- **Crafter Throughput** — Converts a crafter cycle time and items per cycle into estimated items per hour.
- **Pulse Extender** — Calculates the combined delay of the entered repeater-style timing values for a pulse-extension plan.
- **Clock Period** — Calculates the total repeater-chain period represented by the entered timing settings.
- **Counter Timing** — Calculates the total repeater-chain timing used by a counter or pulse-counting design.
- **Signal Timing** — Calculates total signal delay through the entered repeater-style timing values.

#### Storage (8)

- **Storage Capacity** — Breaks an item count into full stacks, remainder, shulker boxes, and double chests for the selected stack size.
- **Bulk Materials** — Summarizes how a bulk item target fits into stacks, shulker boxes, and double chests.
- **Item Compression** — Calculates how many compressed items/blocks can be made from the entered item count and what remains.
- **Material Logistics** — Combines player inventory and carried shulker capacity to estimate how many trips a material haul requires.
- **Transport Trips** — Calculates carried capacity and trip count for moving an item total with the selected number of shulker boxes.
- **Shulker Requirement** — Calculates how many shulker boxes are required for the entered item count and stack size.
- **Chest Requirement** — Calculates how many double chests are required for the entered item count and stack size.
- **Material Weight** — Calculates storage/logistics requirements for material weight from item and stack counts.

#### Technical (30)

- **Mob Cap Calculator** — Estimates the natural-spawn category cap from eligible chunks and the category base cap, with a simple multi-player upper-bound reference.
- **Despawn Radius Planner** — Reports the soft/hard despawn radii and the hard-despawn square bounds around the entered player position.
- **Item Sorter Planner** — Estimates module count, reserved filter items, hopper slots, and distinct sorted items for a conventional sorter layout.
- **Chunk Alignment** — Reports exact 16×16 chunk block bounds around the entered X/Z position.
- **Region Alignment** — Reports exact 32×32-chunk Anvil-region bounds around the entered X/Z position.
- **Cardinal Alignment** — Runs the concrete technical calculation labeled cardinal alignment and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Build Rotation** — Runs the concrete technical calculation labeled build rotation and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Build Symmetry Calculator** — Runs the concrete technical calculation labeled symmetry and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Blueprint Coordinates** — Runs the concrete technical calculation labeled blueprint coordinates and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Chunk Loader Planner** — Runs the concrete technical calculation labeled chunk loader planner and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Loaded Chunk Area** — Runs the concrete technical calculation labeled loaded chunk area and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Simulation Distance Area Calculator** — Calculates the square chunk area and block width covered by the selected simulation-distance radius.
- **Render Distance Area Calculator** — Calculates the square chunk area and block width represented by the selected render-distance radius.
- **Spawn Sphere** — Calculates radius, diameter, and geometric volume for the selected spawning sphere.
- **Mob Spawn Area** — Runs the concrete technical calculation labeled mob spawn area and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Random Tick Area** — Calculates the square chunk/block area affected by the selected simulation-distance radius for random-tick planning.
- **Spawnproof Calculator** — Runs the concrete technical calculation labeled spawnproof calculator and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Farm Separation** — Runs the concrete technical calculation labeled farm separation and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Iron Farm Spacing** — Runs the concrete technical calculation labeled iron farm spacing and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Villager Gossip Radius** — Runs the concrete technical calculation labeled villager gossip radius and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Raid Distance** — Runs the concrete technical calculation labeled raid distance and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Perimeter Planner** — Runs the concrete technical calculation labeled perimeter planner and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Branch Density Calculator** — Runs the concrete technical calculation labeled branch density calculator and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Tunnel Progress** — Runs the concrete technical calculation labeled tunnel progress and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Torch Planner** — Runs the concrete technical calculation labeled torch planner and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Chunk Loader Radius** — Runs the concrete technical calculation labeled chunk loader radius and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Mob Cap Reference Calculator** — Runs the concrete technical calculation labeled mob cap and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Guardian Area** — Runs the concrete technical calculation labeled guardian area and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Fortress Bounding Box** — Runs the concrete technical calculation labeled fortress bounding box and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.
- **Mob Switch Radius** — Runs the concrete technical calculation labeled mob switch radius and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.

#### Speedrunning (4)

- **Eye Throw Triangulation** — Intersects two Minecraft-yaw eye-throw rays to estimate a stronghold direction/position when the throws are not parallel.
- **Stronghold Ring** — Returns the planning radius range and stronghold count for the selected modern stronghold ring index.
- **Blind Travel Coordinate Calculator** — Calculates speedrunning route/triangulation values for blind travel; probabilistic mechanics remain estimates where appropriate.
- **Blaze Route Planner** — Calculates speedrunning route/triangulation values for blaze route planner; probabilistic mechanics remain estimates where appropriate.

#### Resource Usage (11)

- **XP Level Calculator** — Converts Minecraft experience levels into cumulative XP points using the piecewise vanilla level formulas.
- **Mending Repair Calculator** — Uses Mending’s 2 durability per absorbed XP point conversion to estimate maximum repair and average repair across eligible items.
- **Anvil Prior-Work Planner** — Shows the 0, 1, 3, 7… prior-work penalty progression so you can plan a balanced anvil combination tree.
- **Tool Wear** — Estimates expected durability consumption from action count and Unbreaking level, plus a conservative worst-case count.
- **Food Usage** — Estimates consumption, durability, XP, or material requirements for food usage.
- **Rocket Usage** — Estimates consumption, durability, XP, or material requirements for rocket usage.
- **Fuel Usage** — Estimates consumption, durability, XP, or material requirements for fuel usage.
- **Torch Usage** — Estimates consumption, durability, XP, or material requirements for torch usage.
- **Bone Meal Usage** — Estimates consumption, durability, XP, or material requirements for bone meal usage.
- **Material Progress** — Estimates consumption, durability, XP, or material requirements for material progress.
- **Resource Goal Calculator** — Estimates consumption, durability, XP, or material requirements for resource goal calculator.

#### End (3)

- **Gateway Calculator** — Calculates End-dimension routing or coordinate values for gateway calculator.
- **Outer Island Distance** — Calculates End-dimension routing or coordinate values for outer island distance.
- **End City Route** — Calculates End-dimension routing or coordinate values for end city route.

### Building & Farming (59 tools)

#### Build (24)

- **Build Area Calculator** — Calculates width × length for a rectangular build footprint and also reports the related dimensions.
- **Build Volume Calculator** — Calculates width × length × height for a rectangular build volume.
- **Build Surface Area Calculator** — Calculates the total exterior surface area of a rectangular prism from width, length, and height.
- **Build Perimeter Calculator** — Calculates the perimeter around a rectangular width/length footprint.
- **Build Block Count Calculator** — Treats the entered dimensions as a filled rectangular prism and reports the required block count.
- **Stack Count Calculator** — Converts the filled build volume into storage units so you can prepare stacks before building.
- **Shulker Box Requirement** — Converts the filled build volume into the number of shulker boxes required.
- **Double Chests** — Converts the filled build volume into the number of double chests required.
- **Foundation Planner** — Calculates the rectangular foundation footprint and supporting dimension totals from width and length.
- **Stair Calculator** — Calculates a stair run from target height and step spacing so you can check horizontal run before building.
- **Spiral Staircase Planner** — Generates block coordinates for a spiral staircase from diameter, height, and steps per turn.
- **Catenary Calculator** — Generates a block-sampled hanging cable/chain curve from span, sag, and endpoint height difference.
- **Roof Pitch** — Calculates rise/run, pitch ratio, and approximate roof layers from the entered build dimensions.
- **Wall Segments** — Calculates perimeter length and the number of repeated wall segments at the selected spacing.
- **Bridge Span** — Calculates bridge length plus support positions/count from the chosen support spacing.
- **Build Grid Coordinate Calculator** — Calculates Minecraft build measurements/material planning for grid.
- **Lighting Grid** — Generates evenly spaced light positions across a rectangular floor, including the far edges when spacing does not divide evenly.
- **Pillar Spacing** — Calculates how many structural supports are needed along both build axes at the selected spacing.
- **Road Planner** — Calculates road block area and repeated marker/support positions from width, length, and spacing.
- **Crop Layout** — Calculates Minecraft build measurements/material planning for crop layout.
- **Gradient Ratio** — Calculates rise/run ratio and percent grade for a slope from vertical rise and horizontal run.
- **Chunk Grid Builder** — Calculates how many 16×16 chunks a rectangular build spans in X and Z.
- **Circle Layer Export** — Calculates Minecraft build measurements/material planning for circle layer export.
- **Beacon Offset** — Calculates Minecraft build measurements/material planning for beacon offset.

#### Shapes (17)

- **Circle Block Layout** — Generates the discrete block coordinates for a hollow circular outline at the selected radius.
- **Filled Circle** — Generates every block coordinate inside a filled circle at the selected radius.
- **Sphere Block Layout** — Generates a 3D block-coordinate shell approximating a sphere at the selected radius.
- **Hollow Sphere** — Generates a one-block-thick spherical shell rather than a filled solid.
- **Dome** — Generates the upper half of a spherical block shell for dome construction.
- **Cylinder Block Layout** — Extrudes a circular block outline vertically for the selected height.
- **Cone Block Layout** — Generates decreasing circular layers to approximate a Minecraft cone.
- **Spiral** — Generates block-coordinate/layer measurements for a Minecraft spiral shape.
- **Helix Block Layout** — Generates a rising spiral block path around a selected radius and height.
- **Double-Helix Block Layout** — Generates two opposing rising spiral block paths around the same axis.
- **Hexagon Block Layout** — Generates block-coordinate/layer measurements for a Minecraft hexagon shape.
- **Octagon Block Layout** — Generates block-coordinate/layer measurements for a Minecraft octagon shape.
- **Ellipse Block Layout** — Generates block-coordinate/layer measurements for a Minecraft ellipse shape.
- **Pyramid Block Layout** — Generates block-coordinate/layer measurements for a Minecraft pyramid shape.
- **Diamond Block Layout** — Generates block-coordinate/layer measurements for a Minecraft diamond shape.
- **Rounded Rectangle** — Generates block-coordinate/layer measurements for a Minecraft rounded rectangle shape.
- **Arch Block Layout** — Generates block-coordinate/layer measurements for a Minecraft arch shape.

#### Farm (18)

- **Crop Yield** — Runs the concrete farm-planning calculation labeled crop yield and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Tree Yield** — Runs the concrete farm-planning calculation labeled tree yield and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Animal Breeding** — Runs the concrete farm-planning calculation labeled animal breeding and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Villager Breeding** — Runs the concrete farm-planning calculation labeled villager breeding and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Furnace Array** — Runs the concrete farm-planning calculation labeled furnace array and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Fuel Optimizer** — Runs the concrete farm-planning calculation labeled fuel optimizer and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Beacon Pyramid** — Runs the concrete farm-planning calculation labeled beacon pyramid and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Beacon Coverage** — Runs the concrete farm-planning calculation labeled beacon coverage and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Sugar Cane Layout** — Runs the concrete farm-planning calculation labeled sugar cane layout and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Bamboo Layout** — Runs the concrete farm-planning calculation labeled bamboo layout and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Kelp Tower** — Runs the concrete farm-planning calculation labeled kelp tower and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Bee Apiary** — Runs the concrete farm-planning calculation labeled bee apiary and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Villager Hall Layout** — Runs the concrete farm-planning calculation labeled villager hall layout and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Animal Pen** — Runs the concrete farm-planning calculation labeled animal pen and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Crop Row Calculator** — Runs the concrete farm-planning calculation labeled crop row calculator and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Slime Farm Optimizer** — Runs the concrete farm-planning calculation labeled slime farm optimizer and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Fortress Farm Planner** — Runs the concrete farm-planning calculation labeled fortress farm planner and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.
- **Trial Chamber Planner** — Runs the concrete farm-planning calculation labeled trial chamber planner and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.

### RNG (36 tools)

#### RNG Recovery (4)

- **Enchantment / Player RNG Seed Cracker** — Recovers Minecraft enchantment/player RNG state through Earthcomputer EnchantmentCracker v1.9. F3+ downloads and SHA-256 verifies the upstream tool on first use; this workflow never recovers the world seed.
- **Java RNG State Recovery — 2 nextInt Outputs** — Recovers the 48-bit internal state of a java.util.Random-compatible RNG from two consecutive unbounded nextInt() observations, then predicts the next output.
- **Java RNG State Recovery — nextLong Output** — Recovers the 48-bit internal state of a java.util.Random-compatible RNG from one observed nextLong() value by reversing the two consecutive 32-bit outputs that formed it.
- **Recovered Java RNG State Inspector** — Advances or rewinds a recovered 48-bit java.util.Random internal state and predicts subsequent nextInt() outputs.

#### Enchanting (9)

- **Enchantment Probability** — Runs the implemented enchanting calculation for enchantment probability: probability/cost helpers use direct formulas, while simulator-style entries return deterministic sample rolls from the entered gameplay RNG seed. This never implies world-seed recovery.
- **Bookshelf Planner** — Runs the implemented enchanting calculation for bookshelf planner: probability/cost helpers use direct formulas, while simulator-style entries return deterministic sample rolls from the entered gameplay RNG seed. This never implies world-seed recovery.
- **Lapis Cost Calculator** — Runs the implemented enchanting calculation for lapis cost calculator: probability/cost helpers use direct formulas, while simulator-style entries return deterministic sample rolls from the entered gameplay RNG seed. This never implies world-seed recovery.
- **Grindstone Reset Planner** — Runs the implemented enchanting calculation for grindstone reset planner: probability/cost helpers use direct formulas, while simulator-style entries return deterministic sample rolls from the entered gameplay RNG seed. This never implies world-seed recovery.
- **Enchantment Sequence Simulator** — Runs the implemented enchanting calculation for enchantment sequence simulator: probability/cost helpers use direct formulas, while simulator-style entries return deterministic sample rolls from the entered gameplay RNG seed. This never implies world-seed recovery.
- **Enchanting Simulator** — Runs the implemented enchanting calculation for enchanting simulator: probability/cost helpers use direct formulas, while simulator-style entries return deterministic sample rolls from the entered gameplay RNG seed. This never implies world-seed recovery.
- **Best Enchantment Search** — Runs the implemented enchanting calculation for best enchantment search: probability/cost helpers use direct formulas, while simulator-style entries return deterministic sample rolls from the entered gameplay RNG seed. This never implies world-seed recovery.
- **XP Level Planner** — Runs the implemented enchanting calculation for xp level planner: probability/cost helpers use direct formulas, while simulator-style entries return deterministic sample rolls from the entered gameplay RNG seed. This never implies world-seed recovery.
- **Enchantment Table Layout** — Runs the implemented enchanting calculation for enchantment table layout: probability/cost helpers use direct formulas, while simulator-style entries return deterministic sample rolls from the entered gameplay RNG seed. This never implies world-seed recovery.

#### Drops (1)

- **Mob Drop Simulator** — Simulates repeated drop rolls for mob drop simulator from the supplied probability/RNG inputs.

#### Probability (8)

- **RNG Sequence Viewer** — Uses the entered probability/attempt count or deterministic Java-RNG-style sequence helper for rng sequence viewer, returning explicit odds or sample sequence data without treating the RNG seed as a world seed.
- **Gameplay RNG Timeline** — Uses the entered probability/attempt count or deterministic Java-RNG-style sequence helper for rng timeline, returning explicit odds or sample sequence data without treating the RNG seed as a world seed.
- **RNG Probability Calculator** — Uses the entered probability/attempt count or deterministic Java-RNG-style sequence helper for rng probability calculator, returning explicit odds or sample sequence data without treating the RNG seed as a world seed.
- **Loot Odds Calculator** — Uses the entered probability/attempt count or deterministic Java-RNG-style sequence helper for loot odds calculator, returning explicit odds or sample sequence data without treating the RNG seed as a world seed.
- **Rare Drop Odds** — Uses the entered probability/attempt count or deterministic Java-RNG-style sequence helper for rare drop odds, returning explicit odds or sample sequence data without treating the RNG seed as a world seed.
- **Barter Odds** — Uses the entered probability/attempt count or deterministic Java-RNG-style sequence helper for barter odds, returning explicit odds or sample sequence data without treating the RNG seed as a world seed.
- **Trial Reward Odds** — Uses the entered probability/attempt count or deterministic Java-RNG-style sequence helper for trial reward odds, returning explicit odds or sample sequence data without treating the RNG seed as a world seed.
- **Enchantment Odds** — Uses the entered probability/attempt count or deterministic Java-RNG-style sequence helper for enchantment odds, returning explicit odds or sample sequence data without treating the RNG seed as a world seed.

#### Loot (7)

- **Loot Table Simulator** — Runs repeated seeded Bernoulli-style sample rolls for loot table simulator and reports success indices/count/rate. This is a focused probability simulator, not the full current loot engine.
- **Structure Loot Simulator** — Runs repeated seeded Bernoulli-style sample rolls for structure loot simulator and reports success indices/count/rate. This is a focused probability simulator, not the full current loot engine.
- **Trial Chamber Loot Simulator** — Runs repeated seeded Bernoulli-style sample rolls for trial chamber loot simulator and reports success indices/count/rate. This is a focused probability simulator, not the full current loot engine.
- **Fishing Loot Simulator** — Runs repeated seeded Bernoulli-style sample rolls for fishing loot simulator and reports success indices/count/rate. This is a focused probability simulator, not the full current loot engine.
- **Archaeology Loot Simulator** — Runs repeated seeded Bernoulli-style sample rolls for archaeology loot simulator and reports success indices/count/rate. This is a focused probability simulator, not the full current loot engine.
- **Piglin Barter Simulator** — Runs repeated seeded Bernoulli-style sample rolls for piglin barter simulator and reports success indices/count/rate. This is a focused probability simulator, not the full current loot engine.
- **Trial Spawner Reward Simulator** — Runs repeated seeded Bernoulli-style sample rolls for trial spawner reward simulator and reports success indices/count/rate. This is a focused probability simulator, not the full current loot engine.

#### Generation RNG (7)

- **Decoration RNG Preview** — Previews or simulates decoration rng RNG behavior; This is a focused preview, not a full modern world generator.
- **Feature Placement RNG** — Previews or simulates feature placement rng RNG behavior; This is a focused preview, not a full modern world generator.
- **Ore Placement Simulator** — Previews or simulates ore placement simulator RNG behavior; This is a focused preview, not a full modern world generator.
- **Tree Generation Simulator** — Previews or simulates tree generation simulator RNG behavior; This is a focused preview, not a full modern world generator.
- **Geode Placement Simulator** — Previews or simulates geode generator RNG behavior; This is a focused preview, not a full modern world generator.
- **Trial Chamber Generation** — Previews or simulates trial chamber generation RNG behavior; This is a focused preview, not a full modern world generator.
- **Structure Placement Preview** — Previews or simulates structure placement preview RNG behavior; This is a focused preview, not a full modern world generator.

### Villagers (24 tools)

#### Trades (7)

- **Trade Browser** — Browses, searches, compares, or summarizes loaded villager trade data for trade browser.
- **Trade Search** — Browses, searches, compares, or summarizes loaded villager trade data for trade search.
- **Trade Comparison** — Browses, searches, compares, or summarizes loaded villager trade data for trade comparison.
- **Emerald Calculator** — Browses, searches, compares, or summarizes loaded villager trade data for emerald calculator.
- **Trade Cycle Calculator** — Browses, searches, compares, or summarizes loaded villager trade data for trade cycle calculator.
- **Librarian Browser** — Browses, searches, compares, or summarizes loaded villager trade data for librarian browser.
- **Refresh Trades From Installed Version** — Browses, searches, compares, or summarizes loaded villager trade data for refresh trades from installed version.

#### Professions (13)

- **Armorer** — Browses loaded trade definitions for the Armorer villager profession and shows version/source metadata.
- **Butcher** — Browses loaded trade definitions for the Butcher villager profession and shows version/source metadata.
- **Cartographer** — Browses loaded trade definitions for the Cartographer villager profession and shows version/source metadata.
- **Cleric** — Browses loaded trade definitions for the Cleric villager profession and shows version/source metadata.
- **Farmer** — Browses loaded trade definitions for the Farmer villager profession and shows version/source metadata.
- **Fisherman** — Browses loaded trade definitions for the Fisherman villager profession and shows version/source metadata.
- **Fletcher** — Browses loaded trade definitions for the Fletcher villager profession and shows version/source metadata.
- **Leatherworker** — Browses loaded trade definitions for the Leatherworker villager profession and shows version/source metadata.
- **Librarian** — Browses loaded trade definitions for the Librarian villager profession and shows version/source metadata.
- **Mason** — Browses loaded trade definitions for the Mason villager profession and shows version/source metadata.
- **Shepherd** — Browses loaded trade definitions for the Shepherd villager profession and shows version/source metadata.
- **Toolsmith** — Browses loaded trade definitions for the Toolsmith villager profession and shows version/source metadata.
- **Weaponsmith** — Browses loaded trade definitions for the Weaponsmith villager profession and shows version/source metadata.

#### Helpers (4)

- **Zombie Cure Calculator** — Calculates villager-management values for zombie cure calculator.
- **Villager Hall Calculator** — Calculates villager-management values for villager hall calculator.
- **Workstation Count** — Calculates villager-management values for workstation count.
- **Breeding Food Calculator** — Calculates villager-management values for breeding food calculator.

### Guided Setups (12 tools)

#### Mining (3)

- **Branch Mine Setup** — Provides a guided planning preset for branch mine setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.
- **Quarry Setup** — Provides a guided planning preset for quarry setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.
- **Perimeter Setup** — Provides a guided planning preset for perimeter setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.

#### Farming (3)

- **Crop Farm Setup** — Provides a guided planning preset for crop farm setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.
- **Tree Farm Setup** — Provides a guided planning preset for tree farm setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.
- **Villager Hall Setup** — Provides a guided planning preset for villager hall setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.

#### Portals (3)

- **Nether Highway Setup** — Provides a guided planning preset for nether highway setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.
- **Portal Network Setup** — Provides a guided planning preset for portal network setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.
- **Asymmetric Portal Setup** — Provides a guided planning preset for asymmetric portal setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.

#### Building (3)

- **Build Material Setup** — Provides a guided planning preset for build material setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.
- **Lighting Grid Setup** — Provides a guided planning preset for lighting grid setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.
- **Beacon Network Setup** — Provides a guided planning preset for beacon network setup, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.

### Utilities (13 tools)

#### Version & Components (6)

- **Minecraft Version Target** — Changes the Minecraft version used by version-aware calculations and compatibility checks.
- **Compatibility Report** — Summarizes the selected Minecraft version and availability of Cubiomes, Nether Bedrock Cracker, and seed-policy components.
- **Installed Version Scan** — Scans standard Minecraft Java installation locations and lists local version folders F3+ can recognize.
- **Trade Data Status** — Reports which villager trade data source/version is loaded and how many definitions are available.
- **Cubiomes Setup & Status** — Checks the bundled Cubiomes source and, when requested, builds its local shared library.
- **Nether Bedrock Cracker Status** — Reports whether the bundled cracker source and cached platform executable are available.

#### Profiles (2)

- **Export Profiles** — Writes F3+ settings to a portable JSON profile for backup or transfer to another installation.
- **Import Profiles** — Loads a previously exported F3+ JSON profile and applies its compatible settings.

#### Controls (5)

- **Input & Hotkey Bindings** — Shows the active F3+ movement, safety, and capture bindings so you can verify them before running automation.
- **Turn Calibration** — Calculates or records the mouse-turn calibration used by macros that need repeatable camera rotation.
- **Movement Calibration** — Measures or configures the timing assumptions used by coordinate-aware movement routines.
- **Coordinate Capture Settings** — Shows the delay and capture behavior used when F3+ reads F3+C coordinates from Minecraft.
- **Back Up F3+ Settings** — Creates a backup copy of the current F3+ configuration before you make larger changes.

### Safety (10 tools)

#### Controls (10)

- **Emergency Stop** — Immediately stops the active macro and releases tracked keyboard and mouse inputs.
- **Pause / Resume Automation** — Pauses or resumes the active automation routine without discarding it.
- **Release Held Inputs** — Immediately releases all keyboard keys and mouse buttons currently held by F3+.
- **Focus Loss Stop** — Controls whether supported foreground automation stops when F3+ detects that Minecraft no longer has the required focus.
- **Restore Hotbar** — Returns automation to the configured safe/default hotbar state after a workflow changes slots.
- **Automation Runtime Limit** — Limits how long an automation routine may continue before F3+ stops it.
- **Automation Start Countdown** — Adds a countdown before automation begins so you have time to return to Minecraft.
- **Automation Action Counter** — Tracks or limits repeated macro actions so an unattended routine cannot run indefinitely.
- **Movement Stuck Detection** — Checks whether coordinate-aware movement has stopped making expected progress and flags the routine as stuck.
- **Automatic Recovery Limit** — Sets how many automatic recovery attempts a supported routine may make before it stops.

## File guide

- `README.md` — install, startup, and usage overview.
- `FEATURES.md` — this concise tool guide.
- `COMMUNITY_CREDITS.md` — project lineage, technical influences, and community attribution.
- `THIRD_PARTY.md` — redistributed/integrated third-party components and licensing boundaries.
- `LICENSE.md` — project license.

