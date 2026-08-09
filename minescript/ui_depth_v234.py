from __future__ import annotations

"""Shared UI depth pass for tool icons, configuration help, and visual/search guidance."""

import html


_FIELD_HELP = {
    "world_path": "Use an already-generated Java world save when you want F3+ to inspect real generated chunks instead of regenerating them from the seed.",
    "spawner_type": "Choose the mob/block-entity type to match. Cluster tools apply their cluster rule only to this filtered set.",
    "seed": "The Java world seed used by deterministic seed calculations or exact local reference generation.",
    "cx": "Chunk X at the center of the search. One chunk is 16×16 blocks.",
    "cz": "Chunk Z at the center of the search. One chunk is 16×16 blocks.",
    "x": "Block X at the center/reference point.",
    "z": "Block Z at the center/reference point.",
    "radius": "The first/bounded search radius. The unit shown in the label is authoritative; terrain/spawner searches use chunks while sampled biome searches use blocks.",
    "search_mode": "Radius search runs once inside the chosen radius. Search until found expands outward by the configured step until it finds a real match or reaches a stopping condition.",
    "radius_step": "How much the radius grows after each unsuccessful until-found attempt. Larger steps search farther faster but make the reported first-found radius coarser.",
    "max_search_radius": "Normal until-found searches stop at this radius. Enable the explicit ignore-limit toggle only when you intentionally want the search to continue beyond it.",
    "ignore_max_generation_limit": "When enabled, Search until found ignores the configured maximum radius. Exact regenerated-world searches also raise the per-attempt chunk budget as needed. This can consume substantial CPU, memory, disk space, and time.",
    "regenerate_from_seed": "When no save is selected, allow F3+ to run Mojang's matching Java server locally to materialize exact chunks for generated-world inspection.",
    "accept_minecraft_eula": "Required only for local Mojang reference-world generation. Enabling this records your explicit acceptance for the temporary server run.",
    "worldgen_max_chunks": "Normal safety budget for exact reference-world generation. Unbounded until-found mode can explicitly bypass this value when the ignore-limit toggle is enabled.",
    "dimension": "Minecraft dimension used by the selected calculation. Some exact regeneration workflows are Overworld-only and will explain that limitation before running.",
    "target_biome": "Biome target used by the search. The result should show the translated biome name; numeric IDs remain secondary technical data.",
}


def field_help(key: str, label: str = "") -> str:
    return _FIELD_HELP.get(str(key), f"Input used by this tool: {label}" if label else "")


def visual_tool(spec) -> bool:
    top = getattr(spec, "top", "")
    submenu = getattr(spec, "submenu", "")
    if top == "Seed Tools":
        return True
    return top in {"Calculators", "Wizards"} and submenu in {"Build", "Shapes", "Farm", "Technical"}


def task_art_key(spec) -> str:
    from .tool_guides import nav_section, workspace_group

    group = workspace_group(spec)
    if group == "Generated Spawners":
        return "spawner"
    if group in {"Find Biomes", "Terrain & Biome Regions"}:
        return "biome"
    if group in {"Nether Portals", "Nether Generation & Portals", "Portal Setups"}:
        return "portal"
    if group in {"Routes & Surveys", "Live Position", "Coordinate Math & Chunking", "Find Structures", "Structure Relationships & Scoring", "World Evaluation", "Local Area Reports"}:
        return "map"
    if group in {"Shape Layouts", "Build Infrastructure", "Materials & Dimensions", "Construction", "Building Setups"}:
        return "shape"
    if group in {"Farm Systems", "Yield & Breeding", "Technical Farm Planning", "Farming & Stations", "Farm Setups"}:
        return "farm"
    if group == "Redstone & Timing":
        return "redstone"
    if group in {"Storage & Logistics", "Equipment & Inventory"}:
        return "storage"
    if group in {"Browse Trades", "Trade Planning", "Professions", "Curing, Breeding & Halls"}:
        return "trade"
    if nav_section(spec) == "RNG":
        return "rng"
    if nav_section(spec) == "Safety":
        return "safety"
    if nav_section(spec) == "Utilities":
        return "utilities"
    if nav_section(spec) == "Automation":
        return "automation"
    return "chorus_flower"


