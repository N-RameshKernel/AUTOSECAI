"""Dependency-free preview server for the AutoSecAI prototype.

The production-shaped backend is the Django app in `autosecai/` and `scanner/`.
This server exists so the UI and scan API can run in restricted environments
where Django cannot be installed yet.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlparse

from scanner.engine import scan_source


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
HOST = "127.0.0.1"
PORT = 8000


class AutoSecAIHandler(BaseHTTPRequestHandler):
    server_version = "AutoSecAIPreview/0.1"

    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health/":
            self._send_json(
                {
                    "status": "online",
                    "system": "AutoSecAI // HYPER 3D MODE",
                    "engine": "heuristic-owasp-prototype",
                    "server": "stdlib-preview",
                }
            )
            return

        if path in {"", "/"}:
            self._send_file(FRONTEND_DIR / "index.html", "text/html; charset=utf-8")
            return

        if path.startswith("/static/"):
            requested = path.removeprefix("/static/")
            target = (FRONTEND_DIR / requested).resolve()
            if FRONTEND_DIR.resolve() not in target.parents:
                self._send_json({"error": "Invalid static path."}, status=400)
                return
            content_type = "application/javascript" if target.suffix == ".js" else "text/css"
            self._send_file(target, content_type)
            return

        self._send_json({"error": "Not found."}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/scan/":
            self._send_json({"error": "Not found."}, status=404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(body or "{}")
        except (ValueError, json.JSONDecodeError):
            self._send_json({"error": "Invalid JSON body."}, status=400)
            return

        code = payload.get("code")
        if not isinstance(code, str):
            self._send_json({"error": "`code` must be a string."}, status=400)
            return

        result = scan_source(
            code=code,
            language=payload.get("language", "auto"),
            learning_mode=bool(payload.get("learning_mode", True)),
        )
        self._send_json(result)

    def log_message(self, format: str, *args) -> None:
        print(f"[autosecai] {self.address_string()} - {format % args}")

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists() or not path.is_file():
            self._send_json({"error": "Not found."}, status=404)
            return

        data = path.read_bytes()
        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AutoSecAIHandler)
    print(f"AutoSecAI preview server running at http://{HOST}:{PORT}/")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()

