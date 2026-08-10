from __future__ import annotations

import re
from typing import Any

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QScrollArea,
    QSpinBox, QVBoxLayout, QWidget,
)


FIELD_HELP = {
    "world_path": "Existing Java Edition world/save folder to inspect. Choose a generated save when you need observed blocks/entities rather than seed-placement candidates.",
    "cx": "Chunk X coordinate at the center of the operation. One chunk is 16 blocks wide.",
    "cz": "Chunk Z coordinate at the center of the operation. One chunk is 16 blocks wide.",
    "chunk_x": "Chunk X coordinate at the center of the operation.",
    "chunk_z": "Chunk Z coordinate at the center of the operation.",
    "x": "Minecraft block X coordinate (east/west axis).",
    "y": "Minecraft block Y coordinate (vertical axis).",
    "z": "Minecraft block Z coordinate (north/south axis).",
    "x1": "X coordinate of the starting/current position.",
    "y1": "Y coordinate of the starting/current position.",
    "z1": "Z coordinate of the starting/current position.",
    "x2": "X coordinate of the target/second position.",
    "y2": "Y coordinate of the target/second position.",
    "z2": "Z coordinate of the target/second position.",
    "dx": "Signed X offset added to the starting coordinate; negative moves west and positive moves east.",
    "dy": "Signed vertical offset added to the starting Y coordinate.",
    "dz": "Signed Z offset added to the starting coordinate; negative moves north and positive moves south.",
    "radius": "Search/build radius. The visible label states whether this operation measures it in blocks or chunks.",
    "width": "Horizontal build width in blocks.",
    "length": "Horizontal build length/span in blocks.",
    "height": "Vertical build height in blocks unless the visible label names a mechanic-specific meaning.",
    "spacing": "Distance between repeated elements/samples/supports. The visible label states the unit and role for this operation.",
    "sag": "Vertical drop from the endpoints toward the center of the hanging catenary curve.",
    "secondary": "Second operation-specific dimension/count. Its visible label identifies the exact meaning; it is not a generic hidden parameter.",
    "stops": "Route destinations separated by semicolons. Each destination is x,y,z,label, for example 80,64,0,Mine;120,70,50,Village.",
    "points": "Recorded path points separated by semicolons. Each point is x,y,z with an optional label when the selected operation supports labels.",
    "sample_interval": "Seconds between recorded position samples. Smaller values create a denser recorded path.",
    "interval": "Seconds between repeated captures/actions for this operation.",
    "epsilon": "Maximum distance between non-adjacent path points that counts as revisiting the same place during loop detection.",
    "return_to_start": "Adds a final route leg from the last destination back to the start.",
    "search_mode": "Radius search checks one bounded area. Search until found expands outward after an empty result until a match or stopping condition.",
    "radius_step": "Additional radius added after each empty Search until found attempt.",
    "max_search_radius": "Normal maximum radius for Search until found before F3+ reports no match in the allowed area.",
    "ignore_max_generation_limit": "Allows Search until found to continue beyond the configured maximum. Exact generation can consume substantial CPU, RAM, disk space and time.",
    "regenerate_from_seed": "Generate bounded reference chunks using Mojang's matching Java server when no existing save is selected.",
    "accept_minecraft_eula": "Required acknowledgement before F3+ can launch Mojang's server locally to generate reference chunks.",
    "worldgen_max_chunks": "Safety budget for exact Mojang reference generation. Larger values may require substantially more disk, CPU and time.",
    "dimension": "Minecraft dimension whose coordinates/generation rules are used by the selected operation.",
    "target_biome": "Biome the search should attempt to find or compare.",
    "world": "World/save path used by the selected operation.",
    "probability": "Chance of one independent success expressed from 0 to 1 (0.05 = 5%).",
    "target_chance": "Chance of the target outcome in one independent attempt, expressed from 0 to 1.",
    "attempts": "Number of independent attempts/rolls used when calculating cumulative odds or a sequence.",
    "count": "Number of outputs/results to generate or inspect.",
    "first": "First observed signed 32-bit output from java.util.Random.nextInt(). It must be immediately followed by the second observation.",
    "second": "Second consecutive signed 32-bit output from java.util.Random.nextInt().",
    "observed_long": "Observed signed 64-bit value returned by one java.util.Random.nextLong() call.",
    "state": "Recovered/internal 48-bit java.util.Random state. This is gameplay RNG state, not a Minecraft world seed.",
    "steps": "How many Java LCG state transitions to advance (positive) or rewind (negative) before showing outputs.",
    "item": "Minecraft item used by the selected mechanic. Dedicated simulator workbenches provide visual item pickers when applicable.",
    "items": "Total item count being converted into storage/logistics requirements.",
    "stack_size": "Maximum items per inventory stack for the selected material (commonly 64, 16, or 1).",
    "shulkers": "Number of shulker boxes available for the transport/storage plan.",
    "units": "Number of plants, animals, machines, modules, or other units named by this operation.",
    "hours": "Planning duration/cycle quantity named by the operation; read the field label where the mechanic uses a different unit.",
    "level": "Minecraft level/tier used by the selected calculation.",
    "amount": "Quantity consumed, repaired, processed, or otherwise measured by this operation.",
    "speed": "Travel/processing speed in the units stated by the visible field label.",
    "distance": "Distance in Minecraft blocks unless the visible field label states otherwise.",
}


