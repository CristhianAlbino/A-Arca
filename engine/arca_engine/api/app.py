"""HTTP API (FastAPI). Thin layer over arca_engine.service."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from .. import __version__, service
from ..context import AppContext
from ..security.token import bearer_from_header, tokens_match

log = logging.getLogger("arca_engine.api")

# Origins of the ARCA window (Tauri on Windows / other OS) and of the Vite dev server.
ALLOWED_ORIGINS = [
    "http://tauri.localhost",
    "https://tauri.localhost",
    "tauri://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


class RegisterVolume(BaseModel):
    path: str
    label: str


class ChatRequest(BaseModel):
    text: str
    model: str | None = None
    conversation_id: str | None = None
    use_sources: bool = True


class PullRequest(BaseModel):
    model: str


def create_app(ctx: AppContext) -> FastAPI:
    app = FastAPI(
        title="ARCA Engine",
        version=__version__,
        docs_url=None,
        redoc_url=None,
    )

    @app.middleware("http")
    async def require_token(request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        given = bearer_from_header(request.headers.get("authorization"))
        if not tokens_match(ctx.token, given):
            return JSONResponse({"detail": "Token ausente ou inválido."}, status_code=401)
        try:
            return await call_next(request)
        except Exception:
            # Answered here, inside the CORS middleware: an unhandled error would otherwise
            # reach the window without CORS headers and look like "no connection".
            log.exception("Erro interno em %s %s", request.method, request.url.path)
            return JSONResponse(
                {"detail": "Erro interno no motor da ARCA. Detalhes no arquivo de log."}, status_code=500
            )

    # Added after the token middleware so it wraps it: 401 answers also carry CORS headers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(service.ServiceError)
    async def _service_error(_: Request, exc: service.ServiceError):
        return JSONResponse({"detail": str(exc)}, status_code=exc.status)

    @app.get("/health")
    def health() -> dict[str, Any]:
        return service.health(ctx)

    @app.get("/system")
    def system() -> dict[str, Any]:
        return service.system(ctx)

    @app.get("/volumes")
    def volumes(rescan: bool = False) -> list[dict[str, Any]]:
        return service.list_volumes(ctx, rescan=rescan)

    @app.post("/volumes", status_code=201)
    def register_volume(body: RegisterVolume) -> dict[str, Any]:
        return service.register_volume(ctx, body.path, body.label)

    @app.get("/settings")
    def get_settings() -> dict[str, Any]:
        return service.get_settings(ctx)

    @app.put("/settings")
    def put_settings(changes: dict[str, Any]) -> dict[str, Any]:
        return service.update_settings(ctx, changes)

    @app.get("/activity")
    def activity(limit: int = 50) -> list[dict[str, Any]]:
        return service.activity(ctx, limit=limit)

    @app.get("/network/attempts")
    def network_attempts(only_blocked: bool = False) -> list[dict[str, Any]]:
        return service.network_attempts(ctx, only_blocked=only_blocked)

    # --- AI (Phase 2) ----------------------------------------------------
    @app.get("/ai/status")
    def ai_status() -> dict[str, Any]:
        return service.ai_status(ctx)

    @app.post("/ai/models/{model}/unload")
    def unload_model(model: str) -> dict[str, Any]:
        return service.unload_model(ctx, model)

    @app.post("/ai/models/pull")
    def pull_model(body: PullRequest) -> StreamingResponse:
        events = service.pull_model(ctx, body.model)
        lines = (json.dumps(e, ensure_ascii=False) + "\n" for e in events)
        return StreamingResponse(lines, media_type="application/x-ndjson")

    # {model:path}: names such as "library/llama3.2:3b" contain a slash.
    @app.delete("/ai/models/{model:path}")
    def delete_model(model: str) -> dict[str, Any]:
        return service.delete_model(ctx, model)

    # --- Knowledge (Phase 3) ---------------------------------------------
    @app.get("/knowledge/zims")
    def zims(rescan: bool = False) -> list[dict[str, Any]]:
        return service.list_zims(ctx, rescan=rescan)

    @app.get("/knowledge/search")
    def knowledge_search(q: str, zim: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        return service.search_knowledge(ctx, q, zim_id=zim, limit=limit)

    @app.get("/knowledge/article")
    def knowledge_article(zim: str, path: str | None = None) -> dict[str, Any]:
        return service.read_article(ctx, zim, path)

    @app.get("/library/status")
    def library_status() -> dict[str, Any]:
        return service.library_status(ctx)

    @app.post("/library/index", status_code=202)
    def index_library() -> dict[str, Any]:
        return service.index_library(ctx)

    @app.get("/library/search")
    def library_search(q: str, limit: int = 20) -> list[dict[str, Any]]:
        return service.search_library(ctx, q, limit=limit)

    @app.get("/library/docs/{doc_id}")
    def library_doc(doc_id: int) -> dict[str, Any]:
        return service.read_document(ctx, doc_id)

    @app.get("/ai/conversations")
    def conversations(limit: int = 100) -> list[dict[str, Any]]:
        return service.list_conversations(ctx, limit=limit)

    @app.get("/ai/conversations/{conversation_id}")
    def conversation(conversation_id: str) -> dict[str, Any]:
        return service.get_conversation(ctx, conversation_id)

    @app.delete("/ai/conversations/{conversation_id}")
    def delete_conversation(conversation_id: str) -> dict[str, Any]:
        return service.delete_conversation(ctx, conversation_id)

    @app.post("/ai/chat")
    def chat(body: ChatRequest) -> StreamingResponse:
        events = service.chat(ctx, body.text, body.model, body.conversation_id, use_sources=body.use_sources)
        lines = (json.dumps(e, ensure_ascii=False) + "\n" for e in events)
        return StreamingResponse(lines, media_type="application/x-ndjson")

    return app
