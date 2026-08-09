**AI Disclosure:**

F3+ was unfortunately developed with generative AI assistance. In the spirit of transparency, AI use is described below.

Approximately 35% of F3+'s original first-party work is estimated to be substantially AI-created or AI-assisted translation, porting, integration, and refactoring of existing human/community work. The remaining work originates from human-written code and designs, ports of earlier Minescript/M.A.R.T. work, or implementations based on established community tools, algorithms, and research.

Generative AI was also used extensively for integration, debugging, iterative testing in sandboxed environments, UI development, refactoring, documentation, and project organization. Project direction, feature choices, testing feedback, revisions, and release decisions remained human work.

All final inclusions were reviewed and edited by a human before being included in the project.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.

Third-party and community contributions are credited separately in `COMMUNITY_CREDITS.md` and `THIRD_PARTY.md`.

# F3+ 2.3.4

F3+ is an offline-first desktop companion for Minecraft Java Edition built around community tools and Minescript/M.A.R.T. by Lucid. It combines automation, navigation, known-seed analysis, generated-world inspection, technical calculators, construction/farming planning, RNG utilities, villager planning, and safety controls without requiring a modified Minecraft client.

**Release:** 2.3.4  
**Default Minecraft target:** 26.3 Snapshot 7  
**Python:** 3.11 through 3.13  
**Update channel:** `LucidOcelot/F3Plus` `main`

## Start

- **Windows:** extract the ZIP and run `START_F3PLUS.bat`.
- **macOS:** extract the ZIP and run `START_F3PLUS.command`; grant Accessibility/Input Monitoring permission when automation requires it.
- **Linux:** run `START_F3PLUS.sh`. Background input uses the supported Wayland/uinput path where available; calculators and foreground workflows do not depend on it.

The launcher prepares a project-local environment and required Python packages when needed. Existing installations check GitHub `main` at launch, update clean installs automatically, and continue offline when the update check is unavailable. Set `F3PLUS_SKIP_UPDATE=1` only when intentionally skipping the update check for development or recovery.

## What F3+ provides

The interface groups the historical 457 feature IDs into task-oriented workspaces while keeping those IDs stable for favorites, recents, and compatibility. Tool configuration uses task-specific labels and units; normal results translate internal values into readable coordinates, biome names, percentages, statuses, tables, warnings, and visual output instead of exposing backend dictionaries.

Spatial seed/world results can open an interactive X/Z view with wheel zoom, drag panning, fit-to-data, layer visibility controls, grid and point-label toggles, cursor coordinates, and copyable visible coordinates. Construction, shape, farm, and planning tools use the same visual system when they produce a footprint, route, layout, or other useful geometry.

The Villager Trade Explorer uses item textures and **villager profession skin layers** recovered from an installed Java client when available. Trade definitions are tracked separately from artwork: exact installed trade JSON is preferred, and an explicitly labeled planning baseline is used only when no usable installed trade data exists.

The **Simulation Lab** provides a data-driven Loot Table Explorer plus Enchanting Table/Anvil, Brewing Stand, Cauldron/Leather Dye, and Animal/Horse Breeding simulators. Loot tables, enchantment definitions, item tags, and Minecraft icons are read from the installed Java client where available; clearly labeled first-party baseline data and original F3+ icons keep the tools usable when local data or artwork is unavailable.

Spawner tools inspect generated Anvil/NBT data, identify encoded mob types where possible, and support mob-specific filtering plus double/triple/quad/cluster searches. Seed math is not presented as proof that an arbitrary dungeon spawner generated.

## Finder search modes

Location-oriented finders provide **Radius search** and **Search until found** where a real found/not-found result exists. Radius search checks one bounded area. Search until found expands outward by a configurable step and normally stops at the configured maximum radius.

Every tool that exposes Search until found also exposes **Ignore maximum search / generation limit**. When enabled, F3+ continues beyond the configured maximum. If the workflow requires exact Mojang reference-world generation, the configured generated-chunk budget is also raised as needed. This override can consume substantial CPU, memory, disk space, and time; backend failures and an internal runaway-loop guard can still stop the process.

## Minecraft versions and exactness

F3+ keeps three concepts separate: the Minecraft version selected by the user, the generation rules actually used for a calculation, and the installed local-data version used for things such as textures or trade definitions.

The bundled Cubiomes mapping is explicitly bounded through Minecraft 1.21.3. When a newer selected version is unsupported, F3+ keeps the selected version visible and labels the supported calculation fallback rather than claiming snapshot-exact world generation.

Tools that require real generated terrain can inspect an existing Java save. Where supported, they can instead generate bounded reference chunks locally with Mojang's matching server JAR after explicit EULA acceptance. F3+ checks the server metadata for the required Java major version and searches configured Java, `JAVA_HOME`, PATH, and Minecraft Launcher runtimes for a compatible executable.

World/structure-seed recovery remains limited to the **Nether Bedrock Cracker** workflow. Gameplay/player RNG recovery is separate and is not presented as world-seed recovery.

## Minecraft linking and safety

F3+ links automation to a verified Minecraft Java process rather than trusting window-title text alone. Tools that need input show the active background/focus capability before running. Emergency Stop releases tracked held input, and Pause/Resume plus the main global hotkeys are configurable under **Options → Automation**.

Safe Mode is a conservative multiplayer filter, not a substitute for a server's rules.

## Data, network use, and assets

Prepared calculations, settings, local-data browsing, and generated-save analysis run locally. Network access can be required for launch updates, dependency/component acquisition, optional upstream helpers, or exact Mojang reference-world acquisition.

F3+ does not bundle Minecraft client/server JARs or Mojang texture files. Minecraft artwork shown in the interface is read from the player's installed Java files at runtime where available.

## Documentation

`FEATURES.md` contains the detailed feature-family and implementation guide. `COMMUNITY_CREDITS.md` documents community lineage, `THIRD_PARTY.md` covers third-party software/license boundaries, and `LICENSE.md` contains the F3+ license.
