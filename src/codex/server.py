from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from codex.config import Config
from codex.interaction import analyze_payload

CONFIG = Config.from_env()

HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>codex 房地产财经报道助手</title>
  <style>
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f7f7f4; color: #1f2933; }
    main { max-width: 1040px; margin: 0 auto; padding: 32px 20px; }
    h1 { font-size: 30px; margin: 0 0 8px; }
    p { color: #52606d; line-height: 1.6; }
    textarea { width: 100%; min-height: 160px; resize: vertical; border: 1px solid #cbd2d9; border-radius: 8px; padding: 14px; font-size: 16px; box-sizing: border-box; background: #fff; }
    button { margin-top: 12px; border: 0; border-radius: 8px; padding: 11px 18px; font-size: 15px; background: #245b45; color: #fff; cursor: pointer; }
    button.secondary { margin-left: 8px; background: #6b7280; }
    section { margin-top: 20px; }
    .topic { background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; padding: 16px; margin: 12px 0; }
    .meta { color: #52606d; font-size: 14px; }
    pre { white-space: pre-wrap; background: #111827; color: #f9fafb; padding: 16px; border-radius: 8px; overflow: auto; }
  </style>
</head>
<body>
  <main>
    <h1>codex 房地产财经报道助手</h1>
    <p>输入政策、公告、土地成交、融资工具等信息，系统会返回选题、评分、报道角度和采访问题。</p>
    <textarea id="message">武汉土拍城投占比超70%，多宗地块底价成交，地方平台托底土地市场。</textarea>
    <div>
      <button onclick="sendMessage()">生成选题</button>
      <button class="secondary" onclick="runSample()">运行样例</button>
    </div>
    <section id="output"></section>
  </main>
  <script>
    async function post(payload) {
      const response = await fetch('/api/interact', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      return response.json();
    }
    async function sendMessage() {
      render(await post({message: document.getElementById('message').value}));
    }
    async function runSample() {
      render(await post({}));
    }
    function render(data) {
      const output = document.getElementById('output');
      const result = data.result || {};
      if (data.mode !== 'topic_pipeline') {
        output.innerHTML = '<pre>' + escapeHtml(JSON.stringify(result, null, 2)) + '</pre>';
        return;
      }
      const topics = result.topics || [];
      output.innerHTML = '<p>' + escapeHtml(result.message || '') + '</p>' + topics.map((topic, index) => `
        <div class="topic">
          <div class="meta">#${index + 1} · ${escapeHtml(topic.priority || '')} · 评分 ${escapeHtml(String(topic.final_score || ''))}</div>
          <h2>${escapeHtml(topic.topic || '')}</h2>
          <p>${escapeHtml(topic.angle || '')}</p>
          <p><strong>采访对象：</strong>${escapeHtml((topic.interview_targets || []).join('、'))}</p>
          <p><strong>关键问题：</strong><br>${escapeHtml((topic.questions || []).join('\\n'))}</p>
        </div>
      `).join('');
    }
    function escapeHtml(value) {
      return value.replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
    }
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": "codex-real-estate-reporter"})
            return
        if self.path not in {"/", "/index.html"}:
            self.send_error(404)
            return
        self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/api/interact":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        if length > CONFIG.max_body_bytes:
            self._send_json(413, {"error": "请求体过大。"})
            return

        raw_body = self.rfile.read(length).decode("utf-8") if length else "{}"

        try:
            payload = json.loads(raw_body)
            if not isinstance(payload, dict):
                raise ValueError("payload must be an object")
            result = analyze_payload(payload)
            status = 400 if result.get("error") else 200
            self._send_json(status, result)
        except Exception as exc:  # noqa: BLE001
            self._send_json(400, {"error": str(exc)})

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_common_headers("application/json; charset=utf-8", 0)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        if CONFIG.debug:
            super().log_message(format, *args)

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self._send_common_headers(content_type, len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _send_common_headers(self, content_type: str, length: int) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")


def main(host: Optional[str] = None, port: Optional[int] = None) -> None:
    host = host or CONFIG.host
    port = port or _port_from_argv() or CONFIG.port
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"codex server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\ncodex server stopped")
    finally:
        server.server_close()


def _port_from_argv() -> Optional[int]:
    for index, arg in enumerate(sys.argv):
        if arg == "--port" and index + 1 < len(sys.argv):
            return int(sys.argv[index + 1])
        if arg.startswith("--port="):
            return int(arg.split("=", 1)[1])
    value = os.getenv("PORT")
    return int(value) if value and value.isdigit() else None


if __name__ == "__main__":
    main()
