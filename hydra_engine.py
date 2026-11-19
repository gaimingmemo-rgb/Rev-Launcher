import os
import sys
import json
import time
import urllib.request
import threading
from pathlib import Path
from config import CATALOG_FILE, SOURCES_FILE, config

BUILTIN_GAMES_CATALOG = [
    {
        "id": "cp2077",
        "title": "Cyberpunk 2077: Phantom Liberty",
        "source": "SteamRip Official",
        "category": "RPG / Sci-Fi",
        "fileSize": "76.4 GB",
        "uploadDate": "2026-03-12",
        "uris": [
            "magnet:?xt=urn:btih:3fa8294a2b6e709a341b52ce79860b29846dc752&dn=Cyberpunk+2077+Phantom+Liberty+Revision",
            "https://steamrip.com/cyberpunk-2077-phantom-liberty-free-download/",
            "https://gofile.io/d/cp2077_rev_tactical"
        ],
        "description": "An open-world, action-adventure RPG set in the megalopolis of Night City. Includes Update 2.13 and Phantom Liberty DLC.",
        "icon": "🌆"
    },
    {
        "id": "eldenring",
        "title": "ELDEN RING: Shadow of the Erdtree",
        "source": "FitGirl Repacks",
        "category": "Action / RPG",
        "fileSize": "49.2 GB",
        "uploadDate": "2026-02-18",
        "uris": [
            "magnet:?xt=urn:btih:e29bb37612efc4d79e8fa655bc10e98059e0a4f5&dn=Elden+Ring+Shadow+Of+The+Erdtree+FitGirl",
            "https://fitgirl-repacks.site/elden-ring-shadow-of-the-erdtree/",
            "https://datanodes.to/elden_erdtree_rev"
        ],
        "description": "Rise, Tarnished, and be guided by grace to brandish the power of the Elden Ring and become an Elden Lord in the Lands Between.",
        "icon": "⚔️"
    },
    {
        "id": "rdr2",
        "title": "Red Dead Redemption 2: Ultimate Edition",
        "source": "DODI Repacks",
        "category": "Action / Open World",
        "fileSize": "66.3 GB",
        "uploadDate": "2026-01-20",
        "uris": [
            "magnet:?xt=urn:btih:8c7b89f53e2069b2da801824efac01cb67b4f8d2&dn=Red+Dead+Redemption+2+Ultimate+Edition",
            "https://dodi-repacks.site/red-dead-redemption-2-ultimate/",
            "https://buzzheavier.com/f/rdr2_ultimate"
        ],
        "description": "America, 1899. Arthur Morgan and the Van der Linde gang are outlaws on the run across the rugged heartland of America.",
        "icon": "🤠"
    },
    {
        "id": "blackmyth",
        "title": "Black Myth: Wukong",
        "source": "SteamRip Official",
        "category": "Action / Fantasy",
        "fileSize": "118.5 GB",
        "uploadDate": "2026-04-05",
        "uris": [
            "magnet:?xt=urn:btih:b67489da102c94bb51f286847bc01b44917cc510&dn=Black+Myth+Wukong+Full+Release",
            "https://steamrip.com/black-myth-wukong-free-download/"
        ],
        "description": "Action RPG rooted in Chinese mythology. Set out as the Destined One to venture into the challenges and marvels ahead.",
        "icon": "🐒"
    },
    {
        "id": "gow_ragnarok",
        "title": "God of War Ragnarök: Valhalla",
        "source": "FitGirl Repacks",
        "category": "Action / Adventure",
        "fileSize": "84.1 GB",
        "uploadDate": "2026-03-01",
        "uris": [
            "magnet:?xt=urn:btih:7593cba841b52ee7860b29846dc752fa8294a2b6&dn=God+of+War+Ragnarok+PC+FitGirl",
            "https://fitgirl-repacks.site/god-of-war-ragnarok/"
        ],
        "description": "Kratos and Atreus embark on a mythic journey for answers before Ragnarök arrives.",
        "icon": "🪓"
    },
    {
        "id": "gta5",
        "title": "Grand Theft Auto V: Enhanced Edition",
        "source": "DODI Repacks",
        "category": "Action / Open World",
        "fileSize": "58.7 GB",
        "uploadDate": "2026-02-10",
        "uris": [
            "magnet:?xt=urn:btih:41860b29846dc752fa8294a2b6e709a352ce7986&dn=GTA+V+Enhanced+Revision+DODI",
            "https://dodi-repacks.site/grand-theft-auto-v/"
        ],
        "description": "Explore the award-winning world of Los Santos and Blaine County in the ultimate GTA experience.",
        "icon": "🚗"
    },
    {
        "id": "balatro",
        "title": "Balatro: Complete Edition",
        "source": "GOG DRM-Free",
        "category": "Roguelike / Strategy",
        "fileSize": "140 MB",
        "uploadDate": "2026-03-25",
        "uris": [
            "magnet:?xt=urn:btih:51286847bc01b44917cc510b67489da102c94bb5&dn=Balatro+GOG+DRM+Free",
            "https://gog-games.to/game/balatro"
        ],
        "description": "The poker roguelike. Balatro is a hypnotically satisfying deckbuilder where you play illegal poker hands and discover game-changing jokers.",
        "icon": "🃏"
    },
    {
        "id": "hades2",
        "title": "Hades II: Olympus Unbound",
        "source": "SteamRip Official",
        "category": "Roguelike / Action",
        "fileSize": "4.8 GB",
        "uploadDate": "2026-04-10",
        "uris": [
            "magnet:?xt=urn:btih:917cc510b67489da102c94bb551286847bc01b44&dn=Hades+II+Olympus+Unbound+SteamRip",
            "https://steamrip.com/hades-2-free-download/"
        ],
        "description": "Battle beyond the Underworld using dark sorcery to take on the Titan of Time in this spellbinding rogue-like sequel.",
        "icon": "🔥"
    },
    {
        "id": "forza5",
        "title": "Forza Horizon 5: Premium Edition",
        "source": "DODI Repacks",
        "category": "Racing / Simulation",
        "fileSize": "92.0 GB",
        "uploadDate": "2026-01-15",
        "uris": [
            "magnet:?xt=urn:btih:c752fa8294a2b6e709a352ce798641860b29846d&dn=Forza+Horizon+5+Premium+DODI",
            "https://dodi-repacks.site/forza-horizon-5-premium/"
        ],
        "description": "Your Ultimate Horizon Adventure awaits! Explore the vibrant landscapes of Mexico with limitless driving action in hundreds of the world’s greatest cars.",
        "icon": "🏎️"
    },
    {
        "id": "ghost_of_tsushima",
        "title": "Ghost of Tsushima: Director's Cut",
        "source": "FitGirl Repacks",
        "category": "Action / Adventure",
        "fileSize": "42.8 GB",
        "uploadDate": "2026-03-18",
        "uris": [
            "magnet:?xt=urn:btih:a352ce798641860b29846dc752fa8294a2b6e709&dn=Ghost+of+Tsushima+Directors+Cut+FitGirl",
            "https://fitgirl-repacks.site/ghost-of-tsushima-directors-cut/"
        ],
        "description": "A storm is coming. Forge a new path and wage an unconventional war for the freedom of Tsushima.",
        "icon": "⛩️"
    },
    {
        "id": "silksong",
        "title": "Hollow Knight: Silksong",
        "source": "GOG DRM-Free",
        "category": "Metroidvania / Action",
        "fileSize": "8.5 GB",
        "uploadDate": "2026-05-01",
        "uris": [
            "magnet:?xt=urn:btih:846dc752fa8294a2b6e709a352ce798641860b29&dn=Hollow+Knight+Silksong+GOG",
            "https://gog-games.to/game/hollow_knight_silksong"
        ],
        "description": "Play as Hornet, princess-protector of Hallownest, and adventure through a whole new kingdom ruled by silk and song.",
        "icon": "🪡"
    },
    {
        "id": "helldivers2",
        "title": "HELLDIVERS 2: Super Citizen Edition",
        "source": "SteamRip Official",
        "category": "Co-op / Shooter",
        "fileSize": "68.2 GB",
        "uploadDate": "2026-02-28",
        "uris": [
            "magnet:?xt=urn:btih:709a352ce798641860b29846dc752fa8294a2b6e&dn=Helldivers+2+Super+Citizen+SteamRip",
            "https://steamrip.com/helldivers-2-free-download/"
        ],
        "description": "The Galaxy’s Last Line of Offence. Enlist in the Helldivers and join the fight for freedom across a hostile galaxy in a fast, frantic third-person shooter.",
        "icon": "🎖️"
    }
]

