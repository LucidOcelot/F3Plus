# F3+ Security

F3+ is a local desktop companion that can read Minecraft files, synthesize input, inspect running Minecraft processes, prepare Python dependencies, and optionally acquire upstream components. Those capabilities are deliberately separated so calculators and local analysis do not require automation privileges.

## Local files and data

F3+ stores user configuration under `~/.f3plus` and uses project-local runtime/environment directories created by the launchers. Generated reference worlds and temporary component data are created locally for the operation that requested them. Existing Java saves are read for generated-world analysis; F3+ does not need to upload a save to perform those scans.

Minecraft client/server JARs and Mojang texture files are not redistributed by F3+. Installed client JARs may be read locally for textures and data-driven definitions such as loot tables, tags, enchantments, or villager resources.

## Network access

Normal prepared calculators, configuration, installed-data browsing, and generated-save analysis operate locally. Network access may occur for:

- launch/update checks;
- first-run Python dependency/runtime preparation;
- optional upstream/community helper acquisition;
- Mojang metadata/server acquisition for an explicitly requested exact reference-world workflow.

F3+ does not use generative AI during normal operation and does not send world, seed, coordinate, account, or Minecraft-save data to an AI provider.

## Automation permissions

Automation can synthesize keyboard/mouse input and identify a target Minecraft Java process. Depending on the operating system and input mode, background/targeted input may require platform permissions or services. macOS can require Accessibility/Input Monitoring permission. Linux background input depends on the supported Wayland/uinput path; unsupported sessions fall back to foreground behavior.

F3+ reports the active input capability and does not treat a Minecraft-looking window title alone as verified process identity where stronger process verification is available.

Emergency Stop releases tracked held inputs. Pause/Resume, focus behavior, delayed start, runtime/action limits, stuck detection, and recovery limits are common automation controls. Safe Mode is a conservative multiplayer filter and is not a substitute for a server's rules.

## Exact Mojang reference-world generation

Exact generated-terrain workflows may create a bounded local vanilla server reference world. F3+ requires explicit Minecraft EULA acceptance before this workflow and checks the Java major version required by the selected server metadata. Search/generation budgets are bounded unless the user explicitly enables the advanced ignore-limit override.

## Updates and dependencies

The launcher and updater should only acquire components from configured upstream project/Mojang/runtime sources. Release code pins or validates component identities where supported by the underlying bootstrap path. Changes to download URLs, hashes, or update identity handling should receive security review because they expand the application's supply-chain surface.

## Untrusted files

Minecraft worlds, NBT/region data, JAR/ZIP files, and imported settings should be treated as untrusted input. Parsers should fail closed on malformed data, bound recursion/work, avoid executing embedded content, and keep filesystem writes inside the intended project/config/reference-world locations.

## Reporting a vulnerability

Please report security issues privately to the repository maintainer rather than publishing an exploitable issue with reproduction details before a fix is available. Include the affected F3+ version/commit, operating system, reproduction steps, and the smallest non-sensitive sample needed to reproduce the problem.
