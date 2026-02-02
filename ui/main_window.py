"""Main application window."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStatusBar, QLabel,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.yts_api import YTSApi, Movie
from core.database import Database
from core.qbittorrent import QBittorrentClient
from core.library_scanner import scan_folders, build_lookup_set, normalize_title
from ui.filter_bar import FilterBar
from ui.movie_grid import MovieGrid
from ui.movie_dialog import MovieDialog
from ui.styles import DARK_THEME, COLORS


class MovieLoaderThread(QThread):
    """Background thread for loading movies from API."""

    movies_loaded = pyqtSignal(list, int)  # movies, total_count
    error_occurred = pyqtSignal(str)

    def __init__(self, api: YTSApi):
        super().__init__()
        self.api = api
        self.page = 1
        self.genre = None
        self.sort_by = "download_count"
        self.order_by = "desc"
        self.query = None
        self.minimum_rating = 0

    def run(self):
        try:
            movies, total = self.api.list_movies(
                page=self.page,
                limit=20,
                genre=self.genre,
                sort_by=self.sort_by,
                order_by=self.order_by,
                query=self.query if self.query else None,
                minimum_rating=self.minimum_rating
            )
            self.movies_loaded.emit(movies, total)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Initialize components
        self.api = YTSApi()
        self.db = Database()
        self.qb = QBittorrentClient()

        # State
        self.current_page = 1
        self.total_movies = 0
        self.is_loading = False
        self.current_filters = {}
        self.library_lookup = set()
        self.empty_pages_count = 0  # Track consecutive pages with all movies filtered

        # Initialize library folders if not set
        self._init_library()

        self._setup_ui()
        self._connect_signals()
        self._try_connect_qbittorrent()
        self._load_movies()

    def _init_library(self):
        """Initialize library folders and scan for existing movies."""
        folders = self.db.get_library_folders()

        # Set default if no folders configured
        if not folders:
            default_folder = r"D:\Media\Movies"
            self.db.set_library_folders([default_folder])
            folders = [default_folder]

        # Scan folders and build lookup set
        print(f"Scanning library folders: {folders}")
        movies = scan_folders(folders)
        self.library_lookup = build_lookup_set(movies)
        print(f"Found {len(movies)} movies in library")

    def _setup_ui(self):
        self.setWindowTitle("Popcorn Python")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(DARK_THEME)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Filter bar
        self.filter_bar = FilterBar()
        layout.addWidget(self.filter_bar)

        # Movie grid
        self.movie_grid = MovieGrid()
        self.movie_grid.set_downloaded_codes(self.db.get_downloaded_imdb_codes())
        self.movie_grid.set_hidden_codes(self.db.get_hidden_imdb_codes())
        self.movie_grid.set_watched_codes(self.db.get_watched_imdb_codes())
        self.movie_grid.set_watchlist_codes(self.db.get_watchlist_imdb_codes())
        self.movie_grid.set_library_lookup(self.library_lookup)
        layout.addWidget(self.movie_grid)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        self.qb_status = QLabel("qBittorrent: Disconnected")
        self.qb_status.setStyleSheet(f"color: {COLORS['error']};")
        self.status_bar.addPermanentWidget(self.qb_status)

    def _connect_signals(self):
        """Connect widget signals."""
        self.filter_bar.filters_changed.connect(self._on_filters_changed)
        self.movie_grid.movie_clicked.connect(self._on_movie_clicked)
        self.movie_grid.movie_hidden.connect(self._on_movie_hidden)
        self.movie_grid.movie_watched.connect(self._on_movie_watched)
        self.movie_grid.movie_watchlist.connect(self._on_movie_watchlist)
        self.movie_grid.load_more.connect(self._load_more_movies)

    def _try_connect_qbittorrent(self):
        """Try to connect to qBittorrent."""
        if self.qb.connect():
            self.qb_status.setText("qBittorrent: Connected ✓")
            self.qb_status.setStyleSheet(f"color: {COLORS['success']};")
        else:
            self.qb_status.setText("qBittorrent: Disconnected")
            self.qb_status.setStyleSheet(f"color: {COLORS['error']};")

    def _on_filters_changed(self, filters: dict):
        """Handle filter changes."""
        self.current_filters = filters
        self.current_page = 1
        self.empty_pages_count = 0  # Reset empty pages counter
        self._load_movies()

    def _load_movies(self):
        """Load movies from API."""
        if self.is_loading:
            return

        self.is_loading = True
        self.status_label.setText("Loading movies...")

        # Create loader thread
        self.loader = MovieLoaderThread(self.api)
        self.loader.page = self.current_page
        self.loader.genre = self.current_filters.get("genre")
        self.loader.sort_by = self.current_filters.get("sort_by", "download_count")
        self.loader.order_by = self.current_filters.get("order_by", "desc")
        self.loader.query = self.current_filters.get("query")
        self.loader.minimum_rating = self.current_filters.get("minimum_rating", 0)

        self.loader.movies_loaded.connect(self._on_movies_loaded)
        self.loader.error_occurred.connect(self._on_load_error)
        self.loader.start()

    def _load_more_movies(self):
        """Load next page of movies."""
        if self.is_loading:
            return

        self.current_page += 1
        self.is_loading = True
        self.status_label.setText(f"Loading page {self.current_page}...")

        self.loader = MovieLoaderThread(self.api)
        self.loader.page = self.current_page
        self.loader.genre = self.current_filters.get("genre")
        self.loader.sort_by = self.current_filters.get("sort_by", "download_count")
        self.loader.order_by = self.current_filters.get("order_by", "desc")
        self.loader.query = self.current_filters.get("query")
        self.loader.minimum_rating = self.current_filters.get("minimum_rating", 0)

        self.loader.movies_loaded.connect(self._on_more_movies_loaded)
        self.loader.error_occurred.connect(self._on_load_error)
        self.loader.start()

    def _on_movies_loaded(self, movies: list[Movie], total: int):
        """Handle movies loaded."""
        self.is_loading = False
        self.total_movies = total
        self.empty_pages_count = 0  # Reset on initial load

        cards_before = len(self.movie_grid.cards)
        self.movie_grid.set_movies(movies, self.current_filters)
        cards_after = len(self.movie_grid.cards)

        self.status_label.setText(f"Showing {cards_after} of {total} movies")

        if not movies:
            self.movie_grid.show_empty_state("No movies found. Try different filters.")
        elif cards_after == 0 and movies:
            # All movies were filtered out, try loading more
            self.empty_pages_count += 1
            if self.empty_pages_count < 20:  # Try up to 20 pages
                self.movie_grid.check_needs_more()
            else:
                self.movie_grid.show_empty_state("All movies filtered. Try different filters.")
        else:
            # Check if we need more content to fill the viewport
            self.movie_grid.check_needs_more()

    def _on_more_movies_loaded(self, movies: list[Movie], total: int):
        """Handle additional movies loaded."""
        self.is_loading = False
        self.total_movies = total

        cards_before = len(self.movie_grid.cards)
        self.movie_grid.add_movies(movies, self.current_filters)
        cards_after = len(self.movie_grid.cards)

        self.status_label.setText(f"Showing {cards_after} of {total} movies")

        # Track if this page added no visible cards
        if cards_after == cards_before and movies:
            self.empty_pages_count += 1
        else:
            self.empty_pages_count = 0  # Reset on successful add

        # Check if we still need more content to fill the viewport
        # Stop after 20 consecutive empty pages to prevent infinite loop
        if self.empty_pages_count < 20:
            self.movie_grid.check_needs_more()
        elif cards_after == 0:
            self.movie_grid.show_empty_state("All movies filtered. Try different filters.")

    def _on_load_error(self, error: str):
        """Handle load error."""
        self.is_loading = False
        self.status_label.setText(f"Error: {error}")
        self.movie_grid.show_empty_state(f"Failed to load movies:\n{error}")

    def _on_movie_clicked(self, movie: Movie):
        """Handle movie card click."""
        dialog = MovieDialog(movie, self)
        dialog.download_requested.connect(self._on_download_requested)
        dialog.exec()

    def _on_movie_hidden(self, movie: Movie):
        """Handle movie hide/unhide request."""
        is_currently_hidden = self.db.is_hidden(movie.imdb_code)

        if is_currently_hidden:
            # Unhide the movie
            self.db.unhide_movie(movie.imdb_code)
            self.status_label.setText(f"Unhidden: {movie.title}")
        else:
            # Hide the movie
            self.db.hide_movie(movie.imdb_code, movie.title)
            self.status_label.setText(f"Hidden: {movie.title}")

        # Update grid's hidden codes
        self.movie_grid.set_hidden_codes(self.db.get_hidden_imdb_codes())

        # Remove the card from the grid and relayout
        for card in self.movie_grid.cards[:]:
            if card.movie.imdb_code == movie.imdb_code:
                self.movie_grid.grid_layout.removeWidget(card)
                self.movie_grid.cards.remove(card)
                card.deleteLater()
                break

        # Relayout to fill holes
        self.movie_grid.relayout_grid()

    def _on_movie_watched(self, movie: Movie):
        """Handle movie watched/unwatched request."""
        is_currently_watched = self.db.is_watched(movie.imdb_code)

        if is_currently_watched:
            # Unmark as watched
            self.db.unmark_watched(movie.imdb_code)
            self.status_label.setText(f"Unmarked as watched: {movie.title}")
        else:
            # Mark as watched
            self.db.mark_watched(movie.imdb_code, movie.title, movie.year)
            self.status_label.setText(f"Marked as watched: {movie.title}")

        # Update grid's watched codes
        self.movie_grid.set_watched_codes(self.db.get_watched_imdb_codes())

        # Remove the card from the grid and relayout (to update the card state)
        for card in self.movie_grid.cards[:]:
            if card.movie.imdb_code == movie.imdb_code:
                self.movie_grid.grid_layout.removeWidget(card)
                self.movie_grid.cards.remove(card)
                card.deleteLater()
                break

        # Relayout to fill holes
        self.movie_grid.relayout_grid()

    def _on_movie_watchlist(self, movie: Movie):
        """Handle movie watchlist add/remove request."""
        is_currently_in_watchlist = self.db.is_in_watchlist(movie.imdb_code)

        if is_currently_in_watchlist:
            # Remove from watchlist
            self.db.remove_from_watchlist(movie.imdb_code)
            self.status_label.setText(f"Removed from watchlist: {movie.title}")
        else:
            # Add to watchlist
            self.db.add_to_watchlist(movie.imdb_code, movie.title, movie.year)
            self.status_label.setText(f"Added to watchlist: {movie.title}")

        # Update grid's watchlist codes
        self.movie_grid.set_watchlist_codes(self.db.get_watchlist_imdb_codes())

        # Remove the card from the grid and relayout (to update the card state)
        for card in self.movie_grid.cards[:]:
            if card.movie.imdb_code == movie.imdb_code:
                self.movie_grid.grid_layout.removeWidget(card)
                self.movie_grid.cards.remove(card)
                card.deleteLater()
                break

        # Relayout to fill holes
        self.movie_grid.relayout_grid()

    def _on_download_requested(self, movie: Movie, quality: str):
        """Handle download request."""
        if not self.qb.is_connected:
            if not self.qb.connect():
                QMessageBox.warning(
                    self,
                    "Connection Error",
                    "Cannot connect to qBittorrent.\n\n"
                    "Make sure qBittorrent is running with WebUI enabled.\n"
                    "(Tools > Options > Web UI)"
                )
                return

        magnet = movie.get_magnet(quality)
        if not magnet:
            QMessageBox.warning(self, "Error", "Could not get magnet link")
            return

        if self.qb.add_torrent(magnet):
            # Add to downloaded database
            self.db.add_downloaded(
                imdb_code=movie.imdb_code,
                title=movie.title,
                year=movie.year,
                yts_id=movie.id
            )

            # Update grid's downloaded codes
            self.movie_grid.set_downloaded_codes(self.db.get_downloaded_imdb_codes())

            self.status_label.setText(f"Added: {movie.title} ({quality})")
            self.qb_status.setText("qBittorrent: Connected ✓")
            self.qb_status.setStyleSheet(f"color: {COLORS['success']};")
        else:
            QMessageBox.warning(
                self,
                "Download Error",
                f"Failed to add torrent to qBittorrent"
            )

    def closeEvent(self, event):
        """Handle window close."""
        event.accept()
