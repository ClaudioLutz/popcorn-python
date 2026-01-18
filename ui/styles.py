"""Dark theme styles for Popcorn Time clone."""

DARK_THEME = """
QMainWindow, QDialog {
    background-color: #1a1a2e;
}

QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Segoe UI", Arial, sans-serif;
}

/* Header/Filter bar */
#filterBar {
    background-color: #16213e;
    border-bottom: 1px solid #0f3460;
    padding: 10px;
}

/* Buttons */
QPushButton {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1a5276;
}

QPushButton:pressed {
    background-color: #0d2840;
}

QPushButton#downloadBtn {
    background-color: #e94560;
}

QPushButton#downloadBtn:hover {
    background-color: #ff6b6b;
}

/* Combo boxes */
QComboBox {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #1a5276;
    padding: 6px 12px;
    border-radius: 4px;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #e94560;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    selection-background-color: #e94560;
    border: 1px solid #0f3460;
}

/* Line edits (search box) */
QLineEdit {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    padding: 8px 12px;
    border-radius: 4px;
}

QLineEdit:focus {
    border-color: #e94560;
}

QLineEdit::placeholder {
    color: #666;
}

/* Scroll areas */
QScrollArea {
    background-color: #1a1a2e;
    border: none;
}

QScrollBar:vertical {
    background-color: #16213e;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #0f3460;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #1a5276;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* Labels */
QLabel {
    color: #e0e0e0;
}

QLabel#titleLabel {
    font-size: 24px;
    font-weight: bold;
}

QLabel#yearLabel {
    color: #aaa;
    font-size: 14px;
}

QLabel#ratingLabel {
    color: #ffc107;
    font-weight: bold;
}

QLabel#genreLabel {
    color: #888;
    font-size: 12px;
}

/* Movie card */
#movieCard {
    background-color: #16213e;
    border-radius: 8px;
    border: 2px solid transparent;
}

#movieCard:hover {
    border-color: #e94560;
}

/* Status bar */
QStatusBar {
    background-color: #16213e;
    color: #888;
}

/* Checkbox */
QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 2px solid #0f3460;
}

QCheckBox::indicator:checked {
    background-color: #e94560;
    border-color: #e94560;
}

/* Dialog */
QDialog {
    background-color: #1a1a2e;
}

/* Tab widget */
QTabWidget::pane {
    border: 1px solid #0f3460;
    background-color: #1a1a2e;
}

QTabBar::tab {
    background-color: #16213e;
    color: #888;
    padding: 10px 20px;
    border: none;
}

QTabBar::tab:selected {
    background-color: #0f3460;
    color: #e0e0e0;
    border-bottom: 2px solid #e94560;
}

QTabBar::tab:hover:!selected {
    background-color: #1a3a5c;
}

/* Progress bar */
QProgressBar {
    background-color: #16213e;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
}

QProgressBar::chunk {
    background-color: #e94560;
    border-radius: 4px;
}

/* Message box */
QMessageBox {
    background-color: #1a1a2e;
}
"""

# Color constants for programmatic use
COLORS = {
    "background": "#1a1a2e",
    "secondary_bg": "#16213e",
    "accent": "#e94560",
    "accent_hover": "#ff6b6b",
    "text": "#e0e0e0",
    "text_secondary": "#888",
    "border": "#0f3460",
    "rating": "#ffc107",
    "success": "#28a745",
    "warning": "#ffc107",
    "error": "#dc3545",
}
