import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
SOURCES_FILE = DATA_DIR / "sources.json"
CATALOG_FILE = DATA_DIR / "catalog.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
INSTALLED_GAMES_FILE = DATA_DIR / "installed_games.json"
DOWNLOADS_DIR = Path.home() / "Downloads" / "RevLauncher"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SETTINGS = {
    "app_name": "Rev-Launcher",
    "version": "2.0.0",
    "theme": "Revision_Noir_Crimson",
    "window_width": 1360,
    "window_height": 840,
    "auto_refresh_sources": True,
    "p2p_mesh_enabled": True,
    "mesh_port": 8767,
    "torrent_client_auto": True,
    "max_concurrent_downloads": 3,
    "downloads_path": str(DOWNLOADS_DIR)
}

DEFAULT_SOURCES = [
    {
        "id": "steamrip",
        "name": "SteamRip Official",
        "url": "https://raw.githubusercontent.com/hydralinks/hydra-links/master/sources/steamrip.json",
        "enabled": True,
        "type": "hydra",
        "description": "Pre-installed Steam releases with clean direct & mirror links"
    },
    {
        "id": "fitgirl",
        "name": "FitGirl Repacks",
        "url": "https://raw.githubusercontent.com/hydralinks/hydra-links/master/sources/fitgirl.json",
        "enabled": True,
        "type": "hydra",
        "description": "High compression repacks with fast magnet links"
    },
    {
        "id": "dodi",
        "name": "DODI Repacks",
        "url": "https://raw.githubusercontent.com/hydralinks/hydra-links/master/sources/dodi.json",
        "enabled": True,
        "type": "hydra",
        "description": "Verified ultra-fast installation game repacks"
    },
    {
        "id": "gog",
        "name": "GOG DRM-Free",
        "url": "https://raw.githubusercontent.com/hydralinks/hydra-links/master/sources/gog.json",
        "enabled": True,
        "type": "hydra",
        "description": "DRM-free digital installers and bonus goodies"
    }
]

class ConfigManager:
    def __init__(self):
        self.settings = self._load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        self.sources = self._load_json(SOURCES_FILE, DEFAULT_SOURCES)

    def _load_json(self, path: Path, default):
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(default, dict):
                        merged = dict(default)
                        merged.update(data)
                        return merged
                    return data
            except Exception:
                pass
        return default

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"[CONFIG ERROR] Failed to save settings: {e}")

    def save_sources(self):
        try:
            with open(SOURCES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.sources, f, indent=4)
        except Exception as e:
            print(f"[CONFIG ERROR] Failed to save sources: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

config = ConfigManager()
