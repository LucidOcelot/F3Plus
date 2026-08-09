from __future__ import annotations

import math


def _redstone(spec, p):
    n = spec.name
    if spec.submenu != "Redstone":
        return None
    value = max(0.0, float(p.get("value", 0)))
    secondary = max(0.0, float(p.get("secondary", 0)))
    if n == "Repeater Delay":
        setting = max(1, min(4, int(round(value))))
        count = max(1, int(round(secondary)))
        redstone_ticks = setting * count
        return {"operation": n, "repeaters": count, "setting_redstone_ticks_each": setting, "total_redstone_ticks": redstone_ticks, "game_ticks": redstone_ticks * 2, "seconds": redstone_ticks * 0.1}
    if n == "Observer Delay":
        observers = max(1, int(round(value)))
        # One observer pulse is two game ticks (one redstone tick). Chaining observers
        # is therefore modelled explicitly instead of reusing repeater settings.
        return {"operation": n, "observers": observers, "delay_game_ticks": observers * 2, "delay_redstone_ticks": observers, "seconds": observers * 0.1, "note": "Models a simple serial observer chain; circuit topology can add other delays."}
    if n == "Pulse Extender":
        base = value
        extension = secondary
        total = base + extension
        return {"operation": n, "base_pulse_redstone_ticks": base, "extension_redstone_ticks": extension, "output_redstone_ticks": total, "output_seconds": total * 0.1, "note": "Timing arithmetic only; component-specific pulse-extender topology is user supplied."}
    if n == "Clock Period":
        on = value; off = secondary
        return {"operation": n, "on_redstone_ticks": on, "off_redstone_ticks": off, "period_redstone_ticks": on + off, "period_seconds": (on + off) * 0.1, "frequency_hz": 1.0 / max(1e-9, (on + off) * 0.1)}
    if n == "Counter Timing":
        events = max(1, int(round(value))); interval = secondary
        return {"operation": n, "events": events, "interval_redstone_ticks": interval, "elapsed_redstone_ticks": events * interval, "elapsed_seconds": events * interval * 0.1}
    if n == "Signal Timing":
        return {"operation": n, "redstone_ticks": value, "game_ticks": value * 2.0, "seconds": value * 0.1}
    return None


def _farm_and_technical(spec, p):
    n = spec.name
    if n == "Beacon Coverage":
        level = max(1, min(4, int(p.get("spacing", 4))))
        radius = 10 + level * 10
        return {"operation": n, "beacon_level": level, "effect_radius_blocks": radius, "diameter_blocks": radius * 2 + 1, "square_footprint_blocks": (radius * 2 + 1) ** 2, "note": "Horizontal planning footprint for a standard beacon level; vertical/effect behavior still follows the selected Minecraft version."}
    if n == "Tree Yield":
        trees = max(0, int(p.get("units", 0))); cycles = max(0.0, float(p.get("hours", 0)))
        return {"operation": n, "trees": trees, "cycles": cycles, "planning_logs_per_tree": 4.0, "estimated_logs": trees * cycles * 4.0, "note": "Explicit planning assumption of four logs/tree. Species, growth shape and harvesting method change real yield."}
    if n == "Crop Yield":
        plants = max(0, int(p.get("units", 0))); harvests = max(0.0, float(p.get("hours", 0)))
        mean = max(0.0, float(p.get("yield_per_plant", 2.5)))
        return {"operation": n, "plants": plants, "harvests": harvests, "planning_yield_per_plant": mean, "estimated_items": plants * harvests * mean, "note": "User-facing planning mean; this is not presented as a universal crop drop table."}
    if n == "Sugar Cane Layout":
        plants = max(0, int(p.get("units", 0))); spacing = max(1, int(p.get("spacing", 1)))
        return {"operation": n, "plants": plants, "water_edge_positions_required": plants, "linear_spacing": spacing, "planned_length_blocks": max(0, (plants - 1) * spacing + 1), "note": "Layout count only; each cane position still requires valid adjacent water/placement conditions."}
    if n == "Bamboo Layout":
        plants = max(0, int(p.get("units", 0))); spacing = max(1, int(p.get("spacing", 1)))
        side = math.ceil(math.sqrt(plants)) if plants else 0
        return {"operation": n, "plants": plants, "spacing": spacing, "grid_side_positions": side, "footprint_side_blocks": max(0, (side - 1) * spacing + 1)}
    if n == "Crop Row Calculator":
        plants = max(0, int(p.get("units", 0))); spacing = max(1, int(p.get("spacing", 1)))
        row_length = max(1, int(round(math.sqrt(max(1, plants)))))
        rows = math.ceil(plants / row_length) if plants else 0
        return {"operation": n, "plants": plants, "plants_per_row": row_length, "rows": rows, "row_spacing": spacing}
    if n in {"Farm Separation", "Iron Farm Spacing", "Villager Gossip Radius", "Raid Distance"}:
        requested = max(0.0, float(p.get("value", 0))); secondary = max(0.0, float(p.get("secondary", 0)))
        actual = math.hypot(requested, secondary)
        note = {
            "Farm Separation": "General geometric planner; individual farms have mechanic/version-specific interference rules.",
            "Iron Farm Spacing": "No universal safe spacing is fabricated here. Treat the requested spacing as your design requirement and verify the selected-version village/iron-golem mechanics.",
            "Villager Gossip Radius": "Planning radius only; gossip/village behavior is mechanic-specific and not represented as one universal Euclidean constant.",
            "Raid Distance": "Planning distance only; raid center/POI rules are version-specific and should be validated for the selected version.",
        }[n]
        return {"operation": n, "requested_x_offset": requested, "requested_z_offset": secondary, "geometric_distance": actual, "note": note}
    if n == "Material Progress":
        target = max(0.0, float(p.get("target", p.get("amount", 0)))); current = max(0.0, float(p.get("current", p.get("hours", 0))))
        return {"operation": n, "target": target, "current": current, "remaining": max(0.0, target - current), "percent": 100.0 if target == 0 else min(100.0, current / target * 100.0)}
    if n == "Resource Goal Calculator":
        target = max(0.0, float(p.get("target", p.get("amount", 0)))); current = max(0.0, float(p.get("current", 0))); rate = max(0.0, float(p.get("rate_per_hour", p.get("hours", 0))))
        remaining = max(0.0, target - current)
        return {"operation": n, "target": target, "current": current, "remaining": remaining, "rate_per_hour": rate, "hours_remaining": remaining / rate if rate > 0 else None}
    return None


