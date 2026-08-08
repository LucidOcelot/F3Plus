
**AI Disclosure:**

F3+ was unfortunately developed with generative AI assistance.
In the spirit of transparency, AI use is described below. 

Approximately 35% of F3+'s original first-party work is estimated to be substantially AI-created or AI-assisted translation, porting, integration, and refactoring of existing human/community work. The remaining work originates from human-written code and designs, ports of earlier Minescript/M.A.R.T. work, or implementations based on established community tools, algorithms, and research. 

Generative AI was also used extensively for integration, debugging, iterative testing in sandboxed environments, UI development, refactoring, documentation, and project organization. Project, features, testing feedback, revisions, and release decisions remained human work. 

All final inclusions were reviewed and edited by a human before being included in the project.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.

Third-party and community contributions are credited separately in COMMUNITY_CREDITS.md and THIRD_PARTY.md.


# F3+

F3+ is a cross-platform technical companion for Minecraft Java Edition. It combines automation, navigation, known-seed analysis, RNG recovery and simulation, world-save inspection, technical calculators, villager planning, building/farming tools, and guided setup workflows in one desktop application.

## Start

### Windows
1. Extract the ZIP completely.
2. Run `START_F3PLUS.bat`.
3. Leave the setup window open during the first launch.
4. Start Minecraft Java. F3+ links the client automatically when exactly one client is detected; if several are open, choose the intended client.

### macOS
1. Extract the ZIP.
2. Run `START_F3PLUS.command`.
3. Grant Accessibility/Input Monitoring permission when required for input automation.
4. Start Minecraft Java and allow F3+ to link the client.

### Linux
Run `START_F3PLUS.sh`.

Linux background automation uses the native Wayland path. When `ydotool`/`ydotoold` and supported compositor focus control are available, F3+ can focus the linked Minecraft process and send uinput events. Other Linux display sessions remain usable for calculators and foreground workflows.

## Main interface

The main window is organized around four areas:

- **Command deck** — Minecraft link state, background/minimized/camera capability, Relink, Safe Mode, Options, Pause/Resume, and Emergency Stop.
- **Context deck** — global search, dimension, selected Minecraft version, world seed, and live coordinate capture.
- **Workspace rail** — Automation, Navigation, World & Seed, Structures & Biomes, Calculators, Building & Farming, RNG, Villagers, Guided Setups, Utilities, and Safety.
- **Inspector** — the selected tool's purpose, usage instructions, inputs, output, limitations, and result display.

Tool browsing uses cached guide metadata; browsing a workspace does not execute seed searches or other heavy calculations.

## Appearance

Appearance presets and the full custom palette editor are available only under **Options → Appearance**. Fresh installs use the Chorus preset, an End-inspired purple, gold, black, and occasional blue presentation. A bright light preset is also available. On Chorus, Light, and Vanilla presets, F3+ reads a small set of recognizable textures directly from the player's installed Minecraft Java version when available. Those files are never bundled or copied into F3+; original theme-aware 16×16-style F3+ pixel art is used as the fallback and for Cyber and Custom themes.

## Minecraft linking and background input

F3+ automatically links one detected Java client and asks when multiple clients are available.

- **Windows:** targeted linked-window keyboard/mouse-button input, with focus switching when relative camera input requires it.
- **macOS:** process-targeted Quartz input where permitted, with focus switching and operating-system permission handling when required.
- **Linux:** native Wayland focus/uinput workflow when the required local helper and compositor integration are available.

When a macro cannot run safely in the current window state, F3+ explains the limitation before sending input and lets the user proceed with focus switching or cancel.

## Safe Mode

Safe Mode is a conservative strict-SMP filter. It stops active automation when enabled and disables tools that are commonly considered unfair or prohibited on strict multiplayer servers, including automation, seed-analysis/recovery, and RNG-analysis/recovery categories. Restricted tools remain visible so their purpose can still be read.

Safe Mode does not replace a server's rules. The server's actual policy always takes precedence.

## Seed and RNG boundaries

- A **known world seed** may be entered for deterministic calculations.
- **Gameplay/player RNG** is separate from the world seed and may be analyzed or recovered by the RNG tools where the observed mechanic uses a supported generator.
- **World/structure-seed recovery** has one route: Nether Bedrock Cracker using Nether bedrock observations.

Cubiomes source is bundled for supported known-seed generation calculations. F3+ does not present unsupported modern terrain as authoritative Cubiomes output.

## First-run setup

F3+ uses Python 3.11 or newer. If no usable interpreter is available, the launcher can prepare a verified project-local runtime. Runtime Python packages are installed into `.venv` on first use.

Before large package installation, F3+ checks free disk space. Disk-full, network, permission, and compatibility failures are reported separately instead of being retried as the same error.

## Emergency controls

Default Emergency Stop: `Ctrl + Alt + S`

Default Pause / Resume: `Ctrl + Alt + Space`

Emergency Stop releases tracked keyboard and mouse state through the active input backend.

## Troubleshooting

**The program does not open:** run the platform launcher from a fully extracted folder and read the generated `F3Plus_startup.log` if setup fails.

**First-run package setup fails:** check available disk space and network access. The launcher reports the first concrete package/install error.

**Minecraft is not linked:** start Minecraft Java, reach the game window, then use **Relink**. When more than one client is open, select the intended process.

**Background input is unavailable:** open **Connection Status** to see the active capability path. Some actions, especially relative camera motion, require focus even when keyboard/mouse buttons can run in the background.

**macOS input does not work:** confirm Accessibility and Input Monitoring permission for the terminal/Python process used to launch F3+.

**Linux background input does not work:** use a native Wayland session and confirm the configured compositor focus helper and `ydotool`/`ydotoold` access to `/dev/uinput`.

## Included documentation

- `FEATURES.md` — complete tool manual
- `LICENSE.md` — F3+ license
- `THIRD_PARTY.md` — third-party software and license boundaries
- `COMMUNITY_CREDITS.md` — community contributors and technical lineage

F3+ does not include Minecraft client/server JARs, Minecraft texture files, or Microsoft/Mojang assets.
