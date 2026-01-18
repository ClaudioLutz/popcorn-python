"""Filter bar with genre, sort, and search controls."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QCheckBox, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer

from core.yts_api import YTSApi
from ui.styles import COLORS


class FilterBar(QWidget):
    """Filter bar for browsing movies."""

    filters_changed = pyqtSignal(dict)  # Emits filter settings

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("filterBar")
        self._setup_ui()

        # Debounce timer for search
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._emit_filters)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Logo/Title
        title = QLabel("🍿 Popcorn Python")
        title.setStyleSheet(f"""
            color: {COLORS['accent']};
            font-size: 18px;
            font-weight: bold;
        """)
        layout.addWidget(title)

        layout.addSpacing(20)

        # Genre dropdown
        genre_label = QLabel("Genre:")
        genre_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(genre_label)

        self.genre_combo = QComboBox()
        self.genre_combo.addItems(YTSApi.GENRES)
        self.genre_combo.currentTextChanged.connect(self._on_filter_change)
        layout.addWidget(self.genre_combo)

        # Sort dropdown
        sort_label = QLabel("Sort:")
        sort_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(list(YTSApi.SORT_OPTIONS.keys()))
        self.sort_combo.currentTextChanged.connect(self._on_filter_change)
        layout.addWidget(self.sort_combo)

        layout.addStretch()

        # Hide downloaded checkbox
        self.hide_downloaded = QCheckBox("Hide Downloaded")
        self.hide_downloaded.setChecked(True)
        self.hide_downloaded.stateChanged.connect(self._on_filter_change)
        layout.addWidget(self.hide_downloaded)

        # Show hidden checkbox
        self.show_hidden = QCheckBox("Show Hidden")
        self.show_hidden.setChecked(False)
        self.show_hidden.stateChanged.connect(self._on_filter_change)
        layout.addWidget(self.show_hidden)

        # Hide watched checkbox
        self.hide_watched = QCheckBox("Hide Watched")
        self.hide_watched.setChecked(False)
        self.hide_watched.stateChanged.connect(self._on_filter_change)
        layout.addWidget(self.hide_watched)

        layout.addSpacing(10)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search movies...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self._on_search_change)
        self.search_input.returnPressed.connect(self._emit_filters)
        layout.addWidget(self.search_input)

        self.setStyleSheet(f"""
            #filterBar {{
                background-color: {COLORS['secondary_bg']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)

    def _on_filter_change(self):
        """Handle immediate filter changes (dropdowns, checkbox)."""
        self._emit_filters()

    def _on_search_change(self, text):
        """Handle search input with debounce."""
        self._search_timer.stop()
        self._search_timer.start(300)  # 300ms debounce

    def _emit_filters(self):
        """Emit the current filter settings."""
        sort_key = self.sort_combo.currentText()
        filters = {
            "genre": self.genre_combo.currentText(),
            "sort_by": YTSApi.SORT_OPTIONS.get(sort_key, "download_count"),
            "sort_display": sort_key,
            "query": self.search_input.text().strip(),
            "hide_downloaded": self.hide_downloaded.isChecked(),
            "show_hidden": self.show_hidden.isChecked(),
            "hide_watched": self.hide_watched.isChecked(),
        }
        self.filters_changed.emit(filters)

    def get_filters(self) -> dict:
        """Get current filter settings."""
        sort_key = self.sort_combo.currentText()
        return {
            "genre": self.genre_combo.currentText(),
            "sort_by": YTSApi.SORT_OPTIONS.get(sort_key, "download_count"),
            "sort_display": sort_key,
            "query": self.search_input.text().strip(),
            "hide_downloaded": self.hide_downloaded.isChecked(),
            "show_hidden": self.show_hidden.isChecked(),
            "hide_watched": self.hide_watched.isChecked(),
        }

    def set_genre(self, genre: str):
        """Set the genre dropdown."""
        idx = self.genre_combo.findText(genre)
        if idx >= 0:
            self.genre_combo.setCurrentIndex(idx)

    def set_sort(self, sort_display: str):
        """Set the sort dropdown."""
        idx = self.sort_combo.findText(sort_display)
        if idx >= 0:
            self.sort_combo.setCurrentIndex(idx)
