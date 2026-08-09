from __future__ import annotations

"""Color tokens and Qt stylesheet generation for F3+.

Every native Qt container/view gets an explicit surface and foreground. This avoids
platform palette leakage (especially Windows light QList/QScrollArea viewports) when
F3+ is using one of its dark themes.
"""

CHORUS = {
    "primary": "#7B3FF2", "primary2": "#5A27B5", "accent": "#D9B64C", "accent2": "#4388FF",
    "glow": "#9A72FF", "bg": "#08060C", "surface": "#120B1B", "surface2": "#1B1028",
    "surface3": "#29183D", "text": "#F7F3FF", "muted": "#BBAED0", "border": "#50366B",
    "success": "#68D898", "warning": "#E4C35D", "danger": "#FF667A",
}

LIGHT = {
    "primary": "#356FE8", "primary2": "#2454B8", "accent": "#B88617", "accent2": "#7354D8",
    "glow": "#4A86FF", "bg": "#EEF4FC", "surface": "#FFFFFF", "surface2": "#F1F6FD",
    "surface3": "#DDE9FA", "text": "#162033", "muted": "#5D6C85", "border": "#B8C7DE",
    "success": "#267D50", "warning": "#946A00", "danger": "#B83B50",
}

CYBERPUNK = {
    "primary": "#F6E600", "primary2": "#C9BD00", "accent": "#00DDEA", "accent2": "#FF315F",
    "glow": "#00EAF7", "bg": "#08090B", "surface": "#101217", "surface2": "#191C22",
    "surface3": "#242832", "text": "#F3F5F7", "muted": "#A4ADBB", "border": "#3A404C",
    "success": "#57E389", "warning": "#F6E600", "danger": "#FF3855",
}

MINECRAFT = {
    "primary": "#5F9F43", "primary2": "#3F702D", "accent": "#E5BC50", "accent2": "#9B6743",
    "glow": "#47C6CF", "bg": "#0D120E", "surface": "#182019", "surface2": "#233026",
    "surface3": "#304133", "text": "#F3F0E7", "muted": "#B8BCAA", "border": "#566151",
    "success": "#68C95A", "warning": "#E5BC50", "danger": "#C84A45",
}

DEFAULT_CUSTOM_PALETTE = {
    "primary": "#7A5CFF", "primary2": "#5B42C7", "accent": "#E0B84E", "accent2": "#3DC7D3",
    "glow": "#8AA4FF", "bg": "#0B0D12", "surface": "#151922", "surface2": "#202635",
    "surface3": "#2B3346", "text": "#F4F6FB", "muted": "#A5AFC2", "border": "#46516A",
    "success": "#58D69A", "warning": "#E0B84E", "danger": "#FF6678",
}

PALETTES = {
    "chorus": CHORUS,
    "light": LIGHT,
    "cyberpunk": CYBERPUNK,
    "minecraft": MINECRAFT,
    "custom": DEFAULT_CUSTOM_PALETTE,
}

COLOR_KEYS = tuple(DEFAULT_CUSTOM_PALETTE)


def palette(theme: str = "chorus", custom: dict | None = None) -> dict[str, str]:
    if theme == "custom":
        out = dict(DEFAULT_CUSTOM_PALETTE)
        if isinstance(custom, dict):
            for key in COLOR_KEYS:
                value = custom.get(key)
                if isinstance(value, str) and value.strip():
                    out[key] = value.strip()
        return out
    return dict(PALETTES.get(theme, CHORUS))


