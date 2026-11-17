"""Phase 2B: download and remove models (against the fake Ollama)."""

import pytest

from arca_engine import service
from arca_engine.activity import recent_activity
from arca_engine.context import AppContext
from tests.fakes.fake_ollama import FakeOllama


@pytest.fixture
def fake():
    f = FakeOllama(token_delay=0)
    yield f
    f.stop()


@pytest.fixture
def ctx(app_paths, fake):
    c = AppContext.create(app_paths, token="t" * 43, include_drive_roots=False)
    c.update_settings({"ollama_url": fake.start()})
    yield c
    c.close()


def names(ctx):
    return {m["name"] for m in service.ai_status(ctx)["models"]}


def test_pull_refused_while_offline(ctx, fake):
    with pytest.raises(service.ServiceError) as err:
        service.pull_model(ctx, "llama3.2:3b")
    assert err.value.status == 403 and "modo online" in str(err.value)
    assert not any(path == "/api/pull" for _, path, _ in fake.requests)


@pytest.mark.parametrize("bad", ["", "  ", "../etc", "a b", "modelo;rm", ":3b", "x" * 200])
def test_pull_rejects_bad_names(ctx, bad):
    ctx.update_settings({"network_mode": "online"})
    with pytest.raises(service.ServiceError) as err:
        service.pull_model(ctx, bad)
    assert err.value.status == 400


def test_pull_streams_progress_and_installs(ctx):
    ctx.update_settings({"network_mode": "online"})
    events = list(service.pull_model(ctx, "llama3.2:1b"))
    assert events[-1] == {"type": "done", "model": "llama3.2:1b"}
    progress = [e for e in events if e["type"] == "progress" and e["total"]]
    assert progress and progress[-1]["completed"] == progress[-1]["total"]
    assert "llama3.2:1b" in names(ctx)
    log = [a["message"] for a in recent_activity(ctx.db, limit=5)]
    assert "Modelo baixado: llama3.2:1b" in log


def test_pull_error_arrives_as_event(ctx):
    ctx.update_settings({"network_mode": "online"})
    events = list(service.pull_model(ctx, "inexistente:1b"))
    assert events[-1]["type"] == "error" and "does not exist" in events[-1]["message"]
    assert "inexistente:1b" not in names(ctx)


def test_delete_unloads_and_clears_default(ctx, fake):
    ctx.update_settings({"default_model": "teste-pequeno:3b"})
    fake.loaded = "teste-pequeno:3b"
    assert service.delete_model(ctx, "teste-pequeno:3b") == {"deleted": "teste-pequeno:3b"}
    assert fake.loaded is None
    assert "teste-pequeno:3b" not in names(ctx)
    assert ctx.settings.default_model is None


def test_delete_works_offline(ctx):
    assert ctx.settings.network_mode == "blocked"
    service.delete_model(ctx, "teste-padrao:8b")
    assert "teste-padrao:8b" not in names(ctx)


def test_delete_unknown_model_is_404(ctx):
    with pytest.raises(service.ServiceError) as err:
        service.delete_model(ctx, "nao-existe:1b")
    assert err.value.status == 404


def test_http_routes(app_paths, fake):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    import json

    from fastapi.testclient import TestClient

    from arca_engine.api.app import create_app

    token = "token-de-teste-" + "x" * 30
    auth = {"Authorization": f"Bearer {token}"}
    ctx = AppContext.create(app_paths, token=token, include_drive_roots=False)
    ctx.update_settings({"ollama_url": fake.start()})
    try:
        with TestClient(create_app(ctx)) as c:
            assert c.post("/ai/models/pull", json={"model": "llama3.2:1b"}, headers=auth).status_code == 403
            assert c.post("/ai/models/pull", json={"model": "llama3.2:1b"}).status_code == 401
            c.put("/settings", json={"network_mode": "online"}, headers=auth)
            r = c.post("/ai/models/pull", json={"model": "library/llama3.2:1b"}, headers=auth)
            events = [json.loads(line) for line in r.text.splitlines() if line]
            assert events[-1]["type"] == "done"
            assert c.delete("/ai/models/library/llama3.2:1b", headers=auth).json() == {
                "deleted": "library/llama3.2:1b"
            }
            assert c.delete("/ai/models/library/llama3.2:1b", headers=auth).status_code == 404
    finally:
        ctx.close()


@pytest.mark.parametrize("bad", [0, -5, 1441, "5", 2.5, True])
def test_idle_unload_minutes_validated(ctx, bad):
    with pytest.raises(service.ServiceError):
        service.update_settings(ctx, {"model_idle_unload_minutes": bad})


def test_idle_unload_minutes_reaches_ollama(ctx, fake):
    service.update_settings(ctx, {"model_idle_unload_minutes": 30})
    assert service.ai_status(ctx)["idle_unload_minutes"] == 30
    list(service.chat(ctx, "oi", "teste-pequeno:3b", memory_probe=lambda: (8 * 1024**3, 16 * 1024**3)))
    chat_body = next(body for method, path, body in fake.requests if path == "/api/chat")
    assert chat_body["keep_alive"] == "30m"
