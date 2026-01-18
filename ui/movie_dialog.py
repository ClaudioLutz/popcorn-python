"""Movie details dialog with download options."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from core.yts_api import Movie
from ui.styles import COLORS


class MovieDialog(QDialog):
    """Dialog showing movie details and download options."""

    download_requested = pyqtSignal(Movie, str)  # movie, quality

    def __init__(self, movie: Movie, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.network_manager = QNetworkAccessManager()
        self._setup_ui()
        self._load_poster()

    def _setup_ui(self):
        self.setWindowTitle(self.movie.title)
        self.setMinimumSize(700, 500)
        self.setStyleSheet(f"background-color: {COLORS['background']};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left side - Poster
        poster_container = QWidget()
        poster_container.setFixedWidth(300)
        poster_container.setStyleSheet(f"background-color: {COLORS['secondary_bg']};")
        poster_layout = QVBoxLayout(poster_container)
        poster_layout.setContentsMargins(20, 20, 20, 20)

        self.poster_label = QLabel("Loading...")
        self.poster_label.setFixedSize(260, 390)
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_label.setStyleSheet(f"""
            background-color: {COLORS['background']};
            border-radius: 8px;
        """)
        poster_layout.addWidget(self.poster_label)
        poster_layout.addStretch()

        layout.addWidget(poster_container)

        # Right side - Info
        info_scroll = QScrollArea()
        info_scroll.setWidgetResizable(True)
        info_scroll.setStyleSheet("border: none;")

        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(30, 30, 30, 30)
        info_layout.setSpacing(16)

        # Title
        title = QLabel(self.movie.title)
        title.setStyleSheet(f"""
            color: {COLORS['text']};
            font-size: 28px;
            font-weight: bold;
        """)
        title.setWordWrap(True)
        info_layout.addWidget(title)

        # Year, Runtime, Rating row
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(20)

        year = QLabel(f"📅 {self.movie.year}")
        year.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        meta_layout.addWidget(year)

        if self.movie.runtime:
            runtime = QLabel(f"⏱️ {self.movie.runtime} min")
            runtime.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
            meta_layout.addWidget(runtime)

        rating = QLabel(f"⭐ {self.movie.rating}/10")
        rating.setStyleSheet(f"color: {COLORS['rating']}; font-size: 14px; font-weight: bold;")
        meta_layout.addWidget(rating)

        meta_layout.addStretch()
        info_layout.addLayout(meta_layout)

        # Genres
        if self.movie.genres:
            genres_widget = QWidget()
            genres_layout = QHBoxLayout(genres_widget)
            genres_layout.setContentsMargins(0, 0, 0, 0)
            genres_layout.setSpacing(8)

            for genre in self.movie.genres[:5]:
                badge = QLabel(genre)
                badge.setStyleSheet(f"""
                    background-color: {COLORS['border']};
                    color: {COLORS['text']};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                """)
                genres_layout.addWidget(badge)
            genres_layout.addStretch()
            info_layout.addWidget(genres_widget)

        # Synopsis
        if self.movie.synopsis:
            synopsis_label = QLabel("Synopsis")
            synopsis_label.setStyleSheet(f"""
                color: {COLORS['text']};
                font-size: 16px;
                font-weight: bold;
            """)
            info_layout.addWidget(synopsis_label)

            synopsis = QLabel(self.movie.synopsis)
            synopsis.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; line-height: 1.5;")
            synopsis.setWordWrap(True)
            info_layout.addWidget(synopsis)

        info_layout.addSpacing(20)

        # Download section
        download_label = QLabel("Download")
        download_label.setStyleSheet(f"""
            color: {COLORS['text']};
            font-size: 16px;
            font-weight: bold;
        """)
        info_layout.addWidget(download_label)

        # Quality buttons
        quality_widget = QWidget()
        quality_layout = QHBoxLayout(quality_widget)
        quality_layout.setContentsMargins(0, 0, 0, 0)
        quality_layout.setSpacing(12)

        for torrent in self.movie.torrents:
            btn = QPushButton(f"{torrent.quality}\n{torrent.size}")
            btn.setObjectName("downloadBtn")
            btn.setFixedSize(100, 60)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_hover']};
                }}
            """)
            btn.setToolTip(f"Seeds: {torrent.seeds} | Peers: {torrent.peers}")
            btn.clicked.connect(lambda checked, q=torrent.quality: self._on_download(q))
            quality_layout.addWidget(btn)

        quality_layout.addStretch()
        info_layout.addWidget(quality_widget)

        # Torrent info
        if self.movie.torrents:
            best = max(self.movie.torrents, key=lambda t: t.seeds)
            info_text = QLabel(f"Best: {best.quality} with {best.seeds} seeds")
            info_text.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            info_layout.addWidget(info_text)

        info_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        info_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        info_scroll.setWidget(info_container)
        layout.addWidget(info_scroll)

    def _load_poster(self):
        """Load the poster image."""
        if self.movie.large_cover_image:
            request = QNetworkRequest(QUrl(self.movie.large_cover_image))
            request.setAttribute(
                QNetworkRequest.Attribute.RedirectPolicyAttribute,
                QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy
            )
            reply = self.network_manager.get(request)
            reply.finished.connect(lambda: self._on_poster_loaded(reply))
        else:
            self.poster_label.setText("No Image")

    def _on_poster_loaded(self, reply: QNetworkReply):
        """Handle poster loaded."""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            scaled = pixmap.scaled(
                260, 390,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.poster_label.setPixmap(scaled)
        else:
            self.poster_label.setText("Failed to load")
        reply.deleteLater()

    def _on_download(self, quality: str):
        """Handle download button click."""
        self.download_requested.emit(self.movie, quality)
        QMessageBox.information(
            self,
            "Download Started",
            f"Adding {self.movie.title} ({quality}) to qBittorrent..."
        )
