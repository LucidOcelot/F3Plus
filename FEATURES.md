# F3+ Workbench Guide

F3+ is a local technical Minecraft Java Edition workstation for calculations, navigation, world inspection, build planning, simulation, villager planning, and bounded automation.

The desktop is organized by what the player is trying to accomplish. The sidebar, menu bar, search field, and `Ctrl+K` command palette all use the same task structure.

## Desktop navigation

### Home

Home surfaces favorites, recent workbenches, and common starting points. Global search matches task names, workbench names, mechanics, and individual operations.

### Play & Travel

Contains automation, live position tools, coordinate calculations, routes, waypoints, surveys, and portal planning.

### Explore Worlds

Contains structure, biome, Nether, slime, spawner, ore, cave, local-area, and broader world analysis together with world/save profiles.

### Plan & Build

Contains block layouts, geometric shapes, redstone timing, storage/logistics, farms, technical layouts, resources, recipes, and material planning.

### Mechanics & Trading

Contains enchanting, anvil planning, gameplay RNG, loot simulation, generation mechanics, brewing, dye/cauldron behavior, breeding statistics, and villager planning.

### App & Safety

Contains Minecraft/data status, controls and calibration, automation safety, result history, export, and diagnostics.

## Workbench interaction

Workbenches with many operations use a searchable, collapsible tree instead of mixing category labels into a flat selectable list. Typing filters the tree; pressing Enter selects the first matching operation; activating an operation moves focus toward its inputs.

Small configuration dialogs size around their controls rather than opening as large empty windows.

Input copy is split into two layers:

- the visible label and short hint identify what the value controls and its unit or format;
- the tooltip provides additional behavior, accepted values, defaults, and practical consequences of changing it.

Long tooltips wrap to a readable width. Accessibility descriptions retain the same detailed meaning as plain text.

## Automation

### Automation Studio

Automation Studio groups routines into:

- Repeated Actions;
- Travel;
- Mining;
- Farming;
- Building;
- Equipment;
- Macros & Setup.

Each routine description states the action it performs. Configuration dialogs use mechanic-specific labels such as **Attack every**, **Switch item every**, and **Mending slots** rather than exposing implementation-style parameter names.

Timer controls display practical seconds/minutes formatting. Hotbar controls identify valid slots and expected comma-separated formats where applicable.

The current-session panel appears when a routine is active or has meaningful status information. Main-window Pause and Stop Automation controls stay hidden while automation is idle and appear when needed.

### Mending Grinder

Mending Grinder attacks on a configurable timer and rotates through selected hotbar slots so collected XP can repair multiple Mending items.

Its setup controls are:

- **Attack every** — seconds between attack clicks;
- **Switch item every** — how long each selected tool remains active before the next hotbar slot is selected;
- **Mending slots** — hotbar slots cycled in the order entered.

### Equipment routines

Crossbow Volley, Hotbar Workflow, Tool Rotation, Durability Guard, Resource Guard, Food Manager, and Offhand Workflow expose routine-specific setup fields rather than one generic automation form.

### Movement, mining, farming, and construction

Coordinate/waypoint travel, branch mining, stair and area excavation, row farming, bone-meal farming, rectangles, grids, rows, alternating patterns, and perimeter routines expose the distances, timings, directions, slots, and repeat counts used by their specific behavior.

### Macro Studio

Macro Studio supports tap, click, wait, hold, turn, and hotbar-slot steps; built-in templates; manual editing and reordering; optional keyboard/mouse recording; a dry timeline; looped or one-pass playback; local save/delete; JSON import/export; and execution through the common automation engine.

## Navigation and portals

### Live Position

Captures F3+C coordinates, displays current block/chunk information, and supports position-oriented monitoring workflows.

### Coordinate & Travel Calculator

Includes distance, bearing, midpoint, XYZ delta, travel time, chunk/region geometry, snapping, offsets, and Overworld/Nether coordinate conversion.

### Waypoints, Routes & Surveys

Supports saved waypoints, distance sorting, multi-stop route planning, breadcrumb simplification, expedition paths, and survey workflows.

### Portal Network Planner

Includes sister-coordinate conversion, competing-exit calculations, asymmetric routing, link matrices, portal graphs, highway planning, and multi-destination network calculations.

## Explore Worlds

### Search location

Location-aware searches can start from:

- the captured current position;
- entered block coordinates;
- a center chunk.

Radius Search checks one bounded area. Search Until Found expands outward by the configured step until a result is found or the configured stop condition is reached.

### World and save data

World-oriented workbenches can use a known Java world seed, a generated Java save, installed Minecraft data, and supported bounded reference generation.

World Profiles can discover common local Java save locations or use a selected folder. Available `level.dat` information includes world name, version/DataVersion, seed, spawn, mode/hardcore state, and last-played metadata.

### Structure Explorer

Searches individual structures and structure relationships, clusters, density, and route-oriented structure results.

### Slime Chunks

Finds, groups, measures, and ranks slime chunks around a known world seed.

### Spawner Explorer

Reads generated world data for spawners, mob filters, groups, clusters, stronghold silverfish spawners, and trial-spawner information.

### Biome & Terrain Explorer

Includes biome lookup, nearest/intersection searches, region sizing, terrain forms, islands, peaks, valleys, cliffs, rivers, and diversity analysis.

