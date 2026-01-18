"""SQLite database for tracking downloaded movies."""

import sqlite3
import os
from datetime import datetime
from typing import Optional
from pathlib import Path


class Database:
    """SQLite database for tracking downloaded/owned movies."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Store in user's app data
            app_dir = Path.home() / ".popcorn-python"
            app_dir.mkdir(exist_ok=True)
            db_path = str(app_dir / "movies.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloaded_movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    imdb_code TEXT UNIQUE,
                    yts_id INTEGER,
                    title TEXT NOT NULL,
                    year INTEGER,
                    file_path TEXT,
                    added_date TEXT,
                    watched INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_imdb_code
                ON downloaded_movies(imdb_code)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hidden_movies (
                    imdb_code TEXT PRIMARY KEY,
                    title TEXT,
                    hidden_date TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watched_movies (
                    imdb_code TEXT PRIMARY KEY,
                    title TEXT,
                    year INTEGER,
                    watched_date TEXT
                )
            """)
            conn.commit()

    def is_downloaded(self, imdb_code: str) -> bool:
        """Check if a movie is already downloaded."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM downloaded_movies WHERE imdb_code = ?",
                (imdb_code,)
            )
            return cursor.fetchone() is not None

    def get_downloaded_imdb_codes(self) -> set[str]:
        """Get all downloaded movie IMDB codes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT imdb_code FROM downloaded_movies"
            )
            return {row[0] for row in cursor.fetchall()}

    def add_downloaded(
        self,
        imdb_code: str,
        title: str,
        year: int,
        yts_id: int = None,
        file_path: str = None
    ):
        """Add a movie to the downloaded list."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO downloaded_movies
                (imdb_code, yts_id, title, year, file_path, added_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (imdb_code, yts_id, title, year, file_path,
                  datetime.now().isoformat()))
            conn.commit()

    def remove_downloaded(self, imdb_code: str):
        """Remove a movie from downloaded list."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM downloaded_movies WHERE imdb_code = ?",
                (imdb_code,)
            )
            conn.commit()

    def set_watched(self, imdb_code: str, watched: bool = True):
        """Mark a movie as watched/unwatched."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE downloaded_movies SET watched = ? WHERE imdb_code = ?",
                (1 if watched else 0, imdb_code)
            )
            conn.commit()

    def get_all_downloaded(self) -> list[dict]:
        """Get all downloaded movies."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM downloaded_movies ORDER BY added_date DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    # Settings helpers
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key: str, value: str):
        """Set a setting value."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()

    def get_library_folders(self) -> list[str]:
        """Get configured library folders to scan."""
        folders = self.get_setting("library_folders", "")
        return [f.strip() for f in folders.split(";") if f.strip()]

    def set_library_folders(self, folders: list[str]):
        """Set library folders."""
        self.set_setting("library_folders", ";".join(folders))

    # Hidden movies
    def hide_movie(self, imdb_code: str, title: str):
        """Hide a movie from the grid."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO hidden_movies (imdb_code, title, hidden_date) VALUES (?, ?, ?)",
                (imdb_code, title, datetime.now().isoformat())
            )
            conn.commit()

    def unhide_movie(self, imdb_code: str):
        """Unhide a movie."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM hidden_movies WHERE imdb_code = ?", (imdb_code,))
            conn.commit()

    def is_hidden(self, imdb_code: str) -> bool:
        """Check if a movie is hidden."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM hidden_movies WHERE imdb_code = ?", (imdb_code,)
            )
            return cursor.fetchone() is not None

    def get_hidden_imdb_codes(self) -> set[str]:
        """Get all hidden movie IMDB codes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT imdb_code FROM hidden_movies")
            return {row[0] for row in cursor.fetchall()}

    def get_all_hidden(self) -> list[dict]:
        """Get all hidden movies."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM hidden_movies ORDER BY hidden_date DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    # Watched movies
    def mark_watched(self, imdb_code: str, title: str, year: int):
        """Mark a movie as watched."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO watched_movies (imdb_code, title, year, watched_date) VALUES (?, ?, ?, ?)",
                (imdb_code, title, year, datetime.now().isoformat())
            )
            conn.commit()

    def unmark_watched(self, imdb_code: str):
        """Remove watched mark from a movie."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM watched_movies WHERE imdb_code = ?", (imdb_code,))
            conn.commit()

    def is_watched(self, imdb_code: str) -> bool:
        """Check if a movie is marked as watched."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM watched_movies WHERE imdb_code = ?", (imdb_code,)
            )
            return cursor.fetchone() is not None

    def get_watched_imdb_codes(self) -> set[str]:
        """Get all watched movie IMDB codes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT imdb_code FROM watched_movies")
            return {row[0] for row in cursor.fetchall()}

    def get_all_watched(self) -> list[dict]:
        """Get all watched movies."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM watched_movies ORDER BY watched_date DESC"
            )
            return [dict(row) for row in cursor.fetchall()]


# Test
if __name__ == "__main__":
    db = Database()
    print(f"Database at: {db.db_path}")

    # Test adding a movie
    db.add_downloaded("tt1234567", "Test Movie", 2024, yts_id=12345)
    print(f"Is downloaded: {db.is_downloaded('tt1234567')}")
    print(f"All downloaded: {db.get_all_downloaded()}")

    # Clean up test
    db.remove_downloaded("tt1234567")
