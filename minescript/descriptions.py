from __future__ import annotations

"""Human-facing feature descriptions shared by the GUI and FEATURES.md."""

SPECIAL = {
    'Enchantment RNG Seed Cracker': 'Recovers Minecraft enchantment/player RNG state through Earthcomputer EnchantmentCracker v1.9. F3+ downloads and SHA-256 verifies the upstream tool on first use; this workflow never recovers the world seed.',
    'Java LCG State Recovery - 2 nextInt': 'Recovers the 48-bit internal state of a java.util.Random-compatible RNG from two consecutive unbounded nextInt() observations, then predicts the next output.',
    'Java LCG State Recovery - nextLong': 'Recovers the 48-bit internal state of a java.util.Random-compatible RNG from one observed nextLong() value by reversing the two consecutive 32-bit outputs that formed it.',
    'Java LCG State Inspector': 'Advances or rewinds a recovered 48-bit java.util.Random internal state and predicts subsequent nextInt() outputs.',
    'Nether Bedrock Cracker': 'Recovers a Java Edition world seed from observed Nether bedrock positions through the bundled/upstream Nether Bedrock Cracker workflow; this is F3+\'s only world-seed recovery route.',
    'Cubiomes Status': 'Reports whether the bundled Cubiomes source and its compiled local library are available.',
    'Cubiomes Biome Query': 'Queries the bundled Cubiomes generator for the biome at a known-seed coordinate on Minecraft versions supported by that Cubiomes revision.',
    'Current Biome': 'Reports the biome for the requested known-seed/world location when a supported biome-generation backend is available.',
    'Capture Position': 'Captures the player coordinates from Minecraft using the configured coordinate-capture method.',
    'Copy Sister Coordinates': 'Converts the current Overworld/Nether position to its 8:1 sister coordinates and copies the result.',
    'Save Sister Waypoint': 'Converts the current Overworld/Nether position to sister coordinates and stores them as a waypoint.',
    'Create Waypoint': 'Creates and saves a named waypoint from entered or captured coordinates.',
    'Rename Waypoint': 'Renames a saved waypoint without changing its coordinates.',
    'Delete Waypoint': 'Removes a saved waypoint.',
    'Nearest Waypoint': 'Ranks saved waypoints from the current position and returns the nearest destination.',
    'Waypoint Route': 'Builds a greedy travel route through saved waypoints from the current position.',
    'Sort Waypoints by Distance': 'Sorts saved waypoints by travel distance from the current position.',
    'Minecraft Version': 'Changes the Minecraft version used by version-aware calculations and compatibility checks.',
    'Compatibility Report': 'Summarizes the selected Minecraft version and availability of Cubiomes, Nether Bedrock Cracker, and seed-policy components.',
    'Installed Version Scan': 'Scans common Minecraft installation folders and lists locally installed Java Edition versions.',
    'Trade Data Status': 'Reports the source version and number of villager trade definitions currently loaded.',
    'Cubiomes Setup & Status': 'Checks the bundled Cubiomes source and, when requested, builds its local shared library.',
    'Nether Bedrock Cracker Status': 'Reports whether the bundled cracker source and cached platform executable are available.',
    'Export Profiles': 'Exports F3+ settings/profile data in JSON form for backup or transfer.',
    'Import Profiles': 'Imports previously exported F3+ settings/profile data.',
    'Emergency Stop': 'Immediately stops the active macro and releases tracked keyboard and mouse inputs.',
    'Pause/Resume': 'Pauses or resumes the active automation routine without discarding it.',
    'Release Held Inputs': 'Immediately releases all keyboard keys and mouse buttons currently held by F3+.',
    'Focus Loss Stop': 'Configures the safety behavior intended to stop automation when focus is lost where the platform supports it.',
    'Auto Fishing': 'Runs an automatic fishing interaction cycle with configurable timing through the macro engine.',
    'Livestock Breeder': 'Continuously holds feed and performs the configured breeding interaction cycle for livestock.',
    'Coordinate Travel': 'Moves toward a coordinate target using captured-position feedback and the configured movement input backend.',
    'Waypoint Travel': 'Moves toward a saved waypoint using captured-position feedback.',
    'Nether-Assisted Travel': 'Uses coordinate-target travel with Overworld/Nether scaling to support long-distance routing.',
    'Control Bindings': 'Shows the active F3+ movement, safety, and capture bindings so you can verify them before running automation.',
    'Turn Calibration': 'Calculates or records the mouse-turn calibration used by macros that need repeatable camera rotation.',
    'Movement Calibration': 'Measures or configures the timing assumptions used by coordinate-aware movement routines.',
    'Coordinate Capture Settings': 'Shows the delay and capture behavior used when F3+ reads F3+C coordinates from Minecraft.',
    'Backup Settings': 'Creates a backup copy of the current F3+ configuration before you make larger changes.',
    'Restore Hotbar': 'Returns automation to the configured safe/default hotbar state after a workflow changes slots.',
    'Runtime Limit': 'Limits how long an automation routine may continue before F3+ stops it.',
    'Delayed Start': 'Adds a countdown before automation begins so you have time to return to Minecraft.',
    'Action Counter': 'Tracks or limits repeated macro actions so an unattended routine cannot run indefinitely.',
    'Stuck Detection': 'Checks whether coordinate-aware movement has stopped making expected progress and flags the routine as stuck.',
    'Recovery Attempts': 'Sets how many automatic recovery attempts a supported routine may make before it stops.',
    'Focus Loss Stop': 'Controls whether supported foreground automation stops when F3+ detects that Minecraft no longer has the required focus.',
    'Installed Version Scan': 'Scans standard Minecraft Java installation locations and lists local version folders F3+ can recognize.',
    'Trade Data Status': 'Reports which villager trade data source/version is loaded and how many definitions are available.',
    'Export Profiles': 'Writes F3+ settings to a portable JSON profile for backup or transfer to another installation.',
    'Import Profiles': 'Loads a previously exported F3+ JSON profile and applies its compatible settings.',
    'Nether Biome Finder': 'Samples the Nether around the entered seed/chunk center with the bundled supported Cubiomes backend and reports biome-ID composition plus representative sampled chunks.',
    'Fortress Finder': 'Returns nearby Nether Fortress placement-candidate chunks for the entered known world seed and search radius. Final generation still depends on supported version rules and viability checks.',
    'Bastion Finder': 'Returns nearby Bastion Remnant placement-candidate chunks for the entered known world seed and search radius. Final generation still depends on supported version rules and viability checks.',
    'Fortress+Bastion Finder': 'Returns both Nether Fortress and Bastion Remnant placement-candidate chunks around the same known-seed search center so their proximity can be compared.',
    'Nether Structure Density': 'Counts Nether Fortress and Bastion placement candidates in the entered chunk radius and reports total candidates plus candidates per 1,000 sampled chunks.',
    'Sister Portal': 'Converts an Overworld position to its ideal Nether X/Z sister position using the 8:1 horizontal scale while preserving the entered Y as a reference.',
    'Standard Link Calculator': 'Compares the ideal scaled Nether exit with another candidate portal and ranks which exit is geometrically closer to the Overworld portal target.',
    'Portal Conflict Analysis': 'Shows which candidate exit an Overworld portal would select and how close the competing exit is, exposing links likely to steal or redirect a portal connection.',
    'Optimal Portal Placement': 'Chooses the better of the entered candidate Nether portals for the Overworld entry and reports its routing distance and margin over the alternative.',
    'Portal Network': 'Builds an entry-to-exit link summary for the entered Overworld portal, its ideal Nether counterpart, and a competing Nether portal, including detected link cycles.',
    'Highway Planner': 'Estimates Nether-highway travel measurements for the entered Overworld distance so a long trip can be laid out at Nether scale.',
    'Portal Separation': 'Measures the 3D separation between the ideal scaled Nether exit and another candidate exit so you can judge how strongly they compete for the same link.',
    'Portal Coverage': 'Calculates the diameter and horizontal area represented by the entered portal-planning radius.',
    'Multi-Portal Jump': 'Converts two Overworld endpoints to Nether coordinates and reports the Nether leg between them, showing the distance saved by a two-portal shortcut.',
    'Asymmetric Portal Router': 'Generates a candidate chain of alternating low/high Nether portal pairs and evaluates the resulting links. It is intended for asymmetric or one-way portal-link layouts where the return portal can resolve differently from the arrival portal.',
    'Vertical Isolation Analyzer': 'Examines Y separation between same-dimension portals in a generated asymmetric layout so vertically separated candidates can be checked before relying on them for link isolation.',
    'Reliability Margin': 'Reports each generated portal link and its margin over the next-best candidate; larger margins mean the selected exit is less likely to be displaced by a nearby competing portal.',
    'Bidirectional Link Matrix': 'Lists the selected exit, routing distance, and competing-link margin for every portal in the generated Overworld/Nether test layout.',
    'Portal Graph': 'Summarizes the directed portal-link network produced by the generated test layout, including portal counts, selected exits, and any routing cycles.',
    'Loop Detector': 'Finds cycles in the directed portal-link graph, such as entering through one portal and returning through a different chain instead of the intended pair.',
    'Travel Compression': 'Compares effective Overworld distance gained with the physical Nether and Overworld walking required, reporting travel gained per walked block and reduction versus a conventional Nether route.',
    'Bedrock Pattern Helper': 'Hands world-seed recovery off to the permitted Nether Bedrock Cracker workflow; F3+ does not provide a second independent bedrock seed-cracking implementation.',
    'Asymmetric Jump Designer': 'Provides the inputs and planning context for an asymmetric portal-jump layout; use the dedicated asymmetric link analysis tools to validate actual entry-to-exit routing before building.',
    'Maximum Displacement': 'Provides portal-network planning values for testing how far a candidate exit can be displaced from its scaled target; validate the final link with the reliability/link-matrix tools.',
    'Repeating Network Generator': 'Provides planning parameters for repeating portal-network layouts. Use the generated link matrix/graph tools to verify each repeated stage before construction.',
    'Destination Gate Planner': 'Provides planning values for a destination-gated portal network where only selected exits should remain active for a destination.',
    'Portal-State Simulator': 'Provides planning values for evaluating how enabling or disabling candidate portals can change the selected entry-to-exit link.',
    'Routing Table Generator': 'Provides portal-network planning values intended to be turned into an entry-to-exit routing table; pair it with the link-matrix result for concrete link selection.',
    'Corridor Transport': 'Provides planning values for comparing portal-assisted travel with a conventional Nether corridor route.',
    'Standard Route Comparison': 'Provides planning values for comparing conventional paired portals against asymmetric portal-routing layouts.',
    'Multi-Destination Optimizer': 'Provides planning values for a portal network serving several destinations; final link choices must be checked with the link matrix rather than assumed from the title.',
    'Portal Reliability Heatmap': 'Provides portal-network planning values intended for comparing link stability over an area; reliability is represented by routing margin between the best and next-best exits.',
    'Portal Radius Visualizer': 'Provides portal-network planning values for visualizing candidate search/separation radius around a portal target.',
    'Portal Cost Optimizer': 'Provides planning values for comparing portal-network travel cost; it does not alter Minecraft portal mechanics or guarantee an automatically optimal build.',
    'Macro Recorder': 'Defines the recording/template workflow for capturing a repeatable action sequence and turning it into a reusable F3+ automation plan.',
    'Macro Template': 'Shows the reusable action-template format used to assemble taps, waits, held inputs, turns, and repeated steps before running them as automation.',
}

