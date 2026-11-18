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


def relevant_excerpt(title: str, excerpt: str, words: list[str]) -> bool:
    """Require actual evidence from the retrieved passage, not just a loose OR hit.

    A one-keyword question only needs one match. Multi-term questions need at
    least two distinct matches across title + excerpt, with at least one in the
    excerpt itself. This reduces unrelated citations without claiming that
    keyword overlap guarantees factual support.
    """
    if not excerpt.strip() or not words:
        return False
    return (
        matched_words(excerpt, words) >= 1
        and matched_words(f"{title} {excerpt}", words) >= min(2, len(words))
    )


def gather(ctx, question: str) -> list[Source]:
    """Up to MAX_SOURCES passages: library first, then encyclopedias. Never raises."""
    sources: list[Source] = []
    words = keywords(question)
    if not words:
        return sources
    try:
        for hit in ctx.library.passages(words, limit=DOC_SOURCES * 2):
            # FTS5's fallback uses OR: a passage matching only a generic word ("casa")
            # is weak evidence for a multi-term question ("tratar queimadura em casa").
            if not relevant_excerpt(hit["title"], hit["excerpt"], words):
                continue
            sources.append(
                Source(
                    n=len(sources) + 1, kind="doc", title=hit["title"],
                    origin=f"{hit['format'].upper()} · {hit['volume_label']}",
                    excerpt=hit["excerpt"][:EXCERPT_CHARS], ref={"doc_id": hit["id"]},
                )
            )
            if len(sources) >= DOC_SOURCES:
                break
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


def _fold_same_length(text: str) -> str:
    """Like fold(), but one character out per character in, so positions match the original."""
    out = []
    for c in text:
        if c.isascii():
            out.append(c.lower())
        else:
            base = unicodedata.normalize("NFD", c)[:1] or c
            out.append(base.lower()[:1] or c)
    return "".join(out)


def _prose_quality(text: str) -> float:
    """0..1: share of letters, scaled down when lines are very short (lists, tables of contents)."""
    letters = sum(c.isalpha() for c in text) / max(1, len(text))
    lines = [ln for ln in text.split("\n") if ln.strip()]
    avg_line = sum(len(ln) for ln in lines) / max(1, len(lines))
    return letters * min(1.0, avg_line / 40)


def looks_like_contents(text: str) -> bool:
    """A table of contents or list of numbers rather than running text."""
    return _prose_quality(text) < 0.25


def best_window(text: str, words: list[str], size: int = 700, max_candidates: int = 3000) -> str:
    """The stretch of `text` (about `size` characters) that best answers the keywords: most
    distinct keywords nearby, mostly running prose. Tables of contents and lists of numbers
    ("Salmos 1 2 3 … 23 …") lose to the passage itself. Empty if no keyword appears."""
    folded = _fold_same_length(text)
    # (needle, is_stem): long words match by stem at a word start; short ones as whole words.
    needles = {(stem(fold(w)), True) if len(w) >= 6 else (fold(w), False) for w in words}
    positions: list[int] = []
    for n, is_stem in sorted(needles, key=lambda x: len(x[0]), reverse=True):
        start = 0
        while len(positions) < max_candidates:
            at = folded.find(n, start)
            if at < 0:
                break
            before = folded[at - 1] if at > 0 else " "
            after = folded[at + len(n)] if at + len(n) < len(folded) else " "
            if not before.isalnum() and (is_stem or not after.isalnum()):
                positions.append(at)
            start = at + 1
    best_score, best_at = -1.0, -1
    for at in positions:
        lo = max(0, at - 80)  # start just before the match: the passage follows it
        window = text[lo: lo + size]
        # Keywords right next to each other ("23 … Salmo de Davi") weigh most.
        near = matched_words(text[max(0, at - 60): at + 60], words)
        score = near * 10 + matched_words(window, words) * 3 + _prose_quality(window) * 5
        if score > best_score:
            best_score, best_at = score, lo
    if best_at < 0:
        return ""
    lo = best_at
    # start and end on word boundaries
    if lo > 0:
        space = text.find(" ", lo)
        lo = space + 1 if 0 <= space < lo + 40 else lo
    hi = min(len(text), lo + size)
    space = text.rfind(" ", lo, hi)
    hi = space if space > lo + size // 2 else hi
    return ("…" if lo > 0 else "") + text[lo:hi].strip() + ("…" if hi < len(text) else "")


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
