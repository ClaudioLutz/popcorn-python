"""Filter bar with genre, sort, search, and advanced filter controls."""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QLineEdit,
    QCheckBox, QLabel, QPushButton, QSlider, QSpinBox, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QPropertyAnimation, QEasingCurve

from core.yts_api import YTSApi
from ui.styles import COLORS


class FilterBar(QWidget):
    """Filter bar for browsing movies."""

    filters_changed = pyqtSignal(dict)  # Emits filter settings

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("filterBar")
        self._advanced_visible = False
        self._setup_ui()

        # Debounce timer for search
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._emit_filters)

    def _setup_ui(self):
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar container
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Logo/Title
        title = QLabel("Popcorn")
        title.setStyleSheet(f"""
            color: {COLORS['accent']};
            font-size: 18px;
            font-weight: bold;
        """)
        layout.addWidget(title)

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

        # Sort direction toggle
        self.sort_desc = QCheckBox("Desc")
        self.sort_desc.setChecked(True)
        self.sort_desc.setToolTip("Sort direction (checked = descending)")
        self.sort_desc.stateChanged.connect(self._on_filter_change)
        layout.addWidget(self.sort_desc)

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

        # Hide watchlist checkbox
        self.hide_watchlist = QCheckBox("Hide Watchlist")
        self.hide_watchlist.setChecked(True)
        self.hide_watchlist.stateChanged.connect(self._on_filter_change)
        layout.addWidget(self.hide_watchlist)

        # Show watchlist only checkbox
        self.show_watchlist_only = QCheckBox("Watchlist Only")
        self.show_watchlist_only.setChecked(False)
        self.show_watchlist_only.stateChanged.connect(self._on_filter_change)
        layout.addWidget(self.show_watchlist_only)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search movies...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._on_search_change)
        self.search_input.returnPressed.connect(self._emit_filters)
        layout.addWidget(self.search_input)

        # More Filters toggle button
        self.toggle_btn = QPushButton("▼ Filters")
        self.toggle_btn.setFixedWidth(80)
        self.toggle_btn.clicked.connect(self._toggle_advanced)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_hover']};
            }}
        """)
        layout.addWidget(self.toggle_btn)

        main_layout.addWidget(top_bar)

        # Advanced filters section (collapsible)
        self.advanced_section = QFrame()
        self.advanced_section.setObjectName("advancedSection")
        self.advanced_section.setMaximumHeight(0)
        self._setup_advanced_filters()
        main_layout.addWidget(self.advanced_section)

        self.setStyleSheet(f"""
            #filterBar {{
                background-color: {COLORS['secondary_bg']};
                border-bottom: 1px solid {COLORS['border']};
            }}
            #topBar {{
                background-color: {COLORS['secondary_bg']};
            }}
            #advancedSection {{
                background-color: {COLORS['background']};
                border-top: 1px solid {COLORS['border']};
            }}
            QLabel {{
                color: {COLORS['text_secondary']};
            }}
            QSpinBox, QComboBox {{
                background-color: {COLORS['secondary_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 8px;
                color: {COLORS['text']};
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {COLORS['border']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent']};
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['accent']};
                border-radius: 3px;
            }}
        """)

    def _setup_advanced_filters(self):
        """Setup the collapsible advanced filters section."""
        main_layout = QVBoxLayout(self.advanced_section)
        main_layout.setContentsMargins(16, 10, 16, 10)
        main_layout.setSpacing(8)

        current_year = datetime.now().year

        # Row 1: Rating, Year, Runtime, Language
        row1 = QHBoxLayout()
        row1.setSpacing(24)

        # Rating
        row1.addWidget(QLabel("Rating:"))
        self.rating_slider = QSlider(Qt.Orientation.Horizontal)
        self.rating_slider.setRange(0, 90)
        self.rating_slider.setValue(0)
        self.rating_slider.setFixedWidth(100)
        self.rating_slider.valueChanged.connect(self._on_rating_change)
        row1.addWidget(self.rating_slider)
        self.rating_value = QLabel("0+")
        self.rating_value.setFixedWidth(30)
        self.rating_value.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold;")
        row1.addWidget(self.rating_value)

        row1.addSpacing(20)

        # Year
        row1.addWidget(QLabel("Year:"))
        self.min_year = QSpinBox()
        self.min_year.setRange(1900, current_year)
        self.min_year.setValue(1900)
        self.min_year.setFixedWidth(80)
        self.min_year.valueChanged.connect(self._on_filter_change)
        row1.addWidget(self.min_year)
        row1.addWidget(QLabel("to"))
        self.max_year = QSpinBox()
        self.max_year.setRange(1900, current_year)
        self.max_year.setValue(current_year)
        self.max_year.setFixedWidth(80)
        self.max_year.valueChanged.connect(self._on_filter_change)
        row1.addWidget(self.max_year)

        row1.addSpacing(20)

        # Runtime
        row1.addWidget(QLabel("Runtime:"))
        self.min_runtime = QSpinBox()
        self.min_runtime.setRange(0, 500)
        self.min_runtime.setValue(0)
        self.min_runtime.setFixedWidth(70)
        self.min_runtime.setSuffix("m")
        self.min_runtime.valueChanged.connect(self._on_filter_change)
        row1.addWidget(self.min_runtime)
        row1.addWidget(QLabel("to"))
        self.max_runtime = QSpinBox()
        self.max_runtime.setRange(0, 500)
        self.max_runtime.setValue(500)
        self.max_runtime.setFixedWidth(70)
        self.max_runtime.setSuffix("m")
        self.max_runtime.valueChanged.connect(self._on_filter_change)
        row1.addWidget(self.max_runtime)

        row1.addSpacing(20)

        # Language
        row1.addWidget(QLabel("Language:"))
        self.language_combo = QComboBox()
        self.language_combo.setFixedWidth(90)
        self.language_combo.addItems(["All", "English", "Spanish", "French", "German", "Italian", "Japanese", "Korean", "Chinese", "Russian", "Hindi"])
        self.language_combo.currentTextChanged.connect(self._on_filter_change)
        row1.addWidget(self.language_combo)

        row1.addStretch()
        main_layout.addLayout(row1)

        # Row 2: Quality, Seeds
        row2 = QHBoxLayout()
        row2.setSpacing(24)

        # Quality
        row2.addWidget(QLabel("Quality:"))
        self.quality_2160p = QCheckBox("4K")
        self.quality_2160p.setChecked(True)
        self.quality_2160p.stateChanged.connect(self._on_filter_change)
        row2.addWidget(self.quality_2160p)
        self.quality_1080p = QCheckBox("1080p")
        self.quality_1080p.setChecked(True)
        self.quality_1080p.stateChanged.connect(self._on_filter_change)
        row2.addWidget(self.quality_1080p)
        self.quality_720p = QCheckBox("720p")
        self.quality_720p.setChecked(True)
        self.quality_720p.stateChanged.connect(self._on_filter_change)
        row2.addWidget(self.quality_720p)

        row2.addSpacing(40)

        # Seeds
        row2.addWidget(QLabel("Min Seeds:"))
        self.seeds_slider = QSlider(Qt.Orientation.Horizontal)
        self.seeds_slider.setRange(0, 100)
        self.seeds_slider.setValue(0)
        self.seeds_slider.setFixedWidth(120)
        self.seeds_slider.valueChanged.connect(self._on_seeds_change)
        row2.addWidget(self.seeds_slider)
        self.seeds_value = QLabel("0")
        self.seeds_value.setFixedWidth(30)
        self.seeds_value.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold;")
        row2.addWidget(self.seeds_value)

        row2.addStretch()
        main_layout.addLayout(row2)

    def _toggle_advanced(self):
        """Toggle advanced filters visibility with animation."""
        self._advanced_visible = not self._advanced_visible

        if self._advanced_visible:
            self.toggle_btn.setText("▲ Filters")
            target_height = 80  # Expanded height for 2 rows
        else:
            self.toggle_btn.setText("▼ Filters")
            target_height = 0

        self.animation = QPropertyAnimation(self.advanced_section, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.advanced_section.maximumHeight())
        self.animation.setEndValue(target_height)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()

    def _on_filter_change(self):
        """Handle immediate filter changes."""
        self._emit_filters()

    def _on_search_change(self, text):
        """Handle search input with debounce."""
        self._search_timer.stop()
        self._search_timer.start(300)

    def _on_rating_change(self, value):
        """Handle rating slider change."""
        rating = value / 10
        self.rating_value.setText(f"{rating}+")
        self._on_filter_change()

    def _on_seeds_change(self, value):
        """Handle seeds slider change."""
        self.seeds_value.setText(str(value))
        self._on_filter_change()

    def _emit_filters(self):
        """Emit the current filter settings."""
        sort_key = self.sort_combo.currentText()
        filters = {
            # API-level filters
            "genre": self.genre_combo.currentText(),
            "sort_by": YTSApi.SORT_OPTIONS.get(sort_key, "download_count"),
            "sort_display": sort_key,
            "order_by": "desc" if self.sort_desc.isChecked() else "asc",
            "query": self.search_input.text().strip(),
            "minimum_rating": self.rating_slider.value() / 10,

            # Client-side filters
            "hide_downloaded": self.hide_downloaded.isChecked(),
            "show_hidden": self.show_hidden.isChecked(),
            "hide_watched": self.hide_watched.isChecked(),
            "hide_watchlist": self.hide_watchlist.isChecked(),
            "show_watchlist_only": self.show_watchlist_only.isChecked(),

            # Advanced filters (client-side)
            "min_year": self.min_year.value(),
            "max_year": self.max_year.value(),
            "min_runtime": self.min_runtime.value(),
            "max_runtime": self.max_runtime.value(),
            "quality_2160p": self.quality_2160p.isChecked(),
            "quality_1080p": self.quality_1080p.isChecked(),
            "quality_720p": self.quality_720p.isChecked(),
            "min_seeds": self.seeds_slider.value(),
            "language": self.language_combo.currentText(),
        }
        self.filters_changed.emit(filters)

    def get_filters(self) -> dict:
        """Get current filter settings."""
        sort_key = self.sort_combo.currentText()
        return {
            "genre": self.genre_combo.currentText(),
            "sort_by": YTSApi.SORT_OPTIONS.get(sort_key, "download_count"),
            "sort_display": sort_key,
            "order_by": "desc" if self.sort_desc.isChecked() else "asc",
            "query": self.search_input.text().strip(),
            "minimum_rating": self.rating_slider.value() / 10,
            "hide_downloaded": self.hide_downloaded.isChecked(),
            "show_hidden": self.show_hidden.isChecked(),
            "hide_watched": self.hide_watched.isChecked(),
            "hide_watchlist": self.hide_watchlist.isChecked(),
            "show_watchlist_only": self.show_watchlist_only.isChecked(),
            "min_year": self.min_year.value(),
            "max_year": self.max_year.value(),
            "min_runtime": self.min_runtime.value(),
            "max_runtime": self.max_runtime.value(),
            "quality_2160p": self.quality_2160p.isChecked(),
            "quality_1080p": self.quality_1080p.isChecked(),
            "quality_720p": self.quality_720p.isChecked(),
            "min_seeds": self.seeds_slider.value(),
            "language": self.language_combo.currentText(),
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
