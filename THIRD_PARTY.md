# Third-Party Software and Notices

Third-party components retain their upstream licenses. The F3+ MIT license does not replace those terms.

## AI-assisted development disclosure

Generative AI was used during development for code translation/porting, refactoring, integration, debugging, test construction, UI iteration, and documentation. Project direction, feature selection, testing feedback, revisions, release decisions, and final inclusion decisions remained human-directed and human-reviewed.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.

Third-party and community contributions are credited below.

## Cubiomes

- **Project:** Cubiomes by Cubitect and contributors
- **License:** MIT
- **Included:** required C source, headers, generation tables, and upstream license under `third_party/cubiomes/`
- **Use:** supported known-seed biome and structure calculations through the F3+ native bridge

## Nether Bedrock Cracker

- **Project:** Nether Bedrock Cracker by 19MisterX98 and contributors
- **License:** LGPL-3.0
- **Included:** Rust source and upstream LGPL license under `third_party/nether_bedrock_cracker/source/`
- **Use:** F3+'s sole world/structure-seed recovery workflow

Where F3+ has a release-pinned expected SHA-256 for an upstream prebuilt, it may download and verify that payload before execution. Otherwise F3+ uses the bundled source/build path instead of executing an unverified binary.

## Earthcomputer EnchantmentCracker

- **Project:** Earthcomputer/EnchantmentCracker
- **License:** MIT
- **Bundled:** No
- **Use:** optional player/enchantment RNG recovery

F3+ can acquire the supported upstream release on first use and verifies the pinned SHA-256 before extraction. This workflow concerns gameplay/player RNG, not the Minecraft world seed.

## Python and runtime bootstrap

F3+ 2.4.1 supports Python **3.11 through 3.13**. It first uses a runnable compatible local installation. If none is available, it can prepare a project-local runtime under `.runtime/` using uv and a managed CPython distribution.

- **uv:** Astral Software Inc.; Apache-2.0 OR MIT
- **CPython:** Python Software Foundation; upstream Python licensing

Bootstrap/tool downloads that F3+ executes are checked against release-pinned SHA-256 values before extraction or execution.

## Python runtime packages

Installed into F3+'s private `.venv` when required; not bundled in the ZIP:

- **PySide6-Essentials / Qt for Python** — upstream LGPL/GPL/commercial licensing options
- **pynput** — Moses Palmér and contributors; LGPL-3.0
- **pyperclip** — Al Sweigart and contributors; BSD
- **PyObjC Quartz** on macOS — Ronald Oussoren and PyObjC contributors; MIT

## Operating-system input interfaces

F3+ uses operating-system interfaces rather than redistributing another automation product:

- **Windows:** Win32 window discovery/focus and linked-window input messages
- **macOS:** Quartz/PyObjC process-targeted events and system permission/focus services
- **Linux:** native Wayland compositor focus plus optional local uinput delivery

### ydotool

- **Project:** ydotool by ReimuNotMoe and contributors
- **License:** AGPL-3.0
- **Bundled:** No
- **Use:** optional Wayland uinput path when `ydotool`/`ydotoold` is already installed and allowed to access `/dev/uinput`

## Zig compiler fallback

Zig is not bundled. If Cubiomes needs compilation and no suitable local C compiler is available, F3+ can acquire a pinned Zig toolchain as a build helper. The archive is verified before extraction and Zig retains its upstream license.

## Minecraft / Mojang / Microsoft

Minecraft client/server JARs, Microsoft Java runtimes, textures, logos, and other Mojang/Microsoft assets are not distributed with F3+.

F3+ ships original pixel-art interface assets designed to fit Minecraft's block-scale visual language without reproducing or embedding Minecraft texture files.

## Technical references without bundled source

F3+ contains independent implementations informed by public Minecraft mathematics, technical documentation, and community research. Projects acknowledged in `COMMUNITY_CREDITS.md` are not bundled or relicensed unless explicitly listed above.