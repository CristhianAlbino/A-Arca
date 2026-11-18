"""Find passages in the user's library and encyclopedias to ground an AI answer (Phase 3C).

"Search, then read" (ADR 0005): no embeddings yet. The question becomes keywords for the
library's FTS5 index (any keyword, best-ranked first) and a natural-language query for the
ZIM full-text index. A few short, numbered passages go to the model, which is told to cite
them as [1], [2]...
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any

log = logging.getLogger("arca_engine.retrieve")

MAX_SOURCES = 4
DOC_SOURCES = 2
ZIM_SOURCES = 2
EXCERPT_CHARS = 900

# Common Portuguese words that say nothing about the topic.
STOPWORDS = frozenset(
    """
    a à ao aos as às até com como da das de dela dele deles do dos e é em entre era essa esse
    esta este eu foi há isso isto já la lá lhe mais mas me meu minha muito na nas não nem no
    nos o os ou para pela pelas pelo pelos por pra qual quais quando que quem se sem ser seu
    sua são só também te tem um uma umas uns você vocês sobre quanto quantos quantas onde
    porque porquê pode posso fazer faço devo deve preciso explique explica diga diz fale conte
    responda resposta frase frases curta curtas sim ok obrigado obrigada favor portugues português
    """.split()  # noqa: SIM905 (readable word list)
)
_WORD = re.compile(r"[\w-]+", re.UNICODE)


@dataclass
class Source:
    n: int
    kind: str  # "doc" | "zim"
    title: str
    origin: str  # "Wikipédia" / "EPUB · DRIVE"
    excerpt: str
    ref: dict[str, Any] = field(default_factory=dict)  # {"doc_id": 3} or {"zim_id": ..., "path": ...}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def keywords(question: str, limit: int = 8) -> list[str]:
    # Numbers count even when short ("Salmo 23", "NBR 5410").
    words = [
        w for w in _WORD.findall(question.lower())
        if (len(w) >= 3 or w.isdigit()) and w not in STOPWORDS
    ]
    seen: list[str] = []
    for w in words:
        if w not in seen:
            seen.append(w)
    return seen[:limit]


def gather(ctx, question: str) -> list[Source]:
    """Up to MAX_SOURCES passages: library first, then encyclopedias. Never raises."""
    sources: list[Source] = []
    words = keywords(question)
    if not words:
        return sources
    try:
        for hit in ctx.library.passages(words, limit=DOC_SOURCES):
            sources.append(
                Source(
                    n=len(sources) + 1, kind="doc", title=hit["title"],
                    origin=f"{hit['format'].upper()} · {hit['volume_label']}",
                    excerpt=hit["excerpt"][:EXCERPT_CHARS], ref={"doc_id": hit["id"]},
                )
            )
    except Exception:
        log.exception("Falha ao buscar trechos na biblioteca")
    try:
        for hit, strict in _zim_hits(ctx, words):
            if len(sources) >= MAX_SOURCES:
                break
            text = ctx.zims.article_text(hit["zim_id"], hit["path"], EXCERPT_CHARS, words=words)
            # A hit from a one-word search must still mention more of the question.
            enough = min(2, len(words))
            if text and (not strict or matched_words(f"{hit['title']} {text}", words) >= enough):
                sources.append(
                    Source(
                        n=len(sources) + 1, kind="zim", title=hit["title"], origin=hit["zim_title"],
                        excerpt=text, ref={"zim_id": hit["zim_id"], "path": hit["path"]},
                    )
                )
    except Exception:
        log.exception("Falha ao buscar trechos nas enciclopédias")
    return sources


def fold(text: str) -> str:
    """Lowercase without accents: "Água" → "agua"."""
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def stem(word: str) -> str:
    """Crude Portuguese stem so word forms meet: "tratar"/"tratamento" → "trat",
    "queimadura"/"queimaduras" → "queimad". Short words (names like "Prim") stay whole."""
    return word[: max(4, len(word) - 3)] if len(word) >= 6 else word


def fts_terms(words: list[str]) -> list[str]:
    """FTS5 terms: long words as stem prefixes ("trat"*), short ones exact ("prim")."""
    return [f'"{stem(w)}"*' if len(w) >= 6 else f'"{w}"' for w in words]


def matched_words(text: str, words: list[str]) -> int:
    """How many keywords appear in `text` as whole words (short ones) or by stem (long ones),
    ignoring accents and case."""
    folded = " " + re.sub(r"[^\w]+", " ", fold(text)) + " "
    count = 0
    for w in words:
        f = fold(w)
        count += (f" {stem(f)}" in folded) if len(f) >= 6 else (f" {f} " in folded)
    return count


def _zim_hits(ctx, words: list[str]) -> list[tuple[dict[str, Any], bool]]:
    """(hit, strict). The ZIM index wants every word; a question rarely matches that. Try the
    whole set, then the most specific (longest) words one by one. Hits from those one-word
    searches are `strict`: the caller keeps them only if the article mentions more keywords."""
    hits: list[tuple[dict[str, Any], bool]] = []
    seen: set[tuple[str, str]] = set()
    attempts = [(" ".join(words), False)] + [(w, True) for w in sorted(words, key=len, reverse=True)[:3]]
    for query, strict in attempts:
        for hit in ctx.zims.search(query, limit=ZIM_SOURCES * 2):
            key = (hit["zim_id"], hit["path"])
            if key not in seen:
                seen.add(key)
                hits.append((hit, strict and len(words) > 1))
        if len(hits) >= ZIM_SOURCES * 2:
            break
    return hits


def context_block(sources: list[Source]) -> str:
    """Text appended to the user's question for the model (not stored in the conversation)."""
    lines = [
        (
            "Trechos do acervo do usuário (use-os se ajudarem; cite como [1], [2]...; "
            "se não responderem à pergunta, diga isso):"
        ),
    ]
    for s in sources:
        lines.append(f"\n[{s.n}] {s.title} — {s.origin}\n{s.excerpt.strip()}")
    return "\n".join(lines)
