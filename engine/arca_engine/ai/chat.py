"""Conversations with the AI: storage and the streaming chat loop.

The stream is a sequence of events (dicts), sent to the UI as NDJSON:
    {"type": "meta",   "conversation_id": "...", "model": "..."}
    {"type": "sources", "sources": [...]}            optional: passages from the user's collection
    {"type": "notice", "message": "..."}            optional (e.g. slower, partly in RAM)
    {"type": "delta",  "text": "..."}               many
    {"type": "done",   "stats": {...}}
    {"type": "error",  "message": "..."}            instead of done, when something fails
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Callable, Iterator
from typing import Any

from ..activity import log_activity, now_iso
from .base import ChatMessage, ModelProvider, ProviderError, ProviderUnavailable
from .budget import check_fit

SYSTEM_PROMPT = (
    "Você é a ARCA, uma assistente pessoal que roda localmente no computador do usuário, "
    "sem precisar de internet. Responda sempre em português do Brasil (não de Portugal), com "
    "clareza e objetividade. Seja honesta: se não souber, diga que não sabe. Não invente fatos, "
    "números, fontes nem procedimentos médicos ou técnicos. Quando a mensagem trouxer trechos do "
    "acervo numerados, baseie a resposta neles e cite cada informação com o número, como [1] ou "
    "[2]; não cite números que não existem. Se os trechos não tratarem da pergunta, diga que não "
    "encontrou isso no acervo antes de responder com o que sabe."
)
MAX_HISTORY_MESSAGES = 20
TITLE_LENGTH = 60

MemoryProbe = Callable[[], tuple[int | None, int]]  # (free VRAM or None, free RAM), in bytes


class ChatStore:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, provider: str, model: str, first_text: str) -> str:
        conv_id = str(uuid.uuid4())
        title = " ".join(first_text.split())[:TITLE_LENGTH] or "Nova conversa"
        now = now_iso()
        self.conn.execute(
            "INSERT INTO conversations (id, title, provider, model, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (conv_id, title, provider, model, now, now),
        )
        return conv_id

    def exists(self, conv_id: str) -> bool:
        return self.conn.execute("SELECT 1 FROM conversations WHERE id = ?", (conv_id,)).fetchone() is not None

    def add_message(
        self,
        conv_id: str,
        role: str,
        content: str,
        *,
        model: str | None = None,
        status: str = "ok",
        stats: dict[str, Any] | None = None,
    ) -> int:
        now = now_iso()
        cur = self.conn.execute(
            "INSERT INTO messages (conversation_id, role, content, model, status, stats_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (conv_id, role, content, model, status, json.dumps(stats) if stats else None, now),
        )
        self.conn.execute(
            "UPDATE conversations SET updated_at = ?, model = COALESCE(?, model) WHERE id = ?",
            (now, model, conv_id),
        )
        return cur.lastrowid

    def history(self, conv_id: str, limit: int = MAX_HISTORY_MESSAGES) -> list[ChatMessage]:
        rows = self.conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? AND status != 'error' "
            "ORDER BY id DESC LIMIT ?",
            (conv_id, limit),
        ).fetchall()
        return [ChatMessage(r["role"], r["content"]) for r in reversed(rows)]

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """SELECT c.id, c.title, c.provider, c.model, c.created_at, c.updated_at,
                      (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS message_count
               FROM conversations c ORDER BY c.updated_at DESC, c.rowid DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get(self, conv_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        if row is None:
            return None
        messages = self.conn.execute(
            "SELECT id, role, content, model, status, stats_json, created_at FROM messages "
            "WHERE conversation_id = ? ORDER BY id",
            (conv_id,),
        ).fetchall()
        return {
            **dict(row),
            "messages": [
                {**{k: m[k] for k in m.keys() if k != "stats_json"},  # noqa: SIM118 (sqlite3.Row iterates values)
                 "stats": json.loads(m["stats_json"]) if m["stats_json"] else None}
                for m in messages
            ],
        }

    def delete(self, conv_id: str) -> bool:
        return self.conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,)).rowcount > 0


def chat_stream(
    store: ChatStore,
    provider: ModelProvider,
    *,
    text: str,
    model: str,
    conversation_id: str | None,
    memory_probe: MemoryProbe,
    keep_alive_minutes: int = 5,
    sources: list[dict[str, Any]] | None = None,
    context: str | None = None,
) -> Iterator[dict[str, Any]]:
    """`sources` (shown to the user) and `context` (sent to the model with the question)
    come from knowledge.retrieve; only the user's own words are stored as the question."""
    text = text.strip()
    if not text:
        yield {"type": "error", "message": "Escreva uma mensagem."}
        return
    if conversation_id and not store.exists(conversation_id):
        yield {"type": "error", "message": "Conversa não encontrada."}
        return

    # 1) One chat model at a time, and only if it fits.
    try:
        loaded = provider.loaded()
        for other in loaded:
            if other.name != model:
                provider.unload(other.name)
                log_activity(store.conn, "ai", f"Modelo descarregado da memória: {other.name}")
        if model not in {m.name for m in loaded}:
            info = next((m for m in provider.list_models() if m.name == model), None)
            if info is None:
                yield {"type": "error", "message": f"O modelo {model} não está instalado no Ollama."}
                return
            vram_free, ram_free = memory_probe()
            fit = check_fit(info.size_bytes, vram_free, ram_free)
            if not fit.ok:
                yield {"type": "error", "message": fit.message}
                return
            if fit.mode != "gpu":
                yield {"type": "notice", "message": fit.message}
    except (ProviderUnavailable, ProviderError) as exc:
        yield {"type": "error", "message": str(exc)}
        return

    # 2) Save the question, then stream the answer.
    conv_id = conversation_id or store.create(provider.name, model, text)
    store.add_message(conv_id, "user", text)
    yield {"type": "meta", "conversation_id": conv_id, "model": model}
    if sources:
        yield {"type": "sources", "sources": sources}

    messages = [ChatMessage("system", SYSTEM_PROMPT), *store.history(conv_id)]
    if context and messages[-1].role == "user":
        messages[-1] = ChatMessage("user", f"{messages[-1].content}\n\n{context}")
    parts: list[str] = []
    stats: dict[str, Any] = {}
    status = "interrupted"  # if the client goes away mid-answer
    error: str | None = None
    try:
        for chunk in provider.chat(model, messages, keep_alive_minutes=keep_alive_minutes):
            if chunk.text:
                parts.append(chunk.text)
                yield {"type": "delta", "text": chunk.text}
            if chunk.done:
                stats = dict(chunk.stats)
        status = "ok"
    except (ProviderUnavailable, ProviderError) as exc:
        status, error = "error", str(exc)
    finally:
        answer = "".join(parts)
        if sources:
            stats = {**stats, "sources": sources}
        if answer or status != "ok":
            store.add_message(
                conv_id, "assistant", answer or (error or ""), model=model, status=status, stats=stats or None
            )
    if error:
        yield {"type": "error", "message": error}
    else:
        yield {"type": "done", "stats": {k: v for k, v in stats.items() if k != "sources"}}
