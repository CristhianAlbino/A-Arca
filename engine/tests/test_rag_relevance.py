"""Regression tests: a loose FTS5 OR hit must not become an irrelevant AI citation."""

from types import SimpleNamespace

from arca_engine.knowledge import retrieve


def fake_context(hits, article=None):
    class Library:
        def passages(self, words, limit=2):
            return hits[:limit]

    class Zims:
        def search(self, query, limit=4):
            if article is None:
                return []
            return [{"zim_id": "z1", "path": "A/queimadura", "title": "Queimadura",
                     "zim_title": "Manual offline"}]

        def article_text(self, zim_id, path, max_chars, words=None):
            return article or ""

    return SimpleNamespace(library=Library(), zims=Zims())


def test_multiword_question_skips_weak_library_hit():
    hits = [
        {"id": 1, "title": "Viagem", "format": "pdf", "volume_label": "SSD",
         "excerpt": "Uma casa bonita ao lado do rio."},
        {"id": 2, "title": "Primeiros socorros", "format": "txt", "volume_label": "SSD",
         "excerpt": "Tratamento de queimaduras: resfrie a região com água corrente."},
    ]
    sources = retrieve.gather(fake_context(hits), "Como tratar queimadura leve em casa?")
    assert len(sources) == 1
    assert sources[0].kind == "doc"
    assert sources[0].ref["doc_id"] == 2
    assert sources[0].n == 1


def test_title_alone_does_not_justify_irrelevant_excerpt():
    words = retrieve.keywords("Tratamento para queimaduras")
    assert not retrieve.relevant_excerpt(
        "Tratamento para queimaduras", "Uma história sobre uma fazenda.", words
    )
    assert retrieve.relevant_excerpt(
        "Queimaduras", "O tratamento começa pela avaliação da lesão.", words
    )


def test_one_keyword_question_still_retrieves_a_matching_passage():
    hit = {"id": 3, "title": "Bíblia Livre", "format": "epub",
           "volume_label": "DRIVE", "excerpt": "Salmo de Davi."}
    sources = retrieve.gather(fake_context([hit]), "Salmo?")
    assert len(sources) == 1
    assert sources[0].ref["doc_id"] == 3


def test_sources_are_renumbered_after_weak_document_is_dropped():
    hit = {"id": 1, "title": "Viagem", "format": "pdf", "volume_label": "SSD",
           "excerpt": "Uma casa bonita ao lado do rio."}
    ctx = fake_context(
        [hit], article="Para tratar queimaduras, siga orientações de primeiros socorros."
    )
    sources = retrieve.gather(ctx, "Como tratar queimadura leve em casa?")
    assert [source.kind for source in sources] == ["zim"]
    assert [source.n for source in sources] == [1]
    assert sources[0].origin == "Manual offline"
