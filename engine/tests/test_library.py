"""Phase 3B: the user's own library (txt, md, html, pdf) with full-text search."""

import os

import pytest

from arca_engine import service
from arca_engine.context import AppContext
from arca_engine.knowledge.library import extract, fts_query
from tests.fakes.make_pdf import make_pdf


@pytest.fixture
def volume(tmp_path):
    root = tmp_path / "ssd"
    (root / "05_LIVROS").mkdir(parents=True)
    (root / "05_LIVROS" / "agua.txt").write_text(
        "Purificação de água\n\nPara tornar a água potável, ferva por um minuto.", encoding="utf-8"
    )
    (root / "05_LIVROS" / "radio.md").write_text(
        "# Rádio de emergência\n\nUse a frequência combinada com a família.", encoding="utf-8"
    )
    (root / "05_LIVROS" / "fogo.html").write_text(
        "<html><head><title>Fogueira segura</title><script>var x='lenha secreta';</script></head>"
        "<body><p>Escolha lenha seca &amp; proteja do vento.</p></body></html>",
        encoding="utf-8",
    )
    make_pdf(root / "05_LIVROS" / "primeiros-socorros.pdf",
             ["Primeiros socorros", "Em caso de queimadura, resfrie com água corrente."],
             title="Manual de primeiros socorros")
    (root / ".oculta").mkdir()
    (root / ".oculta" / "segredo.txt").write_text("não indexar", encoding="utf-8")
    (root / "05_LIVROS" / "foto.jpg").write_bytes(b"\xff\xd8")
    return root


@pytest.fixture
def ctx(app_paths, volume):
    c = AppContext.create(app_paths, token="t" * 43, include_drive_roots=False)
    c.update_settings({"volume_search_paths": [str(volume)]})
    service.register_volume(c, str(volume), "SSD")
    yield c
    c.close()


def index(ctx):
    return ctx.library.index_now()


def titles(results):
    return [r["title"] for r in results]


def test_fts_query_is_safe():
    assert fts_query("água potável") == '"água" "potável"*'
    assert fts_query('NEAR(a b) OR "x" *') == '"NEAR" "a" "b" "OR" "x"*'
    assert fts_query("  ...  ") is None


def test_extracts_titles_and_text(volume):
    assert extract(volume / "05_LIVROS" / "agua.txt")[1] == "Purificação de água"
    assert extract(volume / "05_LIVROS" / "radio.md")[1] == "Rádio de emergência"
    fmt, title, text = extract(volume / "05_LIVROS" / "fogo.html")
    assert (fmt, title) == ("html", "Fogueira segura")
    assert "lenha seca & proteja" in text and "secreta" not in text
    fmt, title, text = extract(volume / "05_LIVROS" / "primeiros-socorros.pdf")
    assert (fmt, title) == ("pdf", "Manual de primeiros socorros")
    assert "queimadura" in text and "água corrente" in text


def test_index_and_search_without_accents(ctx):
    summary = index(ctx)
    assert summary == {"added": 4, "updated": 0, "unchanged": 0, "removed": 0, "failed": 0}
    assert ctx.library.status()["documents"] == 4
    # "agua" (no accent) finds "água" in the txt and in the PDF
    assert set(titles(service.search_library(ctx, "agua"))) == {"Purificação de água", "Manual de primeiros socorros"}
    hit = service.search_library(ctx, "queimadura")[0]
    assert hit["format"] == "pdf" and hit["available"] is True and hit["volume_label"] == "SSD"
    assert "[[queimadura]]" in hit["snippet"]
    # prefix on the last word, all words required
    assert titles(service.search_library(ctx, "frequencia comb")) == ["Rádio de emergência"]
    assert service.search_library(ctx, "frequencia lenha") == []
    # hidden folders and unsupported files are not indexed
    assert service.search_library(ctx, "indexar") == []


def test_reindex_skips_unchanged_and_tracks_changes(ctx, volume):
    index(ctx)
    assert index(ctx)["unchanged"] == 4
    f = volume / "05_LIVROS" / "agua.txt"
    f.write_text("Água da chuva precisa ser filtrada.", encoding="utf-8")
    os.utime(f, ns=(f.stat().st_atime_ns, f.stat().st_mtime_ns + 5_000_000_000))
    (volume / "05_LIVROS" / "radio.md").unlink()
    summary = index(ctx)
    assert summary["updated"] == 1 and summary["removed"] == 1 and summary["unchanged"] == 2
    assert titles(service.search_library(ctx, "chuva")) == ["agua"]  # no title line any more
    assert service.search_library(ctx, "ferva") == []
    assert service.search_library(ctx, "frequencia") == []


def test_unplugged_volume_keeps_documents(ctx, volume):
    index(ctx)
    (volume / ".arca-volume.json").rename(volume / "guardado.json")
    ctx.volumes.scan()
    summary = index(ctx)
    assert summary["removed"] == 0
    hit = service.search_library(ctx, "queimadura")[0]
    assert hit["available"] is False
    assert service.read_document(ctx, hit["id"])["available"] is False


def test_read_document(ctx):
    index(ctx)
    hit = service.search_library(ctx, "fogueira")[0]
    doc = service.read_document(ctx, hit["id"])
    assert doc["title"] == "Fogueira segura" and "lenha seca" in doc["text"]
    with pytest.raises(service.ServiceError) as err:
        service.read_document(ctx, 999999)
    assert err.value.status == 404


def test_empty_and_broken_files(ctx, volume):
    (volume / "05_LIVROS" / "vazio.txt").write_text("   ", encoding="utf-8")
    (volume / "05_LIVROS" / "quebrado.pdf").write_bytes(b"%PDF-1.4 isto nao e um pdf")
    summary = index(ctx)
    assert summary["added"] == 6 and summary["failed"] == 1
    statuses = dict(ctx.db.execute("SELECT title, status FROM docs").fetchall())
    assert statuses["vazio"] == "sem-texto" and statuses["quebrado"] == "erro"


def test_background_indexing_and_http(app_paths, volume):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from arca_engine.api.app import create_app

    token = "token-de-teste-" + "x" * 30
    auth = {"Authorization": f"Bearer {token}"}
    ctx = AppContext.create(app_paths, token=token, include_drive_roots=False)
    service.register_volume(ctx, str(volume), "SSD")
    try:
        with TestClient(create_app(ctx)) as c:
            assert c.post("/library/index").status_code == 401
            assert c.post("/library/index", headers=auth).status_code == 202
            ctx.library.wait(timeout=30)
            st = c.get("/library/status", headers=auth).json()
            assert st["running"] is False and st["documents"] == 4 and st["last_result"]["added"] == 4
            hits = c.get("/library/search", params={"q": "queimadura"}, headers=auth).json()
            doc = c.get(f"/library/docs/{hits[0]['id']}", headers=auth).json()
            assert "água corrente" in doc["text"]
            assert c.get("/library/search", params={"q": "x" * 301}, headers=auth).status_code == 400
    finally:
        ctx.close()