# Tool-specific explanations for frequently used calculators and ambiguous labels.
# These describe the actual implementation instead of repeating the menu name.
PRECISE = {
    'Distance Calculator': 'Measures the straight-line 3D distance and the horizontal X/Z distance between two Minecraft positions.',
    'Bearing Calculator': 'Calculates Minecraft yaw from one X/Z position to another. The result follows Minecraft orientation: 0° south, -90° east, 90° west, and ±180° north.',
    'Midpoint Calculator': 'Finds the exact X/Y/Z point halfway between two entered positions.',
    'Travel Time Calculator': 'Estimates travel time by dividing the entered distance by movement speed in blocks per second.',
    'Nether Conversion Calculator': 'Converts X/Z coordinates between Overworld and Nether space using the standard 8:1 horizontal scale.',
    'Coordinate Snap': 'Rounds a position to a whole block and reports the center of the chunk containing that position.',
    'Delta XYZ Calculator': 'Reports the signed X, Y, and Z displacement from the first coordinate to the second.',
    'Distance': 'Measures horizontal and full 3D distance between two Minecraft positions.',
    'Bearing': 'Reports Minecraft yaw and cardinal direction from one position to another on the X/Z plane.',
    'Midpoint': 'Finds the X/Y/Z position halfway between two coordinates.',
    'Delta XYZ': 'Reports signed coordinate change from the first position to the second.',
    'Axis Distance': 'Reports the absolute X, Y, and Z separation between two positions so you can see which axis dominates the trip or build.',
    'Chunk': 'Converts a block X/Z position into its Java Edition chunk coordinates and block bounds.',
    'Region': 'Converts a block position into its Anvil region and reports the region chunk/block bounds.',
    'Chunk Center': 'Returns the center block coordinate of the chunk containing the entered position.',
    'Chunk Border': 'Reports the containing chunk and the nearest chunk-line coordinates around the entered block position.',
    'Chunk Corner': 'Returns all four X/Z block corners of the chunk containing the entered position.',
    'Region Border': 'Returns the 32×32-chunk Anvil region bounds containing the entered position.',
    'Cardinal Snap': 'Maps an arbitrary Minecraft yaw to the nearest cardinal facing and its exact snapped yaw.',
    'OW/Nether Conversion': 'Converts X/Z coordinates between Overworld and Nether travel space using the 8:1 horizontal scale.',
    'Tick Converter': 'Converts game ticks into seconds, minutes, and hours using Minecraft’s 20 game ticks per second.',
    'Hopper Timer': 'Estimates hopper-transfer timer duration from item count using one transfer every 8 game ticks while the hopper can transfer normally.',
    'Comparator Strength': 'Calculates comparator output strength from how full a container is relative to its slot and stack capacity.',
    'Repeater Delay': 'Adds the selected repeater settings and returns total redstone ticks, game ticks, and seconds.',
    'Observer Delay': 'Uses the entered timing values to plan the combined game/redstone delay for an observer-driven timing chain.',
    'Minecart Timing': 'Estimates rail travel time from distance using the planner’s assumed 8 blocks/second minecart speed.',
    'Water Stream Timing': 'Estimates item/water-stream travel time from distance using a planning speed; real layouts can change the result.',
    'Ice Boat Timing': 'Estimates boat travel time from distance and the speed value you provide.',
    'Crafter Throughput': 'Converts a crafter cycle time and items per cycle into estimated items per hour.',
    'Pulse Extender': 'Calculates the combined delay of the entered repeater-style timing values for a pulse-extension plan.',
    'Clock Period': 'Calculates the total repeater-chain period represented by the entered timing settings.',
    'Counter Timing': 'Calculates the total repeater-chain timing used by a counter or pulse-counting design.',
    'Signal Timing': 'Calculates total signal delay through the entered repeater-style timing values.',
    'Storage Capacity': 'Breaks an item count into full stacks, remainder, shulker boxes, and double chests for the selected stack size.',
    'Bulk Materials': 'Summarizes how a bulk item target fits into stacks, shulker boxes, and double chests.',
    'Item Compression': 'Calculates how many compressed items/blocks can be made from the entered item count and what remains.',
    'Material Logistics': 'Combines player inventory and carried shulker capacity to estimate how many trips a material haul requires.',
    'Transport Trips': 'Calculates carried capacity and trip count for moving an item total with the selected number of shulker boxes.',
    'Shulker Requirement': 'Calculates how many shulker boxes are required for the entered item count and stack size.',
    'Chest Requirement': 'Calculates how many double chests are required for the entered item count and stack size.',
    'Area': 'Calculates width × length for a rectangular build footprint and also reports the related dimensions.',
    'Volume': 'Calculates width × length × height for a rectangular build volume.',
    'Surface Area': 'Calculates the total exterior surface area of a rectangular prism from width, length, and height.',
    'Perimeter': 'Calculates the perimeter around a rectangular width/length footprint.',
    'Block Count': 'Treats the entered dimensions as a filled rectangular prism and reports the required block count.',
    'Stacks': 'Converts the filled build volume into storage units so you can prepare stacks before building.',
    'Shulkers': 'Converts the filled build volume into the number of shulker boxes required.',
    'Double Chests': 'Converts the filled build volume into the number of double chests required.',
    'Foundation Planner': 'Calculates the rectangular foundation footprint and supporting dimension totals from width and length.',
    'Stair Calculator': 'Calculates a stair run from target height and step spacing so you can check horizontal run before building.',
    'Spiral Staircase Planner': 'Generates block coordinates for a spiral staircase from diameter, height, and steps per turn.',
    'Catenary Calculator': 'Generates a block-sampled hanging cable/chain curve from span, sag, and endpoint height difference.',
    'Roof Pitch': 'Calculates rise/run, pitch ratio, and approximate roof layers from the entered build dimensions.',
    'Wall Segments': 'Calculates perimeter length and the number of repeated wall segments at the selected spacing.',
    'Bridge Span': 'Calculates bridge length plus support positions/count from the chosen support spacing.',
    'Lighting Grid': 'Generates evenly spaced light positions across a rectangular floor, including the far edges when spacing does not divide evenly.',
    'Pillar Spacing': 'Calculates how many structural supports are needed along both build axes at the selected spacing.',
    'Road Planner': 'Calculates road block area and repeated marker/support positions from width, length, and spacing.',
    'Gradient Ratio': 'Calculates rise/run ratio and percent grade for a slope from vertical rise and horizontal run.',
    'Chunk Grid Builder': 'Calculates how many 16×16 chunks a rectangular build spans in X and Z.',
    'Circle': 'Generates the discrete block coordinates for a hollow circular outline at the selected radius.',
    'Filled Circle': 'Generates every block coordinate inside a filled circle at the selected radius.',
    'Sphere': 'Generates a 3D block-coordinate shell approximating a sphere at the selected radius.',
    'Hollow Sphere': 'Generates a one-block-thick spherical shell rather than a filled solid.',
    'Dome': 'Generates the upper half of a spherical block shell for dome construction.',
    'Cylinder': 'Extrudes a circular block outline vertically for the selected height.',
    'Cone': 'Generates decreasing circular layers to approximate a Minecraft cone.',
    'Helix': 'Generates a rising spiral block path around a selected radius and height.',
    'Double Helix': 'Generates two opposing rising spiral block paths around the same axis.',
    'Mob Cap Calculator': 'Estimates the natural-spawn category cap from eligible chunks and the category base cap, with a simple multi-player upper-bound reference.',
    'Despawn Radius Planner': 'Reports the soft/hard despawn radii and the hard-despawn square bounds around the entered player position.',
    'Item Sorter Planner': 'Estimates module count, reserved filter items, hopper slots, and distinct sorted items for a conventional sorter layout.',
    'Chunk Alignment': 'Reports exact 16×16 chunk block bounds around the entered X/Z position.',
    'Region Alignment': 'Reports exact 32×32-chunk Anvil-region bounds around the entered X/Z position.',
    'Simulation Distance': 'Calculates the square chunk area and block width covered by the selected simulation-distance radius.',
    'Render Distance': 'Calculates the square chunk area and block width represented by the selected render-distance radius.',
    'Spawn Sphere': 'Calculates radius, diameter, and geometric volume for the selected spawning sphere.',
    'Random Tick Area': 'Calculates the square chunk/block area affected by the selected simulation-distance radius for random-tick planning.',
    'Mending Repair Calculator': 'Uses Mending’s 2 durability per absorbed XP point conversion to estimate maximum repair and average repair across eligible items.',
    'Anvil Prior-Work Planner': 'Shows the 0, 1, 3, 7… prior-work penalty progression so you can plan a balanced anvil combination tree.',
    'Tool Wear': 'Estimates expected durability consumption from action count and Unbreaking level, plus a conservative worst-case count.',
    'XP Level Calculator': 'Converts Minecraft experience levels into cumulative XP points using the piecewise vanilla level formulas.',
    'Eye Throw Triangulation': 'Intersects two Minecraft-yaw eye-throw rays to estimate a stronghold direction/position when the throws are not parallel.',
    'Stronghold Ring': 'Returns the planning radius range and stronghold count for the selected modern stronghold ring index.',
}