def install() -> None:
    from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QLabel, QVBoxLayout

    from . import app as app_module
    from .app import F3Plus, ValuesDialog
    from .search_modes_v234 import IGNORE_LIMIT_KEY, supports_search_mode

    if getattr(F3Plus, "_ui_depth_v234_installed", False):
        return

    # The app imported tool_art_key by value, so replace the app-module binding too.
    app_module.tool_art_key = task_art_key

    previous_values_init = ValuesDialog.__init__

    def values_init(self, title, fields, parent=None, subtitle=""):
        previous_values_init(self, title, fields, parent, subtitle)
        field_map = {str(key): (str(label), widget) for (key, label, _default, _kind), widget in zip(fields, [self.inputs.get(f[0]) for f in fields]) if widget is not None}
        for key, (label, widget) in field_map.items():
            tip = field_help(key, label)
            if tip:
                widget.setToolTip(tip)
                widget.setAccessibleDescription(tip)

        mode_widget = self.inputs.get("search_mode")
        ignore_widget = self.inputs.get(IGNORE_LIMIT_KEY)
        if isinstance(ignore_widget, QCheckBox):
            ignore_widget.setText("Continue beyond the configured maximum")

        if isinstance(mode_widget, QComboBox):
            card = QFrame()
            card.setObjectName("WarningBanner")
            box = QVBoxLayout(card)
            box.setContentsMargins(10, 8, 10, 8)
            kicker = QLabel("SEARCH BEHAVIOR")
            kicker.setObjectName("DeckLabel")
            box.addWidget(kicker)
            self._search_help = QLabel()
            self._search_help.setWordWrap(True)
            self._search_help.setObjectName("Muted")
            box.addWidget(self._search_help)
            # Insert below the dialog heading/subtitle and above the scrollable form.
            layout = self.layout()
            insert_at = max(0, min(3, layout.count() - 1))
            layout.insertWidget(insert_at, card)

            def sync():
                until_found = mode_widget.currentText() == "Search until found"
                ignore = bool(ignore_widget.isChecked()) if isinstance(ignore_widget, QCheckBox) else False
                for key in ("radius_step", "max_search_radius", IGNORE_LIMIT_KEY):
                    widget = self.inputs.get(key)
                    if widget is not None:
                        widget.setEnabled(until_found)
                max_widget = self.inputs.get("max_search_radius")
                if max_widget is not None and until_found:
                    max_widget.setEnabled(not ignore)
                worldgen_widget = self.inputs.get("worldgen_max_chunks")
                if worldgen_widget is not None:
                    worldgen_widget.setEnabled(not (until_found and ignore))

                if not until_found:
                    text = "Runs one bounded search inside the selected radius. Expansion controls are disabled because they do not affect this mode."
                elif ignore:
                    text = (
                        "Expands outward until a real match is found and ignores the configured maximum radius. For exact regenerated-world searches, the chunk-generation budget is also raised as needed. "
                        "This can become extremely expensive; backend errors and an internal runaway-loop guard can still stop the process."
                    )
                else:
                    text = "Expands outward by the selected step after each empty result and stops at the configured maximum radius. The result records every attempted radius and where the first match was found."
                self._search_help.setText(text)

            mode_widget.currentTextChanged.connect(lambda *_: sync())
            if isinstance(ignore_widget, QCheckBox):
                ignore_widget.toggled.connect(lambda *_: sync())
            sync()

    ValuesDialog.__init__ = values_init

    previous_guide_html = F3Plus._guide_html

    def guide_html(self, spec, guide, restriction=None):
        base = previous_guide_html(self, spec, guide, restriction)
        additions = []
        if supports_search_mode(spec):
            additions.append(
                ("Search controls",
                 "Radius search checks one bounded area. Search until found expands the radius after empty results. The maximum-radius control provides the normal stopping boundary; the explicit ignore-limit toggle removes that configured boundary and, when exact local world generation is required, also bypasses the configured chunk budget. Use the override knowingly because work grows rapidly with radius.")
            )
        if visual_tool(spec):
            additions.append(
                ("Visual result",
                 "When spatial data exists, Results includes an interactive X/Z view. Use the mouse wheel to zoom, drag to pan, Fit to restore the full extent, toggle individual layers/grid/point labels, inspect cursor coordinates, and copy the currently visible coordinate layers. The visual is a navigation/planning aid; the structured result remains the authoritative numeric output.")
            )
        if getattr(spec, "submenu", "") == "Spawners":
            additions.append(
                ("Spawner data",
                 "Spawner searches inspect generated Anvil/NBT data. Mob filters use EntityId, SpawnData, and SpawnPotentials when present. Double/triple/quad tools look for clusters after the mob filter is applied; a single matching spawner is not a successful double/triple/quad result.")
            )
        if getattr(spec, "top", "") == "Villager Explorer":
            additions.append(
                ("Villager artwork & data",
                 "Profession navigation uses villager skin layers recovered from the installed Java client rather than workstation blocks. Trade definitions are versioned separately; if no usable installed trade JSON exists, F3+ labels the non-exact planning baseline instead of presenting it as selected-version truth.")
            )
        if not additions:
            return base
        colors = __import__("minescript.ui_theme", fromlist=["palette"]).palette(self.settings.theme, self.settings.custom_palette)
        extra = "".join(
            f"<h3 style='color:{colors['accent']}'>{html.escape(title)}</h3><p>{html.escape(text)}</p>"
            for title, text in additions
        )
        marker = "</div>"
        return base.replace(marker, extra + marker, 1) if marker in base else base + extra

    F3Plus._guide_html = guide_html

    previous_init = F3Plus.__init__
    previous_selection = F3Plus.selection_changed

    def f3_init(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        try:
            self.guide_btn.setIcon(self._art_icon("map", 18))
            self.guide_btn.setToolTip("Open the full explanation, inputs, output semantics, search behavior, and limitations for the selected tool.")
            self.results_btn.setIcon(self._art_icon("chorus_calc", 18))
            self.results_btn.setToolTip("Open structured results and any interactive map/plan visualization produced by the selected tool.")
        except Exception:
            pass

    def selection_changed(self):
        previous_selection(self)
        spec = self.selected_spec()
        if spec is None:
            return
        try:
            self.run_btn.setIcon(self._art_icon(task_art_key(spec), 18))
            self.run_btn.setToolTip("Configure and run this tool. The icon reflects the tool family rather than using one generic action symbol.")
        except Exception:
            pass

    F3Plus.__init__ = f3_init
    F3Plus.selection_changed = selection_changed
    F3Plus._ui_depth_v234_installed = True
