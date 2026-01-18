"""qBittorrent WebUI API client."""

from typing import Optional
import qbittorrentapi


class QBittorrentClient:
    """Client for qBittorrent WebUI API."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        username: str = "admin",
        password: str = "adminadmin"
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client: Optional[qbittorrentapi.Client] = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to qBittorrent WebUI."""
        try:
            self.client = qbittorrentapi.Client(
                host=f"{self.host}:{self.port}",
                username=self.username,
                password=self.password,
            )
            self.client.auth_log_in()
            self._connected = True
            print(f"Connected to qBittorrent {self.client.app.version}")
            return True
        except qbittorrentapi.LoginFailed:
            print("qBittorrent login failed - check credentials")
            self._connected = False
            return False
        except Exception as e:
            print(f"qBittorrent connection error: {e}")
            self._connected = False
            return False

    @property
    def is_connected(self) -> bool:
        """Check if connected to qBittorrent."""
        if not self._connected or not self.client:
            return False
        try:
            self.client.app.version
            return True
        except Exception:
            self._connected = False
            return False

    def add_torrent(
        self,
        magnet_or_url: str,
        save_path: str = None,
        category: str = "Movies"
    ) -> bool:
        """
        Add a torrent to qBittorrent.

        Args:
            magnet_or_url: Magnet link or torrent URL
            save_path: Download location (optional)
            category: Category to assign

        Returns:
            True if successful
        """
        if not self.is_connected:
            if not self.connect():
                return False

        try:
            options = {"category": category}
            if save_path:
                options["savepath"] = save_path

            if magnet_or_url.startswith("magnet:"):
                self.client.torrents_add(urls=magnet_or_url, **options)
            else:
                self.client.torrents_add(urls=magnet_or_url, **options)

            print(f"Torrent added successfully")
            return True

        except Exception as e:
            print(f"Failed to add torrent: {e}")
            return False

    def get_download_progress(self, torrent_hash: str) -> Optional[dict]:
        """Get download progress for a torrent."""
        if not self.is_connected:
            return None

        try:
            torrents = self.client.torrents_info(torrent_hashes=torrent_hash)
            if torrents:
                t = torrents[0]
                return {
                    "name": t.name,
                    "progress": t.progress * 100,
                    "state": t.state,
                    "download_speed": t.dlspeed,
                    "upload_speed": t.upspeed,
                    "eta": t.eta,
                    "size": t.size,
                }
        except Exception as e:
            print(f"Error getting progress: {e}")
        return None

    def get_all_torrents(self) -> list[dict]:
        """Get all torrents."""
        if not self.is_connected:
            return []

        try:
            torrents = self.client.torrents_info()
            return [{
                "hash": t.hash,
                "name": t.name,
                "progress": t.progress * 100,
                "state": t.state,
                "size": t.size,
            } for t in torrents]
        except Exception:
            return []

    def get_default_save_path(self) -> str:
        """Get qBittorrent's default save path."""
        if not self.is_connected:
            return ""
        try:
            return self.client.app.default_save_path
        except Exception:
            return ""


# Test
if __name__ == "__main__":
    qb = QBittorrentClient()
    if qb.connect():
        print(f"Default save path: {qb.get_default_save_path()}")
        print(f"Current torrents: {len(qb.get_all_torrents())}")
    else:
        print("Could not connect to qBittorrent")
        print("Make sure qBittorrent is running with WebUI enabled")
        print("(Tools > Options > Web UI > Enable Web UI)")
