# Community Credits

F3+ is maintained by **LucidOcelot (Lucid)**. This document credits the first-party project lineage, the community tools F3+ builds around, and public technical research that materially shaped the app. Attribution does not imply endorsement. Redistribution boundaries and bundled-license details are listed separately in `THIRD_PARTY.md`.

## First-party project lineage

**AI Disclosure:**

F3+ was unfortunately developed with generative AI assistance.
In the spirit of transparency, AI use is described below. 

Approximately 35% of F3+'s original first-party work is estimated to be substantially AI-created or AI-assisted translation, porting, integration, and refactoring of existing human/community work. The remaining work originates from human-written code and designs, ports of earlier Minescript/M.A.R.T. work, or implementations based on established community tools, algorithms, and research. 

Generative AI was also used extensively for integration, debugging, iterative testing in sandboxed environments, UI development, refactoring, documentation, and project organization. Project, features, testing feedback, revisions, and release decisions remained human work. 

All final inclusions were reviewed and edited by a human before being included in the project.

F3+ does not use generative AI during normal operation and does not transmit Minecraft, world, seed, coordinate, account, or other user data to an AI provider.

Third-party and community contributions are credited separately in COMMUNITY_CREDITS.md and THIRD_PARTY.md.

**LucidOcelot / Lucid** — creator of the original **Minescript / M.A.R.T.** project and the direct maintainer of F3+. 
Responsible for:

- the original macro tool that evolved into F3+
- the macro engine direction and macro preset system
- player position capture / coordinate-aware movement direction
- player position and location interpolation / travel feedback workflows
- F3+'s asymmetric / non-Euclidean Nether portal tool line


## Bundled or directly integrated upstream tools

**Cubitect** — principal author of **Cubiomes**. F3+ bundles the required Cubiomes source and builds a local bridge for supported known-seed biome and structure calculations.

**Cubiomes contributors** — contributed upstream generation logic, fixes, portability work, and version support relied upon by the bundled Cubiomes source.

**19MisterX98** — author and maintainer of **Nether Bedrock Cracker** and author of **SeedCrackerX**. F3+ uses Nether Bedrock Cracker as its sole world/structure-seed recovery workflow.

**Nether Bedrock Cracker contributors** — contributed to the Rust cracking engine and UI retained under the upstream LGPL terms.

**Earthcomputer (Joseph Burton)** — author of **EnchantmentCracker** and **clientcommands**. F3+ can acquire the verified EnchantmentCracker v1.9 release for supported player/enchantment RNG recovery.

## Research and technical lineage

**KaptainWutax** — major seedfinding reference author across structures, features, biomes, loot, Java RNG, and related Minecraft generation mathematics.

**Neil / hube12** — seedfinding developer and educator with widely referenced public work on Java LCG reversal, structure logic, biomes, terrain, dungeons, and dimension generation.

**Matthew Bolan** — published explanations of Java linear congruential generators, lattice methods, seedfinding, and dungeon-related cracking topics.

**Jurre Groenendijk** — published accessible introductions to the Java SeedFinding / FeatureUtils ecosystem.

**Ninjabrain1** — author of **Ninjabrain Bot**, an important stronghold-triangulation and speedrunning reference.

**xpple** — author of **SeedMapper** and contributor to seed-mapping / locator workflows.

**jan-leila** — author of **js-cubiome** and FastReset, demonstrating public precedents for exposing Cubiomes from other runtimes.

**4gboframram** — author of **Pyubiomes**, another reference point for Python-facing Cubiomes use.

**Qther**, **Brainrotisreal**, **Frederik van der Els**, **Nekzuris**, and **ItzSkyReed** — contributors associated with modern SeedCrackerX maintenance, fixes, and supporting documentation.

**ZodSmar** — author of **SeedSearcherStandaloneTool (SASSA)**, a broad seed-search reference.

**Gaider10** — author of **PigSpawnerFinder**, a spawner-oriented technical seed tool.

**MCRCortex** and **Polymetric** — part of the wider tree-cracking and seedfinding research landscape. F3+ does not expose tree-based world-seed recovery.

**L64 / SciCraft seedfinding work** — public high-performance seed-search material relevant to technical-Minecraft tooling.

**gnembon** — author of **Fabric Carpet**, a major technical-Minecraft observability, automation, and simulation reference.

**Chunk Base** — public calculator / seed-map reference used for feature-coverage comparison only. F3+ does not bundle Chunk Base code or require the site at runtime.

## Runtime and build dependencies

**Qt for Python / PySide contributors** — maintain PySide6, which provides the F3+ desktop interface.

**Moses Palmér and pynput contributors** — maintain pynput, used by the standard cross-platform input path and global hotkeys.

**Al Sweigart and pyperclip contributors** — maintain pyperclip, used for clipboard-oriented coordinate workflows.

**Ronald Oussoren and PyObjC contributors** — maintain PyObjC/Quartz bindings used by the macOS input backend.

**Astral / uv contributors** — maintain uv, used for verified project-local Python/runtime bootstrap fallback.

**Andrew Kelley and Zig contributors** — maintain Zig, used only as an optional compiler fallback when a local C compiler is unavailable.

**ReimuNotMoe and ydotool contributors** — maintain ydotool, which F3+ can use when it is already installed on native Wayland systems. F3+ does not bundle or install ydotool.

**Python Software Foundation and CPython contributors** — maintain Python, the F3+ runtime.

## Attribution boundary

Only software explicitly identified as bundled, runtime-integrated, or acquired by F3+ should be treated as redistributed by the project. Other names in this file credit technical lineage, research influence, and community precedent rather than copied source code.
