from __future__ import annotations

"""Qt-free, human-facing semantics for operation fields.

These strings are part of the public UX contract. A field may be inherited from a
historical compatibility schema, but the player should never see an explanation like
"value used by this operation" or be asked to infer units from an internal key.
"""

import re


FIELD_HELP = {
    "world_path": "Existing Java Edition world/save folder to inspect. Use this when the operation needs observed blocks, entities, NBT, ore exposure, caves, or other generated facts rather than seed-placement candidates.",
    "world": "Local Java world/save folder used as this operation's data source. F3+ reads it locally and does not modify the save unless the operation explicitly says it writes data.",
    "cx": "Chunk X coordinate at the center of the search or analysis. One chunk is 16 blocks wide; block X is converted with floor(X / 16).",
    "cz": "Chunk Z coordinate at the center of the search or analysis. One chunk is 16 blocks wide; block Z is converted with floor(Z / 16).",
    "chunk_x": "Chunk X coordinate. One chunk is 16 blocks wide; negative block coordinates use mathematical floor division.",
    "chunk_z": "Chunk Z coordinate. One chunk is 16 blocks wide; negative block coordinates use mathematical floor division.",
    "center_chunk_x": "Chunk X used as the center of a bounded world search.",
    "center_chunk_z": "Chunk Z used as the center of a bounded world search.",
    "center_x": "Block X coordinate used as the center of the operation.",
    "center_z": "Block Z coordinate used as the center of the operation.",
    "origin_x": "Block X coordinate used as the operation's origin/reference point.",
    "origin_z": "Block Z coordinate used as the operation's origin/reference point.",
    "x": "Minecraft block X coordinate on the east/west axis. Positive X is east and negative X is west.",
    "y": "Minecraft block Y coordinate on the vertical axis. Higher values are upward; lower values are deeper in the world.",
    "z": "Minecraft block Z coordinate on the north/south axis. Positive Z is south and negative Z is north.",
    "x1": "X coordinate of the first/start/current position used by the calculation.",
    "y1": "Y coordinate of the first/start/current position used by the calculation.",
    "z1": "Z coordinate of the first/start/current position used by the calculation.",
    "x2": "X coordinate of the second/target position used by the calculation.",
    "y2": "Y coordinate of the second/target position used by the calculation.",
    "z2": "Z coordinate of the second/target position used by the calculation.",
    "dx": "Signed X offset added to the starting coordinate; negative moves west and positive moves east.",
    "dy": "Signed vertical offset added to the starting Y coordinate.",
    "dz": "Signed Z offset added to the starting coordinate; negative moves north and positive moves south.",
    "other_x": "X coordinate of the second portal/reference point being compared with the primary position.",
    "other_y": "Y coordinate of the second portal/reference point being compared with the primary position.",
    "other_z": "Z coordinate of the second portal/reference point being compared with the primary position.",
    "radius": "Radius of the area or shape named by the visible label. Search radii determine how far F3+ scans from the center; build radii determine the generated block geometry.",
    "radius_step": "Additional search radius added after each empty Search Until Found attempt. Smaller steps are more thorough; larger steps cover distance with fewer expansion attempts.",
    "max_search_radius": "Largest radius Search Until Found may reach before reporting no match, unless the explicit ignore-limit option is enabled.",
    "width": "Horizontal width used by the selected build/layout calculation, normally measured in blocks.",
    "length": "Horizontal length/span used by the selected build/layout calculation, normally measured in blocks.",
    "height": "Vertical height used by the selected build/layout calculation, normally measured in blocks.",
    "spacing": "Distance between repeated elements, samples, supports, rows, or steps. The visible label identifies the exact role and unit for the selected tool.",
    "sag": "Vertical drop from the endpoints toward the center of a hanging/catenary curve, measured in blocks.",
    "secondary": "Second numeric quantity paired with the primary quantity. The selected operation's visible label and contextual help identify whether this means a second radius, width, count, level, timing value, or other mechanic-specific input.",
    "value": "Primary numeric quantity used by the selected mechanic. The operation description and visible label identify whether it represents ticks, items, distance, radius, count, rate, or another unit.",
    "stops": "Route destinations separated by semicolons. Each stop is x,y,z,label; for example: 80,64,0,Mine;120,70,50,Village.",
    "points": "Recorded path points separated by semicolons. Each point is x,y,z with an optional label when supported; for example: 0,64,0,Start;16,64,0,P2.",
    "sample_interval": "Seconds between recorded position samples. Smaller intervals create a denser route history and more points to process.",
    "interval": "Seconds between repeated captures/actions for this operation.",
    "epsilon": "Maximum distance in blocks that counts as revisiting the same place during loop detection.",
    "return_to_start": "When enabled, the route includes a final leg from the last destination back to the starting point.",
    "search_mode": "Radius Search checks one bounded area. Search Until Found expands outward after an empty result until a match or a stopping condition is reached.",
    "ignore_max_generation_limit": "Advanced override that allows an expanding search to pass the configured maximum. Exact generation can consume substantial CPU, memory, disk space, and time.",
    "regenerate_from_seed": "Generate bounded reference chunks with Mojang's matching Java server when no existing generated save is selected.",
    "accept_minecraft_eula": "Explicit acknowledgement required before F3+ may launch Mojang's server locally to generate reference chunks.",
    "worldgen_max_chunks": "Safety budget for exact Mojang reference generation. Higher budgets can require substantially more CPU time, RAM, disk I/O, and storage.",
    "dimension": "Minecraft dimension whose coordinate or generation rules are used by the operation: Overworld, Nether, or End where supported.",
    "target_biome": "Biome the search should locate, compare, or use as the target condition.",
    "second_seed": "Second Java world seed used only for side-by-side seed comparison. It does not replace the primary world seed.",
    "simulation_distance": "Minecraft simulation distance in chunks used to model which chunks are actively ticking around the player.",
    "target_candidates": "Desired number of candidate results used when estimating or optimizing a search radius.",
    "probability": "Chance of one independent success expressed from 0 to 1. Example: 0.05 means a 5% chance per attempt.",
    "target_chance": "Target probability for the named outcome, normally expressed from 0 to 1 unless the visible label states a percentage.",
    "attempts": "Number of independent attempts/rolls included in the probability or sequence calculation.",
    "count": "Number of outputs, samples, predictions, or results requested by the selected operation.",
    "first": "First observed signed 32-bit output from java.util.Random.nextInt(). It must be immediately followed by the second observation for state recovery.",
    "second": "Second consecutive signed 32-bit output from java.util.Random.nextInt() used with the first observation to recover compatible internal states.",
    "observed_long": "Observed signed 64-bit value returned by one java.util.Random.nextLong() call.",
    "state": "Recovered/internal 48-bit java.util.Random state. This is gameplay RNG state, not a Minecraft world seed.",
    "steps": "Number of Java LCG state transitions to advance (positive) or rewind (negative) before displaying predicted outputs.",
    "item": "Minecraft item used by the selected mechanic. Dedicated simulator workbenches use visual item selectors where applicable.",
    "items": "Total number of items being converted into stack, container, transport, or logistics requirements.",
    "stack_size": "Maximum items per inventory stack for the material being planned. Common Minecraft values are 64, 16, and 1.",
    "shulkers": "Number of shulker boxes available in the storage/transport plan; one shulker has 27 inventory slots.",
    "units": "Number of plants, animals, machines, modules, or other mechanic-specific units named by the selected operation.",
    "hours": "Time/cycle quantity used by the selected planning operation. The visible label identifies when the second quantity represents cycles or an ending level instead of literal hours.",
    "level": "Minecraft level or tier used by the selected calculation, such as Unbreaking level, starting XP level, beacon tier, or another mechanic-specific level named by the operation.",
    "amount": "Quantity consumed, repaired, processed, produced, or otherwise measured by the selected resource calculation.",
    "speed": "Travel or processing speed in the units stated by the field label, commonly blocks per second for movement tools.",
    "distance": "Distance in Minecraft blocks unless the visible label explicitly states another unit.",
    "yaw": "Minecraft horizontal facing angle in degrees. F3+ follows Java Edition yaw conventions for the selected navigation calculation.",
    "angle1": "Yaw/bearing angle of the first observation used by the selected triangulation calculation.",
    "angle2": "Yaw/bearing angle of the second observation used by the selected triangulation calculation.",
    "to_nether": "Choose the conversion direction. Enabled converts Overworld X/Z to Nether scale (divide by 8); disabled converts Nether X/Z to Overworld scale (multiply by 8).",
    "overworld_gain": "Overworld distance that would otherwise be traveled when comparing Nether-assisted travel compression.",
    "nether_walk": "Distance traveled inside the Nether portion of the comparison route.",
    "overworld_walk": "Additional Overworld distance traveled outside the Nether-assisted portion of the route.",
    "mc": "Cubiomes Minecraft-version enum used only by the native backend. Prefer the normal Minecraft Version setting unless a backend-level diagnostic explicitly asks for this value.",
    "name": "Human-readable name saved with the item, waypoint, profile, or other local F3+ object created by this action.",
    "new": "Replacement name to save for the selected local object.",
    "waypoint": "Existing saved F3+ waypoint selected for this action.",
}


