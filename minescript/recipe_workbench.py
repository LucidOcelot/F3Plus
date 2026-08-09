from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import zipfile

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QSpinBox, QSplitter, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt

from .villagers import installed_versions, preferred_texture_version


@dataclass(frozen=True)
class RecipeRecord:
    recipe_id: str
    recipe_type: str
    result_id: str
    result_count: float
    ingredients: tuple[tuple[str, ...], ...]
    raw: dict


def _clean(value) -> str:
    return str(value or "").removeprefix("minecraft:")


def _item_choices(value) -> tuple[str, ...]:
    if isinstance(value, str):
        return (_clean(value),)
    if isinstance(value, list):
        out = []
        for child in value: out.extend(_item_choices(child))
        return tuple(dict.fromkeys(out))
    if isinstance(value, dict):
        if "item" in value: return (_clean(value.get("item")),)
        if "id" in value: return (_clean(value.get("id")),)
        if "items" in value: return _item_choices(value.get("items"))
        if "tag" in value: return ("#" + _clean(value.get("tag")),)
    return tuple()


def _result_info(data: dict) -> tuple[str, float]:
    result = data.get("result", data.get("output", {}))
    if isinstance(result, str): return _clean(result), 1.0
    if isinstance(result, dict):
        item = _clean(result.get("id", result.get("item", result.get("name", ""))))
        count = result.get("count", 1)
        if isinstance(count, dict): count = count.get("value", 1)
        try: count = float(count)
        except (TypeError, ValueError): count = 1.0
        return item, max(0.000001, count)
    return "", 1.0


def _ingredients(data: dict) -> tuple[tuple[str, ...], ...]:
    if isinstance(data.get("ingredients"), list):
        return tuple(_item_choices(value) for value in data["ingredients"] if _item_choices(value))
    pattern = data.get("pattern")
    key = data.get("key", {})
    if isinstance(pattern, list) and isinstance(key, dict):
        rows = []
        for line in pattern:
            for symbol in str(line):
                if symbol == " ": continue
                choices = _item_choices(key.get(symbol))
                if choices: rows.append(choices)
        return tuple(rows)
    ingredient = data.get("ingredient")
    choices = _item_choices(ingredient)
    return (choices,) if choices else tuple()


class RecipeData:
    def __init__(self, selected_version: str):
        versions = installed_versions(); exact = next((name for name in versions if name.lower() == str(selected_version).lower()), None)
        self.source_version = exact or preferred_texture_version(selected_version)
        self.path: Path | None = versions.get(self.source_version) if self.source_version else None
        self.records: list[RecipeRecord] = []
        self.by_result: dict[str, list[RecipeRecord]] = {}
        self._load()

    @property
    def source(self):
        return self.source_version or "No installed Minecraft recipe data"

    def _load(self):
        if self.path is None: return
        try:
            with zipfile.ZipFile(self.path) as archive:
                for member in archive.namelist():
                    if not member.endswith(".json") or not ("/recipe/" in member or "/recipes/" in member): continue
                    if not member.startswith("data/"): continue
                    try: raw = json.loads(archive.read(member))
                    except (KeyError, json.JSONDecodeError, UnicodeError): continue
                    if not isinstance(raw, dict): continue
                    parts = member.split("/")
                    namespace = parts[1] if len(parts) > 2 else "minecraft"
                    folder = "recipe" if "recipe" in parts else "recipes"
                    try: index = parts.index(folder); name = "/".join(parts[index + 1:]).removesuffix(".json")
                    except ValueError: continue
                    result_id, result_count = _result_info(raw)
                    if not result_id: continue
                    record = RecipeRecord(f"{namespace}:{name}", str(raw.get("type", "recipe")), result_id, result_count, _ingredients(raw), raw)
                    self.records.append(record); self.by_result.setdefault(result_id, []).append(record)
        except (OSError, zipfile.BadZipFile): return
        self.records.sort(key=lambda row: (row.result_id, row.recipe_id))

    def search(self, text: str = "") -> list[RecipeRecord]:
        query = str(text or "").strip().lower()
        if not query: return list(self.records)
        return [row for row in self.records if query in (row.recipe_id + " " + row.result_id + " " + row.recipe_type).lower()]

    def recursive_bom(self, item: str, desired_count: float = 1.0, max_depth: int = 20) -> dict:
        totals: dict[str, float] = {}; intermediates: dict[str, float] = {}; unresolved: dict[str, float] = {}

        def expand(item_id: str, amount: float, depth: int, trail: tuple[str, ...]):
            recipes = self.by_result.get(_clean(item_id), [])
            if not recipes or depth >= max_depth or item_id in trail:
                totals[item_id] = totals.get(item_id, 0.0) + amount; return
            recipe = recipes[0]
            crafts = math.ceil(amount / max(recipe.result_count, 0.000001))
            intermediates[item_id] = intermediates.get(item_id, 0.0) + amount
            for choices in recipe.ingredients:
                choice = choices[0] if choices else ""
                if not choice: continue
                if choice.startswith("#"):
                    unresolved[choice] = unresolved.get(choice, 0.0) + crafts
                else:
                    expand(choice, crafts, depth + 1, trail + (item_id,))

        expand(_clean(item), max(0.0, float(desired_count)), 0, tuple())
        return {
            "target": _clean(item), "target_count": desired_count,
            "raw_materials": dict(sorted(totals.items())),
            "intermediates": dict(sorted(intermediates.items())),
            "unresolved_tags": dict(sorted(unresolved.items())),
            "source": self.source,
            "note": "For ingredients with alternatives F3+ chooses the first listed option. Tags remain unresolved because an exact material choice depends on the player's intended block/item palette.",
        }


class RecipeExplorerDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner); self.owner = owner; self.data = RecipeData(owner.settings.minecraft_version)
        self.setWindowTitle("Recipe & Material Explorer"); self.resize(1180, 780)
        root = QVBoxLayout(self)
        title = QLabel("Recipe & Material Explorer"); title.setObjectName("WorkspaceTitle"); root.addWidget(title)
        source = QLabel(f"Installed recipe data: {self.data.source} • {len(self.data.records)} recipes"); source.setObjectName("Muted"); root.addWidget(source)
        self.query = QLineEdit(); self.query.setPlaceholderText("Search result item, recipe ID or recipe type…"); self.query.setClearButtonEnabled(True); root.addWidget(self.query)
        split = QSplitter(Qt.Horizontal); root.addWidget(split, 1)
        self.list = QListWidget(); split.addWidget(self.list)
        right = QWidget(); rv = QVBoxLayout(right); self.detail = QTableWidget(0, 2); self.detail.setHorizontalHeaderLabels(["Ingredient slot", "Accepted item(s)"]); self.detail.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch); rv.addWidget(self.detail, 1)
        controls = QHBoxLayout(); self.count = QSpinBox(); self.count.setRange(1, 2_000_000_000); self.count.setValue(64); self.bom = QPushButton("Recursive material list"); controls.addWidget(QLabel("Target count")); controls.addWidget(self.count); controls.addWidget(self.bom); controls.addStretch(); rv.addLayout(controls)
        self.output = QTableWidget(0, 2); self.output.setHorizontalHeaderLabels(["Raw material / unresolved tag", "Amount"]); self.output.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch); rv.addWidget(self.output, 1); split.addWidget(right); split.setSizes([380, 800])
        self.query.textChanged.connect(self.refresh); self.list.itemSelectionChanged.connect(self.select); self.bom.clicked.connect(self.calculate); self.refresh()

    def refresh(self):
        selected = self.list.currentItem().data(Qt.UserRole) if self.list.currentItem() else ""; self.list.clear()
        rows = self.data.search(self.query.text())
        for row in rows:
            item = QListWidgetItem(f"{row.result_id} × {row.result_count:g}\n{row.recipe_id}"); item.setData(Qt.UserRole, row.recipe_id); self.list.addItem(item)
        if self.list.count():
            target = next((i for i in range(self.list.count()) if self.list.item(i).data(Qt.UserRole) == selected), 0); self.list.setCurrentRow(target)

    def current(self):
        item = self.list.currentItem()
        if not item: return None
        rid = item.data(Qt.UserRole); return next((row for row in self.data.records if row.recipe_id == rid), None)

    def select(self):
        row = self.current(); self.detail.setRowCount(0)
        if row is None: return
        self.detail.setRowCount(len(row.ingredients) + 2)
        self.detail.setItem(0, 0, QTableWidgetItem("Recipe type")); self.detail.setItem(0, 1, QTableWidgetItem(row.recipe_type))
        self.detail.setItem(1, 0, QTableWidgetItem("Result")); self.detail.setItem(1, 1, QTableWidgetItem(f"{row.result_count:g} {row.result_id}"))
        for i, choices in enumerate(row.ingredients, 1):
            self.detail.setItem(i + 1, 0, QTableWidgetItem(str(i))); self.detail.setItem(i + 1, 1, QTableWidgetItem(" | ".join(choices)))

    def calculate(self):
        row = self.current()
        if row is None: return
        report = self.data.recursive_bom(row.result_id, self.count.value()); lines = list(report["raw_materials"].items()) + list(report["unresolved_tags"].items()); self.output.setRowCount(len(lines))
        for i, (name, amount) in enumerate(lines):
            self.output.setItem(i, 0, QTableWidgetItem(name)); self.output.setItem(i, 1, QTableWidgetItem(f"{amount:g}"))
