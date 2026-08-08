from __future__ import annotations

from . import macros


def line_steps(length_seconds: float = 0.25):
    return [{"type": "move", "key": "w", "seconds": length_seconds, "place": True}]


def rectangle_steps(side_seconds: float = 2.0):
    steps = []
    for _ in range(4):
        steps.append({"type": "move", "key": "w", "seconds": side_seconds, "place": True})
        steps.append({"type": "turn", "dx": 900})
    return steps


def serpentine_steps(rows: int = 4, row_seconds: float = 1.5, shift_seconds: float = 0.25, place_every_row: bool = True):
    steps = []
    direction = 1
    for row in range(max(1, int(rows))):
        steps.append({"type": "move", "key": "w", "seconds": row_seconds, "place": place_every_row or row % 2 == 0})
        if row == rows - 1:
            break
        steps.extend([
            {"type": "turn", "dx": 900 * direction},
            {"type": "move", "key": "w", "seconds": shift_seconds, "place": True},
            {"type": "turn", "dx": 900 * direction},
        ])
        direction *= -1
    return steps


def grid_steps(rows: int = 4, row_seconds: float = 1.5, spacing_seconds: float = 0.5):
    # First pass creates parallel rows. The second pass rotates 90 degrees and
    # creates a cross-hatched grid rather than reusing the filled-row sequence.
    return serpentine_steps(rows, row_seconds, spacing_seconds, True) + [
        {"type": "turn", "dx": 900},
        *serpentine_steps(rows, row_seconds, spacing_seconds, True),
    ]


def parallel_row_steps(rows: int = 4, row_seconds: float = 1.5, spacing_seconds: float = 0.5):
    return serpentine_steps(rows, row_seconds, spacing_seconds, True)


def alternating_steps(rows: int = 6, row_seconds: float = 1.5, spacing_seconds: float = 0.5):
    return serpentine_steps(rows, row_seconds, spacing_seconds, False)


PRESETS = {
    "Generator Miner": lambda e: macros.guarded_continuous(e, held_mouse=("left",), max_cycles=7200),
    "Hold Attack": lambda e: macros.continuous_action(e, held_mouse=("left",)),
    "Hold Use": lambda e: macros.continuous_action(e, held_mouse=("right",)),
    "Concrete Converter": lambda e: macros.continuous_action(e, held_mouse=("left", "right")),
    "Auto Walk": lambda e: macros.continuous_action(e, held_keys=("w",)),
    "Custom Hold": lambda e: macros.continuous_action(e, held_keys=("w",)),
    "Auto Attack": lambda e: macros.periodic_interaction(e, False, 1000),
    "AFK Mob Grinder": lambda e: macros.periodic_interaction(e, True, 1000),
    "Livestock Breeder": lambda e: macros.livestock_breeder(e, True, 20, 2, 1000),
    "Custom Periodic Action": lambda e: macros.periodic_interaction(e, False, 1000),
    "Auto Fishing": lambda e: macros.auto_fishing(e, 1200, 250),
    "Basic Travel": lambda e: macros.travel(e, ("w",)),
    "Sprint Travel": lambda e: macros.travel(e, ("w", "ctrl")),
    "Sprint-Jump Travel": lambda e: macros.travel(e, ("w", "ctrl"), 800),
    "Swim Travel": lambda e: macros.continuous_action(e, held_keys=("w", "ctrl", "space")),
    "Boat Travel": lambda e: macros.travel(e, ("w",)),
    "Horse/Camel Travel": lambda e: macros.travel(e, ("w", "ctrl")),
    "Elytra Launch": macros.elytra_launch,
    "Elytra Cruise": lambda e: macros.elytra_cruise(e, 10000),
    "Riptide Travel": lambda e: macros.riptide_travel(e, 850, 1600),
    "Spear Dash Travel": lambda e: macros.spear_dash_travel(e, 1, 2, 3, 120, 300, 1650),
    # The UI supplies real destinations for these three presets. These fallback
    # runners remain useful for programmatic callers that only request distance.
    "Coordinate Travel": lambda e: macros.coordinate_travel(e, 64.0),
    "Waypoint Travel": lambda e: macros.coordinate_travel(e, 64.0),
    "Nether-Assisted Travel": lambda e: macros.coordinate_travel(e, 64.0),
    "Tunnel Miner": lambda e: macros.tunnel_miner(e, 12000),
    "Branch Miner": lambda e: macros.coordinate_branch_miner(e, 4, 24, 900, 8, True),
    "Stair Excavator": lambda e: macros.coordinate_stair_excavator(e, 32, 1.0, True),
    "Area Excavator": lambda e: macros.coordinate_area_excavator(e, 8, 16, 1, 900),
    "Crop Farmer": lambda e: macros.crop_farmer(e, 12000),
    "Coordinate Row Farmer": lambda e: macros.row_farmer(e, 8, 10, 0.45, 900, True, True),
    "Multi-Row Farmer": lambda e: macros.row_farmer(e, 16, 10, 0.45, 900, True, True),
    "Bone Meal Farmer": lambda e: macros.bone_meal_farmer(e, 4, 150),
    "Stationary Grow/Harvest": lambda e: macros.bone_meal_farmer(e, 4, 150),
    "Tree Farm Cycle": macros.tree_farm_cycle,
    "Farm Station Controller": macros.tree_farm_cycle,
    "Mending Grinder": lambda e: macros.mending_grinder(e, 1250, 30000, (1, 2, 3)),
    "Crossbow Volley": lambda e: macros.crossbow_volley(e, 1300, 250, (1, 2, 3)),
    "Hotbar Workflow": lambda e: macros.hotbar_workflow(e, (1, 2, 3), 250, True),
    "Tool Rotation": lambda e: macros.tool_rotation(e, (1, 2, 3), 30, False),
    "Durability Guard": lambda e: macros.guarded_continuous(e, held_mouse=("left",), max_cycles=100),
    "Resource Guard": lambda e: macros.guarded_continuous(e, held_mouse=("right",), max_cycles=100),
    "Food Manager": lambda e: macros.food_manager(e, 2, 120, 1.65),
    "Offhand Workflow": lambda e: macros.offhand_workflow(e, "f", 30),
    "Line": lambda e: macros.construction_pattern(e, line_steps(), loop=True),
    "Rectangle": lambda e: macros.construction_pattern(e, rectangle_steps(), loop=False),
    "Filled Rectangle": lambda e: macros.construction_pattern(e, serpentine_steps(8, 1.5, 0.25, True), loop=False),
    "Grid": lambda e: macros.construction_pattern(e, grid_steps(6, 1.5, 0.5), loop=False),
    "Rows": lambda e: macros.construction_pattern(e, parallel_row_steps(8, 1.5, 0.5), loop=False),
    "Alternating Pattern": lambda e: macros.construction_pattern(e, alternating_steps(8, 1.5, 0.5), loop=False),
    "Perimeter": lambda e: macros.construction_pattern(e, rectangle_steps(), loop=False),
    "Repeating Segment": lambda e: macros.construction_pattern(e, line_steps(), loop=True),
    "Action Sequencer": lambda e: macros.route_runner(e, [{"type": "tap", "key": "space"}, {"type": "wait", "seconds": 0.1}], loop=True),
    "Route Runner": lambda e: macros.route_runner(e, [{"type": "hold", "key": "w", "seconds": 1}, {"type": "turn", "dx": 900}], loop=True),
}

MACRO_PRESETS = set(PRESETS)


def runner(name):
    return PRESETS.get(name)
