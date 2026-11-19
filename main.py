import os
import sys
from pathlib import Path

# PyInstaller frozen bundle support
if getattr(sys, "frozen", False):
    _bundle_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    os.chdir(_bundle_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from config import ASSETS_DIR
from rev_network_node import launcher_mesh_server
from launcher_window import RevLauncherWindow

def main():
    # 1. Start embedded Rev-Network P2P Mesh Server (Port 8767, UDP 8769)
    launcher_mesh_server.start()

    # 2. Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Rev-Launcher")
    app.setOrganizationName("ProjectRevision")

    # 3. Load Icon
    icon_path = ASSETS_DIR / "icon.ico"
    if not icon_path.exists():
        icon_path = ASSETS_DIR / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # 4. Apply Revision Noir & Tactical Crimson QSS
    qss_path = ASSETS_DIR / "style.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # 5. Launch Window
    window = RevLauncherWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
