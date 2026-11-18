"""Phase 3C: answers grounded in the user's collection, with numbered sources."""

import pytest

pytest.importorskip("libzim")

from arca_engine import service
from arca_engine.context import AppContext
from arca_engine.knowledge import retrieve
from tests.fakes.fake_ollama import FakeOllama
from tests.fakes.make_zim import make_zim

PLENTY = lambda: (8 * 1024**3, 16 * 1024**3)


@pytest.fixture
def fake():
    f = FakeOllama(token_delay=0)
    yield f
    f.stop()


@pytest.fixture
def ctx(app_paths, tmp_path, fake):
    vol = tmp_path / "ssd"
    (vol / "05_LIVROS").mkdir(parents=True)
    (vol / "05_LIVROS" / "agua.txt").write_text(
        "Purificação de água\n\nPara tornar a água potável sem filtro, ferva por um minuto "
        "e guarde em recipiente limpo e tampado.",
        encoding="utf-8",
    )
    make_zim(vol / "03_ENCICLOPEDIAS" / "teste.zim")
    c = AppContext.create(app_paths, token="t" * 43, include_drive_roots=False)
    c.update_settings({"ollama_url": fake.start(), "volume_search_paths": [str(vol)]})
    service.register_volume(c, str(vol), "SSD")
    c.library.index_now()
    service.list_zims(c, rescan=True)
    yield c
    c.close()


def test_keywords_drop_filler_words():
    assert retrieve.keywords("Responda em português: como deixar água segura para beber?") == [
        "deixar", "água", "segura", "beber",
    ]
    assert retrieve.keywords("e o que é?") == []


def test_gather_takes_library_then_encyclopedia(ctx):
    sources = retrieve.gather(ctx, "como deixar a água potável sem filtro?")
    kinds = [s.kind for s in sources]
    assert kinds[0] == "doc" and "zim" in kinds
    assert [s.n for s in sources] == list(range(1, len(sources) + 1))
    doc = sources[0]
    assert doc.title == "Purificação de água" and "ferva" in doc.excerpt and doc.ref["doc_id"]
    zim = next(s for s in sources if s.kind == "zim")
    assert zim.origin == "Enciclopédia de teste" and "<" not in zim.excerpt and zim.ref["path"]


def test_chat_sends_passages_cites_and_stores_only_the_question(ctx, fake):
    question = "Como deixar a água potável sem filtro?"
    events = list(service.chat(ctx, question, "teste-pequeno:3b", memory_probe=PLENTY))
    kinds = [e["type"] for e in events]
    assert kinds[:2] == ["meta", "sources"] and kinds[-1] == "done"
    sources = events[1]["sources"]
    assert sources[0]["title"] == "Purificação de água"

    sent = next(b for m, p, b in fake.requests if p == "/api/chat")
    last_user = sent["messages"][-1]["content"]
    assert last_user.startswith(question) and "[1] Purificação de água" in last_user
    assert "cite" in sent["messages"][0]["content"] and "português do Brasil" in sent["messages"][0]["content"]
    assert sent["options"]["num_ctx"] == 8192

    conv = service.get_conversation(ctx, events[0]["conversation_id"])
    user_msg, answer = conv["messages"]
    assert user_msg["content"] == question  # passages are not stored as if the user wrote them
    assert answer["stats"]["sources"][0]["title"] == "Purificação de água"
    assert "sources" not in events[-1]["stats"]


def test_chat_without_sources_when_turned_off(ctx, fake):
    events = list(service.chat(ctx, "Como deixar a água potável?", "teste-pequeno:3b",
                               memory_probe=PLENTY, use_sources=False))
    assert "sources" not in [e["type"] for e in events]
    sent = next(b for m, p, b in fake.requests if p == "/api/chat")
    assert "Trechos do acervo" not in sent["messages"][-1]["content"]


def test_no_match_means_no_sources(ctx):
    assert retrieve.gather(ctx, "xilofone quântico intergaláctico") == []
