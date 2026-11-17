"""Local models through Ollama's HTTP API (http://127.0.0.1:11434 by default).

All traffic goes through NetGuard. Loopback is always allowed, so this works
offline; a non-loopback Ollama URL would need the user's online permission.
"""

from __future__ import annotations

import json
import urllib.error
from collections.abc import Iterator
from typing import Any

from ..netguard import NetGuard, NetworkBlocked
from .base import (
    ChatChunk,
    ChatMessage,
    LoadedModel,
    ModelInfo,
    ProviderError,
    ProviderUnavailable,
)

DEFAULT_URL = "http://127.0.0.1:11434"
NOT_RUNNING = (
    "O Ollama não está respondendo em {url}. Instale o Ollama (instalador em "
    "ARCA/14_INSTALADORES no Drive) e deixe-o aberto."
)


class OllamaProvider:
    name = "ollama"
    local = True

    def __init__(self, guard: NetGuard, base_url: str = DEFAULT_URL):
        self.guard = guard
        self.base_url = base_url.rstrip("/")

    # --- helpers ------------------------------------------------------------
    def _json(self, method: str, path: str, body: dict[str, Any] | None = None, timeout: float = 10.0):
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"} if body is not None else {}
        try:
            resp = self.guard.request(method, self.base_url + path, data=data, headers=headers, timeout=timeout)
        except NetworkBlocked:
            raise
        except (urllib.error.URLError, OSError) as exc:
            raise ProviderUnavailable(NOT_RUNNING.format(url=self.base_url)) from exc
        if resp.status >= 400:
            raise ProviderError(_error_text(resp.body) or f"Ollama respondeu {resp.status}")
        return json.loads(resp.body or b"{}")

    # --- ModelProvider ------------------------------------------------------
    def status(self) -> dict[str, Any]:
        try:
            version = self._json("GET", "/api/version", timeout=3).get("version")
        except ProviderUnavailable as exc:
            return {"available": False, "version": None, "reason": str(exc)}
        return {"available": True, "version": version, "reason": None}

    def list_models(self) -> list[ModelInfo]:
        data = self._json("GET", "/api/tags")
        models = []
        for m in data.get("models", []):
            details = m.get("details") or {}
            models.append(
                ModelInfo(
                    name=m.get("name") or m.get("model"),
                    size_bytes=int(m.get("size") or 0),
                    family=details.get("family"),
                    parameter_size=details.get("parameter_size"),
                    quantization=details.get("quantization_level"),
                )
            )
        return sorted(models, key=lambda m: m.name)

    def loaded(self) -> list[LoadedModel]:
        data = self._json("GET", "/api/ps")
        return [
            LoadedModel(
                name=m.get("name") or m.get("model"),
                size_bytes=int(m.get("size") or 0),
                vram_bytes=int(m.get("size_vram") or 0),
                expires_at=m.get("expires_at"),
            )
            for m in data.get("models", [])
        ]

    def unload(self, model: str) -> None:
        # Ollama unloads a model when asked to keep it alive for 0 seconds.
        self._json("POST", "/api/generate", {"model": model, "keep_alive": 0}, timeout=30)

    def chat(
        self, model: str, messages: list[ChatMessage], *, keep_alive_minutes: int = 5
    ) -> Iterator[ChatChunk]:
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "keep_alive": f"{keep_alive_minutes}m",
        }
        try:
            lines = self.guard.stream_lines(
                "POST",
                self.base_url + "/api/chat",
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"},
            )
            for raw in lines:
                event = json.loads(raw)
                if event.get("error"):
                    raise ProviderError(event["error"])
                text = (event.get("message") or {}).get("content", "")
                if event.get("done"):
                    yield ChatChunk(text=text, done=True, stats=_stats(event))
                    return
                if text:
                    yield ChatChunk(text=text)
        except urllib.error.HTTPError as exc:
            raise ProviderError(_error_text(exc.read()) or f"Ollama respondeu {exc.code}") from exc
        except (urllib.error.URLError, ConnectionError) as exc:
            raise ProviderUnavailable(NOT_RUNNING.format(url=self.base_url)) from exc


def _stats(event: dict[str, Any]) -> dict[str, Any]:
    ns = 1_000_000_000
    eval_count = event.get("eval_count")
    eval_ns = event.get("eval_duration")
    return {
        "total_seconds": round(event["total_duration"] / ns, 2) if event.get("total_duration") else None,
        "load_seconds": round(event["load_duration"] / ns, 2) if event.get("load_duration") else None,
        "output_tokens": eval_count,
        "tokens_per_second": round(eval_count / (eval_ns / ns), 1) if eval_count and eval_ns else None,
    }


def _error_text(body: bytes) -> str | None:
    try:
        return json.loads(body).get("error")
    except (ValueError, AttributeError):
        return None
