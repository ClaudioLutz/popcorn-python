"""Movie poster card widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QCursor

from core.yts_api import Movie
from ui.styles import COLORS


class MovieCard(QFrame):
    """A clickable movie poster card."""

    clicked = pyqtSignal(Movie)
    hide_requested = pyqtSignal(Movie)
    watched_requested = pyqtSignal(Movie)

    CARD_WIDTH = 180
    CARD_HEIGHT = 320
    POSTER_HEIGHT = 260

    def __init__(self, movie: Movie, is_downloaded: bool = False, is_hidden: bool = False, is_watched: bool = False, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.is_downloaded = is_downloaded
        self.is_hidden = is_hidden
        self.is_watched = is_watched
        self.hide_btn = None
        self.watched_btn = None
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("movieCard")
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Poster container
        poster_container = QWidget()
        poster_container.setFixedHeight(self.POSTER_HEIGHT)
        poster_layout = QVBoxLayout(poster_container)
        poster_layout.setContentsMargins(0, 0, 0, 0)

        # Poster image
        self.poster_label = QLabel()
        self.poster_label.setFixedSize(self.CARD_WIDTH, self.POSTER_HEIGHT)
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_label.setStyleSheet(f"""
            background-color: {COLORS['secondary_bg']};
            border-radius: 8px 8px 0 0;
        """)
        self.poster_label.setText("Loading...")
        poster_layout.addWidget(self.poster_label)

        # Downloaded badge (overlay)
        if self.is_downloaded:
            badge = QLabel("✓")
            badge.setStyleSheet(f"""
                background-color: {COLORS['success']};
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            """)
            badge.setFixedSize(28, 28)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setParent(poster_container)
            badge.move(self.CARD_WIDTH - 36, 8)

        # Hide/Unhide button (appears on hover) - RED
        if self.is_hidden:
            self.hide_btn = QPushButton("↩", poster_container)
            self.hide_btn.setToolTip("Unhide this movie")
        else:
            self.hide_btn = QPushButton("✕", poster_container)
            self.hide_btn.setToolTip("Hide this movie")

        self.hide_btn.setFixedSize(24, 24)
        self.hide_btn.move(8, 8)
        self.hide_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['error']};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #dc2626;
            }}
        """)
        self.hide_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.hide_btn.clicked.connect(self._on_hide_clicked)
        self.hide_btn.hide()

        # Watched button (appears on hover) - GREEN
        if self.is_watched:
            self.watched_btn = QPushButton("👁", poster_container)
            self.watched_btn.setToolTip("Unmark as watched")
        else:
            self.watched_btn = QPushButton("👁", poster_container)
            self.watched_btn.setToolTip("Mark as watched")

        self.watched_btn.setFixedSize(24, 24)
        self.watched_btn.move(36, 8)  # Next to hide button
        self.watched_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #16a34a;
            }}
        """)
        self.watched_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.watched_btn.clicked.connect(self._on_watched_clicked)
        self.watched_btn.hide()

        # Watched badge (always visible if watched) - GREEN
        if self.is_watched:
            watched_badge = QLabel("👁", poster_container)
            watched_badge.setStyleSheet(f"""
                background-color: {COLORS['success']};
                color: white;
                font-size: 12px;
                padding: 4px;
                border-radius: 4px;
            """)
            watched_badge.setFixedSize(24, 24)
            watched_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            watched_badge.move(self.CARD_WIDTH - 64, 8)

        # Hidden overlay
        if self.is_hidden:
            hidden_overlay = QLabel("HIDDEN", poster_container)
            hidden_overlay.setStyleSheet(f"""
                background-color: rgba(0, 0, 0, 0.6);
                color: {COLORS['error']};
                font-size: 14px;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 4px;
            """)
            hidden_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hidden_overlay.adjustSize()
            hidden_overlay.move(
                (self.CARD_WIDTH - hidden_overlay.width()) // 2,
                self.POSTER_HEIGHT - 30
            )

        layout.addWidget(poster_container)

        # Info section
        info_widget = QWidget()
        info_widget.setStyleSheet(f"""
            background-color: {COLORS['secondary_bg']};
            border-radius: 0 0 8px 8px;
            padding: 8px;
        """)
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setSpacing(4)

        # Title
        title_label = QLabel(self._truncate(self.movie.title, 20))
        title_label.setStyleSheet(f"""
            color: {COLORS['text']};
            font-size: 13px;
            font-weight: bold;
        """)
        title_label.setToolTip(self.movie.title)
        info_layout.addWidget(title_label)

        # Year and rating row
        year_rating = QHBoxLayout()
        year_rating.setSpacing(8)

        year_label = QLabel(str(self.movie.year))
        year_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        year_rating.addWidget(year_label)

        rating_label = QLabel(f"★ {self.movie.rating}")
        rating_label.setStyleSheet(f"color: {COLORS['rating']}; font-size: 12px;")
        year_rating.addWidget(rating_label)

        year_rating.addStretch()
        info_layout.addLayout(year_rating)

        layout.addWidget(info_widget)

    def set_poster(self, pixmap: QPixmap):
        """Set the poster image."""
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self.CARD_WIDTH,
                self.POSTER_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            # Crop to fit
            if scaled.width() > self.CARD_WIDTH or scaled.height() > self.POSTER_HEIGHT:
                x = (scaled.width() - self.CARD_WIDTH) // 2
                y = (scaled.height() - self.POSTER_HEIGHT) // 2
                scaled = scaled.copy(x, y, self.CARD_WIDTH, self.POSTER_HEIGHT)

            self.poster_label.setPixmap(scaled)
        else:
            self.poster_label.setText("No Image")

    def set_placeholder(self):
        """Set a placeholder for the poster."""
        self.poster_label.setText("🎬")
        self.poster_label.setStyleSheet(f"""
            background-color: {COLORS['secondary_bg']};
            border-radius: 8px 8px 0 0;
            font-size: 48px;
        """)

    def _on_hide_clicked(self):
        """Handle hide button click."""
        self.hide_requested.emit(self.movie)

    def _on_watched_clicked(self):
        """Handle watched button click."""
        self.watched_requested.emit(self.movie)

    def mousePressEvent(self, event):
        """Handle click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.movie)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter."""
        self.setStyleSheet(f"""
            #movieCard {{
                border: 2px solid {COLORS['accent']};
                border-radius: 8px;
            }}
        """)
        if self.hide_btn:
            self.hide_btn.show()
        if self.watched_btn:
            self.watched_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave."""
        self.setStyleSheet(f"""
            #movieCard {{
                border: 2px solid transparent;
                border-radius: 8px;
            }}
        """)
        if self.hide_btn:
            self.hide_btn.hide()
        if self.watched_btn:
            self.watched_btn.hide()
        super().leaveEvent(event)

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        """Truncate text with ellipsis."""
        if len(text) > max_len:
            return text[:max_len - 3] + "..."
        return text
