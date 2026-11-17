"""Offline encyclopedias in ZIM files (Kiwix format), read with python-libzim.

ZIM files are found on the connected ARCA volumes and referred to by
vol://<uuid>/... URIs, never by drive letters. Search uses the ZIM's own
full-text index when present, otherwise title suggestions (ADR 0005).

Article HTML is cleaned for display inside the app: scripts, iframes, forms,
event handlers and external resources are removed; images stored in the ZIM
are inlined as data: URIs so nothing is fetched from the network.
"""

from __future__ import annotations

import base64
import html
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urljoin

try:  # optional at import time so the rest of the engine runs without it
    from libzim.reader import Archive
    from libzim.search import Query, Searcher
    from libzim.suggestion import SuggestionSearcher

    LIBZIM_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only without the dependency
    LIBZIM_AVAILABLE = False

MAX_SCAN_DEPTH = 5
SKIP_DIRS = {"$recycle.bin", "system volume information", "node_modules", ".git"}
MAX_INLINE_IMAGE = 512 * 1024
SNIPPET_CHARS = 220


class KnowledgeError(Exception):
    def __init__(self, message: str, status: int = 400):
        self.status = status
        super().__init__(message)


@dataclass
class ZimInfo:
    id: str  # the archive's own UUID
    uri: str  # vol://<volume>/<path>
    path: Path
    title: str
    description: str
    language: str
    article_count: int
    size_bytes: int
    has_fulltext: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "uri": self.uri,
            "title": self.title,
            "description": self.description,
            "language": self.language,
            "article_count": self.article_count,
            "size_bytes": self.size_bytes,
            "has_fulltext": self.has_fulltext,
        }


def _meta(archive: "Archive", key: str) -> str:
    try:
        return bytes(archive.get_metadata(key)).decode("utf-8", "replace").strip()
    except (KeyError, RuntimeError):
        return ""


def find_zim_files(root: Path, max_depth: int = MAX_SCAN_DEPTH) -> list[Path]:
    """*.zim files under `root`, skipping hidden and system folders."""
    found: list[Path] = []
    root = Path(root)
    base_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).parts) - base_depth
        dirnames[:] = [
            d for d in dirnames if not d.startswith(".") and d.lower() not in SKIP_DIRS and depth < max_depth
        ]
        found.extend(Path(dirpath) / f for f in filenames if f.lower().endswith(".zim"))
    return sorted(found)


