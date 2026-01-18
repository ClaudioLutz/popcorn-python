# Popcorn Python

A Popcorn Time-style movie browser built with Python and PyQt6. Browse trending movies from YTS, filter by genre, search, and send downloads directly to qBittorrent.

## Features

- **Movie Browser** - Fetches trending movies with poster images
- **Genre Filter** - Filter by 20+ genres (Action, Horror, Comedy, etc.)
- **Sort Options** - Trending, Latest, Rating, Seeds, Year, Title
- **Search** - Search movies by title
- **Hide Downloaded** - Toggle to hide movies you already have
- **Movie Details** - Click any movie to see synopsis, rating, and quality options
- **Download Integration** - Sends magnet links directly to qBittorrent
- **Dark Theme** - Popcorn Time-style dark UI
- **Infinite Scroll** - Automatically loads more movies as you scroll

## Requirements

- Python 3.10+
- qBittorrent with Web UI enabled (for downloads)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/popcorn-python.git
   cd popcorn-python
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `.\venv\Scripts\Activate.ps1`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python main.py
```

## qBittorrent Setup

To enable download functionality:

1. Open qBittorrent
2. Go to **Tools > Options > Web UI**
3. Check **"Enable the Web User Interface (Remote control)"**
4. Set the port to `8080`
5. Set username: `admin`
6. Set password: `adminadmin`

Or update the credentials in `core/qbittorrent.py` to match your settings.

## Project Structure

```
popcorn-python/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── core/
│   ├── yts_api.py      # YTS API client with mirror fallback
│   ├── database.py     # SQLite for tracking downloads
│   └── qbittorrent.py  # qBittorrent WebUI client
└── ui/
    ├── main_window.py  # Main application window
    ├── movie_grid.py   # Scrollable poster grid
    ├── movie_card.py   # Individual movie poster card
    ├── filter_bar.py   # Genre/sort/search controls
    ├── movie_dialog.py # Movie details popup
    └── styles.py       # Dark theme colors
```

## Configuration

Downloaded movie tracking is stored in:
- Windows: `%USERPROFILE%\.popcorn-python\movies.db`
- Linux/Mac: `~/.popcorn-python/movies.db`

## API Mirrors

The app automatically tries multiple YTS API mirrors if one is unavailable:
- yts.lt
- yts.mx
- yts.rs
- yts.torrentbay.to

## License

MIT
