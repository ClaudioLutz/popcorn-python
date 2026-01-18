"""YTS API Client for fetching movie data."""

import requests
from typing import Optional
from dataclasses import dataclass


@dataclass
class Torrent:
    url: str
    hash: str
    quality: str
    type: str
    size: str
    size_bytes: int
    seeds: int
    peers: int


@dataclass
class Movie:
    id: int
    imdb_code: str
    title: str
    title_long: str
    year: int
    rating: float
    runtime: int
    genres: list[str]
    synopsis: str
    language: str
    background_image: str
    small_cover_image: str
    medium_cover_image: str
    large_cover_image: str
    torrents: list[Torrent]

    @classmethod
    def from_dict(cls, data: dict) -> "Movie":
        torrents = []
        for t in data.get("torrents", []):
            torrents.append(Torrent(
                url=t.get("url", ""),
                hash=t.get("hash", ""),
                quality=t.get("quality", ""),
                type=t.get("type", ""),
                size=t.get("size", ""),
                size_bytes=t.get("size_bytes", 0),
                seeds=t.get("seeds", 0),
                peers=t.get("peers", 0),
            ))

        return cls(
            id=data.get("id", 0),
            imdb_code=data.get("imdb_code", ""),
            title=data.get("title", ""),
            title_long=data.get("title_long", ""),
            year=data.get("year", 0),
            rating=data.get("rating", 0.0),
            runtime=data.get("runtime", 0),
            genres=data.get("genres", []),
            synopsis=data.get("synopsis", ""),
            language=data.get("language", ""),
            background_image=data.get("background_image", ""),
            small_cover_image=data.get("small_cover_image", ""),
            medium_cover_image=data.get("medium_cover_image", ""),
            large_cover_image=data.get("large_cover_image", ""),
            torrents=torrents,
        )

    def get_magnet(self, quality: str = "1080p") -> Optional[str]:
        """Get magnet link for specified quality."""
        for torrent in self.torrents:
            if torrent.quality == quality:
                return f"magnet:?xt=urn:btih:{torrent.hash}&dn={self.title}&tr=udp://open.demonii.com:1337/announce&tr=udp://tracker.openbittorrent.com:80"
        # Fallback to first available
        if self.torrents:
            t = self.torrents[0]
            return f"magnet:?xt=urn:btih:{t.hash}&dn={self.title}&tr=udp://open.demonii.com:1337/announce&tr=udp://tracker.openbittorrent.com:80"
        return None


class YTSApi:
    """Client for YTS movie API."""

    # Multiple mirrors in case one is blocked
    MIRRORS = [
        "https://yts.lt/api/v2",
        "https://yts.mx/api/v2",
        "https://yts.rs/api/v2",
        "https://yts.torrentbay.to/api/v2",
    ]

    BASE_URL = MIRRORS[0]  # Will be updated if mirror fails

    GENRES = [
        "All", "Action", "Adventure", "Animation", "Biography", "Comedy",
        "Crime", "Documentary", "Drama", "Family", "Fantasy", "Film-Noir",
        "History", "Horror", "Music", "Musical", "Mystery", "Romance",
        "Sci-Fi", "Sport", "Thriller", "War", "Western"
    ]

    SORT_OPTIONS = {
        "Trending": "download_count",
        "Latest": "date_added",
        "Rating": "rating",
        "Seeds": "seeds",
        "Year": "year",
        "Title": "title",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PopcornPython/1.0"
        })
        self.current_mirror_idx = 0
        self._find_working_mirror()

    def _find_working_mirror(self):
        """Try each mirror until one works with valid JSON response."""
        for idx, mirror in enumerate(self.MIRRORS):
            try:
                response = self.session.get(
                    f"{mirror}/list_movies.json",
                    params={"limit": 1},
                    timeout=5
                )
                if response.status_code == 200:
                    # Validate that response is actually valid JSON with expected structure
                    data = response.json()
                    if data.get("status") == "ok" and "data" in data:
                        self.BASE_URL = mirror
                        self.current_mirror_idx = idx
                        print(f"Using YTS mirror: {mirror}")
                        return
                    else:
                        print(f"Mirror {mirror} returned invalid data structure")
            except (requests.RequestException, ValueError) as e:
                print(f"Mirror {mirror} failed: {e}")
                continue
        print("Warning: No YTS mirrors reachable")

    def _try_request(self, endpoint: str, params: dict) -> Optional[dict]:
        """Try request on current mirror, fallback to others if it fails."""
        mirrors_to_try = (
            [self.MIRRORS[self.current_mirror_idx]] +
            [m for i, m in enumerate(self.MIRRORS) if i != self.current_mirror_idx]
        )

        for mirror in mirrors_to_try:
            try:
                response = self.session.get(
                    f"{mirror}/{endpoint}",
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "ok":
                    # Update to working mirror if it changed
                    if mirror != self.BASE_URL:
                        self.BASE_URL = mirror
                        self.current_mirror_idx = self.MIRRORS.index(mirror)
                        print(f"Switched to YTS mirror: {mirror}")
                    return data
            except (requests.RequestException, ValueError) as e:
                print(f"Mirror {mirror} failed for {endpoint}: {e}")
                continue

        return None

    def list_movies(
        self,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "download_count",
        genre: Optional[str] = None,
        query: Optional[str] = None,
        minimum_rating: int = 0,
        order_by: str = "desc",
    ) -> tuple[list[Movie], int]:
        """
        Fetch list of movies from YTS API.

        Returns:
            Tuple of (movies list, total movie count)
        """
        params = {
            "page": page,
            "limit": limit,
            "sort_by": sort_by,
            "order_by": order_by,
            "minimum_rating": minimum_rating,
        }

        if genre and genre.lower() != "all":
            params["genre"] = genre.lower()

        if query:
            params["query_term"] = query

        data = self._try_request("list_movies.json", params)

        if not data:
            print("YTS API error: All mirrors failed")
            return [], 0

        movie_data = data.get("data", {})
        movie_count = movie_data.get("movie_count", 0)
        movies_raw = movie_data.get("movies", [])

        if not movies_raw:
            return [], movie_count

        movies = [Movie.from_dict(m) for m in movies_raw]
        return movies, movie_count

    def get_movie_details(self, movie_id: int) -> Optional[Movie]:
        """Fetch detailed info for a specific movie."""
        params = {"movie_id": movie_id, "with_images": True, "with_cast": True}
        data = self._try_request("movie_details.json", params)

        if not data:
            return None

        movie_data = data.get("data", {}).get("movie")
        if movie_data:
            return Movie.from_dict(movie_data)
        return None

    def get_suggestions(self, movie_id: int) -> list[Movie]:
        """Get movie suggestions based on a movie."""
        params = {"movie_id": movie_id}
        data = self._try_request("movie_suggestions.json", params)

        if not data:
            return []

        movies_raw = data.get("data", {}).get("movies", [])
        return [Movie.from_dict(m) for m in movies_raw]


# Test the API
if __name__ == "__main__":
    api = YTSApi()
    movies, count = api.list_movies(limit=5, sort_by="download_count")
    print(f"Total movies: {count}")
    for movie in movies:
        print(f"  - {movie.title} ({movie.year}) - Rating: {movie.rating}")
        print(f"    Genres: {', '.join(movie.genres)}")
        print(f"    Poster: {movie.medium_cover_image}")
