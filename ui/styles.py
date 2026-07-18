"""Theme definitions for Audiobook Maker Pro."""

from typing import Dict


THEMES: Dict[str, dict] = {
    "aurora": {
        "name": "Aurora Daydream",
        "base": "#F3F7FC",
        "workspace": "#F7F9FD",
        "sidebar": "#EAF8FB",
        "surface": "#FFFFFF",
        "surface_alt": "#F5F1FF",
        "surface_hover": "#EDF9FC",
        "input": "#FBFDFF",
        "text": "#253252",
        "muted": "#667392",
        "subtle": "#91A0B8",
        "border": "#D9E6F0",
        "border_strong": "#BDE3EC",
        "accent": "#49CFE0",
        "accent_hover": "#33BDD0",
        "accent_soft": "#DDF7FA",
        "secondary": "#A99BEF",
        "pink": "#EF9BCF",
        "danger": "#E96B91",
        "danger_hover": "#D85D83",
        "success": "#31A98A",
        "warning": "#D69938",
        "scroll": "#B7CDD9",
        "selection": "#CFF3F7",
        "disabled": "#E9EEF4",
        "disabled_text": "#A9B4C4",
    },
    "midnight": {
        "name": "Midnight Bloom",
        "base": "#171627",
        "workspace": "#1B1A2D",
        "sidebar": "#211F38",
        "surface": "#25233D",
        "surface_alt": "#2C2948",
        "surface_hover": "#302E4D",
        "input": "#1E1D33",
        "text": "#F5F3FF",
        "muted": "#C0BCD7",
        "subtle": "#8F8BAA",
        "border": "#3B3858",
        "border_strong": "#57527A",
        "accent": "#78D8E7",
        "accent_hover": "#8FE6F2",
        "accent_soft": "#293F4C",
        "secondary": "#B8A9FF",
        "pink": "#F2A4D3",
        "danger": "#EF769E",
        "danger_hover": "#FA8AAF",
        "success": "#6BD6B6",
        "warning": "#F0C36B",
        "scroll": "#595673",
        "selection": "#374B61",
        "disabled": "#2B293F",
        "disabled_text": "#716E87",
    },
}


def normalize_theme(theme_name: str) -> str:
    """Return a valid theme key, defaulting to Aurora."""
    return theme_name if theme_name in THEMES else "aurora"


def get_theme_options() -> Dict[str, str]:
    """Return theme keys mapped to their user-facing names."""
    return {key: value["name"] for key, value in THEMES.items()}


