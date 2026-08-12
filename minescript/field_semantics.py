from __future__ import annotations

"""Human-facing input help used by generic operation forms."""

import re


FIELD_HELP = {
    "world_path": "Select the Java Edition world folder to read. Use the folder that contains level.dat; scans read generated chunks, entities, and block data from this save.",
    "world": "Select the Java Edition world folder to read. The chosen save supplies generated chunk and world data for this operation.",
    "cx": "Center chunk X. One chunk is 16 blocks wide; block X converts to chunk X with floor(X / 16), including negative coordinates.",
    "cz": "Center chunk Z. One chunk is 16 blocks wide; block Z converts to chunk Z with floor(Z / 16), including negative coordinates.",
    "chunk_x": "Chunk X coordinate. One chunk spans 16 blocks on the X axis; negative coordinates use floor division.",
    "chunk_z": "Chunk Z coordinate. One chunk spans 16 blocks on the Z axis; negative coordinates use floor division.",
    "center_chunk_x": "Chunk X at the center of the search area.",
    "center_chunk_z": "Chunk Z at the center of the search area.",
    "center_x": "Block X coordinate at the center of the search or analysis area.",
    "center_z": "Block Z coordinate at the center of the search or analysis area.",
    "origin_x": "Block X coordinate used as the starting reference point.",
    "origin_z": "Block Z coordinate used as the starting reference point.",
    "x": "Block X coordinate. Positive X is east; negative X is west.",
    "y": "Block Y coordinate. Larger values are higher; smaller values are deeper.",
    "z": "Block Z coordinate. Positive Z is south; negative Z is north.",
    "x1": "X coordinate of the first or starting position.",
    "y1": "Y coordinate of the first or starting position.",
    "z1": "Z coordinate of the first or starting position.",
    "x2": "X coordinate of the second or target position.",
    "y2": "Y coordinate of the second or target position.",
    "z2": "Z coordinate of the second or target position.",
    "dx": "Signed X offset from the starting position. Negative moves west; positive moves east.",
    "dy": "Signed vertical offset from the starting Y coordinate.",
    "dz": "Signed Z offset from the starting position. Negative moves north; positive moves south.",
    "other_x": "X coordinate of the other portal, waypoint, or comparison point.",
    "other_y": "Y coordinate of the other portal, waypoint, or comparison point.",
    "other_z": "Z coordinate of the other portal, waypoint, or comparison point.",
    "radius": "Radius from the selected center. Search tools scan within this distance; build radii determine the generated block geometry for shape tools.",
    "radius_step": "Amount added to the radius after an empty search pass. Smaller steps check distance more gradually; larger steps expand faster.",
    "max_search_radius": "Largest radius an expanding search may reach before stopping.",
    "width": "Horizontal width of the selected build, area, or layout, measured in blocks unless the label states another unit.",
    "length": "Horizontal length of the selected build, area, or layout, measured in blocks unless the label states another unit.",
    "height": "Vertical height of the selected build, area, or layout, measured in blocks unless the label states another unit.",
    "spacing": "Distance between repeated rows, supports, samples, or components. The field label identifies what is being spaced.",
    "sag": "Vertical drop from the endpoints to the lowest part of the hanging curve, measured in blocks.",
    "stops": "Route stops separated by semicolons. Format each stop as x,y,z,label, for example 80,64,0,Mine;120,70,50,Village.",
    "points": "Path points separated by semicolons. Format each point as x,y,z with an optional label when supported.",
    "sample_interval": "Seconds between recorded position samples. Lower values record a denser path.",
    "interval": "Seconds between repeated captures or actions.",
    "epsilon": "Maximum distance, in blocks, that counts as returning to the same place during loop detection.",
    "return_to_start": "Add a final route leg from the last destination back to the starting point.",
    "search_mode": "Radius Search checks one fixed area. Search Until Found expands the radius until it finds a match or reaches the stopping limit.",
    "ignore_max_generation_limit": "Allow an expanding generated-world search to continue beyond the configured radius limit. This can substantially increase CPU, memory, disk, and runtime use.",
    "regenerate_from_seed": "Create bounded reference chunks with the matching Minecraft Java server when no generated save is selected.",
    "accept_minecraft_eula": "Confirm the Minecraft EULA before F3+ launches the local server used to generate reference chunks.",
    "worldgen_max_chunks": "Safety budget for one reference-generation job, measured in chunks. Larger values require more CPU time, memory, and disk I/O.",
    "dimension": "Dimension used by the calculation: Overworld, Nether, or End where supported.",
    "target_biome": "Biome that the search should locate or use as its match condition.",
    "second_seed": "Second Java world seed used for comparison with the primary seed.",
    "simulation_distance": "Simulation distance in chunks used when modeling which nearby chunks are actively ticking.",
    "target_candidates": "Number of candidate locations the search should aim to return.",
    "probability": "Chance of one independent success from 0 to 1. For example, 0.05 means 5 percent.",
    "target_chance": "Desired chance for the named outcome, from 0 to 1 unless the field label explicitly uses percent.",
    "attempts": "Number of independent attempts, rolls, or trials included in the calculation.",
    "count": "Number of results, samples, predictions, or repetitions to produce.",
    "first": "First signed 32-bit value observed from java.util.Random.nextInt(), immediately followed by the value in Second.",
    "second": "Second consecutive signed 32-bit value observed from java.util.Random.nextInt().",
    "observed_long": "Signed 64-bit value observed from one java.util.Random.nextLong() call.",
    "state": "Internal 48-bit java.util.Random state used for gameplay RNG calculations.",
    "steps": "Number of Java RNG state transitions to move. Positive values advance; negative values rewind.",
    "item": "Minecraft item used by this calculation or simulator.",
    "items": "Total number of items included in the storage, transport, crafting, or logistics calculation.",
    "stack_size": "Maximum items per inventory stack. Common Minecraft stack sizes are 64, 16, and 1.",
    "shulkers": "Number of shulker boxes available. Each shulker box contains 27 inventory slots.",
    "units": "Number of plants, animals, machines, modules, or other repeated units named by this operation.",
    "hours": "Time value in hours unless the visible field label names a different cycle quantity.",
    "level": "Minecraft level or tier named by this field, such as XP, enchantment, beacon, or prior-work level.",
    "amount": "Quantity consumed, repaired, processed, produced, or measured by the selected calculation.",
    "speed": "Movement or processing speed in the units shown by the field label, commonly blocks per second.",
    "distance": "Distance in Minecraft blocks unless the field label states another unit.",
    "yaw": "Horizontal Minecraft facing angle in degrees using Java Edition yaw conventions.",
    "angle1": "Facing or bearing angle, in degrees, for the first triangulation observation.",
    "angle2": "Facing or bearing angle, in degrees, for the second triangulation observation.",
    "to_nether": "Turn on to convert Overworld X/Z to Nether scale by dividing by 8. Turn off for Nether-to-Overworld conversion by multiplying by 8.",
    "overworld_gain": "Overworld distance avoided or replaced when comparing Nether-assisted travel.",
    "nether_walk": "Distance traveled inside the Nether portion of the route.",
    "overworld_walk": "Additional distance traveled in the Overworld outside the Nether-assisted section.",
    "mc": "Minecraft generation-version value passed to the Cubiomes backend for this calculation.",
    "name": "Name saved with the waypoint, profile, route, or other object created by this action.",
    "new": "Replacement name to save for the selected object.",
    "waypoint": "Saved waypoint used by this action.",
}


