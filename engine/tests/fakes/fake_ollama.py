"""A tiny stand-in for Ollama's HTTP API, for tests and UI previews.

Implements /api/version, /api/tags, /api/ps, /api/chat (streaming NDJSON) and
/api/generate with keep_alive=0 (unload). It never runs a real model: the
answer is a fixed, clearly labelled echo of the last user message.

    python engine/tests/fakes/fake_ollama.py 11434
"""

from __future__ import annotations

import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

GB = 1024**3

DEFAULT_MODELS = {
    "teste-pequeno:3b": {"size": int(2.0 * GB), "family": "teste", "parameter_size": "3B", "q": "Q4_K_M"},
    "teste-padrao:8b": {"size": int(4.9 * GB), "family": "teste", "parameter_size": "8B", "q": "Q4_K_M"},
    "teste-gigante:70b": {"size": int(40 * GB), "family": "teste", "parameter_size": "70B", "q": "Q4_K_M"},
}


class FakeOllama:
    def __init__(self, models: dict | None = None, token_delay: float = 0.02):
        self.models = dict(models or DEFAULT_MODELS)
        self.loaded: str | None = None
        self.token_delay = token_delay
        self.requests: list[tuple[str, str, dict | None]] = []
        self._server: ThreadingHTTPServer | None = None

    # --- server lifecycle -----------------------------------------------------
    def start(self, port: int = 0) -> str:
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _body(self):
                length = int(self.headers.get("Content-Length") or 0)
                return json.loads(self.rfile.read(length)) if length else None

            def _json(self, status, payload):
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):  # noqa: N802
                fake.requests.append(("GET", self.path, None))
                if self.path == "/api/version":
                    self._json(200, {"version": "0.0.0-fake"})
                elif self.path == "/api/tags":
                    self._json(200, {"models": fake.tags()})
                elif self.path == "/api/ps":
                    self._json(200, {"models": fake.ps()})
                else:
                    self._json(404, {"error": "not found"})

            def do_POST(self):  # noqa: N802
                body = self._body()
                fake.requests.append(("POST", self.path, body))
                if self.path == "/api/generate" and body.get("keep_alive") == 0:
                    if fake.loaded == body.get("model"):
                        fake.loaded = None
                    self._json(200, {"model": body.get("model"), "done": True, "done_reason": "unload"})
                elif self.path == "/api/chat":
                    model = body.get("model")
                    if model not in fake.models:
                        self._json(404, {"error": f"model '{model}' not found"})
                        return
                    fake.loaded = model
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-ndjson")
                    self.end_headers()
                    for event in fake.chat_events(body):
                        self.wfile.write(json.dumps(event).encode() + b"\n")
                        self.wfile.flush()
                        time.sleep(fake.token_delay)
                else:
                    self._json(404, {"error": "not found"})

        self._server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()

    # --- fake behaviour -------------------------------------------------------
    def tags(self):
        return [
            {
                "name": name,
                "model": name,
                "size": m["size"],
                "details": {"family": m["family"], "parameter_size": m["parameter_size"], "quantization_level": m["q"]},
            }
            for name, m in self.models.items()
        ]

    def ps(self):
        if not self.loaded:
            return []
        size = self.models[self.loaded]["size"]
        return [{"name": self.loaded, "model": self.loaded, "size": size, "size_vram": size}]

    def chat_events(self, body):
        last_user = next((m["content"] for m in reversed(body["messages"]) if m["role"] == "user"), "")
        words = f"[Ollama de teste] Você disse: {last_user}".split(" ")
        for i, word in enumerate(words):
            yield {"model": body["model"], "message": {"role": "assistant", "content": word if i == 0 else " " + word}, "done": False}
        yield {
            "model": body["model"],
            "message": {"role": "assistant", "content": ""},
            "done": True,
            "total_duration": 1_500_000_000,
            "load_duration": 200_000_000,
            "eval_count": len(words),
            "eval_duration": 1_000_000_000,
        }


if __name__ == "__main__":
    fake = FakeOllama(token_delay=0.05)
    print(fake.start(int(sys.argv[1]) if len(sys.argv) > 1 else 11434), flush=True)
    threading.Event().wait()