def field_help(key: str, label: str = "") -> str:
    key = str(key); label_text = str(label or "").strip(); low = label_text.lower()

    # The same historical key is used by world-generation and simulation tools. The
    # label is therefore part of the public semantic contract.
    if key == "seed":
        if any(token in low for token in ("simulation", "rng", "random", "reproduc")):
            return "Deterministic simulator/RNG seed used to reproduce this calculation. It is not the Minecraft world seed."
        return "Known Java Edition world seed used by deterministic world-generation calculations or bounded reference generation."
    if key in {"cx", "cz", "chunk_x", "chunk_z"} and "radius" in low:
        return "Chunk coordinate used to center the bounded search area. You can use the shared Search Center panel instead where available."
    if key == "mc":
        return "Cubiomes Minecraft-version constant used only by the supported native backend. Prefer the normal Minecraft Version setting unless you specifically need a backend-level query."

    direct = FIELD_HELP.get(key)
    if direct:
        return direct

    # Meaningful label-driven fallback for compatibility fields not yet given a stable
    # key. This avoids the old non-explanation: 'Value used by this operation'.
    if "radius" in low:
        unit = "chunks" if "chunk" in low else "blocks"
        return f"Radius of the area this operation examines, measured in {unit}. Larger radii require more work."
    if "seed" in low:
        return "Deterministic seed used by the calculation. The label/context determines whether this is a world-generation seed or a simulator reproducibility seed."
    if "chance" in low or "probability" in low:
        return "Probability of the named event for one attempt. Enter the value in the format implied by the control/label (normally 0–1 for F3+ probability fields)."
    if "count" in low or "pull" in low or "attempt" in low:
        return "Number of repetitions/results requested. Larger values improve statistical sample size but take longer to compute."
    if "path" in low or "folder" in low or "save" in low:
        return "Local path used as the data source for this operation. F3+ reads it locally and does not modify the Minecraft world unless the operation explicitly states otherwise."
    if "x" == low or low.endswith(" x"):
        return "Minecraft X coordinate (east/west)."
    if "y" == low or low.endswith(" y"):
        return "Minecraft Y coordinate (vertical)."
    if "z" == low or low.endswith(" z"):
        return "Minecraft Z coordinate (north/south)."
    cleaned = re.sub(r"\s+", " ", label_text).strip()
    if cleaned:
        return f"{cleaned} used by this specific operation. Change it only when you want to alter the named part of the calculation."
    return "Operation-specific input. Its meaning is defined by the selected operation rather than by a shared generic calculator field."


def make_widget(kind: str, default: Any):
    if kind == "int":
        widget = QSpinBox(); widget.setRange(-2_147_483_647, 2_147_483_647); widget.setValue(int(default))
    elif kind == "float":
        widget = QDoubleSpinBox(); widget.setDecimals(6); widget.setRange(-1e12, 1e12); widget.setValue(float(default))
    elif kind == "bool":
        widget = QCheckBox(); widget.setChecked(bool(default))
    elif kind == "choice":
        widget = QComboBox(); widget.addItems([str(value) for value in default])
    else:
        widget = QLineEdit(str(default))
    return widget


