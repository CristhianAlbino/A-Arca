"""Preview server for the desktop UI, using only the Python standard library.

It serves the esbuild preview (build.mjs) and answers the same API routes the
UI uses, backed by the REAL engine logic (arca_engine.service), just without
FastAPI. Only for previews and visual tests in environments where FastAPI
cannot be installed; the app itself always uses arca_engine/api/app.py.

    python scripts/ui-preview/server.py <ui_dir> <port> <token> [ollama_url]
"""

from __future__ import annotations

import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine"))

from arca_engine import service  # noqa: E402
from arca_engine.config.paths import resolve_app_paths  # noqa: E402
from arca_engine.context import AppContext  # noqa: E402
from arca_engine.security.token import bearer_from_header, tokens_match  # noqa: E402


def main() -> None:
    ui_dir, port, token = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    ctx = AppContext.create(resolve_app_paths().ensure(), token, include_drive_roots=False)
    if len(sys.argv) > 4:
        ctx.update_settings({"ollama_url": sys.argv[4]})
    service.engine_started(ctx)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=ui_dir, **kwargs)

        def log_message(self, *args):
            pass

        def _send_json(self, status: int, payload) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _api(self) -> bool:
            url = urlsplit(self.path)
            if url.path.endswith((".js", ".css", ".html")) or url.path == "/":
                return False
            if not tokens_match(token, bearer_from_header(self.headers.get("Authorization"))):
                self._send_json(401, {"detail": "Token ausente ou inválido."})
                return True
            query = parse_qs(url.query)
            path = url.path
            try:
                if self.command == "POST" and path == "/ai/chat":
                    data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-ndjson")
                    self.end_headers()
                    for event in service.chat(ctx, data["text"], data.get("model"), data.get("conversation_id")):
                        self.wfile.write(json.dumps(event, ensure_ascii=False).encode() + b"\n")
                        self.wfile.flush()
                    return True
                if self.command == "GET" and path == "/ai/status":
                    self._send_json(200, service.ai_status(ctx))
                    return True
                if self.command == "GET" and path == "/ai/conversations":
                    self._send_json(200, service.list_conversations(ctx))
                    return True
                if path.startswith("/ai/conversations/"):
                    conv_id = path.rsplit("/", 1)[1]
                    if self.command == "GET":
                        self._send_json(200, service.get_conversation(ctx, conv_id))
                    else:
                        self._send_json(200, service.delete_conversation(ctx, conv_id))
                    return True
                if self.command == "GET" and url.path == "/system":
                    self._send_json(200, service.system(ctx))
                elif self.command == "GET" and url.path == "/activity":
                    self._send_json(200, service.activity(ctx, int(query.get("limit", ["50"])[0])))
                elif self.command == "GET" and url.path == "/volumes":
                    self._send_json(200, service.list_volumes(ctx, rescan="rescan" in query))
                elif self.command == "POST" and url.path == "/volumes":
                    data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                    self._send_json(201, service.register_volume(ctx, data["path"], data["label"]))
                else:
                    self._send_json(404, {"detail": "Rota não encontrada."})
            except service.ServiceError as exc:
                self._send_json(exc.status, {"detail": str(exc)})
            return True

        def do_GET(self):  # noqa: N802
            if not self._api():
                super().do_GET()

        def do_POST(self):  # noqa: N802
            self._api()

        def do_DELETE(self):  # noqa: N802
            self._api()

    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
