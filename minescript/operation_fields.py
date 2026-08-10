from __future__ import annotations

"""Operation-specific parameter schemas that prevent category fallbacks leaking into UI.

A ``None`` return means the normal executor policy should choose the schema. An empty
list deliberately means the operation has no manual parameters.
"""


def fields_for(spec):
    top, sub, name = spec.top, spec.submenu, spec.name

    if top == "Navigation" and sub == "Position":
        if name in {"Capture Position", "Copy Sister Coordinates", "Save Sister Waypoint", "Current Position"}:
            return []
        if name == "Continuous Capture":
            return [("interval", "Capture interval (seconds)", 1.0, "float")]
        if name == "Distance Announcer":
            return [
                ("x1", "Current X", 0.0, "float"), ("y1", "Current Y", 64.0, "float"), ("z1", "Current Z", 0.0, "float"),
                ("x2", "Target X", 100.0, "float"), ("y2", "Target Y", 64.0, "float"), ("z2", "Target Z", 100.0, "float"),
            ]
        if name == "Bearing Lock":
            return [
                ("x1", "Current X", 0.0, "float"), ("z1", "Current Z", 0.0, "float"),
                ("x2", "Target X", 100.0, "float"), ("z2", "Target Z", 100.0, "float"),
            ]

    if top == "Navigation" and sub == "Coordinates":
        if name == "Coordinate Offset":
            return [
                ("x1", "Start X", 0.0, "float"), ("y1", "Start Y", 64.0, "float"), ("z1", "Start Z", 0.0, "float"),
                ("dx", "Offset X", 0.0, "float"), ("dy", "Offset Y", 0.0, "float"), ("dz", "Offset Z", 0.0, "float"),
            ]
        if name == "Coordinate History":
            return []

    if top == "Navigation" and sub == "Waypoints" and name == "Waypoint Groups":
        return []

    if top == "Navigation" and sub == "Routes":
        if name == "Loop Detection":
            return [("epsilon", "Revisit tolerance (blocks)", 4.0, "float")]
        if name in {"Coordinate Route", "Resource Route", "Structure Tour", "Biome Expedition", "Expedition Recorder", "Survey Mode", "Breadcrumb Recorder"}:
            return [
                ("x1", "Start X", 0.0, "float"), ("y1", "Start Y", 64.0, "float"), ("z1", "Start Z", 0.0, "float"),
                ("x2", "Target X", 100.0, "float"), ("y2", "Target Y", 64.0, "float"), ("z2", "Target Z", 100.0, "float"),
            ]

    return None
