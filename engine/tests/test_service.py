import pytest

from arca_engine import service
from arca_engine.context import AppContext
from arca_engine.netguard import NetworkBlocked


@pytest.fixture
def ctx(app_paths):
    c = AppContext.create(app_paths, token="t" * 43, include_drive_roots=False)
    yield c
    c.close()


def test_health(ctx):
    h = service.health(ctx)
    assert h["status"] == "ok" and h["network_mode"] == "blocked" and h["db_schema"] >= 1


def test_system_includes_volumes(ctx, tmp_path):
    (tmp_path / "ssd").mkdir()
    service.register_volume(ctx, str(tmp_path / "ssd"), "ARCA-EXT")
    snap = service.system(ctx)
    assert snap["memory"]["total_bytes"] > 0
    assert snap["volumes"][0]["label"] == "ARCA-EXT"


def test_register_volume_errors_are_friendly(ctx, tmp_path):
    with pytest.raises(service.ServiceError):
        service.register_volume(ctx, str(tmp_path / "nao-existe"), "X")
    with pytest.raises(service.ServiceError):
        service.register_volume(ctx, str(tmp_path), "   ")


def test_settings_update_persists_and_logs(ctx, app_paths):
    out = service.update_settings(ctx, {"network_mode": "online", "network_allowlist": ["api.anthropic.com"]})
    assert out["network_mode"] == "online"
    assert app_paths.settings_file.exists()
    ctx.netguard.check("https://api.anthropic.com/v1/messages")  # now allowed
    assert any("ONLINE" in a["message"] for a in service.activity(ctx))


def test_settings_reject_unknown_and_invalid(ctx):
    with pytest.raises(service.ServiceError):
        service.update_settings(ctx, {"token": "x"})
    with pytest.raises(service.ServiceError):
        service.update_settings(ctx, {"network_mode": "talvez"})


def test_blocked_network_shows_up_in_activity(ctx):
    with pytest.raises(NetworkBlocked):
        ctx.netguard.check("https://example.com/")
    assert service.network_attempts(ctx, only_blocked=True)[0]["host"] == "example.com"
    assert service.activity(ctx)[0]["kind"] == "network"


def test_register_volume_needs_full_path(app_paths, tmp_path):
    from arca_engine.context import AppContext

    ctx = AppContext.create(app_paths, token="t" * 43, include_drive_roots=False)
    try:
        for bad in ["ollama", "pasta/sub", "  "]:
            with pytest.raises(service.ServiceError, match="caminho completo"):
                service.register_volume(ctx, bad, "X")
        (tmp_path / "ok").mkdir()
        assert service.register_volume(ctx, f'"{tmp_path / "ok"}"', "OK")["label"] == "OK"
    finally:
        ctx.close()