def get_stylesheet(theme_name: str = "aurora") -> str:
    """Build the application stylesheet for the requested theme."""
    c = THEMES[normalize_theme(theme_name)]
    return f"""
/* Foundation */
QMainWindow, QDialog {{
    background-color: {c['base']};
    color: {c['text']};
}}

QWidget {{
    color: {c['text']};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}}

QWidget#appRoot,
QFrame#workspaceFrame,
QStackedWidget#mainStack {{
    background-color: {c['workspace']};
}}

QScrollArea#settingsPanel,
QWidget#settingsContent {{
    background-color: {c['workspace']};
    border: none;
}}

QFrame#sidebar {{
    background-color: {c['sidebar']};
    border-right: 1px solid {c['border']};
}}

QLabel#brandMark {{
    color: {c['accent_hover']};
    font-size: 23pt;
    font-weight: 800;
}}

QLabel#brandTitle {{
    color: {c['text']};
    font-size: 13pt;
    font-weight: 750;
}}

QLabel#brandSubtitle,
QLabel#sidebarCaption {{
    color: {c['muted']};
    font-size: 9pt;
}}

QLabel#sectionLabel {{
    color: {c['subtle']};
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
}}

/* Sidebar navigation */
QPushButton#navButton {{
    background-color: transparent;
    color: {c['muted']};
    border: 1px solid transparent;
    border-radius: 13px;
    padding: 10px 14px;
    text-align: left;
    font-size: 10pt;
    font-weight: 600;
}}

QPushButton#navButton:hover {{
    background-color: {c['surface_hover']};
    color: {c['text']};
    border-color: {c['border']};
}}

QPushButton#navButton:checked {{
    background-color: {c['accent_soft']};
    color: {c['text']};
    border-color: {c['border_strong']};
}}

QPushButton#sidebarToolButton {{
    background-color: transparent;
    color: {c['muted']};
    border: none;
    border-radius: 10px;
    padding: 8px 12px;
    text-align: left;
}}

QPushButton#sidebarToolButton:hover {{
    background-color: {c['surface_hover']};
    color: {c['text']};
}}

QFrame#themeCard {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 14px;
}}

/* Menus and status */
QMenuBar {{
    background-color: {c['base']};
    color: {c['text']};
    border-bottom: 1px solid {c['border']};
    padding: 3px 7px;
}}

QMenuBar::item {{
    background-color: transparent;
    border-radius: 7px;
    padding: 5px 10px;
}}

QMenuBar::item:selected {{
    background-color: {c['surface_hover']};
}}

QMenu {{
    background-color: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    padding: 6px;
}}

QMenu::item {{
    border-radius: 7px;
    padding: 7px 28px 7px 10px;
}}

QMenu::item:selected {{
    background-color: {c['accent_soft']};
    color: {c['text']};
}}

QMenu::separator {{
    background-color: {c['border']};
    height: 1px;
    margin: 5px 8px;
}}

QStatusBar {{
    background-color: {c['base']};
    color: {c['muted']};
    border-top: 1px solid {c['border']};
    padding: 2px 8px;
}}

QStatusBar[statusType="success"] {{ color: {c['success']}; }}
QStatusBar[statusType="error"] {{ color: {c['danger']}; }}
QStatusBar[statusType="warning"] {{ color: {c['warning']}; }}
QStatusBar[statusType="info"] {{ color: {c['accent_hover']}; }}

/* Buttons */
QPushButton {{
    background-color: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 11px;
    padding: 7px 15px;
    min-height: 24px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {c['surface_hover']};
    border-color: {c['border_strong']};
}}

QPushButton:pressed {{
    background-color: {c['accent_soft']};
    padding-top: 9px;
    padding-bottom: 5px;
}}

QPushButton:disabled {{
    background-color: {c['disabled']};
    color: {c['disabled_text']};
    border-color: {c['border']};
}}

QPushButton#primaryButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c['accent']}, stop:0.58 {c['secondary']}, stop:1 {c['pink']});
    color: #FFFFFF;
    border: 1px solid {c['secondary']};
    border-radius: 13px;
    padding: 8px 20px;
    font-size: 10pt;
    font-weight: 750;
}}

QPushButton#primaryButton:hover {{
    border-color: {c['pink']};
}}

QPushButton#dangerButton {{
    background-color: {c['danger']};
    color: #FFFFFF;
    border-color: {c['danger']};
    border-radius: 13px;
}}

QPushButton#dangerButton:hover {{
    background-color: {c['danger_hover']};
    border-color: {c['danger_hover']};
}}

QPushButton#secondaryButton {{
    background-color: {c['surface']};
    color: {c['secondary']};
    border-color: {c['secondary']};
    border-radius: 13px;
}}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit,
QSpinBox, QDoubleSpinBox {{
    background-color: {c['input']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 6px 8px;
    selection-background-color: {c['selection']};
    selection-color: {c['text']};
}}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover,
QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {c['border_strong']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {c['accent']};
}}

QComboBox {{
    background-color: {c['input']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 6px 26px 6px 9px;
    min-height: 24px;
}}

QComboBox:hover, QComboBox:focus {{
    border-color: {c['accent']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    width: 0px;
    height: 0px;
}}

QComboBox QAbstractItemView {{
    background-color: {c['surface']};
    color: {c['text']};
    selection-background-color: {c['accent_soft']};
    selection-color: {c['text']};
    border: 1px solid {c['border']};
    outline: 0;
    padding: 4px;
}}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background-color: {c['surface_alt']};
    border: none;
    width: 18px;
}}

/* Sliders and progress */
QSlider::groove:horizontal {{
    background-color: {c['border']};
    height: 6px;
    border-radius: 3px;
}}

QSlider::sub-page:horizontal {{
    background-color: {c['accent']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {c['surface']};
    border: 2px solid {c['accent']};
    width: 15px;
    margin: -6px 0;
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background-color: {c['accent_soft']};
    border-color: {c['secondary']};
}}

QProgressBar {{
    background-color: {c['surface_alt']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    text-align: center;
    color: {c['text']};
    font-weight: 650;
    min-height: 24px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c['accent']}, stop:0.55 {c['secondary']}, stop:1 {c['pink']});
    border-radius: 9px;
}}

/* Tabs and content cards */
QTabWidget::pane {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 13px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {c['muted']};
    border: 1px solid transparent;
    padding: 7px 14px;
    margin-right: 3px;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background-color: {c['surface']};
    color: {c['text']};
    border-color: {c['border']};
    border-bottom-color: {c['surface']};
}}

QTabBar::tab:hover:!selected {{
    background-color: {c['surface_hover']};
    color: {c['text']};
}}

QGroupBox {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 14px;
    margin-top: 10px;
    padding: 15px 10px 10px 10px;
    font-weight: 700;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 7px;
    color: {c['text']};
    background-color: {c['surface']};
}}

QFrame#contentCard {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 14px;
}}

QLabel {{
    color: {c['text']};
    background-color: transparent;
}}

/* Selection controls */
QCheckBox, QRadioButton {{
    color: {c['text']};
    spacing: 8px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {c['border_strong']};
    background-color: {c['input']};
}}

QCheckBox::indicator {{ border-radius: 5px; }}
QRadioButton::indicator {{ border-radius: 9px; }}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {c['accent']};
    border: 3px solid {c['surface']};
}}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {c['accent']};
}}

/* Lists, tables and trees */
QListWidget, QListView, QTreeWidget, QTableWidget {{
    background-color: {c['input']};
    alternate-background-color: {c['surface_alt']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    outline: 0;
}}

QListWidget::item, QListView::item, QTreeWidget::item {{
    border-radius: 7px;
    padding: 5px;
}}

QListWidget::item:selected, QListView::item:selected,
QTreeWidget::item:selected, QTableWidget::item:selected {{
    background-color: {c['accent_soft']};
    color: {c['text']};
}}

QListWidget::item:hover, QListView::item:hover, QTreeWidget::item:hover {{
    background-color: {c['surface_hover']};
}}

QHeaderView::section {{
    background-color: {c['surface_alt']};
    color: {c['muted']};
    border: none;
    border-right: 1px solid {c['border']};
    border-bottom: 1px solid {c['border']};
    padding: 7px;
    font-weight: 650;
}}

/* Scroll bars */
QScrollBar:vertical {{
    background-color: transparent;
    width: 11px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background-color: {c['scroll']};
    min-height: 28px;
    border-radius: 5px;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 11px;
    margin: 2px;
}}

QScrollBar::handle:horizontal {{
    background-color: {c['scroll']};
    min-width: 28px;
    border-radius: 5px;
}}

QScrollBar::handle:hover {{ background-color: {c['accent']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QSplitter::handle {{
    background-color: transparent;
    width: 9px;
    height: 9px;
}}

QSplitter::handle:hover {{ background-color: {c['accent_soft']}; }}

QToolTip {{
    background-color: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border_strong']};
    border-radius: 7px;
    padding: 5px 7px;
}}
"""
