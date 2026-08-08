from __future__ import annotations
from dataclasses import dataclass


RELATIVE_MOUSE_MACROS = {
    "Branch Miner", "Area Excavator", "Coordinate Row Farmer", "Multi-Row Farmer",
    "Rectangle", "Filled Rectangle", "Grid", "Rows", "Alternating Pattern", "Perimeter",
    "Route Runner",
}

MOUSE_BUTTON_MACROS = {
    "Generator Miner","Hold Attack","Hold Use","Concrete Converter","Auto Attack","AFK Mob Grinder",
    "Livestock Breeder","Custom Periodic Action","Auto Fishing","Elytra Launch","Elytra Cruise",
    "Riptide Travel","Spear Dash Travel","Tunnel Miner","Branch Miner","Stair Excavator","Area Excavator",
    "Crop Farmer","Coordinate Row Farmer","Multi-Row Farmer","Bone Meal Farmer","Stationary Grow/Harvest",
    "Tree Farm Cycle","Farm Station Controller","Mending Grinder","Crossbow Volley","Durability Guard",
    "Resource Guard","Food Manager","Line","Rectangle","Filled Rectangle","Grid","Rows",
    "Alternating Pattern","Perimeter","Repeating Segment","Route Runner",
}


@dataclass(frozen=True)
class MacroRequirements:
    keyboard: bool = True
    mouse_buttons: bool = False
    relative_mouse: bool = False


def requirements_for_macro(name: str) -> MacroRequirements:
    return MacroRequirements(True, name in MOUSE_BUTTON_MACROS, name in RELATIVE_MOUSE_MACROS)


def focus_issue(name: str, capabilities, target_minimized: bool | None=False) -> str | None:
    req=requirements_for_macro(name)
    reasons=[]
    if getattr(capabilities,"all_input_requires_focus",False):
        reasons.append("this desktop session requires Minecraft to be focused for automation")
    if req.relative_mouse and not getattr(capabilities,"targeted_relative_mouse",False):
        reasons.append("this macro turns the camera, and relative mouse movement requires Minecraft focus")
    if target_minimized and not getattr(capabilities,"minimized",False):
        reasons.append("the linked Minecraft window is minimized and this backend cannot target it while minimized")
    if reasons:return "; ".join(dict.fromkeys(reasons))
    return None
