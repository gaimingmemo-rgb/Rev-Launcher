import os
import sys
import time
import threading
import urllib.request
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from config import DOWNLOADS_DIR

class DownloadTask(QObject):
    progress = Signal(int, str, str) # percent, speed_str, status_str
    completed = Signal(str)          # dest_path
    error = Signal(str)              # error_message

    def __init__(self, title: str, uri: str, dest_dir: Path = DOWNLOADS_DIR):
        super().__init__()
        self.title = title
        self.uri = uri
        self.dest_dir = dest_dir
        self.is_magnet = uri.startswith("magnet:")
        self.is_canceled = False
        self.dest_path = None

    def start(self):
        if self.is_magnet:
            self._handle_magnet()
        else:
            threading.Thread(target=self._download_http, daemon=True).start()

    def _handle_magnet(self):
        try:
            # On Windows, os.startfile on a magnet link invokes qBittorrent, uTorrent, etc.
            if os.name == "nt":
                os.startfile(self.uri)
            self.progress.emit(100, "TORRENT CLIENT", "Sent to Torrent Client")
            self.completed.emit(self.uri)
        except Exception as e:
            self.error.emit(f"Could not open magnet automatically: {e}")

    def _download_http(self):
        try:
            filename = self.uri.split("/")[-1].split("?")[0]
            if not filename or len(filename) > 60:
                safe_title = "".join(c for c in self.title if c.isalnum() or c in " _-")
                filename = f"{safe_title}.zip"

            self.dest_path = self.dest_dir / filename
            self.progress.emit(0, "0 KB/s", "Connecting to mirror...")

            req = urllib.request.Request(
                self.uri,
                headers={"User-Agent": "Revision-Launcher-Downloader/2.0"}
            )

            with urllib.request.urlopen(req, timeout=15) as res:
                total_size = int(res.headers.get("Content-Length", 0))
                downloaded = 0
                start_time = time.time()
                chunk_size = 64 * 1024

                with open(self.dest_path, "wb") as f:
                    while not self.is_canceled:
                        chunk = res.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        elapsed = time.time() - start_time
                        speed = downloaded / elapsed if elapsed > 0 else 0
                        speed_str = f"{speed / (1024 * 1024):.2f} MB/s"

                        percent = int((downloaded / total_size) * 100) if total_size > 0 else 50
                        self.progress.emit(percent, speed_str, f"{downloaded // (1024*1024)} MB / {total_size // (1024*1024)} MB")

            if not self.is_canceled:
                self.progress.emit(100, "COMPLETE", "Downloaded successfully")
                self.completed.emit(str(self.dest_path))
        except Exception as e:
            self.error.emit(str(e))

class DownloadManager:
    def __init__(self):
        self.active_downloads = []

    def queue_download(self, title: str, uri: str) -> DownloadTask:
        task = DownloadTask(title, uri)
        self.active_downloads.append(task)
        task.start()
        return task

download_manager = DownloadManager()
