import os
import sys
import json
import time
import socket
import subprocess
import webbrowser
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QGridLayout, QFrame,
    QDialog, QMessageBox, QStackedWidget, QTextEdit, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont

from config import config, ASSETS_DIR, DOWNLOADS_DIR
from hydra_engine import hydra_engine
from ecosystem_manager import ecosystem_manager, ECOSYSTEM_APPS
from download_manager import download_manager
from rev_network_node import launcher_node_state, launcher_mesh_server

WEBSITE_URL = "http://rev-network.ddns.net:8000"
WEBSITE_LOCAL_URL = "http://127.0.0.1:8000"

def _ensure_website_server_running():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        res = s.connect_ex(("127.0.0.1", 8000))
        s.close()
        if res != 0:
            server_script = Path(r"C:\Users\ZarTo\Desktop\Projects\Website\server.py")
            if server_script.exists():
                subprocess.Popen([sys.executable, str(server_script)], cwd=str(server_script.parent))
    except Exception:
        pass

def open_website():
    _ensure_website_server_running()
    # Try localhost first as it never suffers from router hairpin NAT
    webbrowser.open(WEBSITE_LOCAL_URL)

class GameDetailsDialog(QDialog):
    def __init__(self, game_data: dict, parent=None):
        super().__init__(parent)
        self.game_data = game_data
        self.setWindowTitle(f"REV-LAUNCHER // {game_data.get('title', 'Game')}")
        self.setFixedSize(640, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0e14;
                border: 2px solid #8a0e1c;
            }
            QLabel { color: #e6edf3; font-family: 'Segoe UI', Arial, sans-serif; }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Header Banner
        top_box = QHBoxLayout()
        icon_lbl = QLabel(self.game_data.get("icon", "🎮"))
        icon_lbl.setStyleSheet("font-size: 36px; padding-right: 8px;")
        top_box.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_lbl = QLabel(self.game_data.get("title", "Unknown Title"))
        title_lbl.setStyleSheet("font-size: 17px; font-weight: 800; color: #ffffff;")
        title_box.addWidget(title_lbl)

        sub_lbl = QLabel(f"Source: {self.game_data.get('source')}  •  Size: {self.game_data.get('fileSize')}  •  Updated: {self.game_data.get('uploadDate')}")
        sub_lbl.setStyleSheet("font-size: 11px; color: #00f0ff; font-weight: bold;")
        title_box.addWidget(sub_lbl)
        top_box.addLayout(title_box, 1)
        layout.addLayout(top_box)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background-color: #1e2636; max-height: 1px;")
        layout.addWidget(div)

        # Description
        desc_lbl = QLabel(self.game_data.get("description", "No description available."))
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 12px; color: #8b949e; line-height: 1.5;")
        layout.addWidget(desc_lbl)

        # Download Links
        links_header = QLabel("AVAILABLE DOWNLOAD MIRRORS & URIs:")
        links_header.setStyleSheet("font-size: 11px; font-weight: 900; color: #ff1e38; letter-spacing: 1.5px; margin-top: 10px;")
        layout.addWidget(links_header)

        uris = self.game_data.get("uris", [])
        for idx, uri in enumerate(uris):
            row = QHBoxLayout()
            is_magnet = uri.startswith("magnet:")
            tag = "[TORRENT MAGNET]" if is_magnet else f"[DIRECT MIRROR {idx+1}]"

            tag_lbl = QLabel(tag)
            tag_lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {'#00ff88' if is_magnet else '#ffb703'};")
            tag_lbl.setFixedWidth(130)
            row.addWidget(tag_lbl)

            uri_preview = uri[:55] + "..." if len(uri) > 55 else uri
            uri_lbl = QLabel(uri_preview)
            uri_lbl.setStyleSheet("font-size: 11px; color: #7f8a9e;")
            row.addWidget(uri_lbl, 1)

            dl_btn = QPushButton("OPEN MAGNET" if is_magnet else "DOWNLOAD")
            dl_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff1e38;
                    color: #ffffff;
                    font-size: 10px;
                    font-weight: 800;
                    padding: 5px 12px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #ff3b52;
                }
            """)
            dl_btn.clicked.connect(lambda _, u=uri: self.handle_uri(u))
            row.addWidget(dl_btn)
            layout.addLayout(row)

        layout.addStretch()

        btn_close = QPushButton("CLOSE")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #141824;
                border: 1px solid #283348;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
                padding: 9px;
                border-radius: 4px;
            }
            QPushButton:hover {
                border-color: #ff1e38;
            }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def handle_uri(self, uri: str):
        if uri.startswith("magnet:"):
            try:
                if os.name == "nt":
                    os.startfile(uri)
                QMessageBox.information(self, "Torrent Client Forwarded", "Magnet URI forwarded to default torrent client.")
            except Exception:
                QApplication.clipboard().setText(uri)
                QMessageBox.information(self, "Magnet Copied", "Magnet link copied to clipboard!")
        else:
            webbrowser.open(uri)

class AddSourceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("REV-LAUNCHER // ADD SOURCE")
        self.setFixedSize(520, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0e14;
                border: 2px solid #8a0e1c;
            }
            QLabel { color: #e6edf3; font-family: 'Segoe UI', Arial, sans-serif; }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("ADD GAME SOURCE REPOSITORY")
        title.setStyleSheet("font-size: 14px; font-weight: 800; color: #ff1e38; letter-spacing: 1.5px;")
        layout.addWidget(title)

        desc = QLabel("Enter a source name and raw JSON URL (Hydra-compatible source).")
        desc.setStyleSheet("font-size: 11px; color: #8b949e;")
        layout.addWidget(desc)

        layout.addWidget(QLabel("SOURCE NAME:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Community Repacks Feed")
        self.name_input.setStyleSheet("background: #11151e; border: 1px solid #232c3d; color: #fff; padding: 8px; border-radius: 4px;")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("SOURCE URL (RAW JSON):"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://raw.githubusercontent.com/.../source.json")
        self.url_input.setStyleSheet("background: #11151e; border: 1px solid #232c3d; color: #fff; padding: 8px; border-radius: 4px;")
        layout.addWidget(self.url_input)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_add = QPushButton("ADD SOURCE")
        btn_add.setStyleSheet("background: #ff1e38; color: #fff; font-weight: bold; padding: 8px 18px; border: none; border-radius: 4px;")
        btn_add.clicked.connect(self.save_and_add)
        btn_box.addWidget(btn_add)

        btn_cancel = QPushButton("CANCEL")
        btn_cancel.setStyleSheet("background: #161c28; color: #fff; font-weight: bold; padding: 8px 18px; border: 1px solid #293549; border-radius: 4px;")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        layout.addLayout(btn_box)

    def save_and_add(self):
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        if not name or not url:
            QMessageBox.warning(self, "Invalid Input", "Please provide both Source Name and valid URL.")
            return

        hydra_engine.add_custom_source(name, url)
        QMessageBox.information(self, "Source Added", f"Game source '{name}' added successfully!")
        self.accept()

class RevLauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("REV-LAUNCHER // TACTICAL GROUND-UP CORE")
        self.resize(config.get("window_width", 1360), config.get("window_height", 860))
        self.setMinimumSize(960, 620)

        # Set Window Icon
        ico_path = ASSETS_DIR / "icon.ico"
        if not ico_path.exists():
            ico_path = ASSETS_DIR / "icon.png"
        if ico_path.exists():
            self.setWindowIcon(QIcon(str(ico_path)))

        self.current_source_filter = "ALL"
        self.current_category_filter = "ALL"

        self.init_ui()

        # Telemetry / Mesh update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.start(3000)

    def init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 1. Top Bar ──
        title_bar = QWidget()
        title_bar.setObjectName("LauncherTitleBar")
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(16, 0, 16, 0)
        tb_layout.setSpacing(10)

        crest_icon = QLabel("⎊")
        crest_icon.setStyleSheet("color: #ff1e38; font-size: 22px; font-weight: bold;")
        tb_layout.addWidget(crest_icon)

        title_lbl = QLabel("REV-LAUNCHER")
        title_lbl.setObjectName("TitleBarLabel")
        tb_layout.addWidget(title_lbl)

        version_pill = QLabel("v2.0 NATIVE")
        version_pill.setStyleSheet("background: #141b27; border: 1px solid #222d42; color: #8b949e; font-size: 9px; font-weight: bold; padding: 2px 6px; border-radius: 3px;")
        tb_layout.addWidget(version_pill)

        # Mesh / VPN Status Badge
        badge_text = f"🛡️ VPN ACTIVE [{launcher_node_state.vpn_ip}]" if launcher_node_state.vpn_active else "● MESH ONLINE [PORT 8767]"
        self.mesh_badge = QLabel(badge_text)
        self.mesh_badge.setObjectName("MeshStatusBadge")
        self.mesh_badge.setToolTip("DDoS Shielded via Virtual VPN Adapter" if launcher_node_state.vpn_active else "Rev-Network P2P Node Online")
        tb_layout.addWidget(self.mesh_badge)

        tb_layout.addStretch()

        # Prominent Website Access Button
        btn_site = QPushButton("🌐 OPEN WEBSITE")
        btn_site.setObjectName("WebsiteHubBtn")
        btn_site.setToolTip("Open Project Revision Community Web Gateway (rev-network.ddns.net:8000)")
        btn_site.clicked.connect(open_website)
        tb_layout.addWidget(btn_site)

        # Releases Button
        btn_rel = QPushButton("🚀 RELEASES")
        btn_rel.setObjectName("ReleasesHubBtn")
        btn_rel.clicked.connect(lambda: webbrowser.open("https://github.com/gaimingmemo-rgb/rev-network/releases"))
        tb_layout.addWidget(btn_rel)

        # Discord Button
        btn_disc = QPushButton("💬 DISCORD")
        btn_disc.setObjectName("DiscordHubBtn")
        btn_disc.clicked.connect(lambda: webbrowser.open("https://discord.gg/8rnKQKbaHj"))
        tb_layout.addWidget(btn_disc)

        # Clean "+ Add Source" Button (Clean, unclipped, requested by user)
        btn_add_src = QPushButton("✚ Add Source")
        btn_add_src.setObjectName("AddSourceBtn")
        btn_add_src.clicked.connect(self.open_add_source_dialog)
        tb_layout.addWidget(btn_add_src)

        main_layout.addWidget(title_bar)

        # ── 2. Navigation Tabs Bar ──
        nav_container = QWidget()
        nav_container.setObjectName("LauncherNavContainer")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(16, 4, 16, 4)
        nav_layout.setSpacing(6)

        self.tab_buttons = []
        tabs = [
            ("🎮 GAME LIBRARY", 0),
            ("⚡ REVISION SUITE", 1),
            ("🌐 WEB PORTAL", 2),
            ("📡 P2P MESH MATRIX", 3),
            ("⚙️ SETTINGS", 4)
        ]

        for label, idx in tabs:
            btn = QPushButton(label)
            btn.setProperty("class", "NavTabBtn")
            btn.setProperty("active", "true" if idx == 0 else "false")
            btn.clicked.connect(lambda _, i=idx: self.switch_tab(i))
            nav_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        nav_layout.addStretch()
        main_layout.addWidget(nav_container)

        # ── 3. Stacked Pages Widget ──
        self.stack = QStackedWidget()
        self.stack.addWidget(self.build_library_page())
        self.stack.addWidget(self.build_ecosystem_page())
        self.stack.addWidget(self.build_web_portal_page())
        self.stack.addWidget(self.build_mesh_page())
        self.stack.addWidget(self.build_settings_page())
        main_layout.addWidget(self.stack, 1)

    def switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ─── TAB 1: GAME LIBRARY (CLEAN & SLEEK) ─────────────────────────────────
    def build_library_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setObjectName("LauncherSearchBar")
        self.search_input.setPlaceholderText("🔍 Search PC Games across all active sources (e.g. 'Cyberpunk', 'Hades', 'Elden Ring')...")
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_input)

        # Filter Chips Bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        lbl_filter = QLabel("FILTER SOURCE:")
        lbl_filter.setStyleSheet("font-size: 11px; font-weight: bold; color: #8b949e;")
        filter_bar.addWidget(lbl_filter)

        self.filter_chips = []
        sources = ["ALL", "SteamRip", "FitGirl", "DODI", "GOG"]
        for s in sources:
            chip = QPushButton(s)
            chip.setProperty("class", "FilterChip")
            chip.setProperty("active", "true" if s == "ALL" else "false")
            chip.clicked.connect(lambda _, src=s: self.on_source_filter_changed(src))
            filter_bar.addWidget(chip)
            self.filter_chips.append(chip)

        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        # Scroll Area for Cards
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setStyleSheet("background: transparent; border: none;")

        self.cards_container = QWidget()
        self.cards_grid = QGridLayout(self.cards_container)
        self.cards_grid.setContentsMargins(0, 0, 0, 0)
        self.cards_grid.setSpacing(16)

        self.cards_scroll.setWidget(self.cards_container)
        layout.addWidget(self.cards_scroll, 1)

        self.render_game_cards()
        return page

    def render_game_cards(self, query: str = ""):
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        games = hydra_engine.search_games(
            query=query,
            source_filter=self.current_source_filter,
            category_filter=self.current_category_filter
        )

        cols = 3
        for idx, game in enumerate(games):
            row = idx // cols
            col = idx % cols

            card = QFrame()
            card.setProperty("class", "GameCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.setSpacing(0)

            # Header Banner
            header_widget = QWidget()
            header_widget.setProperty("class", "GameCardHeader")
            h_layout = QHBoxLayout(header_widget)
            h_layout.setContentsMargins(14, 12, 14, 12)

            icon_lbl = QLabel(game.get("icon", "🎮"))
            icon_lbl.setStyleSheet("font-size: 26px; padding-right: 6px;")
            h_layout.addWidget(icon_lbl)

            t_box = QVBoxLayout()
            title_lbl = QLabel(game.get("title", "Game"))
            title_lbl.setProperty("class", "GameCardTitle")
            title_lbl.setWordWrap(True)
            t_box.addWidget(title_lbl)

            cat_lbl = QLabel(game.get("category", "PC Game"))
            cat_lbl.setProperty("class", "GameCardCategory")
            t_box.addWidget(cat_lbl)
            h_layout.addLayout(t_box, 1)

            card_layout.addWidget(header_widget)

            # Body Container
            body_widget = QWidget()
            b_layout = QVBoxLayout(body_widget)
            b_layout.setContentsMargins(14, 12, 14, 14)
            b_layout.setSpacing(10)

            # Badges Row
            badge_row = QHBoxLayout()
            src_badge = QLabel(game.get("source", "Hydra"))
            src_badge.setProperty("class", "GameCardBadge")
            badge_row.addWidget(src_badge)

            size_badge = QLabel(game.get("fileSize", "Unknown"))
            size_badge.setProperty("class", "GameCardSize")
            badge_row.addWidget(size_badge)

            badge_row.addStretch()
            b_layout.addLayout(badge_row)

            # Description snippet
            desc = game.get("description", "")
            if len(desc) > 90:
                desc = desc[:90] + "..."
            desc_lbl = QLabel(desc)
            desc_lbl.setProperty("class", "GameCardDesc")
            desc_lbl.setWordWrap(True)
            b_layout.addWidget(desc_lbl)

            b_layout.addStretch()

            # Action Buttons
            btn_box = QHBoxLayout()
            btn_box.setSpacing(8)

            btn_details = QPushButton("DETAILS")
            btn_details.setProperty("class", "BtnSecondary")
            btn_details.clicked.connect(lambda _, g=game: self.open_game_details(g))
            btn_box.addWidget(btn_details)

            btn_download = QPushButton("DOWNLOAD")
            btn_download.setProperty("class", "BtnPrimary")
            btn_download.clicked.connect(lambda _, g=game: self.quick_download_game(g))
            btn_box.addWidget(btn_download)

            b_layout.addLayout(btn_box)
            card_layout.addWidget(body_widget)

            self.cards_grid.addWidget(card, row, col)

    def on_search_changed(self, text: str):
        self.render_game_cards(query=text)

    def on_source_filter_changed(self, source: str):
        self.current_source_filter = source
        for chip in self.filter_chips:
            chip.setProperty("active", "true" if chip.text() == source else "false")
            chip.style().unpolish(chip)
            chip.style().polish(chip)
        self.render_game_cards(query=self.search_input.text())

    def open_game_details(self, game: dict):
        dlg = GameDetailsDialog(game, self)
        dlg.exec()

    def quick_download_game(self, game: dict):
        uris = game.get("uris", [])
        if not uris:
            QMessageBox.warning(self, "No Links", "No download URIs found for this release.")
            return

        first_uri = uris[0]
        if first_uri.startswith("magnet:"):
            try:
                if os.name == "nt":
                    os.startfile(first_uri)
                QMessageBox.information(self, "Torrent Client Opened", f"Sent '{game.get('title')}' magnet to your torrent client.")
            except Exception:
                QApplication.clipboard().setText(first_uri)
                QMessageBox.information(self, "Magnet Copied", "Magnet link copied to clipboard!")
        else:
            webbrowser.open(first_uri)

    def open_add_source_dialog(self):
        dlg = AddSourceDialog(self)
        if dlg.exec():
            self.render_game_cards(query=self.search_input.text())

    # ─── TAB 2: REVISION SUITE (CLEAN FONT & STYLING) ─────────────────────────
    def build_ecosystem_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("⚡ REVISION ECOSYSTEM // INTERCONNECTED TACTICAL SUITE")
        title.setStyleSheet("font-size: 16px; font-weight: 900; color: #ff1e38; letter-spacing: 2px;")
        layout.addWidget(title)

        subtitle = QLabel("Every application in Project Revision communicates across the Rev-Network P2P mesh connection.")
        subtitle.setStyleSheet("font-size: 12px; color: #8b949e;")
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(16)
        self.app_status_labels = {}

        for idx, app in enumerate(ECOSYSTEM_APPS):
            card = QFrame()
            card.setProperty("class", "SuiteCard")
            c_layout = QVBoxLayout(card)
            c_layout.setSpacing(12)

            top_h = QHBoxLayout()
            icon_lbl = QLabel(app["icon"])
            icon_lbl.setStyleSheet("font-size: 30px; padding-right: 8px;")
            top_h.addWidget(icon_lbl)

            t_box = QVBoxLayout()
            t_lbl = QLabel(app["name"])
            t_lbl.setProperty("class", "SuiteAppTitle")
            t_box.addWidget(t_lbl)

            tag_lbl = QLabel(app["tagline"])
            tag_lbl.setProperty("class", "SuiteAppTag")
            t_box.addWidget(tag_lbl)
            top_h.addLayout(t_box, 1)

            status_pill = QLabel("CHECKING...")
            status_pill.setStyleSheet("background: #141b25; border: 1px solid #283344; color: #7f8a9e; font-size: 10px; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
            top_h.addWidget(status_pill)
            self.app_status_labels[app["id"]] = status_pill

            c_layout.addLayout(top_h)

            d_lbl = QLabel(app["description"])
            d_lbl.setProperty("class", "SuiteAppDesc")
            d_lbl.setWordWrap(True)
            c_layout.addWidget(d_lbl)

            # Fixed bullet character (no raw &bull;)
            port_text = f"Port: {app['port']}" if app['port'] else "Embedded"
            meta_lbl = QLabel(f"Role: {app['role']}  •  {port_text}")
            meta_lbl.setProperty("class", "SuiteMetaText")
            c_layout.addWidget(meta_lbl)

            c_layout.addStretch()

            # Button
            if app["id"] == "rev_website":
                btn_launch = QPushButton("🌐 OPEN OFFICIAL WEBSITE")
                btn_launch.setProperty("class", "BtnPrimary")
                btn_launch.clicked.connect(open_website)
                c_layout.addWidget(btn_launch)
            elif app["entry_point"]:
                btn_launch = QPushButton(f"🚀 LAUNCH {app['name'].upper()}")
                btn_launch.setProperty("class", "BtnPrimary")
                btn_launch.clicked.connect(lambda _, a_id=app["id"]: self.launch_eco_app(a_id))
                c_layout.addWidget(btn_launch)
            else:
                btn_launch = QPushButton("📡 VIEW MESH TELEMETRY")
                btn_launch.setProperty("class", "BtnSecondary")
                btn_launch.clicked.connect(lambda: self.switch_tab(3))
                c_layout.addWidget(btn_launch)

            grid.addWidget(card, idx // 2, idx % 2)

        layout.addLayout(grid)
        layout.addStretch()
        return page

    def launch_eco_app(self, app_id: str):
        ok, msg = ecosystem_manager.launch_app(app_id)
        if ok:
            QMessageBox.information(self, "Application Launched", msg)
        else:
            QMessageBox.warning(self, "Launch Notice", msg)

    # ─── TAB 3: WEB PORTAL ACCESS (DIRECT ACCESS TO WEBSITE) ──────────────────
    def build_web_portal_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("🌐 PROJECT REVISION // OFFICIAL WEB PORTAL & ORIGIN HUB")
        title.setStyleSheet("font-size: 16px; font-weight: 900; color: #00f0ff; letter-spacing: 2px;")
        layout.addWidget(title)

        banner = QFrame()
        banner.setStyleSheet("background: #0f141e; border: 1px solid #1c2738; border-left: 4px solid #00f0ff; border-radius: 6px; padding: 18px;")
        b_layout = QVBoxLayout(banner)
        b_layout.setSpacing(10)

        b_title = QLabel("REVISION COMMUNITY DISTRIBUTION & DOWNLOAD BAY")
        b_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        b_layout.addWidget(b_title)

        b_desc = QLabel("The official web gateway connects pilots worldwide, synchronizes live chat with the official Discord server, hosts tactical installers, and tracks P2P mesh relay nodes.")
        b_desc.setStyleSheet("font-size: 12px; color: #8b949e; line-height: 1.5;")
        b_desc.setWordWrap(True)
        b_layout.addWidget(b_desc)

        layout.addWidget(banner)

        # Action Buttons Box
        action_card = QFrame()
        action_card.setStyleSheet("background: #10141e; border: 1px solid #1e2637; border-radius: 8px; padding: 20px;")
        ac_layout = QVBoxLayout(action_card)
        ac_layout.setSpacing(14)

        ac_title = QLabel("ACCESS OPTIONS & DDOS-PROTECTED LINKS:")
        ac_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #ff1e38; letter-spacing: 1px;")
        ac_layout.addWidget(ac_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_open_web = QPushButton("🌐 OPEN WEBSITE (INSTANT)")
        btn_open_web.setStyleSheet("""
            QPushButton {
                background-color: #00f0ff;
                color: #080a0e;
                font-weight: 800;
                font-size: 12px;
                padding: 12px 20px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #55f5ff;
            }
        """)
        btn_open_web.clicked.connect(open_website)
        btn_row.addWidget(btn_open_web)

        btn_open_rev = QPushButton("⚡ OPEN IN REVISION-WEB")
        btn_open_rev.setStyleSheet("""
            QPushButton {
                background-color: #ff1e38;
                color: #ffffff;
                font-weight: 800;
                font-size: 12px;
                padding: 12px 20px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #ff3b52;
            }
        """)
        btn_open_rev.clicked.connect(lambda: ecosystem_manager.launch_app("revision_web"))
        btn_row.addWidget(btn_open_rev)

        btn_copy_vpn = QPushButton("🛡️ COPY VPN LINK (26.68.132.89:8000)")
        btn_copy_vpn.setStyleSheet("""
            QPushButton {
                background-color: #1a2233;
                border: 1px solid #00ff88;
                color: #00ff88;
                font-weight: bold;
                font-size: 12px;
                padding: 12px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #00ff88;
                color: #050d12;
            }
        """)
        btn_copy_vpn.clicked.connect(self.copy_vpn_link)
        btn_row.addWidget(btn_copy_vpn)

        btn_start_server = QPushButton("🔄 RESTART SERVER (PORT 8000)")
        btn_start_server.setStyleSheet("""
            QPushButton {
                background-color: #171d2b;
                border: 1px solid #2d3b52;
                color: #c9d1d9;
                font-weight: 700;
                font-size: 12px;
                padding: 12px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                border-color: #ffb703;
                color: #ffb703;
            }
        """)
        btn_start_server.clicked.connect(self.restart_origin_server)
        btn_row.addWidget(btn_start_server)

        ac_layout.addLayout(btn_row)

        # VPN Shield Callout
        vpn_box = QFrame()
        vpn_box.setStyleSheet("background: #0d1916; border: 1px solid #00ff88; border-radius: 6px; padding: 12px;")
        vb_layout = QVBoxLayout(vpn_box)
        vb_title = QLabel("🛡️ VPN DDOS SHIELD ACTIVE: Radmin VPN (26.68.132.89)")
        vb_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #00ff88;")
        vb_layout.addWidget(vb_title)
        vb_desc = QLabel("Your home router IP is shielded. Mesh traffic and website requests route through the encrypted virtual LAN adapter so attackers cannot DDoS your home network.")
        vb_desc.setStyleSheet("font-size: 11px; color: #88d4aa;")
        vb_layout.addWidget(vb_desc)
        ac_layout.addWidget(vpn_box)

        layout.addWidget(action_card)

        # Installers Section
        inst_header = QLabel("OFFICIAL REVISION INSTALLERS & PACKAGES:")
        inst_header.setStyleSheet("font-size: 12px; font-weight: 900; color: #ffffff; letter-spacing: 1px; margin-top: 10px;")
        layout.addWidget(inst_header)

        # Unified Suite Installer hero button
        suite_card = QFrame()
        suite_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #100409, stop:1 #0a0d16);
                border: 2px solid #ff1e38;
                border-radius: 8px;
            }
        """)
        sc_layout = QHBoxLayout(suite_card)
        sc_layout.setContentsMargins(14, 12, 14, 12)
        sc_layout.setSpacing(14)

        sc_text = QVBoxLayout()
        sc_text.setSpacing(3)
        sc_title = QLabel("⚡ PROJECT REVISION — SUITE INSTALLER")
        sc_title.setStyleSheet("font-size: 12px; font-weight: 900; color: #ffffff; letter-spacing: 1px;")
        sc_text.addWidget(sc_title)
        sc_desc = QLabel("One installer — pick Rev-Launcher, Revision-Web, or Revision-Ai. Download & install only what you want.")
        sc_desc.setStyleSheet("font-size: 10px; color: #7a8599;")
        sc_desc.setWordWrap(True)
        sc_text.addWidget(sc_desc)
        sc_layout.addLayout(sc_text, 1)

        btn_suite = QPushButton("DOWNLOAD INSTALLER")
        btn_suite.setStyleSheet("background: #ff1e38; color: #fff; font-size: 11px; font-weight: bold; padding: 10px 18px; border: none; border-radius: 4px; letter-spacing: 1px; min-width: 160px;")
        btn_suite.clicked.connect(lambda: webbrowser.open("http://127.0.0.1:8000/downloads/Rev-Suite-Installer.zip"))
        sc_layout.addWidget(btn_suite)
        layout.addWidget(suite_card)

        sep2 = QLabel("— or download individually —")
        sep2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep2.setStyleSheet("font-size: 10px; color: #2a3650; margin: 4px 0; letter-spacing: 1px;")
        layout.addWidget(sep2)

        inst_grid = QGridLayout()
        inst_grid.setSpacing(10)

        installers = [
            ("🚀 Rev-Launcher", "Rev-Launcher.zip", "Native PySide6 Build", "http://127.0.0.1:8000/downloads/Rev-Launcher.zip"),
            ("🌐 Revision-Web", "Revision-Web-Setup.exe", "245 MB EXE Installer", "http://127.0.0.1:8000/downloads/Revision-Web-Setup.exe"),
            ("⚡ Revision-Ai", "Revision-Ai-v2.2.zip", "AI Automation Suite", "http://127.0.0.1:8000/downloads/Revision-Ai-v2.2.zip"),
            ("⚓ Zartogrify", "Zartogrify-v2.2.zip", "Discord Coordinator", "http://127.0.0.1:8000/downloads/Zartogrify-v2.2.zip")
        ]

        for i, (name, fname, fsize, durl) in enumerate(installers):
            i_card = QFrame()
            i_card.setStyleSheet("background: #121622; border: 1px solid #202838; border-radius: 6px; padding: 12px;")
            ic_layout = QVBoxLayout(i_card)
            ic_layout.setSpacing(6)

            n_lbl = QLabel(name)
            n_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #fff;")
            ic_layout.addWidget(n_lbl)

            s_lbl = QLabel(f"{fname}  •  {fsize}")
            s_lbl.setStyleSheet("font-size: 10px; color: #00f0ff;")
            ic_layout.addWidget(s_lbl)

            btn_dl = QPushButton("DOWNLOAD")
            btn_dl.setStyleSheet("background: #ff1e38; color: #fff; font-size: 10px; font-weight: bold; padding: 6px; border: none; border-radius: 3px;")
            btn_dl.clicked.connect(lambda _, u=durl: webbrowser.open(u))
            ic_layout.addWidget(btn_dl)

            inst_grid.addWidget(i_card, i // 2, i % 2)

        layout.addLayout(inst_grid)

        # Status readout
        self.lbl_portal_status = QLabel("Checking Website Gateway on port 8000...")
        self.lbl_portal_status.setStyleSheet("font-size: 12px; color: #ffb703; font-weight: bold; padding-top: 10px;")
        layout.addWidget(self.lbl_portal_status)

        layout.addStretch()
        return page

    def restart_origin_server(self):
        _ensure_website_server_running()
        QMessageBox.information(self, "Server Online", "Website Origin Server started on port 8000!")

    def copy_vpn_link(self):
        vpn_url = f"http://{launcher_node_state.vpn_ip or '26.68.132.89'}:8000"
        QApplication.clipboard().setText(vpn_url)
        QMessageBox.information(self, "VPN Link Copied", f"DDoS-Protected VPN Gateway URL copied to clipboard:\n\n{vpn_url}\n\nShare this with pilots connected to your Radmin VPN network!")

    # ─── TAB 4: P2P MESH MATRIX ──────────────────────────────────────────────
    def build_mesh_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("🌐 REV-NETWORK // INTERCONNECTED P2P MESH MATRIX")
        title.setStyleSheet("font-size: 16px; font-weight: 900; color: #00ff88; letter-spacing: 2px;")
        layout.addWidget(title)

        telemetry_frame = QFrame()
        telemetry_frame.setStyleSheet("background: #11151e; border: 1px solid #1e2634; border-radius: 6px; padding: 16px;")
        t_layout = QGridLayout(telemetry_frame)

        self.lbl_node_id = QLabel(f"Node ID: {launcher_node_state.node_id}")
        self.lbl_node_id.setStyleSheet("font-size: 12px; color: #fff;")
        t_layout.addWidget(self.lbl_node_id, 0, 0)

        self.lbl_node_port = QLabel(f"Mesh Port: {launcher_node_state.port} (UDP Broadcast: 8769)")
        self.lbl_node_port.setStyleSheet("font-size: 12px; color: #00f0ff;")
        t_layout.addWidget(self.lbl_node_port, 0, 1)

        self.lbl_node_power = QLabel(f"Power Contribution: {launcher_node_state.power_score} TFLOPS-EQ")
        self.lbl_node_power.setStyleSheet("font-size: 12px; color: #ffb703;")
        t_layout.addWidget(self.lbl_node_power, 1, 0)

        self.lbl_active_peers = QLabel("Active Peers: 1 (Self)")
        self.lbl_active_peers.setStyleSheet("font-size: 12px; color: #00ff88; font-weight: bold;")
        t_layout.addWidget(self.lbl_active_peers, 1, 1)

        layout.addWidget(telemetry_frame)

        layout.addWidget(QLabel("DISCOVERED COMMUNITY MESH NODES & LOCAL APPS:"))
        self.peers_log = QTextEdit()
        self.peers_log.setReadOnly(True)
        self.peers_log.setStyleSheet("background: #090c10; border: 1px solid #1d2432; color: #7ee787; font-family: 'Consolas', monospace; font-size: 11px;")
        layout.addWidget(self.peers_log, 1)

        return page

    # ─── TAB 5: SETTINGS ─────────────────────────────────────────────────────
    def build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("⚙️ SOURCES & CLIENT CONFIGURATION")
        title.setStyleSheet("font-size: 16px; font-weight: 900; color: #ff1e38; letter-spacing: 2px;")
        layout.addWidget(title)

        sources_box = QFrame()
        sources_box.setStyleSheet("background: #11151e; border: 1px solid #1e2634; border-radius: 6px; padding: 16px;")
        s_layout = QVBoxLayout(sources_box)
        s_layout.addWidget(QLabel("ACTIVE HYDRA REPOSITORIES:"))

        for src in config.sources:
            s_row = QHBoxLayout()
            s_name = QLabel(f"• {src.get('name')}")
            s_name.setStyleSheet("font-weight: bold; color: #fff; font-size: 12px;")
            s_row.addWidget(s_name, 1)

            s_url = QLabel(src.get("url"))
            s_url.setStyleSheet("color: #7f8a9e; font-size: 11px;")
            s_row.addWidget(s_url, 2)
            s_layout.addLayout(s_row)

        layout.addWidget(sources_box)

        btn_bar = QHBoxLayout()
        btn_sync = QPushButton("🔄 SYNC ALL SOURCES")
        btn_sync.setProperty("class", "BtnSecondary")
        btn_sync.clicked.connect(self.refresh_sources)
        btn_bar.addWidget(btn_sync)

        btn_add = QPushButton("✚ Add Source")
        btn_add.setProperty("class", "BtnPrimary")
        btn_add.clicked.connect(self.open_add_source_dialog)
        btn_bar.addWidget(btn_add)

        layout.addLayout(btn_bar)
        layout.addStretch()
        return page

    def refresh_sources(self):
        hydra_engine.refresh_all_sources()
        QMessageBox.information(self, "Refreshing Sources", "Querying all Hydra source repositories in background...")

    def update_telemetry(self):
        # Update app status pills
        for app in ECOSYSTEM_APPS:
            pill = self.app_status_labels.get(app["id"])
            if pill:
                online = ecosystem_manager.check_app_status(app)
                if online:
                    pill.setText("● ONLINE")
                    pill.setStyleSheet("background: #0d2218; border: 1px solid #00ff88; color: #00ff88; font-size: 10px; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
                else:
                    pill.setText("○ STANDBY")
                    pill.setStyleSheet("background: #1a1012; border: 1px solid #ff1e38; color: #ff556b; font-size: 10px; font-weight: bold; padding: 4px 10px; border-radius: 4px;")

        # Update Web Portal status readout
        if hasattr(self, 'lbl_portal_status'):
            site_online = ecosystem_manager.check_app_status({"port": 8000})
            if site_online:
                self.lbl_portal_status.setText("● Website Gateway Online on port 8000 (Serving rev-network.ddns.net:8000 & 127.0.0.1:8000)")
                self.lbl_portal_status.setStyleSheet("font-size: 12px; color: #00ff88; font-weight: bold;")
            else:
                self.lbl_portal_status.setText("○ Website Gateway Offline on port 8000 (Click restart above to launch)")
                self.lbl_portal_status.setStyleSheet("font-size: 12px; color: #ff556b; font-weight: bold;")

        # Update peers log in Mesh Page
        with launcher_node_state.lock:
            peers = list(launcher_node_state.active_peers.values())

        self.lbl_active_peers.setText(f"Active Mesh Nodes: {len(peers)}")
        log_text = f"[{time.strftime('%H:%M:%S')}] P2P Mesh Active Nodes ({len(peers)}):\n"
        for p in peers:
            log_text += f" -> {p.get('app', 'App')} (Pilot: {p.get('username')}) @ {p.get('ip')}:{p.get('port')} | Power: {p.get('power')} TFLOPS-EQ\n"
        self.peers_log.setPlainText(log_text)