LABEL_HELP = {
    "minecraft action/key": "Key or mouse binding held by the routine. Examples include w, space, f, mouse:left, and mouse:right.",
    "mouse button": "Mouse button clicked by each periodic action cycle.",
    "actions per cycle": "Number of mouse clicks performed each time the periodic timer fires.",
    "hold feed/use": "Keep the use button held while the livestock routine is active.",
    "growth cycle": "Minutes between livestock interaction cycles. Use this to match the breeding cooldown or growth timing of the animals being managed.",
    "swings per cycle": "Number of interaction swings sent during each livestock cycle.",
    "swing spacing": "Seconds between interaction swings within one livestock cycle.",
    "wait before reel": "Seconds between casting and the reel action in the timer-based fishing cycle.",
    "recast delay": "Seconds after reeling before the next cast is sent.",
    "sprint": "Hold the sprint input while the travel routine moves toward the destination.",
    "overworld destination x": "Overworld X coordinate of the destination. When traveling in the Nether, F3+ divides this coordinate by 8 before moving.",
    "overworld destination z": "Overworld Z coordinate of the destination. When traveling in the Nether, F3+ divides this coordinate by 8 before moving.",
    "current dimension": "Dimension the player is currently traveling in, used to decide whether Overworld destination coordinates need 8:1 Nether scaling.",
    "travel y": "Y coordinate used as the vertical destination for coordinate travel.",
    "target x": "Destination X coordinate for the coordinate travel routine.",
    "target y": "Destination Y coordinate for the coordinate travel routine.",
    "target z": "Destination Z coordinate for the coordinate travel routine.",
    "row/side travel time": "Seconds spent moving along each row or perimeter side in the timed construction path.",
    "row spacing time": "Seconds spent shifting sideways before beginning the next construction row.",
    "main tunnel spacing": "Blocks traveled along the main tunnel between successive branch entrances.",
    "branch depth": "Blocks traveled outward from the main tunnel before the branch miner turns back.",
    "branches": "Number of side branches the branch-mining routine should excavate.",
    "alternate sides": "Alternate left and right branch directions instead of placing every branch on the same side of the main tunnel.",
    "distance per step": "Forward block distance covered before each vertical stair step.",
    "descending": "Move the staircase downward when enabled; otherwise build or excavate upward.",
    "row distance": "Block distance excavated along each row of the area excavation pattern.",
    "row shift": "Block distance moved sideways between excavation rows.",
    "row travel time": "Seconds spent moving down each farming row.",
    "row shift time": "Seconds spent shifting sideways between farming rows.",
    "hold attack/harvest": "Hold attack while moving down a farming row so mature crops or plants are broken.",
    "hold use/replant": "Hold use while moving so the selected crop can be replanted when possible.",
    "bone meal clicks": "Number of bone-meal use clicks sent during each growth cycle.",
    "click delay": "Seconds between repeated bone-meal clicks.",
    "plant slot": "Hotbar slot containing the item to plant before bone meal is applied.",
    "bone meal slot": "Hotbar slot containing bone meal.",
    "crossbow slots": "Hotbar slots containing the crossbows included in the volley rotation.",
    "charge time": "Seconds the use button is held to charge each crossbow before firing.",
    "swap delay": "Seconds to wait after selecting the next crossbow before charging it.",
    "slots": "Hotbar slots visited by the workflow, in the order entered.",
    "delay between slots": "Seconds to wait after selecting one hotbar slot before moving to the next.",
    "loop": "Repeat the hotbar sequence after the final configured slot.",
    "tool slots": "Hotbar slots containing the tools included in the rotation.",
    "seconds per tool": "Seconds each tool remains selected before the next configured slot becomes active.",
    "hold attack": "Keep attack held while the selected tool is active.",
    "action": "Mouse action the guard routine should hold while its cycle limit is active.",
    "maximum status cycles": "Maximum automation status cycles allowed before the guard stops the held action.",
    "food slot": "Hotbar slot containing the food item selected before each eating attempt.",
    "eat every": "Seconds between automatic eating attempts.",
    "use duration": "Seconds to hold use during each eating attempt.",
    "swap key": "Minecraft key binding pressed to swap the main-hand and offhand items.",
    "swap interval": "Seconds between offhand swap-key presses.",
}


