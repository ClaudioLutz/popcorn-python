"""Movie grid with lazy loading and infinite scroll."""

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from core.yts_api import Movie
from core.library_scanner import normalize_title
from ui.movie_card import MovieCard
from ui.styles import COLORS


class ImageLoader(QObject):
    """Async image loader using Qt network."""

    image_loaded = pyqtSignal(str, QPixmap)  # url, pixmap

    def __init__(self):
        super().__init__()
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._on_finished)
        self._pending = {}  # url -> callback
        self._original_urls = {}  # reply -> original_url (to track redirects)

    def load(self, url: str, callback):
        """Load an image from URL."""
        if not url:
            return

        self._pending[url] = callback
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(
            QNetworkRequest.Attribute.CacheLoadControlAttribute,
            QNetworkRequest.CacheLoadControl.PreferCache
        )
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy
        )
        # Store original URL as custom attribute
        request.setAttribute(
            QNetworkRequest.Attribute.User,
            url
        )
        self.network_manager.get(request)

    def _on_finished(self, reply: QNetworkReply):
        """Handle network reply."""
        final_url = reply.url().toString()
        # Get original URL from custom attribute
        original_url = reply.request().attribute(QNetworkRequest.Attribute.User)
        error = reply.error()

        # Try original URL first, then final URL
        lookup_url = original_url if original_url in self._pending else final_url

        if lookup_url in self._pending:
            callback = self._pending.pop(lookup_url)
            if error == QNetworkReply.NetworkError.NoError:
                data = reply.readAll()
                pixmap = QPixmap()
                pixmap.loadFromData(data)
                callback(pixmap)
            else:
                print(f"Image load error for {lookup_url}: {reply.errorString()}")
                callback(None)

        reply.deleteLater()


class MovieGrid(QScrollArea):
    """Scrollable grid of movie cards with infinite scroll."""

    movie_clicked = pyqtSignal(Movie)
    movie_hidden = pyqtSignal(Movie)
    movie_watched = pyqtSignal(Movie)
    load_more = pyqtSignal()

    COLUMNS = 5
    CARD_SPACING = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.image_loader = ImageLoader()
        self.cards: list[MovieCard] = []
        self.downloaded_codes: set[str] = set()
        self.hidden_codes: set[str] = set()
        self.watched_codes: set[str] = set()
        self.library_lookup: set[tuple[str, int | None]] = set()

    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"background-color: {COLORS['background']}; border: none;")

        # Container widget
        self.container = QWidget()
        self.container.setStyleSheet(f"background-color: {COLORS['background']};")

        # Grid layout
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(self.CARD_SPACING)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.setWidget(self.container)

        # Connect scroll for infinite loading
        self.verticalScrollBar().valueChanged.connect(self._check_scroll)

    def _check_scroll(self, value):
        """Check if scrolled near bottom to load more."""
        scrollbar = self.verticalScrollBar()
        if scrollbar.maximum() > 0:
            if value >= scrollbar.maximum() - 200:
                self.load_more.emit()

    def check_needs_more(self):
        """Check if we need to load more content to fill the viewport."""
        # Use a timer to defer the check until layout is complete
        QTimer.singleShot(100, self._do_check_needs_more)

    def _do_check_needs_more(self):
        """Actually check if more content is needed."""
        scrollbar = self.verticalScrollBar()
        # If there's no scrollbar (content fits in viewport), we need more
        if scrollbar.maximum() == 0 and len(self.cards) > 0:
            self.load_more.emit()

    def set_downloaded_codes(self, codes: set[str]):
        """Set the list of downloaded movie IMDB codes."""
        self.downloaded_codes = codes

    def set_hidden_codes(self, codes: set[str]):
        """Set the list of hidden movie IMDB codes."""
        self.hidden_codes = codes

    def set_watched_codes(self, codes: set[str]):
        """Set the list of watched movie IMDB codes."""
        self.watched_codes = codes

    def set_library_lookup(self, lookup: set[tuple[str, int | None]]):
        """Set the library lookup set for matching existing movies."""
        self.library_lookup = lookup

    def _is_in_library(self, movie: Movie) -> bool:
        """Check if a movie exists in the local library."""
        normalized = normalize_title(movie.title)

        # Check exact match with year
        if (normalized, movie.year) in self.library_lookup:
            return True

        # Check match without year (filename might not have year)
        for lib_title, lib_year in self.library_lookup:
            if lib_title == normalized:
                if lib_year is None or lib_year == movie.year:
                    return True

        return False

    def _on_hide_requested(self, movie: Movie):
        """Handle hide request from card."""
        self.movie_hidden.emit(movie)

    def _on_watched_requested(self, movie: Movie):
        """Handle watched request from card."""
        self.movie_watched.emit(movie)

    def clear(self):
        """Clear all movie cards."""
        for card in self.cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()

    def add_movies(self, movies: list[Movie], hide_downloaded: bool = True, show_hidden: bool = False, hide_watched: bool = False):
        """Add movies to the grid."""
        start_idx = len(self.cards)

        for movie in movies:
            is_hidden = movie.imdb_code in self.hidden_codes
            is_watched = movie.imdb_code in self.watched_codes

            # Skip hidden movies unless show_hidden is enabled
            if is_hidden and not show_hidden:
                continue

            # Skip watched movies if hide_watched is enabled
            if is_watched and hide_watched:
                continue

            # Check if movie exists in downloaded DB or local library
            in_downloaded_db = movie.imdb_code in self.downloaded_codes
            in_library = self._is_in_library(movie)
            is_owned = in_downloaded_db or in_library

            # Skip owned movies if hiding
            if hide_downloaded and is_owned:
                continue

            is_downloaded = is_owned
            card = MovieCard(movie, is_downloaded, is_hidden, is_watched)
            card.clicked.connect(self.movie_clicked.emit)
            card.hide_requested.connect(self._on_hide_requested)
            card.watched_requested.connect(self._on_watched_requested)

            # Calculate grid position
            idx = len(self.cards)
            row = idx // self.COLUMNS
            col = idx % self.COLUMNS

            self.grid_layout.addWidget(card, row, col)
            self.cards.append(card)

            # Load poster asynchronously
            if movie.medium_cover_image:
                self.image_loader.load(
                    movie.medium_cover_image,
                    card.set_poster
                )
            else:
                card.set_placeholder()

    def set_movies(self, movies: list[Movie], hide_downloaded: bool = True, show_hidden: bool = False, hide_watched: bool = False):
        """Replace all movies in the grid."""
        self.clear()
        self.add_movies(movies, hide_downloaded, show_hidden, hide_watched)

    def relayout_grid(self):
        """Re-layout all cards to fill holes."""
        for i, card in enumerate(self.cards):
            row = i // self.COLUMNS
            col = i % self.COLUMNS
            self.grid_layout.addWidget(card, row, col)

    def set_loading(self, loading: bool):
        """Show/hide loading indicator."""
        # Could add a loading spinner here
        pass

    def show_empty_state(self, message: str = "No movies found"):
        """Show empty state message."""
        self.clear()
        label = QLabel(message)
        label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 18px;
            padding: 40px;
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid_layout.addWidget(label, 0, 0, 1, self.COLUMNS)

    def resizeEvent(self, event):
        """Adjust columns based on width."""
        width = event.size().width()
        card_width = MovieCard.CARD_WIDTH + self.CARD_SPACING
        self.COLUMNS = max(2, width // card_width)
        # Could re-layout here if needed
        super().resizeEvent(event)
