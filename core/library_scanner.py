"""Scan local movie folders to find existing movies."""

import re
from pathlib import Path


# Common video extensions
VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.m4v', '.webm'}


def extract_title_year(filename: str) -> tuple[str, int | None]:
    """
    Extract movie title and year from filename.
    Handles formats like:
    - Movie Name (2020).mkv
    - Movie.Name.2020.1080p.BluRay.mkv
    - Movie Name [2020].mkv
    """
    # Remove extension
    name = Path(filename).stem

    # Try to find year in parentheses: "Movie Name (2020)"
    match = re.search(r'^(.+?)\s*[\(\[](\d{4})[\)\]]', name)
    if match:
        title = match.group(1).strip()
        year = int(match.group(2))
        return title, year

    # Try to find year with dots: "Movie.Name.2020.1080p"
    match = re.search(r'^(.+?)\.(\d{4})\.', name)
    if match:
        title = match.group(1).replace('.', ' ').strip()
        year = int(match.group(2))
        return title, year

    # Try to find standalone year: "Movie Name 2020"
    match = re.search(r'^(.+?)\s+(\d{4})(?:\s|$)', name)
    if match:
        title = match.group(1).strip()
        year = int(match.group(2))
        return title, year

    # No year found, just clean up the title
    title = re.sub(r'[\._]', ' ', name)
    title = re.sub(r'\s+', ' ', title).strip()
    return title, None


def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    # Lowercase, remove punctuation, normalize whitespace
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def scan_folder(folder_path: str) -> list[dict]:
    """
    Scan a folder for movie files.
    Returns list of dicts with title, year, and path.
    """
    movies = []
    folder = Path(folder_path)

    if not folder.exists():
        return movies

    # Scan for video files (including in subdirectories)
    for path in folder.rglob('*'):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            title, year = extract_title_year(path.name)
            movies.append({
                'title': title,
                'normalized_title': normalize_title(title),
                'year': year,
                'path': str(path),
            })

    return movies


def scan_folders(folder_paths: list[str]) -> list[dict]:
    """Scan multiple folders for movies."""
    all_movies = []
    for folder in folder_paths:
        all_movies.extend(scan_folder(folder))
    return all_movies


def build_lookup_set(movies: list[dict]) -> set[tuple[str, int | None]]:
    """Build a set of (normalized_title, year) tuples for fast lookup."""
    return {(m['normalized_title'], m['year']) for m in movies}


def movie_exists_in_library(title: str, year: int, lookup_set: set) -> bool:
    """Check if a movie exists in the library."""
    normalized = normalize_title(title)

    # Exact match with year
    if (normalized, year) in lookup_set:
        return True

    # Match without year (in case year is missing from filename)
    for lib_title, lib_year in lookup_set:
        if lib_title == normalized:
            # If years match or one is missing, consider it a match
            if lib_year is None or lib_year == year:
                return True

    return False


# Test
if __name__ == "__main__":
    test_names = [
        "Inception (2010).mkv",
        "The.Dark.Knight.2008.1080p.BluRay.x264.mkv",
        "Interstellar [2014].mp4",
        "Avatar 2009.avi",
        "Some Random Movie.mkv",
    ]

    for name in test_names:
        title, year = extract_title_year(name)
        print(f"{name} -> '{title}' ({year})")