class ZimLibrary:
    """The ZIMs on the connected volumes. Archives are opened lazily and cached."""

    def __init__(self, get_volumes):
        self._get_volumes = get_volumes
        self._lock = threading.Lock()
        self._zims: dict[str, ZimInfo] = {}
        self._archives: dict[str, Archive] = {}
        self._scanned = False

    def scan(self) -> list[ZimInfo]:
        if not LIBZIM_AVAILABLE:
            raise KnowledgeError("Leitor de ZIM (python-libzim) não instalado no motor.", status=503)
        volumes = self._get_volumes()
        zims: dict[str, ZimInfo] = {}
        for vol in volumes.status():
            if not vol["available"]:
                continue
            for path in find_zim_files(Path(vol["root"])):
                try:
                    archive = Archive(path)
                except RuntimeError:
                    continue  # damaged or partial download
                zim_id = str(archive.uuid)
                if zim_id in zims:
                    continue  # same ZIM copied on two volumes
                zims[zim_id] = ZimInfo(
                    id=zim_id,
                    uri=volumes.to_uri(path),
                    path=path,
                    title=_meta(archive, "Title") or path.stem,
                    description=_meta(archive, "Description"),
                    language=_meta(archive, "Language"),
                    article_count=archive.article_count,
                    size_bytes=path.stat().st_size,
                    has_fulltext=archive.has_fulltext_index,
                )
        with self._lock:
            self._zims = zims
            self._archives = {k: v for k, v in self._archives.items() if k in zims}
            self._scanned = True
        return list(zims.values())

    def list(self, rescan: bool = False) -> list[ZimInfo]:
        if rescan or not self._scanned:
            self.scan()
        return sorted(self._zims.values(), key=lambda z: z.title.lower())

    def _archive(self, zim_id: str) -> tuple[ZimInfo, "Archive"]:
        if not self._scanned:
            self.scan()
        info = self._zims.get(zim_id)
        if info is None:
            raise KnowledgeError("Enciclopédia não encontrada. O disco dela está conectado?", status=404)
        with self._lock:
            archive = self._archives.get(zim_id)
            if archive is None:
                if not info.path.exists():
                    raise KnowledgeError(f"O arquivo de “{info.title}” não está mais acessível.", status=404)
                archive = self._archives[zim_id] = Archive(info.path)
        return info, archive

    # --- search ---------------------------------------------------------------
    def search(self, query: str, zim_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        targets = [zim_id] if zim_id else [z.id for z in self.list()]
        results: list[dict[str, Any]] = []
        for zid in targets:
            info, archive = self._archive(zid)
            results.extend(self._search_one(info, archive, query, limit))
        return results[: limit * max(1, len(targets))]

    def _search_one(self, info: ZimInfo, archive: "Archive", query: str, limit: int) -> list[dict[str, Any]]:
        paths: list[str] = []
        if info.has_fulltext:
            search = Searcher(archive).search(Query().set_query(query))
            paths = list(search.getResults(0, limit))
        if not paths:
            suggestion = SuggestionSearcher(archive).suggest(query)
            paths = list(suggestion.getResults(0, limit))
        out = []
        seen = set()
        for path in paths:
            try:
                entry = archive.get_entry_by_path(path)
            except KeyError:
                continue
            target = entry.get_redirect_entry() if entry.is_redirect else entry
            if target.path in seen:
                continue
            seen.add(target.path)
            out.append(
                {
                    "zim_id": info.id,
                    "zim_title": info.title,
                    "path": target.path,
                    "title": target.title or target.path,
                    "snippet": _snippet(target),
                }
            )
        return out

    # --- reading --------------------------------------------------------------
    def article(self, zim_id: str, path: str | None = None) -> dict[str, Any]:
        info, archive = self._archive(zim_id)
        try:
            entry = archive.get_entry_by_path(path) if path else archive.main_entry
        except KeyError as exc:
            raise KnowledgeError("Artigo não encontrado nesta enciclopédia.", status=404) from exc
        while entry.is_redirect:
            entry = entry.get_redirect_entry()
        item = entry.get_item()
        if not item.mimetype.startswith("text/html"):
            raise KnowledgeError("Este item não é um artigo de texto.", status=415)
        raw = bytes(item.content).decode("utf-8", "replace")
        return {
            "zim_id": info.id,
            "zim_title": info.title,
            "path": entry.path,
            "title": entry.title or entry.path,
            "html": clean_article_html(raw, entry.path, archive),
        }


# --- HTML cleaning ---------------------------------------------------------------
_REMOVE_BLOCKS = re.compile(
    r"<(script|style|iframe|object|embed|form|noscript|template|svg|math)\b[^>]*>.*?</\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_REMOVE_SINGLE = re.compile(r"<(script|iframe|object|embed|link|meta|base|input|button)\b[^>]*/?>", re.IGNORECASE)
_EVENT_ATTR = re.compile(r"\s+on\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.IGNORECASE)
_STYLE_ATTR = re.compile(r"\s+style\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)
_HREF = re.compile(r"(<a\b[^>]*?\s)href\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)
_IMG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_SRC = re.compile(r"\ssrc\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)
_ALT = re.compile(r"\salt\s*=\s*(\"[^\"]*\"|'[^']*')", re.IGNORECASE)
_BODY = re.compile(r"<body\b[^>]*>(.*)</body\s*>", re.IGNORECASE | re.DOTALL)
_TAGS = re.compile(r"<[^>]+>")
_EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.IGNORECASE)


def _unquote_attr(value: str) -> str:
    return html.unescape(value[1:-1])


def _resolve(base_path: str, href: str) -> str | None:
    """ZIM path that `href` points to, relative to the current article; None if external."""
    if _EXTERNAL.match(href) or href.startswith("#"):
        return None
    href = href.split("#", 1)[0].split("?", 1)[0]
    joined = urljoin("/" + base_path, href).lstrip("/")
    return unquote(str(PurePosixPath(joined))) if joined else None


def clean_article_html(raw: str, base_path: str, archive: "Archive | None" = None) -> str:
    body_match = _BODY.search(raw)
    body = body_match.group(1) if body_match else raw
    body = _REMOVE_BLOCKS.sub("", body)
    body = _REMOVE_SINGLE.sub("", body)
    body = _EVENT_ATTR.sub("", body)
    body = _STYLE_ATTR.sub("", body)

    def fix_link(m: re.Match) -> str:
        href = _unquote_attr(m.group(2))
        if href.startswith("#"):
            return f'{m.group(1)}href="{html.escape(href)}"'
        target = _resolve(base_path, href)
        if target is None:  # external: keep the address visible, never navigable
            return f'{m.group(1)}data-external="{html.escape(href)}"'
        return f'{m.group(1)}data-zim-path="{html.escape(target)}"'

    body = _HREF.sub(fix_link, body)

    def fix_img(m: re.Match) -> str:
        tag = m.group(0)
        src_m = _SRC.search(tag)
        alt_m = _ALT.search(tag)
        alt = html.escape(_unquote_attr(alt_m.group(1))) if alt_m else ""
        data_uri = None
        if src_m and archive is not None:
            target = _resolve(base_path, _unquote_attr(src_m.group(1)))
            if target:
                try:
                    item = archive.get_entry_by_path(target).get_item()
                    if item.mimetype.startswith("image/") and item.size <= MAX_INLINE_IMAGE:
                        data_uri = f"data:{item.mimetype};base64,{base64.b64encode(bytes(item.content)).decode()}"
                except (KeyError, RuntimeError):
                    pass
        if data_uri is None:
            return f'<span class="zim-noimg">[imagem{": " + alt if alt else ""}]</span>' if alt else ""
        return f'<img src="{data_uri}" alt="{alt}">'

    body = _IMG.sub(fix_img, body)
    return body.strip()


def _snippet(entry) -> str:
    try:
        item = entry.get_item()
        if not item.mimetype.startswith("text/html"):
            return ""
        raw = bytes(item.content)[:20000].decode("utf-8", "replace")
    except RuntimeError:
        return ""
    body_match = _BODY.search(raw)
    text = _REMOVE_BLOCKS.sub(" ", body_match.group(1) if body_match else raw)
    text = html.unescape(_TAGS.sub(" ", text))
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r" ([.,;:!?)])", r"\1", text)
    title = (entry.title or "").strip()
    if title and text.startswith(title):
        text = text[len(title):].lstrip(" :-—")
    return text[:SNIPPET_CHARS] + ("…" if len(text) > SNIPPET_CHARS else "")
