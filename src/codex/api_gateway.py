from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from codex.services.control_center import build_control_center
from codex.services.executive_intelligence import run_executive_intelligence
from codex.services.health_check import run_health_check
from codex.services.realtime_pipeline import run_realtime_pipeline

STATIC_DIR = Path(__file__).parent / "static"


class NewsroomAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        if path in {"/", "/dashboard"}:
            self._serve_dashboard()
            return

        routes = {
            "/health": lambda: run_health_check(),
            "/control-center": lambda: build_control_center(),
            "/executive-intelligence": lambda: run_executive_intelligence(),
        }
        handler = routes.get(path)
        if not handler:
            self._json_response({"error": "not_found", "path": path}, status=404)
            return
        try:
            self._json_response(handler())
        except Exception as exc:  # noqa: BLE001
            self._json_response({"error": str(exc), "path": path}, status=500)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        payload = self._read_json_body()
        routes = {
            "/pipeline": lambda: run_realtime_pipeline(payload),
        }
        handler = routes.get(path)
        if not handler:
            self._json_response({"error": "not_found", "path": path}, status=404)
            return
        try:
            self._json_response(handler())
        except Exception as exc:  # noqa: BLE001
            self._json_response({"error": str(exc), "path": path}, status=500)

    def _serve_dashboard(self) -> None:
        dashboard = STATIC_DIR / "dashboard.html"
        if not dashboard.exists():
            self.send_error(404, "dashboard_not_found")
            return
        content = dashboard.read_text(encoding="utf-8").encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if not length:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _json_response(self, payload: Dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), NewsroomAPIHandler)
    print(f"Newsroom OS API gateway listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
