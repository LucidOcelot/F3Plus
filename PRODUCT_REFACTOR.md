# F3+ Product Refactor Checklist

This document consolidates the UI, QA, architecture, and product issues identified during the project audit. The goal is a task-first technical Minecraft workstation with concise inputs and outputs, fewer navigation decisions, and no loss of calculation or automation capability.

## Navigation and information architecture

- [x] Replace implementation-oriented workspaces with six top-level destinations: Home, Play & Travel, Explore Worlds, Plan & Build, Mechanics & Trading, and App & Safety.
- [x] Group workbenches by player task instead of historical source categories such as Gameplay, Seed Tools, Calculators, and RNG Tools.
- [x] Keep all existing operation handlers reachable from the reorganized workbench library.
- [ ] Update the desktop shell so search filters, inspector breadcrumbs, and card metadata use the new task section and group names everywhere instead of internal `ToolSpec.workspace` labels.
- [ ] Make search results open a matching operation directly when the query clearly matches one operation rather than forcing a second workbench-selection step.
- [ ] Add a goal-oriented Home entry surface for common jobs such as portal conversion, structure search, material planning, villager planning, enchanting, and world scanning.
- [ ] Reduce persistent top-bar automation chrome when no automation routine is active; expand safety controls when automation starts.

## Workbench consolidation

- [x] Preserve underlying functionality while presenting related operations together.
- [ ] Merge overlapping automation entry points into fewer visible workbenches while retaining distinct modes internally.
- [ ] Merge overlapping resource/storage calculators into a shared material and logistics planning flow.
- [ ] Merge world-search tools around common center/radius/save/seed controls rather than duplicating similar forms.
- [ ] Move world/profile selection into a reusable project/world context shared by search, scan, route, and planning workbenches.
- [ ] Remove files whose only purpose is an obsolete UI generation after the task-first shell fully replaces them; avoid adding another numbered `appXX.py` compatibility layer.

## Inputs

- [x] Put concrete help on generic input controls using tooltips and accessibility descriptions.
- [x] Remove repeated inline help paragraphs that duplicate tooltips and make forms visually noisy.
- [x] Replace generic compatibility-language fallbacks with direct value descriptions.
- [x] Explain coordinate direction, units, ranges, formats, choices, and defaults where available.
- [ ] Audit operation-specific fields whose labels are still too generic (`value`, `secondary`, `amount`, `units`, etc.) and rename them at the operation schema so the label itself communicates the mechanic.
- [ ] Prefer pickers, dropdowns, world selectors, item selectors, and waypoint selectors over free-form identifiers when a finite domain is known.
- [ ] Add inline validation messages for invalid ranges and formats before execution rather than returning avoidable run-time errors.

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

- [x] Remove compatibility and historical-version framing from the main README.
- [x] Remove template-style workbench copy from the guide generator.
- [x] Remove statements written like instructions to an evaluator or AI agent, including phrases such as `does not claim`, `never presented`, and compatibility-contract boilerplate.
- [x] Avoid confidence-level presentation in player-facing results.
- [ ] Audit `FEATURES.md`, old descriptions, and operation notes for remaining evaluator-facing wording and rewrite them as direct user documentation.
- [ ] Remove references to historical operation counts from player-facing documentation and UI.

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

- [ ] Keep automation focused on bounded deterministic workflows rather than general autonomous play.
- [ ] Add a dry-run view showing planned actions, movement, stop conditions, and recovery behavior before execution.
- [ ] Standardize long-running operations around a common progress contract: stage, progress, search extent, cancellation support, and partial-result availability.
- [ ] Add clearer visual indication when automation safety controls become relevant and collapse them when idle.

## QA

- [x] Replace release-era UI contracts with task-first navigation and wording contracts.
- [x] Keep semantic tests proving distinct operations still return distinct outputs.
- [x] Keep cross-platform Python CI and native Cubiomes compiler checks.
- [x] Keep Mojang reference-world integration testing.
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
- [ ] Audit numbered/versioned UI modules and consolidate them once the new shell is complete.
- [ ] Delete release-specific tests that no longer protect current behavior after equivalent current-product tests exist.
- [ ] Consolidate duplicate descriptions between README, FEATURES, tool guides, and source-level operation descriptions so each fact has one maintained source.
- [ ] Add a public issue/backlog structure for defects, UX problems, unsupported mechanics, and planned workflow improvements.