def widget_value(widget):
    if isinstance(widget, (QSpinBox, QDoubleSpinBox)): return widget.value()
    if isinstance(widget, QCheckBox): return widget.isChecked()
    if isinstance(widget, QComboBox): return widget.currentText()
    return widget.text()


class ParameterDialog(QDialog):
    """Reusable inline-explained editor for small operation schemas."""

    def __init__(self, title: str, fields, parent=None, subtitle: str = "", run_label: str = "Run"):
        super().__init__(parent)
        self.setWindowTitle(title); self.resize(620, 560); self.inputs: dict[str, QWidget] = {}
        root = QVBoxLayout(self); heading = QLabel(title); heading.setObjectName("WorkspaceTitle"); root.addWidget(heading)
        if subtitle:
            note = QLabel(subtitle); note.setWordWrap(True); note.setObjectName("Muted"); root.addWidget(note)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        host = QWidget(); form = QFormLayout(host); form.setHorizontalSpacing(18); form.setVerticalSpacing(12); form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow); scroll.setWidget(host); root.addWidget(scroll, 1)
        for key, label, default, kind in fields:
            widget = make_widget(kind, default); tip = field_help(str(key), str(label)); widget.setToolTip(tip); widget.setAccessibleDescription(tip); self.inputs[str(key)] = widget
            column = QWidget(); column_layout = QVBoxLayout(column); column_layout.setContentsMargins(0, 0, 0, 0); column_layout.setSpacing(3); column_layout.addWidget(widget)
            hint = QLabel(tip); hint.setWordWrap(True); hint.setObjectName("Muted"); column_layout.addWidget(hint); form.addRow(str(label), column)

        self.search_card = QFrame(); self.search_card.setObjectName("WarningBanner"); card = QVBoxLayout(self.search_card); card.setContentsMargins(10, 8, 10, 8); kicker = QLabel("SEARCH BEHAVIOR"); kicker.setObjectName("DeckLabel"); card.addWidget(kicker); self.search_help = QLabel(); self.search_help.setWordWrap(True); self.search_help.setObjectName("Muted"); card.addWidget(self.search_help); root.insertWidget(2 if subtitle else 1, self.search_card); self.search_card.setVisible("search_mode" in self.inputs)

        mode = self.inputs.get("search_mode"); ignore = self.inputs.get("ignore_max_generation_limit")
        if isinstance(mode, QComboBox): mode.currentTextChanged.connect(lambda *_: self._sync_search())
        if isinstance(ignore, QCheckBox): ignore.setText("Continue beyond the configured maximum"); ignore.toggled.connect(lambda *_: self._sync_search())
        self._sync_search()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); buttons.button(QDialogButtonBox.Ok).setText(run_label); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def _sync_search(self):
        mode = self.inputs.get("search_mode")
        if not isinstance(mode, QComboBox): return
        until = mode.currentText() == "Search until found"; ignore = self.inputs.get("ignore_max_generation_limit"); unlimited = bool(ignore.isChecked()) if isinstance(ignore, QCheckBox) else False
        for key in ("radius_step", "max_search_radius", "ignore_max_generation_limit"):
            widget = self.inputs.get(key)
            if widget is not None: widget.setEnabled(until)
        maximum = self.inputs.get("max_search_radius")
        if maximum is not None and until: maximum.setEnabled(not unlimited)
        budget = self.inputs.get("worldgen_max_chunks")
        if budget is not None: budget.setEnabled(not (until and unlimited))
        if not until: text = "Runs one bounded search inside the selected radius. Expansion controls do not affect this mode."
        elif unlimited: text = "Expands until a real match is found while ignoring the configured maximum. Exact generation can consume substantial CPU, memory, disk space and time; backend errors and the runaway guard can still stop it."
        else: text = "Expands outward by the selected step after each empty result and stops at the configured maximum radius."
        self.search_help.setText(text)

    def values(self) -> dict[str, Any]: return {key: widget_value(widget) for key, widget in self.inputs.items()}
