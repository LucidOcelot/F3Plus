from __future__ import annotations

"""Villager profession portraits recovered from the player's installed Minecraft JAR.

The trade explorer previously represented professions with workstation block textures.
This layer uses the villager entity/type/profession skin layers instead, while keeping
an original F3+ villager icon as the fallback when no usable client artwork is present.
"""


def profession_texture_members(profession: str) -> tuple[str, ...]:
    clean = str(profession or "none").strip().lower().replace(" ", "_")
    return (
        "assets/minecraft/textures/entity/villager/villager.png",
        "assets/minecraft/textures/entity/villager/type/plains.png",
        f"assets/minecraft/textures/entity/villager/profession/{clean}.png",
    )


def install() -> None:
    from PySide6.QtCore import QRect, QSize, Qt
    from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
    from PySide6.QtWidgets import QFrame, QLabel, QListWidget, QListWidgetItem, QVBoxLayout

    from .pixel_art import icon_pixmap
    from .villager_explorer import MinecraftTextureProvider, VillagerExplorer
    from .villagers import PROFESSIONS

    if getattr(VillagerExplorer, "_villager_portraits_v234_installed", False):
        return

    def _read_image(provider: MinecraftTextureProvider, member: str) -> QImage | None:
        data = provider._read([member])
        if not data:
            return None
        image = QImage()
        if not image.loadFromData(data):
            return None
        return image

    def profession_portrait(self: MinecraftTextureProvider, profession: str, size: int = 42) -> QPixmap:
        key = (f"villager_profession:{profession}", int(size))
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        members = profession_texture_members(profession)
        layers = [_read_image(self, member) for member in members]
        layers = [layer for layer in layers if layer is not None]
        if not layers:
            pix = icon_pixmap("villager", self.colors, size)
            self.cache[key] = pix
            return pix

        # Build a small front-facing portrait from the conventional villager texture
        # UVs. Profession/type PNGs are transparent overlays, so drawing the same UV
        # regions in order produces the visible robe/head treatment rather than a
        # workstation surrogate.
        canvas = QImage(32, 42, QImage.Format_ARGB32_Premultiplied)
        canvas.fill(Qt.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing, False)
        for image in layers:
            # Torso/front robe.
            painter.drawImage(QRect(8, 19, 16, 21), image, QRect(20, 20, 8, 12))
            # Front of the head.
            painter.drawImage(QRect(6, 2, 20, 20), image, QRect(8, 8, 8, 8))
            # Hat/head overlay when present in the profession/type layer.
            painter.drawImage(QRect(5, 1, 22, 22), image, QRect(40, 8, 8, 8))
        painter.end()

        pix = QPixmap.fromImage(canvas).scaled(int(size), int(size), Qt.KeepAspectRatio, Qt.FastTransformation)
        if pix.isNull():
            pix = icon_pixmap("villager", self.colors, size)
        self.cache[key] = pix
        return pix

    def profession_icon(self: MinecraftTextureProvider, profession: str, size: int = 36) -> QIcon:
        return QIcon(self.profession_portrait(profession, size))

    MinecraftTextureProvider.profession_portrait = profession_portrait
    MinecraftTextureProvider.profession_icon = profession_icon

    def profession_panel(self: VillagerExplorer):
        frame = QFrame()
        frame.setObjectName("ExplorerRail")
        layout = QVBoxLayout(frame)
        label = QLabel("PROFESSIONS")
        label.setObjectName("DeckLabel")
        layout.addWidget(label)

        note = QLabel("Villager portraits use skin layers from your installed Java client when available.")
        note.setObjectName("Muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.profession_list = QListWidget()
        self.profession_list.setObjectName("ProfessionList")
        self.profession_list.setIconSize(QSize(38, 38))

        all_item = QListWidgetItem("All professions")
        all_item.setData(Qt.UserRole, "")
        all_item.setIcon(QIcon(self.textures.profession_portrait("none", 38)))
        all_item.setToolTip("Show trades from every villager profession.")
        self.profession_list.addItem(all_item)

        for profession in PROFESSIONS:
            item = QListWidgetItem(profession.title())
            item.setData(Qt.UserRole, profession)
            item.setIcon(self.textures.profession_icon(profession, 38))
            item.setToolTip(
                f"{profession.title()} villager — portrait recovered from installed villager skin layers when available."
            )
            self.profession_list.addItem(item)
        layout.addWidget(self.profession_list, 1)
        return frame

    VillagerExplorer._profession_panel = profession_panel
    VillagerExplorer._villager_portraits_v234_installed = True
