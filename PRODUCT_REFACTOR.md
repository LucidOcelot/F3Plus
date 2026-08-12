# F3+ Product Refactor Checklist

This document consolidates the UI, QA, architecture, and product issues identified during the project audits. The goal is a task-first technical Minecraft workstation with concise inputs and outputs, fewer navigation decisions, and no loss of calculation or automation capability.

## Navigation and information architecture

- [x] Replace implementation-oriented workspaces with six top-level destinations: Home, Play & Travel, Explore Worlds, Plan & Build, Mechanics & Trading, and App & Safety.
- [x] Group workbenches by player task instead of source categories such as Gameplay, Seed Tools, Calculators, and RNG Tools.
- [x] Keep all existing operation handlers reachable from the reorganized workbench library.
- [x] Use the task section and player-facing group names consistently in cards, filters, menus, search, and inspector breadcrumbs.
- [x] Replace flat workbench operation lists with real collapsible group navigation rather than disabled pseudo-header rows.
- [x] Replace the Automation Studio routine list with collapsible task categories and keyboard-friendly search/activation.
- [x] Make the menu bar use the same task hierarchy as the main navigation instead of exposing a second organization model.
- [x] Reduce persistent automation chrome while idle; Pause and Stop Automation appear when automation is active.
- [x] Collapse the permanent desktop inspector into an optional Details drawer so the workbench grid owns the main window by default.
- [x] Add a visible Open Selected action so workbench launch does not depend on discovering double-click behavior.
- [ ] Make search results open a matching operation directly when the query clearly matches one operation rather than forcing a second workbench-selection step.
- [ ] Add a goal-oriented Home entry surface for common jobs such as portal conversion, structure search, material planning, villager planning, enchanting, and world scanning.

## Workbench consolidation

- [x] Preserve underlying functionality while presenting related operations together.
- [x] Remove the obsolete versioned desktop shell and make `minescript/desktop.py` the runtime desktop implementation.
- [ ] Merge overlapping automation entry points into fewer visible workbenches while retaining distinct modes internally.
- [ ] Merge overlapping resource/storage calculators into a shared material and logistics planning flow.
- [ ] Merge world-search tools around common center/radius/save/seed controls rather than duplicating similar forms.
- [ ] Move world/profile selection into a reusable project/world context shared by search, scan, route, and planning workbenches.
- [ ] Audit the remaining numbered/versioned UI helper modules and rename or consolidate them where the version suffix no longer communicates a meaningful implementation boundary.

## Inputs

- [x] Put concrete help on generic input controls using tooltips and accessibility descriptions.
- [x] Remove repeated inline help paragraphs that duplicated tooltips and made forms visually noisy.
- [x] Make visible hints and detailed tooltips different: the hint identifies the unit/purpose while the tooltip explains behavior, range, default, and consequences of changing the value.
- [x] Wrap long tooltips to a readable width instead of allowing single-line tooltips to stretch across the screen.
- [x] Replace vague Mending Grinder labels with `Attack every`, `Switch item every`, and `Mending slots`.
- [x] Add mechanic-specific help for built-in automation setup fields including travel, mining, construction, farming, fishing, livestock, hotbar, crossbow, food, offhand, and guard routines.
- [x] Format timer fields as human-readable seconds/minutes with practical precision instead of raw six-decimal floats.
- [x] Make small parameter dialogs size to their contents instead of opening as mostly-empty large windows.
- [x] Separate Qt-free input semantics from widget code so help text can be tested on headless CI runners.
- [x] Explain coordinate direction, units, ranges, formats, choices, and defaults where available.
- [ ] Audit operation-specific fields whose labels are still too generic (`value`, `secondary`, `amount`, `units`, etc.) and rename them at the operation schema so the label itself communicates the mechanic.
- [ ] Prefer pickers, dropdowns, world selectors, item selectors, and waypoint selectors over free-form identifiers when a finite domain is known.
- [ ] Add inline validation messages for invalid ranges and formats before execution rather than returning avoidable run-time errors.

## Descriptions and workbench copy

- [x] Replace generic Automation Studio routine descriptions with sentences describing the actual action performed.
- [x] Remove repetitive Automation Studio requirement/run-behavior prose that restated the selected routine.
- [x] Stop using the same summary twice in generated workbench guide data.
- [x] Replace generic operation output prose with concrete returned values where output keys are known.
- [x] Keep workbench cards concise and make their tooltip list contained operations rather than repeating the card description.
- [x] Keep Command Palette tooltips action-oriented instead of duplicating workbench summaries.
- [x] Rewrite `FEATURES.md` around the current task-first interface and remove obsolete shell/alias/help wording.
- [ ] Continue auditing dedicated simulator/villager workbenches for repeated explanation cards whose controls already make the mechanic clear.

## Outputs