def _unit_from_label(low: str) -> str:
    if "chunk" in low:
        return "chunks"
    if "block" in low:
        return "blocks"
    if "second" in low or " sec" in low:
        return "seconds"
    if "tick" in low:
        return "ticks"
    if "degree" in low or "yaw" in low or "angle" in low:
        return "degrees"
    if "hour" in low:
        return "hours"
    if "percent" in low or "%" in low:
        return "percent"
    return "the unit shown by the field label"


def field_help(key: str, label: str = "") -> str:
    key = str(key)
    label_text = re.sub(r"\s+", " ", str(label or "")).strip()
    low = label_text.lower()

    if key == "seed":
        if any(token in low for token in ("simulation", "rng", "random", "reproduc")):
            return "Seed used to reproduce this simulator or RNG run. Numbers and text may be accepted by workbenches that say so."
        return "Java Edition world seed used by this world-generation calculation. Signed 64-bit numeric seeds are valid."

    direct_label = LABEL_HELP.get(low)
    if direct_label:
        return direct_label

    direct = FIELD_HELP.get(key)
    if direct:
        return direct

    if "radius" in low:
        return f"Radius for {label_text or 'this area'}, measured in {_unit_from_label(low)}."
    if "seed" in low:
        return f"Seed value used by {label_text or 'this calculation'} to produce repeatable results."
    if "chance" in low or "probability" in low or "odds" in low:
        return f"Probability for {label_text or 'this event'}. Use 0 to 1 unless the label explicitly states percent."
    if any(token in low for token in ("count", "pull", "attempt", "samples", "cycles")):
        return f"Number of {label_text or 'repetitions'} to process or return. Larger values usually require more computation."
    if any(token in low for token in ("path", "folder", "save")):
        return f"Local filesystem location for {label_text or 'the selected data source'}."
    if "spacing" in low:
        return f"Spacing for {label_text}, measured in {_unit_from_label(low)}."
    if any(token in low for token in ("width", "length", "height", "distance")):
        return f"{label_text or 'Dimension'} measured in {_unit_from_label(low)}."
    if "level" in low:
        return f"Minecraft level or tier for {label_text or 'this mechanic'}."
    if low == "x" or low.endswith(" x"):
        return "Minecraft X coordinate. Positive is east; negative is west."
    if low == "y" or low.endswith(" y"):
        return "Minecraft Y coordinate. Larger values are higher; smaller values are deeper."
    if low == "z" or low.endswith(" z"):
        return "Minecraft Z coordinate. Positive is south; negative is north."
    if "version" in low:
        return f"Minecraft version used for {label_text or 'this operation'}."
    if "item" in low or "material" in low:
        return f"Minecraft item or material selected for {label_text or 'this calculation'}."
    if label_text:
        return f"Set {label_text}. The accepted value type and default are shown with this control."
    return "Set this input using the value type and default shown with the control."