def _wizard_fields(name):
    if "Branch" in name:
        return [("spacing", "Branch spacing", 4, "int"), ("depth", "Branch depth", 32, "int"), ("branches", "Branches", 8, "int"), ("torch_spacing", "Torch spacing", 12, "int")]
    if "Quarry" in name:
        return [("width", "Width", 16, "int"), ("length", "Length", 16, "int"), ("depth", "Depth", 16, "int")]
    if "Perimeter" in name:
        return [("width", "Width", 256, "int"), ("length", "Length", 256, "int"), ("depth", "Depth", 64, "int")]
    if "Crop" in name:
        return [("rows", "Rows", 8, "int"), ("row_length", "Row length", 32.0, "float")]
    if "Tree" in name:
        return [("sapling_slot", "Sapling hotbar slot", 1, "int"), ("bonemeal_slot", "Bone meal hotbar slot", 2, "int"), ("tool_slot", "Tool hotbar slot", 3, "int")]
    if "Villager" in name:
        return [("villagers", "Villagers", 20, "int"), ("spacing", "Station spacing", 1, "int")]
    if "Highway" in name:
        return [("x1", "Start X", 0.0, "float"), ("y1", "Start Y", 64.0, "float"), ("z1", "Start Z", 0.0, "float"), ("x2", "Destination X", 8000.0, "float"), ("y2", "Destination Y", 64.0, "float"), ("z2", "Destination Z", 0.0, "float"), ("speed", "Nether travel speed", 72.7, "float")]
    if "Asymmetric" in name:
        return [("stages", "Portal stages", 6, "int")]
    if "Portal" in name:
        return [("portals", "Portal count", 4, "int")]
    if "Build Material" in name:
        return [("width", "Width", 16, "int"), ("length", "Length", 16, "int"), ("height", "Height", 8, "int")]
    if "Lighting" in name:
        return [("width", "Width", 32, "int"), ("length", "Length", 32, "int"), ("spacing", "Light spacing", 8, "int")]
    if "Beacon" in name:
        return [("beacons", "Beacon count", 4, "int"), ("levels", "Pyramid level", 4, "int")]
    return []