- [x] Remove confidence/exactness fields from the normal result surface.
- [x] Hide internal result metadata such as contracts, backend markers, and presentation-control fields.
- [x] Lead result cards with concrete metrics such as locations found, chunks scanned, radius searched, distance, probability, and min/average/max values.
- [x] Rename vague table headers from generic `Metric`, `Column`, and `Value` labels where the renderer can infer a better name.
- [x] Keep data-source text only when it helps interpret the result.
- [x] Rewrite map help so it explains exactly what a marker or connected route represents.
- [ ] Continue adding operation-specific output labels for result keys that still fall through to automatic title-casing.
- [ ] Add result actions such as Copy Coordinates, Save Waypoint, Add to Map, Use as Route Destination, and Send to Material Planner.
- [ ] Allow one workbench result to become another workbench input without manual copy/paste.

## Product language

- [x] Remove historical/backward-compatibility framing from the main README and player-facing shell.
- [x] Remove template-style workbench copy from the guide generator.
- [x] Remove statements written like instructions to an evaluator or AI agent, including phrases such as `does not claim`, `never presented`, and compatibility-contract boilerplate.
- [x] Avoid confidence-level presentation in player-facing results.
- [x] Stop making tests require negative disclaimer wording when a direct positive description explains the distinction more clearly.
- [x] Rewrite `FEATURES.md` as direct player documentation rather than release-audit prose.
- [ ] Audit older source-level operation notes for remaining evaluator-facing wording where those notes still reach the UI.
- [ ] Remove references to historical operation counts from any remaining player-facing surfaces.

## Projects and cross-tool workflows

- [ ] Add persistent Projects containing a world/save, seed, version, dimension, waypoints, routes, build plans, material lists, villager plans, and saved results.
- [ ] Add a persistent layered world map that can display structures, slime chunks, routes, waypoints, portals, scans, and build sites.
- [ ] Add `Add to map` to coordinate-producing results.
- [ ] Expand the portal planner into a saved portal network with collision/separation checks and route comparisons.
- [ ] Expand farm planning into guided workflows combining location requirements, spawn mechanics, storage throughput, and materials.
- [ ] Expand storage/logistics planning with hopper, water-stream, minecart, shulker-loader, and bulk-storage throughput.
- [ ] Add a visual redstone timing timeline for signal chains.
- [ ] Expand recipes/materials into a reusable acquisition dependency graph for large builds.
- [ ] Add world comparison and save-health diagnostics for generated-chunk growth, region size, entity/block-entity concentrations, and suspicious/corrupt areas.

## Automation

- [x] Collapse top-level automation-only controls when no routine is running.
- [x] Show a concise Current Session card only while a routine is running or has a meaningful status message.
- [ ] Keep automation focused on bounded deterministic workflows rather than general autonomous play.
- [ ] Add a dry-run view showing planned actions, movement, stop conditions, and recovery behavior before execution.
- [ ] Standardize long-running operations around a common progress contract: stage, progress, search extent, cancellation support, and partial-result availability.

## QA

- [x] Replace release-era UI contracts with task-first navigation and wording contracts.
- [x] Keep semantic tests proving distinct operations still return distinct outputs.
- [x] Keep cross-platform Python CI and native Cubiomes compiler checks.
- [x] Keep Mojang reference-world integration testing.
- [x] Add a Windows UI review capture for the Mending Grinder settings dialog that exposed the second-review defects.
- [x] Make the UI artifact runner launch the canonical desktop rather than the removed versioned shell.
- [x] Add source/UI contracts for grouped tree navigation, distinct hint/tooltip copy, wrapped tooltips, concise parameter labels, idle automation chrome, and the collapsed Details drawer.
- [x] Update navigation tests to exercise the new tree structure instead of assuming a flat list API.
- [x] Update shape-result tests to protect descriptive `Block positions` output instead of generic `Points` wording.
- [x] Pass the complete Windows/macOS/Ubuntu Python 3.11–3.13 matrix, release audit, semantic audit, Cubiomes compiler audit, Mojang worldgen integration, and Windows UI screenshot capture after the second review.
- [ ] Add selected visual-regression image comparisons for stable UI regions rather than screenshot capture alone.
- [ ] Add high-DPI and minimum-window-size layout checks.
- [ ] Add keyboard-navigation/accessibility smoke tests for search, workbench cards, forms, and result actions.
- [ ] Add end-to-end tests for the most common two-step workflows: search -> save waypoint, build -> materials, villager -> resource plan, portal -> route.

## Security and robustness

- [ ] Add archive path-traversal and symlink-escape tests for JAR/ZIP extraction and component acquisition.
- [ ] Add malformed/deep/oversized NBT and region-file parser tests with explicit work limits.
- [ ] Add download identity/hash mismatch tests.
- [ ] Add generated-world output-directory containment tests.
- [ ] Validate imported settings against a schema before applying them.

## Repository cleanup

- [x] Rewrite the README around the current product rather than compatibility history.
- [x] Delete the obsolete `app25.py` shell after moving startup, menus, CI screenshots, and canonical UI tests to `desktop.py`.
- [x] Remove UI tests that protected the old eight-section navigation and obsolete menu hierarchy.
- [x] Rewrite catalog integrity tests around current operation reachability rather than preserving old IDs as a product requirement.
- [ ] Consolidate duplicate descriptions between README, FEATURES, tool guides, and source-level operation descriptions so each fact has one maintained source.
- [ ] Add a public issue/backlog structure for defects, UX problems, unsupported mechanics, and planned workflow improvements.
