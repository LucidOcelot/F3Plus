from __future__ import annotations

"""Operation-specific parameter schemas that prevent category fallbacks leaking into UI.

A ``None`` return means the normal executor policy should choose the schema. An empty
list deliberately means the operation has no manual parameters.

Schemas in this module are part of the user-facing operation contract: every field
listed here must be consumed by the corresponding handler, and every value required by
that handler must be obtainable from the UI or from explicitly documented live state.
"""


_START_FIELDS = [
    ("x1", "Start X", 0.0, "float"),
    ("y1", "Start Y", 64.0, "float"),
    ("z1", "Start Z", 0.0, "float"),
]

_TARGET_FIELDS = [
    ("x2", "Target X", 100.0, "float"),
    ("y2", "Target Y", 64.0, "float"),
    ("z2", "Target Z", 100.0, "float"),
]


def _route_stops(label: str = "Stops"):
    return (
        "stops",
        f"{label} (x,y,z,label; ...)",
        "80,64,0,A;80,64,80,B;0,64,80,C",
        "text",
    )


def _recorded_points():
    return (
        "points",
        "Recorded points (x,y,z,label; ...)",
        "0,64,0,Start;16,64,0,P2;16,64,16,P3",
        "text",
    )


def fields_for(spec):
    top, sub, name = spec.top, spec.submenu, spec.name

    if top == "Navigation" and sub == "Position":
        if name in {"Capture Position", "Copy Sister Coordinates", "Save Sister Waypoint", "Current Position"}:
            return []
        if name == "Continuous Capture":
            return [("interval", "Capture interval (seconds)", 1.0, "float")]
        if name == "Distance Announcer":
            return [
                ("x1", "Current X", 0.0, "float"),
                ("y1", "Current Y", 64.0, "float"),
                ("z1", "Current Z", 0.0, "float"),
                ("x2", "Target X", 100.0, "float"),
                ("y2", "Target Y", 64.0, "float"),
                ("z2", "Target Z", 100.0, "float"),
            ]
        if name == "Bearing Lock":
            return [
                ("x1", "Current X", 0.0, "float"),
                ("z1", "Current Z", 0.0, "float"),
                ("x2", "Target X", 100.0, "float"),
                ("z2", "Target Z", 100.0, "float"),
            ]

    if top == "Navigation" and sub == "Coordinates":
        if name == "Coordinate Offset":
            return [
                ("x1", "Start X", 0.0, "float"),
                ("y1", "Start Y", 64.0, "float"),
                ("z1", "Start Z", 0.0, "float"),
                ("dx", "Offset X", 0.0, "float"),
                ("dy", "Offset Y", 0.0, "float"),
                ("dz", "Offset Z", 0.0, "float"),
            ]
        if name == "Coordinate History":
            return []

    if top == "Navigation" and sub == "Waypoints" and name == "Waypoint Groups":
        return []

    if top == "Navigation" and sub == "Routes":
        if name == "Coordinate Route":
            return [*_START_FIELDS, *_TARGET_FIELDS]
        if name == "Resource Route":
            return [*_START_FIELDS, _route_stops("Resource stops")]
        if name == "Structure Tour":
            return [
                *_START_FIELDS,
                _route_stops("Structure stops"),
                ("return_to_start", "Return to start", True, "bool"),
            ]
        if name == "Biome Expedition":
            return [*_START_FIELDS, _route_stops("Biome stops")]
        if name in {"Breadcrumb Recorder", "Expedition Recorder"}:
            return [
                _recorded_points(),
                ("sample_interval", "Sample interval (seconds)", 1.0, "float"),
            ]
        if name == "Survey Mode":
            return [
                *_START_FIELDS,
                ("radius", "Survey radius (blocks)", 128, "int"),
                ("spacing", "Sample spacing (blocks)", 32, "int"),
            ]
        if name == "Loop Detection":
            return [
                ("points", "Path points (x,y,z; ...)", "0,64,0;20,64,0;20,64,20;0,64,20;1,64,1", "text"),
                ("epsilon", "Revisit tolerance (blocks)", 4.0, "float"),
            ]

    if top == "Calculators" and sub == "Shapes":
        radius = ("radius", "Radius (blocks)", 8, "int")
        height = ("height", "Height (blocks)", 12, "int")
        if name in {"Circle", "Filled Circle", "Sphere", "Hollow Sphere", "Dome", "Hexagon", "Octagon", "Diamond", "Arch"}:
            return [radius]
        if name in {"Cylinder", "Cone", "Pyramid", "Double Helix"}:
            return [radius, height]
        if name in {"Spiral", "Helix"}:
            return [radius, height, ("secondary", "Turns", 2, "int")]
        if name == "Ellipse":
            return [radius, ("secondary", "Second radius (blocks)", 5, "int")]
        if name == "Rounded Rectangle":
            return [radius, ("secondary", "Straight section (blocks)", 5, "int")]

    if top == "Calculators" and sub == "Build":
        width = ("width", "Width (blocks)", 16, "int")
        length = ("length", "Length (blocks)", 20, "int")
        height = ("height", "Height (blocks)", 8, "int")
        spacing = ("spacing", "Spacing (blocks)", 4, "int")
        if name in {"Area", "Perimeter", "Foundation Planner"}:
            return [width, length]
        if name in {"Volume", "Surface Area", "Block Count", "Stacks", "Shulkers", "Double Chests"}:
            return [width, length, height]
        if name == "Stair Calculator":
            return [height, ("spacing", "Blocks forward per step", 4, "int")]
        if name == "Spiral Staircase Planner":
            return [width, height, ("spacing", "Steps per turn", 4, "int")]
        if name == "Catenary Calculator":
            return [length, height, ("sag", "Sag (blocks)", 4.0, "float")]
        if name == "Roof Pitch":
            return [width, height]
        if name in {"Wall Segments", "Bridge Span"}:
            return [width, length, spacing] if name == "Wall Segments" else [length, spacing]
        if name in {"Grid", "Lighting Grid", "Pillar Spacing", "Road Planner", "Crop Layout"}:
            return [width, length, spacing]
        if name == "Gradient Ratio":
            return [length, height]
        if name == "Chunk Grid Builder":
            return [width, length]
        if name == "Circle Layer Export":
            return [("width", "Circle radius (blocks)", 16, "int")]
        if name == "Beacon Offset":
            return [width, length, ("height", "Beacon tier (1-4)", 4, "int")]

    return None
