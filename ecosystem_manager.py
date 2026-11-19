import os
import sys
import socket
import subprocess
from pathlib import Path

BASE_PROJECTS_DIR = Path(r"C:\Users\ZarTo\Desktop\Projects")

ECOSYSTEM_APPS = [
    {
        "id": "revision_web",
        "name": "Revision-Web",
        "tagline": "Tactical Ad-Shielding P2P Web Browser",
        "description": "Engineered for pure speed, zero telemetry tracking, tactical ad vaporization, and integrated Rev-Network P2P mesh relay. Replaced the old Rev-Network browser.",
        "icon": "🌐",
        "port": 8765,
        "entry_point": BASE_PROJECTS_DIR / "Rev-Network" / "main.py",
        "working_dir": BASE_PROJECTS_DIR / "Rev-Network",
        "version": "v2.0 Tactical",
        "role": "Web Command Deck"
    },
    {
        "id": "revision_ai",
        "name": "Revision-Ai",
        "tagline": "Autonomous Local PC Controller & Automation Suite",
        "description": "Local intelligence agent for autonomous PC orchestration, command execution, and deep system analysis. Connects directly into the Rev-Network P2P mesh.",
        "icon": "⚡",
        "port": 8766,
        "entry_point": BASE_PROJECTS_DIR / "Revision-Ai" / "main.py",
        "working_dir": BASE_PROJECTS_DIR / "Revision-Ai",
        "version": "v2.2 Noir",
        "role": "Autonomous PC Agent"
    },
    {
        "id": "rev_network_node",
        "name": "Rev-Network P2P Mesh Node",
        "tagline": "Decentralized Interconnected Server & Shared Power",
        "description": "The interconnected peer-to-peer backbone. Turns every PC into an interconnected server, relaying community chat, health telemetry, and distributed hosting power.",
        "icon": "📡",
        "port": 8767,
        "entry_point": None, # Embedded inside Rev-Launcher & other apps
        "working_dir": None,
        "version": "v2.0 P2P Protocol",
        "role": "Mesh Relay & Interconnection"
    },
    {
        "id": "rev_website",
        "name": "Project Revision Web Hub & Origin",
        "tagline": "Decentralized Distribution Gateway & Pilot Portal",
        "description": "The central distribution portal and live mesh monitoring bay for all Project Revision pilots, tactical builds, and Discord bridge synchronizer.",
        "icon": "🏛️",
        "port": 8000,
        "entry_point": BASE_PROJECTS_DIR / "Website" / "server.py",
        "working_dir": BASE_PROJECTS_DIR / "Website",
        "version": "v2.0 Hub",
        "role": "Distribution Bay"
    }
]

class EcosystemManager:
    def __init__(self):
        pass

    def check_app_status(self, app_info: dict) -> bool:
        port = app_info.get("port")
        if not port:
            return False
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            res = s.connect_ex(("127.0.0.1", port))
            s.close()
            return res == 0
        except Exception:
            return False

    def launch_app(self, app_id: str) -> tuple[bool, str]:
        app = next((a for a in ECOSYSTEM_APPS if a["id"] == app_id), None)
        if not app:
            return False, f"Unknown application ID: {app_id}"

        entry_point = app.get("entry_point")
        working_dir = app.get("working_dir")

        if not entry_point or not entry_point.exists():
            return False, f"Entry point not found at: {entry_point}"

        try:
            # Spawn in detached background process so it doesn't block the launcher
            subprocess.Popen(
                [sys.executable, str(entry_point)],
                cwd=str(working_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
            )
            return True, f"Successfully launched {app['name']}"
        except Exception as e:
            return False, f"Failed to launch {app['name']}: {e}"

ecosystem_manager = EcosystemManager()
