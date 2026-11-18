"""HTTP layer tests. Need fastapi and httpx (pip install -e .[dev])."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from arca_engine.api.app import create_app
from arca_engine.context import AppContext

TOKEN = "token-de-teste-" + "x" * 30


@pytest.fixture
def client(app_paths):
    ctx = AppContext.create(app_paths, token=TOKEN, include_drive_roots=False)
    with TestClient(create_app(ctx)) as c:
        yield c
    ctx.close()


def auth():
    return {"Authorization": f"Bearer {TOKEN}"}


def test_requests_without_token_are_refused(client):
    assert client.get("/health").status_code == 401
    assert client.get("/health", headers={"Authorization": "Bearer errado"}).status_code == 401


def test_health_with_token(client):
    r = client.get("/health", headers=auth())
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_cors_preflight_from_tauri_window(client):
    r = client.options(
        "/health",
        headers={"Origin": "http://tauri.localhost", "Access-Control-Request-Method": "GET"},
    )
    assert r.headers.get("access-control-allow-origin") == "http://tauri.localhost"


def test_unknown_origin_gets_no_cors(client):
    r = client.get("/health", headers={**auth(), "Origin": "https://site-qualquer.com"})
    assert "access-control-allow-origin" not in r.headers


def test_volume_and_settings_roundtrip(client, tmp_path):
    (tmp_path / "ssd").mkdir()
    r = client.post("/volumes", json={"path": str(tmp_path / "ssd"), "label": "ARCA-EXT"}, headers=auth())
    assert r.status_code == 201
    assert client.get("/volumes", headers=auth()).json()[0]["available"] is True
    r = client.put("/settings", json={"network_mode": "talvez"}, headers=auth())
    assert r.status_code == 400


def test_ai_chat_streams_ndjson(app_paths, tmp_path):
    import json

    from tests.fakes.fake_ollama import FakeOllama

    fake = FakeOllama(token_delay=0)
    ctx = AppContext.create(app_paths, token=TOKEN, include_drive_roots=False)
    ctx.update_settings({"ollama_url": fake.start(), "default_model": "teste-pequeno:3b"})
    try:
        with TestClient(create_app(ctx)) as c:
            assert c.get("/ai/status", headers=auth()).json()["available"] is True
            r = c.post("/ai/chat", json={"text": "oi"}, headers=auth())
            events = [json.loads(line) for line in r.text.splitlines() if line]
            assert events[0]["type"] in ("meta", "notice")
            assert events[-1]["type"] in ("done", "error")
            assert c.post("/ai/chat", json={"text": "oi"}).status_code == 401
    finally:
        ctx.close()
        fake.stop()
