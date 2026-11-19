import os
import sys
import json
import time
import webbrowser
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QGridLayout, QFrame,
    QDialog, QMessageBox, QFileDialog, QStackedWidget, QTextEdit,
    QProgressBar, QApplication
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon, QFont

from config import config, ASSETS_DIR, DOWNLOADS_DIR
from hydra_engine import hydra_engine
from ecosystem_manager import ecosystem_manager, ECOSYSTEM_APPS
from download_manager import download_manager
from rev_network_node import launcher_node_state, launcher_mesh_server

class GameDetailsDialog(QDialog):
    def __init__(self, game_data: dict, parent=None):
        super().__init__(parent)
        self.game_data = game_data
        self.setWindowTitle(f"REV-LAUNCHER // {game_data.get('title', 'Game')}")
        self.setFixedSize(620, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0e14;
                border: 2px solid #8a0e1c;
            }
            QLabel { color: #e0e6ed; }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Header
        top_box = QHBoxLayout()
        icon_lbl = QLabel(self.game_data.get("icon", "🎮"))
        icon_lbl.setStyleSheet("font-size: 32px;")
        top_box.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_lbl = QLabel(self.game_data.get("title", "Unknown"))
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        title_box.addWidget(title_lbl)

        sub_lbl = QLabel(f"Source: {self.game_data.get('source')} | Size: {self.game_data.get('fileSize')} | Date: {self.game_data.get('uploadDate')}")
        sub_lbl.setStyleSheet("font-size: 11px; color: #00f0ff;")
        title_box.addWidget(sub_lbl)
        top_box.addLayout(title_box)
        layout.addLayout(top_box)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background-color: #212838; max-height: 1px;")
        layout.addWidget(div)

        # Description
        desc_lbl = QLabel(self.game_data.get("description", "No description available."))
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 12px; color: #9aa5b8; line-height: 1.4;")
        layout.addWidget(desc_lbl)

        # Download Links header
        links_header = QLabel("AVAILABLE DOWNLOAD MIRRORS & URIs:")
        links_header.setStyleSheet("font-size: 11px; font-weight: bold; color: #ff1e38; letter-spacing: 1.5px; margin-top: 10px;")
        layout.addWidget(links_header)

        # Links Box
        uris = self.game_data.get("uris", [])
        for idx, uri in enumerate(uris):
            row = QHBoxLayout()
            is_magnet = uri.startswith("magnet:")
            tag = "[MAGNET TORRENT]" if is_magnet else f"[MIRROR {idx+1}]"

            tag_lbl = QLabel(tag)
            tag_lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {'#00ff88' if is_magnet else '#ffb703'};")
            tag_lbl.setFixedWidth(130)
            row.addWidget(tag_lbl)

            uri_preview = uri[:50] + "..." if len(uri) > 50 else uri
            uri_lbl = QLabel(uri_preview)
            uri_lbl.setStyleSheet("font-size: 10px; color: #7f8a9e;")
            row.addWidget(uri_lbl, 1)

            dl_btn = QPushButton("GET LINK" if not is_magnet else "LAUNCH TORRENT")
            dl_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a2230;
                    border: 1px solid #ff1e38;
                    color: #ffffff;
                    font-size: 10px;
                    font-weight: bold;
                    padding: 4px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #ff1e38;
                }
            """)
            dl_btn.clicked.connect(lambda _, u=uri: self.handle_uri(u))
            row.addWidget(dl_btn)
            layout.addLayout(row)

        layout.addStretch()

        # Close button
        btn_close = QPushButton("CLOSE DIALOG")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #141722;
                border: 1px solid #283244;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
                padding: 8px;
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
                QMessageBox.information(self, "Torrent Client Launched", "Magnet URI forwarded to default torrent client.")
            except Exception as e:
                # Copy to clipboard fallback
                QApplication.clipboard().setText(uri)
                QMessageBox.information(self, "Magnet Copied", "Magnet link copied to clipboard!")
        else:
            webbrowser.open(uri)

class AddSourceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("REV-LAUNCHER // ADD HYDRA SOURCE")
        self.setFixedSize(540, 320)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0e14;
                border: 2px solid #8a0e1c;
            }
            QLabel { color: #e0e6ed; }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("ADD CUSTOM HYDRA GAME REPOSITORY")
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #ff1e38; letter-spacing: 2px;")
        layout.addWidget(title)

        desc = QLabel("Enter the name and raw JSON URL of any Hydra-compatible source.")
        desc.setStyleSheet("font-size: 11px; color: #8b949e;")
        layout.addWidget(desc)

        layout.addWidget(QLabel("SOURCE NAME:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. My Custom Steam Source")
        self.name_input.setStyleSheet("background: #11151e; border: 1px solid #232c3d; color: #fff; padding: 6px;")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("HYDRA SOURCE URL (RAW JSON):"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://raw.githubusercontent.com/.../source.json")
        self.url_input.setStyleSheet("background: #11151e; border: 1px solid #232c3d; color: #fff; padding: 6px;")
        layout.addWidget(self.url_input)

        btn_box = QHBoxLayout()
        btn_add = QPushButton("ADD & SYNC SOURCE")
        btn_add.setStyleSheet("background: #ff1e38; color: #fff; font-weight: bold; padding: 8px 16px; border: none; border-radius: 4px;")
        btn_add.clicked.connect(self.save_and_add)
        btn_box.addWidget(btn_add)

        btn_cancel = QPushButton("CANCEL")
        btn_cancel.setStyleSheet("background: #18202c; color: #fff; font-weight: bold; padding: 8px 16px; border: 1px solid #2c384c; border-radius: 4px;")
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
        QMessageBox.information(self, "Source Added", f"Hydra source '{name}' added and syncing in background!")
        self.accept()

class RevLauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("REV-LAUNCHER // TACTICAL GROUND-UP CORE")
        self.resize(config.get("window_width", 1360), config.get("window_height", 840))
        self.setMinimumSize(950, 600)

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

        # ── 1. Tactical Title Bar ──
        title_bar = QWidget()
        title_bar.setObjectName("LauncherTitleBar")
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(16, 0, 16, 0)

        crest_icon = QLabel("⎊")
        crest_icon.setStyleSheet("color: #ff1e38; font-size: 20px; font-weight: bold;")
        tb_layout.addWidget(crest_icon)

        title_lbl = QLabel("REV-LAUNCHER // TACTICAL GROUND-UP CORE")
        title_lbl.setObjectName("TitleBarLabel")
        tb_layout.addWidget(title_lbl)

        # Live Mesh Badge
        self.mesh_badge = QLabel("● MESH ONLINE [PORT 8767]")
        self.mesh_badge.setObjectName("MeshStatusBadge")
        tb_layout.addWidget(self.mesh_badge)

        tb_layout.addStretch()

        # Action Buttons
        btn_site = QPushButton("🌐 WEBSITE")
        btn_site.setObjectName("WebsiteHubBtn")
        btn_site.clicked.connect(lambda: webbrowser.open("https://gaimingmemo-rgb.github.io/rev-network/"))
        tb_layout.addWidget(btn_site)

        btn_rel = QPushButton("🚀 RELEASES")
        btn_rel.setStyleSheet("background: #241608; border: 1px solid #ffb703; color: #ffb703; font-size: 10px; font-weight: bold; padding: 4px 10px; border-radius: 3px;")
        btn_rel.clicked.connect(lambda: webbrowser.open("https://github.com/gaimingmemo-rgb/rev-network/releases"))
        tb_layout.addWidget(btn_rel)

        btn_disc = QPushButton("💬 DISCORD")
        btn_disc.setObjectName("DiscordHubBtn")
        btn_disc.clicked.connect(lambda: webbrowser.open("https://discord.gg/8rnKQKbaHj"))
        tb_layout.addWidget(btn_disc)

        main_layout.addWidget(title_bar)

        # ── 2. Top Navigation Tabs Bar ──
        nav_container = QWidget()
        nav_container.setObjectName("LauncherNavContainer")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(16, 6, 16, 6)
        nav_layout.setSpacing(10)

        self.tab_buttons = []
        tabs = [
            ("🎮 HYDRA LIBRARY", 0),
            ("⚡ REVISION SUITE", 1),
            ("🌐 P2P MESH MATRIX", 2),
            ("⚙️ SOURCES & SETTINGS", 3)
        ]

        for label, idx in tabs:
            btn = QPushButton(label)
            btn.setProperty("class", "NavTabBtn")
            btn.setProperty("active", "true" if idx == 0 else "false")
            btn.clicked.connect(lambda _, i=idx: self.switch_tab(i))
            nav_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        nav_layout.addStretch()

        # "+ Add Hydra Source" quick button
        btn_add_src = QPushButton("✚ ADD HYDRA SOURCE")
        btn_add_src.setStyleSheet("background: #ff1e38; color: #fff; font-size: 10px; font-weight: bold; padding: 5px 12px; border-radius: 3px; border: none;")
        btn_add_src.clicked.connect(self.open_add_source_dialog)
        nav_layout.addWidget(btn_add_src)

        main_layout.addWidget(nav_container)

        # ── 3. Stacked Pages Widget ──
        self.stack = QStackedWidget()
        self.stack.addWidget(self.build_library_page())
        self.stack.addWidget(self.build_ecosystem_page())
        self.stack.addWidget(self.build_mesh_page())
        self.stack.addWidget(self.build_settings_page())
        main_layout.addWidget(self.stack, 1)

    def switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ─── TAB 1: HYDRA GAMES LIBRARY ──────────────────────────────────────────
    def build_library_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Search Bar + Filters
        top_filter_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("LauncherSearchBar")
        self.search_input.setPlaceholderText("🔍 Search 10,000+ PC Games across all active Hydra sources (e.g. 'Cyberpunk', 'Hades', 'Elden')...")
        self.search_input.textChanged.connect(self.on_search_changed)
        top_filter_bar.addWidget(self.search_input, 1)

        # Filter Chips (Sources)
        self.filter_chips = []
        sources = ["ALL", "SteamRip", "FitGirl", "DODI", "GOG"]
        for s in sources:
            chip = QPushButton(s)
            chip.setProperty("class", "FilterChip")
            chip.setProperty("active", "true" if s == "ALL" else "false")
            chip.clicked.connect(lambda _, src=s: self.on_source_filter_changed(src))
            top_filter_bar.addWidget(chip)
            self.filter_chips.append(chip)

        layout.addLayout(top_filter_bar)

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

        # Initial render of game cards
        self.render_game_cards()

        return page

    def render_game_cards(self, query: str = ""):
        # Clear existing cards
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
            card_layout.setContentsMargins(14, 14, 14, 14)
            card_layout.setSpacing(8)

            # Top row: icon + title
            top_row = QHBoxLayout()
            icon_lbl = QLabel(game.get("icon", "🎮"))
            icon_lbl.setStyleSheet("font-size: 24px;")
            top_row.addWidget(icon_lbl)

            title_lbl = QLabel(game.get("title", "Game"))
            title_lbl.setProperty("class", "GameCardTitle")
            title_lbl.setWordWrap(True)
            top_row.addWidget(title_lbl, 1)
            card_layout.addLayout(top_row)

            # Badges row: source + size
            badge_row = QHBoxLayout()
            src_badge = QLabel(game.get("source", "Hydra"))
            src_badge.setProperty("class", "GameCardBadge")
            badge_row.addWidget(src_badge)

            size_badge = QLabel(game.get("fileSize", "Unknown"))
            size_badge.setStyleSheet("color: #ffb703; font-size: 10px; font-weight: bold;")
            badge_row.addWidget(size_badge)

            badge_row.addStretch()
            card_layout.addLayout(badge_row)

            # Description snippet
            desc = game.get("description", "")
            if len(desc) > 85:
                desc = desc[:85] + "..."
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: #7f8a9e; font-size: 10px; line-height: 1.3;")
            desc_lbl.setWordWrap(True)
            card_layout.addWidget(desc_lbl)

            card_layout.addStretch()

            # Action buttons
            btn_box = QHBoxLayout()
            btn_details = QPushButton("DETAILS")
            btn_details.setProperty("class", "BtnSecondary")
            btn_details.clicked.connect(lambda _, g=game: self.open_game_details(g))
            btn_box.addWidget(btn_details)

            btn_download = QPushButton("DOWNLOAD")
            btn_download.setProperty("class", "BtnPrimary")
            btn_download.clicked.connect(lambda _, g=game: self.quick_download_game(g))
            btn_box.addWidget(btn_download)

            card_layout.addLayout(btn_box)

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

    # ─── TAB 2: REVISION ECOSYSTEM APPS ──────────────────────────────────────
    def build_ecosystem_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("⚡ REVISION ECOSYSTEM // INTERCONNECTED TACTICAL APPS")
        title.setStyleSheet("font-size: 15px; font-weight: 900; color: #ff1e38; letter-spacing: 2px;")
        layout.addWidget(title)

        subtitle = QLabel("Every application in Project Revision is powered by the Rev-Network P2P connection layer. Launch or orchestrate any app below.")
        subtitle.setStyleSheet("font-size: 11px; color: #8b949e;")
        layout.addWidget(subtitle)

        # App Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        self.app_status_labels = {}

        for idx, app in enumerate(ECOSYSTEM_APPS):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #11151e;
                    border: 1px solid #1f2736;
                    border-radius: 6px;
                    padding: 16px;
                }
                QFrame:hover {
                    border-color: #ff1e38;
                }
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setSpacing(10)

            # Icon & Title
            top_h = QHBoxLayout()
            icon_lbl = QLabel(app["icon"])
            icon_lbl.setStyleSheet("font-size: 26px;")
            top_h.addWidget(icon_lbl)

            t_box = QVBoxLayout()
            t_lbl = QLabel(app["name"])
            t_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
            t_box.addWidget(t_lbl)

            tag_lbl = QLabel(app["tagline"])
            tag_lbl.setStyleSheet("font-size: 10px; color: #00f0ff;")
            t_box.addWidget(tag_lbl)
            top_h.addLayout(t_box, 1)

            # Online status pill
            status_pill = QLabel("CHECKING...")
            status_pill.setStyleSheet("background: #141b25; border: 1px solid #283344; color: #7f8a9e; font-size: 9px; font-weight: bold; padding: 3px 8px; border-radius: 3px;")
            top_h.addWidget(status_pill)
            self.app_status_labels[app["id"]] = status_pill

            c_layout.addLayout(top_h)

            # Description
            d_lbl = QLabel(app["description"])
            d_lbl.setStyleSheet("font-size: 11px; color: #8b949e; line-height: 1.4;")
            d_lbl.setWordWrap(True)
            c_layout.addWidget(d_lbl)

            # Metadata info
            meta_lbl = QLabel(f"Role: {app['role']} &bull; Port: {app['port'] or 'Embedded'}")
            meta_lbl.setStyleSheet("font-size: 10px; color: #ffb703;")
            c_layout.addWidget(meta_lbl)

            c_layout.addStretch()

            # Launch Button
            if app["entry_point"]:
                btn_launch = QPushButton(f"🚀 LAUNCH {app['name'].upper()}")
                btn_launch.setStyleSheet("""
                    QPushButton {
                        background-color: #ff1e38;
                        border: none;
                        color: #ffffff;
                        font-weight: bold;
                        font-size: 11px;
                        padding: 8px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #ff3850;
                    }
                """)
                btn_launch.clicked.connect(lambda _, a_id=app["id"]: self.launch_eco_app(a_id))
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

    # ─── TAB 3: P2P MESH MATRIX ──────────────────────────────────────────────
    def build_mesh_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("🌐 REV-NETWORK // INTERCONNECTED P2P MESH MATRIX")
        title.setStyleSheet("font-size: 15px; font-weight: 900; color: #00ff88; letter-spacing: 2px;")
        layout.addWidget(title)

        info_box = QFrame()
        info_box.setStyleSheet("background: #0f141c; border-left: 3px solid #00ff88; border-radius: 4px; padding: 12px;")
        ib_layout = QVBoxLayout(info_box)
        ib_lbl = QLabel("Every PC running Rev-Launcher, Revision-Web, or Revision-Ai acts as a decentralized node. Nodes automatically discover each other via UDP Broadcast (port 8769) and sync through the DDNS origin tracker.")
        ib_lbl.setStyleSheet("font-size: 11px; color: #c9d1d9; line-height: 1.4;")
        ib_lbl.setWordWrap(True)
        ib_layout.addWidget(ib_lbl)
        layout.addWidget(info_box)

        # Node Telemetry Grid
        telemetry_frame = QFrame()
        telemetry_frame.setStyleSheet("background: #11151e; border: 1px solid #1e2634; border-radius: 6px; padding: 16px;")
        t_layout = QGridLayout(telemetry_frame)

        self.lbl_node_id = QLabel(f"Node ID: {launcher_node_state.node_id}")
        self.lbl_node_id.setStyleSheet("font-size: 11px; color: #fff;")
        t_layout.addWidget(self.lbl_node_id, 0, 0)

        self.lbl_node_port = QLabel(f"Mesh Port: {launcher_node_state.port} (UDP: 8769)")
        self.lbl_node_port.setStyleSheet("font-size: 11px; color: #00f0ff;")
        t_layout.addWidget(self.lbl_node_port, 0, 1)

        self.lbl_node_power = QLabel(f"Power Contribution: {launcher_node_state.power_score} TFLOPS-EQ")
        self.lbl_node_power.setStyleSheet("font-size: 11px; color: #ffb703;")
        t_layout.addWidget(self.lbl_node_power, 1, 0)

        self.lbl_active_peers = QLabel("Active Peers: 1 (Self)")
        self.lbl_active_peers.setStyleSheet("font-size: 11px; color: #00ff88; font-weight: bold;")
        t_layout.addWidget(self.lbl_active_peers, 1, 1)

        layout.addWidget(telemetry_frame)

        # Active Peers List Log
        layout.addWidget(QLabel("DISCOVERED COMMUNITY MESH PEERS & APPS:"))
        self.peers_log = QTextEdit()
        self.peers_log.setReadOnly(True)
        self.peers_log.setStyleSheet("background: #090c10; border: 1px solid #1d2432; color: #7ee787; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.peers_log, 1)

        return page

    # ─── TAB 4: SOURCES & SETTINGS ───────────────────────────────────────────
    def build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("⚙️ HYDRA SOURCES REPOSITORY & CLIENT CONFIGURATION")
        title.setStyleSheet("font-size: 15px; font-weight: 900; color: #ff1e38; letter-spacing: 2px;")
        layout.addWidget(title)

        # Sources List
        sources_box = QFrame()
        sources_box.setStyleSheet("background: #11151e; border: 1px solid #1e2634; border-radius: 6px; padding: 16px;")
        s_layout = QVBoxLayout(sources_box)
        s_layout.addWidget(QLabel("CONFIGURED HYDRA REPOSITORIES:"))

        for src in config.sources:
            s_row = QHBoxLayout()
            s_name = QLabel(f"• {src.get('name')}")
            s_name.setStyleSheet("font-weight: bold; color: #fff; font-size: 12px;")
            s_row.addWidget(s_name, 1)

            s_url = QLabel(src.get("url"))
            s_url.setStyleSheet("color: #7f8a9e; font-size: 10px;")
            s_row.addWidget(s_url, 2)
            s_layout.addLayout(s_row)

        layout.addWidget(sources_box)

        # Buttons
        btn_bar = QHBoxLayout()
        btn_sync = QPushButton("🔄 SYNC & REFRESH ALL SOURCES")
        btn_sync.setStyleSheet("background: #192230; border: 1px solid #00f0ff; color: #00f0ff; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        btn_sync.clicked.connect(self.refresh_sources)
        btn_bar.addWidget(btn_sync)

        btn_add = QPushButton("✚ ADD NEW SOURCE")
        btn_add.setStyleSheet("background: #ff1e38; color: #fff; font-weight: bold; padding: 8px 16px; border-radius: 4px; border: none;")
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
                    pill.setStyleSheet("background: #0d2218; border: 1px solid #00ff88; color: #00ff88; font-size: 9px; font-weight: bold; padding: 3px 8px; border-radius: 3px;")
                else:
                    pill.setText("○ STANDBY")
                    pill.setStyleSheet("background: #1a1012; border: 1px solid #ff1e38; color: #ff556b; font-size: 9px; font-weight: bold; padding: 3px 8px; border-radius: 3px;")

        # Update peers log in Mesh Page
        with launcher_node_state.lock:
            peers = list(launcher_node_state.active_peers.values())

        self.lbl_active_peers.setText(f"Active Mesh Nodes: {len(peers)}")
        log_text = f"[{time.strftime('%H:%M:%S')}] P2P Mesh Active Nodes ({len(peers)}):\n"
        for p in peers:
            log_text += f" -> {p.get('app', 'App')} (Pilot: {p.get('username')}) @ {p.get('ip')}:{p.get('port')} | Power: {p.get('power')} TFLOPS-EQ\n"
        self.peers_log.setPlainText(log_text)
