import os
import sys
import json
import time
import socket
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from config import DATA_DIR, config

MESSAGES_FILE = DATA_DIR / "mesh_messages.json"
UDP_DISCOVERY_PORT = 8769

class LauncherNodeState:
    def __init__(self, app_name="Rev-Launcher", port=8767):
        self.lock = threading.Lock()
        self.app_name = app_name
        self.port = port
        self.local_ip = self._get_local_ip()
        self.node_id = f"rev-launcher-{int(time.time()*1000) % 100000}"
        self.start_time = time.time()
        self.power_score = self._compute_power_score()
        self.active_peers = {} # ip_port -> peer dict
        self.messages = []

        # Register self
        self.register_peer("127.0.0.1", "Pilot (Host)", port=self.port, app=self.app_name, is_self=True)

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _compute_power_score(self):
        try:
            cores = os.cpu_count() or 4
            return round(cores * 2.5 + 10.0, 1)
        except Exception:
            return 15.0

    def register_peer(self, ip, username, port=8765, app="Revision-App", is_self=False, power=15.0):
        with self.lock:
            now = time.time()
            key = f"{ip}:{port}"
            self.active_peers[key] = {
                "ip": ip,
                "port": port,
                "app": app,
                "username": username or f"Peer_{ip.replace('.', '_')}",
                "power": power,
                "last_seen": now,
                "is_self": is_self or (ip in ["127.0.0.1", self.local_ip] and port == self.port)
            }

    def cleanup_peers(self):
        with self.lock:
            now = time.time()
            to_del = []
            for key, p in self.active_peers.items():
                if not p.get("is_self") and (now - p["last_seen"]) > 60:
                    to_del.append(key)
            for key in to_del:
                del self.active_peers[key]

launcher_node_state = LauncherNodeState(app_name="Rev-Launcher", port=8767)

class LauncherHTTPHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        client_ip = self.client_address[0]

        launcher_node_state.cleanup_peers()

        if path in ["/api/status", "/api/network/status"]:
            with launcher_node_state.lock:
                peers_list = list(launcher_node_state.active_peers.values())
                active_count = len(peers_list)
            self._send_json({
                "app": launcher_node_state.app_name,
                "node_id": launcher_node_state.node_id,
                "local_ip": launcher_node_state.local_ip,
                "port": launcher_node_state.port,
                "power_score": launcher_node_state.power_score,
                "active_peers_count": active_count,
                "peers": peers_list,
                "role": "Hydra Distribution & Launcher Client Node"
            })
        elif path in ["/api/peers", "/api/network/peers"]:
            with launcher_node_state.lock:
                peers_list = list(launcher_node_state.active_peers.values())
            self._send_json({"count": len(peers_list), "peers": peers_list})
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def _run_udp_broadcast(port: int, app_name: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        try:
            msg = json.dumps({
                "magic": "REV_P2P_V2",
                "app": app_name,
                "node_id": launcher_node_state.node_id,
                "port": port,
                "power_score": launcher_node_state.power_score,
                "time": time.time()
            }).encode("utf-8")
            s.sendto(msg, ("<broadcast>", UDP_DISCOVERY_PORT))
        except Exception:
            pass
        time.sleep(8)

def _run_udp_listener(my_port: int):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        pass
    try:
        s.bind(("", UDP_DISCOVERY_PORT))
        while True:
            try:
                data, addr = s.recvfrom(2048)
                payload = json.loads(data.decode("utf-8"))
                if payload.get("magic") == "REV_P2P_V2":
                    peer_ip = addr[0]
                    peer_port = payload.get("port", 8765)
                    peer_app = payload.get("app", "Revision-App")
                    peer_power = payload.get("power_score", 15.0)
                    if not (peer_ip in ["127.0.0.1", launcher_node_state.local_ip] and peer_port == my_port):
                        launcher_node_state.register_peer(
                            ip=peer_ip,
                            username=f"{peer_app} Pilot",
                            port=peer_port,
                            app=peer_app,
                            is_self=False,
                            power=peer_power
                        )
            except Exception:
                pass
    except Exception:
        pass

def _heartbeat_to_origin():
    import ssl
    ssl_unverified = ssl._create_unverified_context()
    origin_url = os.environ.get("REV_ORIGIN_URL", "https://rev-network.ddns.net:8000")
    endpoints = [f"{origin_url.rstrip('/')}/api/register-node", "http://127.0.0.1:8000/api/register-node"]

    while True:
        payload = json.dumps({
            "node_id": launcher_node_state.node_id,
            "app": launcher_node_state.app_name,
            "port": launcher_node_state.port,
            "role": "Community Mesh Relay & Launcher Node",
            "power_score": launcher_node_state.power_score
        }).encode("utf-8")

        for ep in endpoints:
            try:
                from urllib.request import Request, urlopen
                req = Request(ep, data=payload, headers={"Content-Type": "application/json"})
                with urlopen(req, timeout=4, context=ssl_unverified if ep.startswith("https") else None) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                pass
        time.sleep(20)

class RevLauncherNodeServer:
    def __init__(self, port=8767):
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        try:
            self.server = ThreadingHTTPServer(("0.0.0.0", self.port), LauncherHTTPHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            print(f"[REV-LAUNCHER NODE] Online on port {self.port} (IP: {launcher_node_state.local_ip})")

            threading.Thread(target=_heartbeat_to_origin, daemon=True).start()
            threading.Thread(target=_run_udp_broadcast, args=(self.port, launcher_node_state.app_name), daemon=True).start()
            threading.Thread(target=_run_udp_listener, args=(self.port,), daemon=True).start()
        except Exception as e:
            print(f"[REV-LAUNCHER NODE NOTICE] Port {self.port} status: {e}")

    def stop(self):
        if self.server:
            self.server.shutdown()

launcher_mesh_server = RevLauncherNodeServer(port=8767)