MACRO_DESC = {
    'Generator Miner': 'Holds mining input continuously for generator-style block breaking while preserving emergency-stop input release.',
    'Hold Attack': 'Holds the attack button until stopped.',
    'Hold Use': 'Holds the use/place button until stopped.',
    'Concrete Converter': 'Holds attack and use together for stationary concrete-conversion workflows.',
    'Auto Walk': 'Holds forward movement until stopped.',
    'Custom Hold': 'Runs the configurable continuous held-input macro template.',
    'Auto Attack': 'Performs repeated attack actions at a fixed interval.',
    'AFK Mob Grinder': 'Performs repeated attack/use interaction for stationary mob-grinder operation.',
    'Custom Periodic Action': 'Runs the configurable periodic interaction macro template.',
    'Basic Travel': 'Holds forward movement for continuous travel.',
    'Sprint Travel': 'Holds forward and sprint for continuous travel.',
    'Sprint-Jump Travel': 'Combines forward movement, sprinting, and repeated jumping.',
    'Swim Travel': 'Holds forward, sprint, and swim/jump input for continuous swimming.',
    'Boat Travel': 'Maintains forward vehicle input for boat travel.',
    'Horse/Camel Travel': 'Maintains forward mount movement until stopped.',
    'Elytra Launch': 'Performs the configured elytra launch input sequence.',
    'Elytra Cruise': 'Maintains the elytra cruise input sequence for a configured duration.',
    'Riptide Travel': 'Cycles use/charge timing for repeated Riptide propulsion.',
    'Spear Dash Travel': 'Runs the configured multi-slot spear/dash travel sequence.',
    'Tunnel Miner': 'Combines forward travel and mining input for continuous tunnel excavation.',
    'Branch Miner': 'Runs a coordinate-aware branch-mining pattern with turns and branch spacing.',
    'Stair Excavator': 'Runs a coordinate-aware staircase excavation pattern.',
    'Area Excavator': 'Runs a coordinate-aware multi-row excavation pattern.',
    'Crop Farmer': 'Moves and interacts through a repeating crop-harvest/replant cycle.',
    'Coordinate Row Farmer': 'Farms a row while using coordinate feedback to control row length and turns.',
    'Multi-Row Farmer': 'Runs repeated coordinate-aware farming rows with turns between rows.',
    'Bone Meal Farmer': 'Cycles use/harvest inputs for bone-meal-driven farming.',
    'Stationary Grow/Harvest': 'Repeats stationary growth and harvest interactions.',
    'Tree Farm Cycle': 'Runs the configured stationary tree-farm interaction cycle.',
    'Farm Station Controller': 'Runs the reusable farm-station interaction sequence.',
    'Mending Grinder': 'Cycles combat/tool slots for an XP-based mending workflow.',
    'Crossbow Volley': 'Cycles configured hotbar slots while charging and firing crossbows.',
    'Hotbar Workflow': 'Executes a repeated sequence across selected hotbar slots.',
    'Tool Rotation': 'Rotates through selected hotbar tools on a configured cadence.',
    'Durability Guard': 'Runs held mining input with a bounded cycle guard to reduce unattended overrun.',
    'Resource Guard': 'Runs held use input with a bounded cycle guard to reduce unattended resource consumption.',
    'Food Manager': 'Periodically selects and uses the configured food slot during automation.',
    'Offhand Workflow': 'Periodically performs the configured offhand-swap workflow.',
    'Line': 'Places blocks while moving through a repeating straight-line construction pattern.',
    'Rectangle': 'Executes four placement/movement sides with quarter turns to build a rectangle perimeter.',
    'Filled Rectangle': 'Repeats rows and turns to fill a rectangular construction area.',
    'Grid': 'Builds a repeating row-and-turn placement grid.',
    'Rows': 'Builds repeated parallel placement rows.',
    'Alternating Pattern': 'Runs the reusable alternating row construction sequence.',
    'Perimeter': 'Runs a four-sided placement sequence around a perimeter.',
    'Repeating Segment': 'Repeats a short placement/movement construction segment.',
    'Action Sequencer': 'Runs a reusable ordered sequence of taps, waits, holds, turns, and other macro actions.',
    'Route Runner': 'Executes a repeating movement-and-turn route sequence.',
}