def stylesheet(theme: str = "chorus", custom: dict | None = None) -> str:
    p = palette(theme, custom)
    cyber = theme == "cyberpunk"
    minecraft = theme == "minecraft"
    light = theme == "light"

    if cyber:
        radius, card_radius = 2, 3
        top_bg = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0A0B0D,stop:.60 #111319,stop:1 #181A20)"
        rail_bg = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #121418,stop:.70 #0A0B0D,stop:1 #050607)"
        primary_text = selected_text = "#090A0C"
        title_family = "'Bahnschrift SemiCondensed','Segoe UI',sans-serif"
        card_border = p["accent"]
    elif minecraft:
        radius, card_radius = 4, 5
        top_bg = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #172318,stop:.55 #253526,stop:1 #172219)"
        rail_bg = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #273329,stop:.55 #182019,stop:1 #101611)"
        primary_text = selected_text = "#F8F6ED"
        title_family = "'Segoe UI Semibold','Segoe UI',sans-serif"
        card_border = p["accent2"]
    elif light:
        radius, card_radius = 7, 9
        top_bg = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #FFFFFF,stop:.65 #F3F7FD,stop:1 #E7F0FC)"
        rail_bg = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #FFFFFF,stop:1 #E9F1FB)"
        primary_text = selected_text = "#FFFFFF"
        title_family = "'Segoe UI Semibold','Segoe UI',sans-serif"
        card_border = p["accent"]
    else:
        radius, card_radius = 7, 9
        top_bg = f"qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {p['surface']},stop:.62 {p['surface2']},stop:1 {p['bg']})"
        rail_bg = f"qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {p['surface2']},stop:1 {p['bg']})"
        primary_text = selected_text = "#FFFFFF"
        title_family = "'Segoe UI Semibold','Segoe UI',sans-serif"
        card_border = p["accent"]

    return f"""
    * {{ font-family: 'Segoe UI', 'Inter', 'SF Pro Text', sans-serif; font-size: 10.25pt; }}

    QMainWindow, QDialog {{ background: {p['bg']}; color: {p['text']}; }}
    QWidget {{ color: {p['text']}; }}
    QWidget#AppRoot {{ background: {p['bg']}; color: {p['text']}; }}
    QWidget#OptionsPage {{ background: {p['surface']}; color: {p['text']}; }}
    QLabel, QCheckBox, QRadioButton {{ color: {p['text']}; background: transparent; }}

    QMenuBar {{ background: {p['bg']}; color: {p['muted']}; padding: 3px 8px; border-bottom: 1px solid {p['border']}; }}
    QMenuBar::item {{ padding: 5px 9px; }}
    QMenuBar::item:selected, QMenu::item:selected {{ background: {p['surface3']}; color: {p['text']}; }}
    QMenu {{ background: {p['surface']}; color: {p['text']}; border: 1px solid {p['border']}; padding: 6px; }}

    QFrame#CommandDeck {{ background: {top_bg}; border: 0; border-bottom: 2px solid {p['primary']}; }}
    QFrame#ContextDeck {{ background: {p['surface']}; border: 0; border-bottom: 1px solid {p['border']}; }}
    QFrame#NavRail {{ background: {rail_bg}; border: 0; border-right: 1px solid {p['border']}; }}
    QFrame#LibraryPane, QFrame#InspectorPane {{ background: {p['surface']}; border: 1px solid {p['border']}; border-radius: {card_radius}px; }}
    QFrame#StatusCard {{ background: {p['surface2']}; border: 1px solid {card_border}; border-radius: {radius}px; }}
    QFrame#InspectorHero, QFrame#ExplorerHero {{ background: {p['surface2']}; border-left: 3px solid {p['primary']}; border-radius: {radius}px; }}
    QFrame#ExplorerFilters, QFrame#ExplorerRail, QFrame#ExplorerTrades, QFrame#TradeDetail,
    QFrame#ResultCard, QFrame#ResultSection, QFrame#ToolConfigCard {{ background: {p['surface']}; border: 1px solid {p['border']}; border-radius: {card_radius}px; }}
    QFrame#TradeCard {{ background: {p['surface2']}; border: 1px solid {p['border']}; border-radius: {card_radius}px; }}
    QFrame#TradeStack, QFrame#TradeTransaction, QFrame#DetailStack, QFrame#ResultMetric {{ background: {p['surface2']}; border: 1px solid {p['border']}; border-radius: {radius}px; }}
    QFrame#WarningBanner {{ background: {p['surface3']}; border: 1px solid {p['warning']}; border-left: 4px solid {p['warning']}; border-radius: {radius}px; }}

    QLabel#AppTitle {{ font-family: {title_family}; font-size: 24pt; font-weight: 900; letter-spacing: 1.2px; color: {p['text']}; }}
    QLabel#AppSubtitle {{ color: {p['muted']}; font-size: 8.75pt; }}
    QLabel#DeckLabel {{ color: {p['muted']}; font-size: 8pt; font-weight: 700; letter-spacing: 1.5px; }}
    QLabel#WorkspaceTitle {{ font-family: {title_family}; font-size: 20pt; font-weight: 800; }}
    QLabel#DetailTitle {{ font-family: {title_family}; font-size: 20pt; font-weight: 850; }}
    QLabel#Muted {{ color: {p['muted']}; }}
    QLabel#Accent {{ color: {p['accent']}; font-weight: 750; }}
    QLabel#StatusGood {{ color: {p['success']}; font-weight: 700; }}
    QLabel#StatusWarn {{ color: {p['warning']}; font-weight: 700; }}
    QLabel#StatusBad {{ color: {p['danger']}; font-weight: 700; }}
    QLabel#VersionChip {{ background: {p['surface3']}; border: 1px solid {p['border']}; border-radius: {radius}px; padding: 5px 9px; color: {p['muted']}; }}
    QLabel#WarningChip {{ background: {p['surface3']}; border: 1px solid {p['warning']}; border-radius: {radius}px; padding: 5px 9px; color: {p['warning']}; font-weight: 700; }}
    QLabel#TradeLevel {{ color: {p['accent']}; font-weight: 800; }}
    QLabel#TradeOperator, QLabel#TradeArrow {{ color: {p['accent']}; font-size: 18pt; font-weight: 800; }}
    QLabel#MetricValue {{ font-family: {title_family}; font-size: 18pt; font-weight: 850; color: {p['text']}; }}
    QLabel#MetricLabel {{ color: {p['muted']}; font-size: 8.5pt; font-weight: 700; }}

    QPushButton {{ background: {p['surface2']}; border: 1px solid {p['border']}; border-radius: {radius}px; padding: 7px 12px; color: {p['text']}; font-weight: 650; }}
    QPushButton:hover {{ background: {p['surface3']}; border-color: {p['glow']}; }}
    QPushButton:pressed {{ background: {p['primary2']}; color: {selected_text}; }}
    QPushButton:disabled {{ color: {p['muted']}; background: {p['surface']}; border-color: {p['border']}; }}
    QPushButton#PrimaryButton {{ background: {p['primary']}; border-color: {p['primary']}; color: {primary_text}; font-weight: 800; padding: 9px 15px; }}
    QPushButton#PrimaryButton:hover {{ border-color: {p['glow']}; }}
    QPushButton#DangerButton {{ background: {p['danger']}; border-color: {p['danger']}; color: #FFFFFF; font-weight: 800; }}
    QPushButton#AccentButton {{ border-color: {p['accent']}; color: {p['accent']}; }}
    QPushButton#SafeModeButton {{ border-color: {p['warning']}; color: {p['warning']}; font-weight: 750; }}
    QPushButton#SafeModeButton:checked {{ background: {p['warning']}; color: #101114; border-color: {p['warning']}; }}
    QPushButton#SegmentButton {{ border-radius: {radius}px; padding: 7px 16px; }}
    QPushButton#SegmentButton:checked {{ background: {p['primary2']}; border-color: {p['glow']}; color: {selected_text}; }}

    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextBrowser, QTableWidget {{
        background: {p['surface2']}; color: {p['text']}; border: 1px solid {p['border']};
        border-radius: {radius}px; padding: 7px; selection-background-color: {p['primary2']};
        selection-color: {selected_text};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {p['glow']}; }}
    QComboBox::drop-down {{ border: 0; width: 24px; }}
    QComboBox QAbstractItemView {{ background: {p['surface']}; color: {p['text']}; selection-background-color: {p['surface3']}; selection-color: {p['text']}; border: 1px solid {p['border']}; }}
    QCheckBox::indicator {{ width: 15px; height: 15px; background: {p['surface2']}; border: 1px solid {p['border']}; border-radius: 3px; }}
    QCheckBox::indicator:checked {{ background: {p['primary']}; border-color: {p['glow']}; }}
    QCheckBox:disabled {{ color: {p['muted']}; }}

    QTabWidget::pane {{ background: {p['surface']}; border: 1px solid {p['border']}; border-radius: {radius}px; top: -1px; }}
    QTabWidget QStackedWidget > QWidget {{ background: {p['surface']}; color: {p['text']}; }}
    QTabBar::tab {{ background: {p['surface2']}; color: {p['muted']}; border: 1px solid {p['border']}; padding: 8px 14px; min-width: 92px; }}
    QTabBar::tab:selected {{ background: {p['surface3']}; color: {p['text']}; border-bottom-color: {p['primary']}; }}
    QTabBar::tab:hover {{ border-color: {p['glow']}; color: {p['text']}; }}

    QAbstractItemView {{
        background-color: {p['surface']}; color: {p['text']}; border: 1px solid {p['border']};
        outline: 0; selection-background-color: {p['surface3']}; selection-color: {p['text']};
    }}
    QListView, QTreeView, QTableView, QListWidget, QTableWidget {{
        background-color: {p['surface']}; color: {p['text']}; border: 1px solid {p['border']};
        alternate-background-color: {p['surface2']}; selection-background-color: {p['surface3']};
        selection-color: {p['text']}; outline: 0;
    }}
    QListView::item, QTreeView::item, QListWidget::item {{ color: {p['text']}; background-color: {p['surface']}; padding: 7px; }}
    QListView::item:selected, QTreeView::item:selected, QListWidget::item:selected {{ background-color: {p['surface3']}; color: {p['text']}; }}
    QListView::item:hover, QTreeView::item:hover, QListWidget::item:hover {{ background-color: {p['surface2']}; color: {p['text']}; }}

    /* These named lists used to be transparent. Windows can paint their internal
       viewport with the native light palette, so give the list itself a real surface. */
    QListWidget#NavList {{ background-color: {p['bg']}; color: {p['text']}; border: 0; outline: 0; }}
    QListWidget#ToolList, QListWidget#TradeCardList, QListWidget#CompareList, QListWidget#ProfessionList {{ background-color: {p['surface']}; color: {p['text']}; border: 0; outline: 0; }}
    QListWidget#NavList QWidget#qt_scrollarea_viewport {{ background-color: {p['bg']}; }}
    QListWidget#ToolList QWidget#qt_scrollarea_viewport,
    QListWidget#TradeCardList QWidget#qt_scrollarea_viewport,
    QListWidget#CompareList QWidget#qt_scrollarea_viewport,
    QListWidget#ProfessionList QWidget#qt_scrollarea_viewport {{ background-color: {p['surface']}; }}
    QListWidget#NavList::item, QListWidget#ProfessionList::item {{ padding: 10px 10px; margin: 2px 5px; border-radius: {radius}px; color: {p['muted']}; }}
    QListWidget#NavList::item {{ background-color: {p['bg']}; }}
    QListWidget#ProfessionList::item {{ background-color: {p['surface']}; }}
    QListWidget#NavList::item:selected, QListWidget#ProfessionList::item:selected {{ background-color: {p['surface3']}; color: {p['text']}; border-left: 3px solid {p['primary']}; }}
    QListWidget#NavList::item:hover, QListWidget#ProfessionList::item:hover {{ background-color: {p['surface2']}; color: {p['text']}; }}
    QListWidget#ToolList::item {{ background-color: {p['surface2']}; color: {p['text']}; border: 1px solid {p['border']}; border-radius: {card_radius}px; padding: 10px; margin: 4px 2px; }}
    QListWidget#ToolList::item:selected {{ background-color: {p['surface3']}; color: {p['text']}; border: 1px solid {p['glow']}; }}
    QListWidget#ToolList::item:hover {{ background-color: {p['surface3']}; border-color: {p['accent']}; }}
    QListWidget#TradeCardList::item {{ background-color: {p['surface']}; border: 0; padding: 0; margin: 0; }}
    QListWidget#TradeCardList::item:selected {{ background-color: {p['surface3']}; border-left: 3px solid {p['primary']}; }}
    QListWidget#CompareList::item {{ padding: 6px; margin: 2px; background-color: {p['surface2']}; border: 1px solid {p['border']}; border-radius: {radius}px; }}

    QHeaderView::section {{ background: {p['surface3']}; color: {p['text']}; border: 0; border-right: 1px solid {p['border']}; border-bottom: 1px solid {p['border']}; padding: 7px; font-weight: 700; }}
    QTableWidget {{ gridline-color: {p['border']}; alternate-background-color: {p['surface2']}; }}

    QAbstractScrollArea {{ background-color: {p['surface']}; color: {p['text']}; border-color: {p['border']}; }}
    QAbstractScrollArea QWidget#qt_scrollarea_viewport {{ background-color: {p['surface']}; color: {p['text']}; }}
    QScrollArea {{ background-color: {p['surface']}; border: 0; }}
    QScrollArea > QWidget > QWidget {{ background-color: {p['surface']}; color: {p['text']}; }}
    QStackedWidget {{ background: transparent; border: 0; }}
    QSplitter {{ background: {p['bg']}; }}
    QSplitter::handle {{ background: {p['border']}; width: 1px; }}
    QSplitter::handle:hover {{ background: {p['glow']}; }}
    QScrollBar:vertical {{ background: {p['surface']}; width: 10px; margin: 3px; }}
    QScrollBar::handle:vertical {{ background: {p['border']}; min-height: 26px; border-radius: 4px; }}
    QScrollBar::handle:vertical:hover {{ background: {p['primary']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

    QGroupBox {{ background: {p['surface']}; color: {p['text']}; border: 1px solid {p['border']}; border-radius: {card_radius}px; margin-top: 10px; padding: 12px; font-weight: 700; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; color: {p['accent']}; }}
    QToolTip {{ background: {p['surface3']}; color: {p['text']}; border: 1px solid {p['accent']}; padding: 6px; }}
    QStatusBar {{ background: {p['bg']}; color: {p['muted']}; border-top: 1px solid {p['border']}; }}
    """