### Ore & Cave Explorer

Includes:

- Ore Distribution;
- Ore Exposure Estimate;
- Cave Exposure Estimate;
- Ancient City Area Analysis.

These operations work with generated block-state data from a Java save or supported bounded reference generation. Results can include ore totals, Y-level distributions, exposed counts, scan coverage, cave measurements, charts, and returned coordinates where applicable.

### Local Area and World Analysis

Area reports combine relevant biome, structure, resource, loading, spawn, and suitability measurements for bounded regions or broader world-planning tasks.

## Plan & Build

### Build & Shape Planner

Build calculators cover dimensions, materials, stairs, bridges, roofs, grids, lighting, roads, gradients, and related planning measurements.

Shape layouts include circles, filled circles, arches, diamonds, ellipses, hexagons, octagons, spheres, hollow spheres, domes, cylinders, cones, spirals, helices, and double helices.

Two-dimensional results render block cells directly. Three-dimensional shapes expose selectable Y layers so the build can be read slice by slice.

### Redstone & Timing Lab

Includes tick conversion, hopper/comparator/repeater timing, transport timing, crafter throughput, clocks, counters, and signal-planning calculations.

### Storage & Logistics

Includes stack/container capacity, shulker requirements, chests, compression, bulk-material storage, transport trips, and logistics calculations.

### Farm & Breeding Planner

Includes yield, breeding, furnace/fuel, crop layouts, apiaries, villager halls, pens, beacon coverage, slime/fortress/trial planning, and related farm setup calculations.

### Technical Minecraft Calculator

Includes mob/loading radii, chunk alignment, sorters, perimeters, branch density, spawnproofing, technical spacing, and related geometry.

### Recipe & Material Explorer

Reads installed Minecraft recipe JSON and can search by recipe ID, result item, or recipe type. Recursive material expansion converts a target output into a bill of materials for larger build planning.

## Mechanics & Trading

### RNG & Enchanting Workbench

Enchanting Table uses a Minecraft item picker, bookshelf count, reproducibility seed, and three offer cards. Installed enchantment definitions and tags are loaded when available.

Anvil planning uses left item, sacrifice/book, result, visual enchantment editing, prior-work values, rename options, and level-cost metrics.

RNG tools include Java LCG state operations, sequence/timeline views, probability calculations, and gameplay-RNG recovery workflows.

### Loot & Drop Workbench

Indexes installed loot tables in the background, lets users browse possible results, and runs repeatable statistical simulations outside the UI thread. Simulation inputs stay visible while jobs run and can be adjusted for another run.

### Generation RNG

Includes decoration, feature, ore, tree, geode, trial-chamber, and structure-placement generation calculations.

### Minecraft Mechanics Lab

- **Brewing Stand** shows potion + ingredient → output transitions.
- **Leather Dye & Cauldron** provides selectable colors and wash/water-level behavior.
- **Horse/Donkey Breeding** reports inherited-stat ranges and averages in gameplay units.

### Villager Explorer

Villager Explorer uses a virtualized trade list so large filtered result sets remain responsive.

It supports:

- profession and level browsing;
- trade search and comparison;
- librarian enchanted-book reference information;
- max uses and planned restocks;
- emerald flow and XP details;
- favorites/comparison state;
- curing, breeding, workstation, and hall-planning helpers.

Installed-version trade data and local Minecraft artwork are loaded when available.

## Results and visualization

Results prioritize the values produced by the operation rather than renderer metadata.

Examples include:

- locations found;
- chunks scanned;
- radius searched;
- distance and bearing;
- material totals;
- storage capacity;
- probability;
- minimum, average, and maximum values.

Coordinate-producing results can render interactive X/Z maps. Ordered routes are connected; independent search locations are shown as independent markers. Maps support zoom, pan, layer visibility, labels, cursor coordinates, fit-to-data, and copying coordinates.

Statistical results can render labeled charts. Shape/build results use block-layer previews. Raw structured data is available in a collapsed advanced section.

## Minecraft data and artwork

F3+ can read installed Java Edition JAR data for recipes, loot tables, tags, enchantments, villager resources, and textures.

Artwork lookup first uses suitable installed Minecraft textures. Recolorable F3+ artwork is used when a matching local asset is unavailable.

Themes are **Chorus, Light, Cyber, Vanilla, and Custom**.

## Long-running operations

World searches, reference generation, loot simulation, and installed-data indexing use background work where supported so the desktop remains responsive. Activity indicators and cancellation controls are shown on surfaces that can take noticeable time.

## Validation

CI runs on Windows, macOS, and Ubuntu with Python 3.11, 3.12, and 3.13. It checks Python compilation, regression tests, native Cubiomes compilation, release metadata, workbench routing, input-help semantics, Mojang reference-world integration, and Windows UI screenshots.

The Windows screenshot artifact covers all five themes and major surfaces including world search, ore/cave analysis, automation, Mending Grinder configuration, villagers, enchanting, anvil planning, RNG, mechanics, loot, maps, charts, and block-layer previews.

## Updates

Validated Stable releases are used by default. Preview can follow development `main` with `F3PLUS_UPDATE_CHANNEL=preview`. Update checks can be disabled or skipped with the documented launcher environment variables.