class HydraEngine:
    def __init__(self):
        self.lock = threading.Lock()
        self.catalog = self._load_catalog()
        self.is_fetching = False

    def _load_catalog(self):
        if CATALOG_FILE.exists():
            try:
                with open(CATALOG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return data
            except Exception:
                pass
        
        # Save default built-in catalog if not existing
        self._save_catalog(BUILTIN_GAMES_CATALOG)
        return list(BUILTIN_GAMES_CATALOG)

    def _save_catalog(self, games_list):
        try:
            with open(CATALOG_FILE, "w", encoding="utf-8") as f:
                json.dump(games_list, f, indent=2)
        except Exception as e:
            print(f"[HYDRA ENGINE ERROR] Failed to save catalog: {e}")

    def get_all_games(self):
        with self.lock:
            return list(self.catalog)

    def search_games(self, query: str = "", source_filter: str = "ALL", category_filter: str = "ALL"):
        with self.lock:
            results = []
            q = query.lower().strip()
            for game in self.catalog:
                title = game.get("title", "").lower()
                source = game.get("source", "")
                cat = game.get("category", "")

                # Text filter
                if q and q not in title and q not in cat.lower() and q not in source.lower():
                    continue

                # Source filter
                if source_filter != "ALL" and source_filter.lower() not in source.lower():
                    continue

                # Category filter
                if category_filter != "ALL" and category_filter.lower() not in cat.lower():
                    continue

                results.append(game)
            return results

    def add_custom_source(self, name: str, url: str, description: str = ""):
        with self.lock:
            new_src = {
                "id": f"src_{int(time.time())}",
                "name": name.strip(),
                "url": url.strip(),
                "enabled": True,
                "type": "hydra",
                "description": description.strip() or "Custom Hydra Game Source"
            }
            config.sources.append(new_src)
            config.save_sources()

        # Trigger async fetch for this source
        threading.Thread(target=self.fetch_source_async, args=(new_src,), daemon=True).start()
        return new_src

    def remove_source(self, source_id: str):
        with self.lock:
            config.sources = [s for s in config.sources if s.get("id") != source_id]
            config.save_sources()

    def fetch_source_async(self, source: dict):
        url = source.get("url")
        if not url:
            return

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Revision-Launcher/2.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=12) as res:
                raw_bytes = res.read()
                data = json.loads(raw_bytes.decode("utf-8"))

            downloads = []
            if isinstance(data, dict):
                downloads = data.get("downloads", [])
            elif isinstance(data, list):
                downloads = data

            parsed_games = []
            src_name = source.get("name", "Hydra Source")

            for item in downloads:
                title = item.get("title") or item.get("name")
                uris = item.get("uris") or item.get("links") or []
                if not title or not uris:
                    continue

                parsed_games.append({
                    "id": f"hydra_{hash(title) % 10000000}",
                    "title": title,
                    "source": src_name,
                    "category": item.get("category", "PC Game"),
                    "fileSize": item.get("fileSize") or item.get("file_size") or "Unknown",
                    "uploadDate": item.get("uploadDate") or item.get("upload_date") or time.strftime("%Y-%m-%d"),
                    "uris": uris,
                    "description": item.get("description", f"Downloaded release from {src_name}"),
                    "icon": "🎮"
                })

            if parsed_games:
                with self.lock:
                    # Merge into catalog (avoid duplicates by title)
                    existing_titles = {g.get("title", "").lower() for g in self.catalog}
                    for g in parsed_games:
                        if g.get("title", "").lower() not in existing_titles:
                            self.catalog.append(g)
                            existing_titles.add(g.get("title", "").lower())
                    self._save_catalog(self.catalog)
                print(f"[HYDRA ENGINE] Imported {len(parsed_games)} games from {src_name}")
        except Exception as e:
            print(f"[HYDRA ENGINE NOTICE] Could not fetch source {url}: {e}")

    def refresh_all_sources(self):
        if self.is_fetching:
            return
        self.is_fetching = True

        def _worker():
            for src in list(config.sources):
                if src.get("enabled", True):
                    self.fetch_source_async(src)
            self.is_fetching = False

        threading.Thread(target=_worker, daemon=True).start()

hydra_engine = HydraEngine()