def describe(spec) -> str:
    name, top, sub = spec.name, spec.top, spec.submenu
    if name in SPECIAL:
        return SPECIAL[name]
    if name in PRECISE and not (top=='Gameplay' and name=='Perimeter'):
        return PRECISE[name]
    if top == 'Gameplay':
        if name in MACRO_DESC:
            return MACRO_DESC[name]
        if name.endswith('Wizard'):
            return f'Opens or calculates the {name[:-7].lower()} planning workflow used to configure a related gameplay routine.'
        if 'Planner' in name or 'Optimizer' in name:
            return f'Calculates planning values for {name.lower()} rather than directly controlling Minecraft.'
        return f'Runs the {name.lower()} gameplay automation or configuration workflow through F3+\'s input/macro engine.'
    if top == 'Navigation':
        if sub == 'Coordinates':
            return f'Calculates {name.lower()} from entered Minecraft coordinates without modifying the world.'
        if sub == 'Routes':
            return f'Builds or analyzes a route using {name.lower()} logic and supplied/saved positions.'
        if sub == 'Portal Helpers':
            return f'Calculates or analyzes Nether portal routing using Java Edition coordinate scaling and portal-placement geometry for {name.lower()}.'
        if sub == 'Position':
            return f'Uses captured player position data to provide {name.lower()} behavior.'
        if sub == 'Waypoints':
            return f'Manages or analyzes saved waypoint data for {name.lower()}.'
    if top == 'Seed Tools':
        if sub == 'Slime':
            return f'Uses the Java Edition slime-chunk formula with a known world seed to calculate {name.lower()}.'
        if sub == 'Nether':
            if 'Biome' in name or 'Fortress' in name or 'Bastion' in name or 'Structure' in name:
                return f'Searches or evaluates known-seed Nether generation for {name.lower()}, using supported generation rules/backends and clearly separating placement candidates from final terrain viability.'
            return f'Analyzes Nether travel or portal geometry for {name.lower()} using deterministic coordinate math.'
        if sub == 'Structures':
            if name in {'Village','Trial Chamber','Ancient City','Woodland Mansion','Ocean Monument','Desert Pyramid','Jungle Temple','Swamp Hut','Igloo','Pillager Outpost','Ruined Portal','Shipwreck','Ocean Ruin','Buried Treasure','Mineshaft','Nether Fortress','Bastion','End City','Stronghold'}:
                return f'Finds known-seed {name.lower()} placement-attempt chunks using the active supported structure-generation rules; final generation can still depend on biome, terrain, and version checks.'
            if name == 'Structure Finder':
                return 'Returns nearby placement-candidate sets for Village, Trial Chamber, Ocean Monument, and Pillager Outpost around the entered seed/chunk center.'
            return f'Returns candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as planning data for {name.lower()}. It does not claim a specialized {name.lower()} solver when the current backend only supplies those candidate counts.'
        if sub == 'Spawners':
            return f'Inspects generated Java Edition Anvil/NBT world-save data to locate or rank {name.lower()} rather than pretending all spawners are seed-predictable.'
        if sub == 'Biomes':
            return f'Samples biome IDs on a grid around the entered seed/X/Z center and reports sample coordinates plus biome counts for the {name.lower()} view. Terrain-shape labels do not imply heightmap analysis unless a dedicated backend is present.'
        if sub == 'Local Area':
            return f'Reports the selected center/radius, sampled-chunk count, and local slime-chunk count as the current data behind the {name.lower()} view.'
        if sub == 'World Analysis':
            return f'Reports nearby placement-candidate counts for Village, Trial Chamber, Ocean Monument, and Pillager Outpost as the current seed-analysis data behind {name.lower()}; it does not fabricate a numeric score that is not actually calculated.'
    if top == 'Calculators':
        if sub == 'Shapes':
            return f'Generates block-coordinate/layer measurements for a Minecraft {name.lower()} shape.'
        if sub == 'Redstone':
            return f'Converts or estimates timing/throughput values for the {name.lower()} redstone mechanic.'
        if sub == 'Storage':
            return f'Calculates storage/logistics requirements for {name.lower()} from item and stack counts.'
        if sub == 'Farm':
            return f'Runs the concrete farm-planning calculation labeled {name.lower()} and returns its implemented population, throughput, resource, layout, spacing, or coverage fields rather than a generic farm score.'
        if sub == 'Technical':
            return f'Runs the concrete technical calculation labeled {name.lower()} and reports the implemented coordinates, bounds, radius, spacing, timing, or capacity fields used by that mechanic.'
        if sub == 'Speedrunning':
            return f'Calculates speedrunning route/triangulation values for {name.lower()}; probabilistic mechanics remain estimates where appropriate.'
        if sub == 'Resource Usage':
            return f'Estimates consumption, durability, XP, or material requirements for {name.lower()}.'
        if sub == 'End':
            return f'Calculates End-dimension routing or coordinate values for {name.lower()}.'
        if sub == 'Build':
            return f'Calculates Minecraft build measurements/material planning for {name.lower()}.'
        if sub == 'Coordinate':
            return f'Calculates the coordinate/travel value represented by {name.lower()} from the entered Minecraft positions.'
    if top == 'RNG Tools':
        if sub == 'Enchanting':
            return f'Runs the implemented enchanting calculation for {name.lower()}: probability/cost helpers use direct formulas, while simulator-style entries return deterministic sample rolls from the entered gameplay RNG seed. This is not world-seed RNG.'
        if sub == 'Drops':
            return f'Simulates repeated drop rolls for {name.lower()} from the supplied probability/RNG inputs.'
        if sub == 'Probability':
            return f'Uses the entered probability/attempt count or deterministic Java-RNG-style sequence helper for {name.lower()}, returning explicit odds or sample sequence data without treating the RNG seed as a world seed.'
        if sub == 'Loot':
            return f'Runs repeated seeded Bernoulli-style sample rolls for {name.lower()} and reports success indices/count/rate. It is a probability simulator, not Mojang\'s complete current-version loot-table engine.'
        if sub == 'Generation RNG':
            return f'Previews or simulates {name.lower()} RNG behavior; F3+ does not claim this is a complete 26.x terrain/block-state generator.'
    if top == 'Villager Explorer':
        if sub == 'Professions':
            return f'Browses loaded trade definitions for the {name} villager profession and shows version/source metadata.'
        if sub == 'Trades':
            return f'Browses, searches, compares, or summarizes loaded villager trade data for {name.lower()}.'
        return f'Calculates villager-management values for {name.lower()}.'
    if top == 'Wizards':
        return f'Provides a guided planning preset for {name.lower()}, returning the measurements/settings needed before running the related build, farm, mining, or portal workflow.'
    if top == 'Utilities':
        return f'Provides the {name.lower()} application utility or settings control.'
    if top == 'Safety':
        return f'Configures or reports the {name.lower()} automation safety control.'
    return f'Runs the {name} F3+ tool.'
