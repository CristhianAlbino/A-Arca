"""Phase 3: offline encyclopedias (ZIM) on ARCA volumes."""

import pytest

pytest.importorskip("libzim")

from arca_engine import service  # noqa: E402
from arca_engine.context import AppContext  # noqa: E402
from arca_engine.knowledge.kiwix import clean_article_html, find_zim_files  # noqa: E402
from tests.fakes.make_zim import make_zim  # noqa: E402


@pytest.fixture
def volume(tmp_path):
    root = tmp_path / "ssd"
    root.mkdir()
    return root


@pytest.fixture
def ctx(app_paths, volume):
    c = AppContext.create(app_paths, token="t" * 43, include_drive_roots=False)
    c.update_settings({"volume_search_paths": [str(volume)]})
    service.register_volume(c, str(volume), "SSD")
    yield c
    c.close()


@pytest.fixture
def zim(ctx, volume):
    make_zim(volume / "03_ENCICLOPEDIAS" / "teste.zim")
    return service.list_zims(ctx, rescan=True)[0]


def test_find_skips_hidden_and_system_folders(tmp_path):
    for rel in ["a/x.zim", ".oculta/y.zim", "System Volume Information/z.zim", "b/notas.txt"]:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(b"")
    assert [p.name for p in find_zim_files(tmp_path)] == ["x.zim"]


def test_zim_listed_with_volume_uri(zim, ctx):
    assert zim["title"] == "Enciclopédia de teste"
    assert zim["language"] == "por" and zim["article_count"] >= 3
    assert zim["uri"].startswith("vol://") and zim["uri"].endswith("/03_ENCICLOPEDIAS/teste.zim")
    assert ":\\" not in zim["uri"]


def test_unplugged_volume_hides_zim(zim, ctx, volume):
    (volume / ".arca-volume.json").rename(volume / "marcador-guardado.json")
    ctx.volumes.scan()
    assert service.list_zims(ctx, rescan=True) == []
    with pytest.raises(service.ServiceError) as err:
        service.read_article(ctx, zim["id"], "Agua_potavel")
    assert err.value.status == 404


def test_search_finds_article_with_snippet(zim, ctx):
    results = service.search_knowledge(ctx, "ferver")
    titles = [r["title"] for r in results]
    assert "Água potável" in titles
    hit = next(r for r in results if r["title"] == "Água potável")
    assert hit["zim_title"] == "Enciclopédia de teste"
    assert "consumo humano" in hit["snippet"] and "<" not in hit["snippet"]
    assert " ." not in hit["snippet"]


def test_search_without_fulltext_uses_titles(ctx, volume):
    make_zim(volume / "so-titulos.zim", title="Só títulos", fulltext=False)
    zim = service.list_zims(ctx, rescan=True)[0]
    assert zim["has_fulltext"] is False
    assert [r["title"] for r in service.search_knowledge(ctx, "Rádio", zim_id=zim["id"])] == ["Rádio amador"]


def test_redirect_resolves_and_dedupes(zim, ctx):
    article = service.read_article(ctx, zim["id"], "Agua")
    assert article["path"] == "Agua_potavel" and article["title"] == "Água potável"


def test_main_page_when_no_path(zim, ctx):
    assert service.read_article(ctx, zim["id"])["path"] == "Agua_potavel"


def test_article_html_is_cleaned(zim, ctx):
    html = service.read_article(ctx, zim["id"], "Agua_potavel")["html"]
    assert "<script" not in html and "alert(" not in html
    assert "onclick" not in html and "style=" not in html
    assert 'data-zim-path="Filtro_de_agua"' in html
    assert 'data-external="https://pt.wikipedia.org/wiki/Agua"' in html
    assert "href=\"https://" not in html
    assert 'src="data:image/png;base64,' in html
    assert "<body" not in html and "<h1>Água potável</h1>" in html


def test_relative_links_resolve_from_subfolders():
    out = clean_article_html('<a href="../B/Outro#sec">x</a><img src="http://x.com/a.png" alt="foto">', "A/Um")
    assert 'data-zim-path="B/Outro"' in out
    assert "http://x.com" not in out and "[imagem: foto]" in out


def test_missing_article_and_unknown_zim(zim, ctx):
    with pytest.raises(service.ServiceError) as err:
        service.read_article(ctx, zim["id"], "Nao_existe")
    assert err.value.status == 404
    with pytest.raises(service.ServiceError) as err:
        service.read_article(ctx, "zim-desconhecido", "x")
    assert err.value.status == 404


def test_http_routes(app_paths, volume):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from arca_engine.api.app import create_app

    token = "token-de-teste-" + "x" * 30
    auth = {"Authorization": f"Bearer {token}"}
    ctx = AppContext.create(app_paths, token=token, include_drive_roots=False)
    ctx.update_settings({"volume_search_paths": [str(volume)]})
    service.register_volume(ctx, str(volume), "SSD")
    make_zim(volume / "teste.zim")
    try:
        with TestClient(create_app(ctx)) as c:
            assert c.get("/knowledge/zims").status_code == 401
            zims = c.get("/knowledge/zims?rescan=true", headers=auth).json()
            zid = zims[0]["id"]
            hits = c.get("/knowledge/search", params={"q": "radioamadorismo"}, headers=auth).json()
            assert hits[0]["path"] == "Radio_amador"
            art = c.get("/knowledge/article", params={"zim": zid, "path": "Radio_amador"}, headers=auth)
            assert art.json()["title"] == "Rádio amador"
            assert c.get("/knowledge/search", params={"q": "x" * 301}, headers=auth).status_code == 400
    finally:
        ctx.close()