def _unit_from_label(low: str) -> str:
    if "chunk" in low: return "chunks"
    if "block" in low: return "blocks"
    if "second" in low or " sec" in low: return "seconds"
    if "tick" in low: return "ticks"
    if "degree" in low or "yaw" in low or "angle" in low: return "degrees"
    if "hour" in low: return "hours"
    if "percent" in low or "%" in low: return "percent"
    return "the unit named by the field label"


def field_help(key: str, label: str = "") -> str:
    key = str(key); label_text = re.sub(r"\s+", " ", str(label or "")).strip(); low = label_text.lower()
    if key == "seed":
        if any(token in low for token in ("simulation", "rng", "random", "reproduc")):
            return "Deterministic simulator/RNG seed used only to reproduce this calculation. It is not the Minecraft world seed and does not select world generation."
        return "Known Java Edition world seed used by deterministic world-generation calculations or bounded reference generation. Negative and positive signed 64-bit seeds are valid."
    direct = FIELD_HELP.get(key)
    if direct: return direct
    if "radius" in low:
        unit = _unit_from_label(low); return f"Radius of the area or shape named by this field, measured in {unit}. Larger search radii require more work; larger build radii generate more blocks."
    if "seed" in low:
        return "Deterministic seed for the mechanic named by this field. World-generation seeds and simulator reproducibility seeds are separate concepts and are labeled separately in F3+."
    if "chance" in low or "probability" in low or "odds" in low:
        return "Probability for the named event. F3+ probability fields normally use 0 to 1 unless the label explicitly states percent; 0.25 means 25%."
    if any(token in low for token in ("count", "pull", "attempt", "samples", "cycles")):
        return "Number of repetitions or results requested for the named task. Larger values usually improve sample size or coverage but take longer to compute."
    if any(token in low for token in ("path", "folder", "save")):
        return "Local filesystem location used as this operation's data source. F3+ reads it locally; selecting a world folder does not upload the save."
    if "spacing" in low:
        return f"Spacing between the named repeated elements, measured in {_unit_from_label(low)}."
    if any(token in low for token in ("width", "length", "height", "distance")):
        return f"{label_text or 'Dimension'} used by the calculation, measured in {_unit_from_label(low)}."
    if "level" in low:
        return "Minecraft level/tier named by this field. The surrounding operation description identifies whether this means XP level, enchantment tier, beacon tier, or another mechanic level."
    if low == "x" or low.endswith(" x"): return "Minecraft X coordinate on the east/west axis. Positive is east; negative is west."
    if low == "y" or low.endswith(" y"): return "Minecraft Y coordinate on the vertical axis. Higher values move upward; lower values move deeper."
    if low == "z" or low.endswith(" z"): return "Minecraft Z coordinate on the north/south axis. Positive is south; negative is north."
    if "version" in low:
        return "Minecraft/data version selected for this operation. F3+ reports when the active calculation or local data source uses a different version."
    if "item" in low or "material" in low:
        return "Minecraft item or material used by the named calculation. Use the exact item requested by the visible operation rather than an internal numeric ID."
    if label_text:
        return f"Input for “{label_text}”. Its role is defined by the selected operation and the contextual description shown directly above this control; changing it changes that named part of the calculation."
    return "Operation input whose purpose is shown in the selected operation's contextual description. F3+ does not expose unused internal compatibility values as user fields."