def install() -> None:
    from .feature_executor import FeatureExecutor
    from .navigation.routes import Point, greedy_route
    from .qa_features import navigation as qa_navigation
    from . import wizards

    if getattr(FeatureExecutor, "_catalog_direct_installed", False):
        return
    old_navigation = FeatureExecutor._navigation
    old_calculator = FeatureExecutor._calculator
    old_wizard = FeatureExecutor._wizard
    old_fields = FeatureExecutor.input_fields

    def navigation(self, spec, p):
        n = spec.name
        if n in {"Multi-stop Route", "Breadcrumb Simplifier"}:
            value = qa_navigation(n, p)
            return self._result(spec, "ok", value or {"available": False, "reason": "No valid route points supplied."})
        if n in {"Nearest Waypoint", "Sort Waypoints by Distance", "Waypoint Route"}:
            settings = getattr(self, "settings", None)
            saved = dict(getattr(settings, "waypoints", {}) or {}) if settings is not None else {}
            if not saved:
                return self._result(spec, "unavailable", {"requires_saved_waypoints": True, "reason": "Save at least one waypoint in F3+ before running this waypoint operation."})
            origin = Point(float(p.get("x1", 0)), float(p.get("y1", 64)), float(p.get("z1", 0)), "Current")
            points = [Point(float(v[0]), float(v[1]), float(v[2]), name) for name, v in saved.items()]
            route = greedy_route(origin, points)
            rows = [{"name": q.name, "x": q.x, "y": q.y, "z": q.z} for q in route["route"][1:]]
            if n == "Nearest Waypoint": rows = rows[:1]
            if n == "Sort Waypoints by Distance":
                rows = sorted(rows, key=lambda q: math.dist((origin.x, origin.y, origin.z), (q["x"], q["y"], q["z"])))
            return self._result(spec, "ok", {"operation": n, "distance": route["distance"], "waypoints": rows, "source": "Settings.waypoints"})
        return old_navigation(self, spec, p)

    def calculator(self, spec, p):
        value = _redstone(spec, p)
        if value is None:
            value = _farm_and_technical(spec, p)
        if value is not None:
            return self._result(spec, "ok", value)
        return old_calculator(self, spec, p)

    def wizard(self, spec, p):
        n = spec.name
        if "Branch" in n: data = wizards.branch_mine(p.get("spacing",4), p.get("depth",32), p.get("branches",8), p.get("torch_spacing",12))
        elif "Quarry" in n: data = wizards.quarry(p.get("width",16), p.get("length",16), p.get("depth",16))
        elif "Perimeter" in n: data = wizards.perimeter(p.get("width",256), p.get("length",256), p.get("depth",64))
        elif "Crop" in n: data = wizards.crop(p.get("rows",8), p.get("row_length",32))
        elif "Tree" in n: data = wizards.tree(p.get("sapling_slot",1), p.get("bonemeal_slot",2), p.get("tool_slot",3))
        elif "Villager" in n: data = wizards.villager_hall(p.get("villagers",20), p.get("spacing",1))
        elif "Highway" in n:
            start=(p.get("x1",0),p.get("y1",64),p.get("z1",0)); dest=(p.get("x2",8000),p.get("y2",64),p.get("z2",0)); data=wizards.nether_highway(start,dest,p.get("speed",72.7))
        elif "Asymmetric" in n: data = wizards.asymmetric_portal(p.get("stages",6))
        elif "Portal" in n: data = wizards.portal_network(p.get("portals",4))
        elif "Lighting" in n: data = wizards.lighting(p.get("width",32),p.get("length",32),p.get("spacing",8))
        elif "Beacon" in n: data = wizards.beacon_network(p.get("beacons",4),p.get("levels",4))
        elif "Build Material" in n: data = wizards.build_material(p.get("width",16),p.get("length",16),p.get("height",8))
        else: return old_wizard(self, spec, p)
        return self._result(spec, "ok", data)

    def fields(self, feature):
        spec = self.spec(feature)
        if spec.top == "Wizards" or spec.name.endswith("Wizard") or spec.name.endswith("Setup"):
            schema = _wizard_fields(spec.name)
            if schema:
                return schema
        if spec.top == "Navigation" and spec.name in {"Multi-stop Route", "Breadcrumb Simplifier"}:
            if spec.name == "Breadcrumb Simplifier":
                return [("points", "Points x,y,z separated by ;", "0,64,0;8,64,0;16,64,0;16,64,8", "text"), ("tolerance", "Simplification tolerance", 2.0, "float")]
            return [("x1", "Start X", 0.0, "float"), ("y1", "Start Y", 64.0, "float"), ("z1", "Start Z", 0.0, "float"), ("stops", "Stops x,y,z,name separated by ;", "80,64,0,A;80,64,80,B;0,64,80,C", "text"), ("return_to_start", "Return to start", False, "bool")]
        if spec.name == "Material Progress":
            return [("target", "Target item count", 10000.0, "float"), ("current", "Current item count", 2500.0, "float")]
        if spec.name == "Resource Goal Calculator":
            return [("target", "Target item count", 10000.0, "float"), ("current", "Current item count", 2500.0, "float"), ("rate_per_hour", "Collection rate/hour", 1000.0, "float")]
        return old_fields(self, feature)

    FeatureExecutor._navigation = navigation
    FeatureExecutor._calculator = calculator
    FeatureExecutor._wizard = wizard
    FeatureExecutor.input_fields = fields
    FeatureExecutor._catalog_direct_installed = True
