"""HTTP API (FastAPI). Thin layer over arca_engine.service."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .. import __version__, service
from ..context import AppContext
from ..security.token import bearer_from_header, tokens_match

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
        return await call_next(request)

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

    return app
