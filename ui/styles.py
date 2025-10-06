"""
QSS (Qt Style Sheets) for the application.
Implements a modern dark theme matching the original Tkinter design.
"""


DARK_THEME = """
/* Global Styles */
QMainWindow, QDialog, QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

/* Menu Bar */
QMenuBar {
    background-color: #2b2b2b;
    color: #ffffff;
    border-bottom: 1px solid #404040;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 12px;
}

QMenuBar::item:selected {
    background-color: #404040;
}

QMenu {
    background-color: #2b2b2b;
    color: #ffffff;
    border: 1px solid #404040;
}

QMenu::item:selected {
    background-color: #404040;
}

/* Status Bar */
QStatusBar {
    background-color: #2b2b2b;
    color: #00ff00;
    border-top: 1px solid #404040;
}

/* Buttons */
QPushButton {
    background-color: #404040;
    color: #ffffff;
    border: 1px solid #505050;
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #505050;
}

QPushButton:pressed {
    background-color: #353535;
}

QPushButton:disabled {
    background-color: #303030;
    color: #666666;
}

/* Text Inputs */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #505050;
    border-radius: 3px;
    padding: 4px;
    selection-background-color: #505050;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #606060;
}

/* Combo Boxes */
QComboBox {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #505050;
    border-radius: 3px;
    padding: 4px 8px;
    min-height: 24px;
}

QComboBox:hover {
    border: 1px solid #606060;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: url(down_arrow.png);
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #3c3c3c;
    color: #ffffff;
    selection-background-color: #505050;
    border: 1px solid #505050;
}

/* Spin Boxes */
QSpinBox, QDoubleSpinBox {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #505050;
    border-radius: 3px;
    padding: 4px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #404040;
    border: 1px solid #505050;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #505050;
}

/* Sliders */
QSlider::groove:horizontal {
    background: #3c3c3c;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #606060;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #707070;
}

/* Progress Bar */
QProgressBar {
    background-color: #3c3c3c;
    border: 1px solid #505050;
    border-radius: 3px;
    text-align: center;
    color: #ffffff;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #4a9eff;
    border-radius: 2px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #404040;
    background-color: #2b2b2b;
}

QTabBar::tab {
    background-color: #404040;
    color: #ffffff;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #505050;
}

QTabBar::tab:hover {
    background-color: #4a4a4a;
}

/* Group Box */
QGroupBox {
    border: 1px solid #404040;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #ffffff;
}

/* Labels */
QLabel {
    color: #ffffff;
    background-color: transparent;
}

/* Check Boxes */
QCheckBox {
    color: #ffffff;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #505050;
    border-radius: 3px;
    background-color: #3c3c3c;
}

QCheckBox::indicator:checked {
    background-color: #4a9eff;
    border-color: #4a9eff;
}

QCheckBox::indicator:hover {
    border-color: #606060;
}

/* Radio Buttons */
QRadioButton {
    color: #ffffff;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #505050;
    border-radius: 8px;
    background-color: #3c3c3c;
}

QRadioButton::indicator:checked {
    background-color: #4a9eff;
    border-color: #4a9eff;
}

/* Scroll Bars */
QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #505050;
    min-height: 20px;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background-color: #606060;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2b2b2b;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #505050;
    min-width: 20px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #606060;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* List Widget */
QListWidget {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #505050;
    border-radius: 3px;
}

QListWidget::item {
    padding: 4px;
}

QListWidget::item:selected {
    background-color: #505050;
}

QListWidget::item:hover {
    background-color: #454545;
}

/* Tool Tips */
QToolTip {
    background-color: #404040;
    color: #ffffff;
    border: 1px solid #505050;
    padding: 4px;
    border-radius: 3px;
}

/* Splitter */
QSplitter::handle {
    background-color: #404040;
}

QSplitter::handle:hover {
    background-color: #505050;
}

/* Special Status Colors */
.status-success {
    color: #00ff00;
}

.status-error {
    color: #ff0000;
}

.status-warning {
    color: #ffff00;
}

.status-info {
    color: #00ffff;
}
"""


def get_stylesheet():
    """Returns the application stylesheet"""
    return DARK_THEME