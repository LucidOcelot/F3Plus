from __future__ import annotations

from .ui_theme import palette


def desktop_stylesheet(theme: str, custom: dict | None = None) -> str:
    """Additional 2.5 shell styles layered over the existing five themes."""
    p = palette(theme, custom)
    light = theme == "light"
    selected_text = "#FFFFFF" if light else p["text"]
    shadow = "rgba(0,0,0,22)" if light else "rgba(0,0,0,70)"
    return f"""
    QFrame#TopBar {{
        background: {p['surface']}; border: 0; border-bottom: 1px solid {p['border']};
    }}
    QFrame#StatusBar25 {{
        background: {p['surface2']}; border: 0; border-bottom: 1px solid {p['border']};
    }}
    QFrame#NavRail25 {{
        background: {p['surface']}; border: 0; border-right: 1px solid {p['border']};
    }}
    QFrame#WorkbenchCanvas {{
        background: {p['bg']}; border: 0;
    }}
    QFrame#Inspector25 {{
        background: {p['surface']}; border: 0; border-left: 1px solid {p['border']};
    }}
    QFrame#InspectorSection, QFrame#QuickStatusCard, QFrame#InputCard25 {{
        background: {p['surface2']}; border: 1px solid {p['border']}; border-radius: 10px;
    }}
    QFrame#InspectorSection:hover, QFrame#QuickStatusCard:hover {{ border-color: {p['glow']}; }}
    QLabel#HeroTitle25 {{ font-size: 22pt; font-weight: 850; color: {p['text']}; }}
    QLabel#SectionTitle25 {{ font-size: 13pt; font-weight: 800; color: {p['text']}; }}
    QLabel#Eyebrow25 {{ font-size: 8pt; font-weight: 800; letter-spacing: 1.4px; color: {p['muted']}; }}
    QLabel#StatusPillGood {{ background: {p['surface3']}; color: {p['success']}; border: 1px solid {p['success']}; border-radius: 9px; padding: 5px 9px; font-weight: 750; }}
    QLabel#StatusPillWarn {{ background: {p['surface3']}; color: {p['warning']}; border: 1px solid {p['warning']}; border-radius: 9px; padding: 5px 9px; font-weight: 750; }}
    QLabel#StatusPill {{ background: {p['surface3']}; color: {p['muted']}; border: 1px solid {p['border']}; border-radius: 9px; padding: 5px 9px; }}
    QLineEdit#GlobalSearch25 {{ min-height: 22px; padding: 8px 11px; border-radius: 9px; }}
    QListWidget#NavList25 {{ background: transparent; border: 0; outline: 0; padding: 4px; }}
    QListWidget#NavList25::item {{ padding: 9px 10px; margin: 2px 0; border-radius: 8px; color: {p['muted']}; }}
    QListWidget#NavList25::item:selected {{ background: {p['surface3']}; color: {p['text']}; border-left: 3px solid {p['primary']}; }}
    QListWidget#NavList25::item:hover {{ background: {p['surface2']}; color: {p['text']}; }}
    QListWidget#WorkbenchGrid {{ background: transparent; border: 0; outline: 0; }}
    QListWidget#WorkbenchGrid::item {{ background: transparent; border: 0; padding: 0; margin: 0; }}
    QListWidget#WorkbenchGrid::item:selected {{ background: transparent; border: 0; }}
    QPushButton#PrimaryAction25 {{ background: {p['primary']}; color: {selected_text}; border: 1px solid {p['primary']}; border-radius: 9px; padding: 9px 15px; font-weight: 800; }}
    QPushButton#PrimaryAction25:hover {{ border-color: {p['glow']}; background: {p['primary2']}; }}
    QPushButton#QuietAction25 {{ background: transparent; border: 1px solid {p['border']}; border-radius: 8px; padding: 7px 11px; color: {p['muted']}; }}
    QPushButton#QuietAction25:hover {{ background: {p['surface2']}; color: {p['text']}; border-color: {p['glow']}; }}
    QPushButton#Command25 {{ background: {p['surface3']}; border: 1px solid {p['border']}; border-radius: 8px; padding: 7px 11px; }}
    QPushButton#Command25:hover {{ border-color: {p['glow']}; }}
    QTextBrowser#InspectorGuide25, QTextBrowser#InspectorResult25 {{ background: transparent; border: 0; padding: 0; }}
    QComboBox#GroupFilter25 {{ min-width: 150px; }}
    QDialog#CommandPalette25 {{ background: {p['surface']}; }}
    QListWidget#PaletteList25 {{ background: {p['surface']}; border: 1px solid {p['border']}; border-radius: 9px; padding: 5px; }}
    QListWidget#PaletteList25::item {{ padding: 9px; margin: 2px; border-radius: 7px; }}
    QListWidget#PaletteList25::item:selected {{ background: {p['surface3']}; color: {p['text']}; }}
    QToolTip {{ background: {p['surface3']}; color: {p['text']}; border: 1px solid {p['glow']}; padding: 6px; }}
    """
