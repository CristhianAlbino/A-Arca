"""The user's own library: text documents on ARCA volumes, searchable offline.

Files (.txt, .md, .html, .pdf, .epub) are found on the connected volumes, their text is
extracted and stored in an SQLite FTS5 index (ADR 0003). Documents are referred to
by vol:// URIs; an unplugged volume keeps its documents in the index, marked as
unavailable, and they are never deleted because of it.

Indexing runs in a background thread; the API reports progress.
"""

from __future__ import annotations

import html
import logging
import os
import re
import sqlite3
import threading
import unicodedata
import zipfile
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from ..activity import log_activity, now_iso
from ..storage.db import connect
from ..storage.volumes import parse_uri

try:
    from pypdf import PdfReader

    PDF_AVAILABLE = True
except ImportError:  # pragma: no cover
    PDF_AVAILABLE = False

log = logging.getLogger("arca_engine.library")

FORMATS = {
    ".txt": "txt", ".md": "md", ".markdown": "md", ".html": "html", ".htm": "html",
    ".pdf": "pdf", ".epub": "epub",
}
MAX_EPUB_PART_BYTES = 20 * 1024 * 1024  # one chapter; guards against zip bombs
MAX_FILE_BYTES = 200 * 1024 * 1024
MAX_TEXT_CHARS = 5_000_000  # keep the index reasonable for huge files
MAX_SCAN_DEPTH = 8
SKIP_DIRS = {"$recycle.bin", "system volume information", "node_modules", ".git", "__pycache__"}

_TAGS = re.compile(r"<[^>]+>")
_DROP_BLOCKS = re.compile(r"<(script|style|noscript|template)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title\s*>", re.IGNORECASE | re.DOTALL)
_MD_HEADING = re.compile(r"^\s{0,3}#\s+(.+?)\s*#*\s*$", re.MULTILINE)
_WORD = re.compile(r"\w+", re.UNICODE)


class LibraryError(Exception):
    def __init__(self, message: str, status: int = 400):
        self.status = status
        super().__init__(message)


# --- text extraction ---------------------------------------------------------------
def _read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def _html_to_text(markup: str) -> str:
    markup = re.sub(r"<(br|/p|/div|/h[1-6]|/li|/tr)\b[^>]*>", "\n", markup, flags=re.IGNORECASE)
    text = html.unescape(_TAGS.sub(" ", _DROP_BLOCKS.sub(" ", markup)))
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return re.sub(r"\n\s*\n\s*(\n\s*)+", "\n\n", text).strip()


def _extract_epub(path: Path) -> tuple[str, str]:
    """(title, text) of an EPUB: chapters in reading order (OPF spine)."""
    with zipfile.ZipFile(path) as zf:
        container = ET.fromstring(zf.read("META-INF/container.xml"))
        rootfile = container.find(".//{*}rootfile")
        if rootfile is None:
            raise ValueError("EPUB sem content.opf")
        opf_path = rootfile.get("full-path", "")
        opf = ET.fromstring(zf.read(opf_path))
        base = PurePosixPath(opf_path).parent
        title_el = opf.find(".//{*}metadata/{*}title")
        title = (title_el.text or "").strip() if title_el is not None else ""
        manifest = {
            item.get("id"): item.get("href", "")
            for item in opf.iterfind(".//{*}manifest/{*}item")
            if "html" in (item.get("media-type") or "")
        }
        parts: list[str] = []
        total = 0
        for ref in opf.iterfind(".//{*}spine/{*}itemref"):
            href = manifest.get(ref.get("idref"))
            if not href:
                continue
            name = str(base / unquote(href)) if str(base) != "." else unquote(href)
            try:
                info = zf.getinfo(name)
            except KeyError:
                continue
            if info.file_size > MAX_EPUB_PART_BYTES:
                continue
            text = _html_to_text(zf.read(info).decode("utf-8", "replace"))
            if text:
                parts.append(text)
                total += len(text)
            if total > MAX_TEXT_CHARS:
                break
    return title, "\n\n".join(parts)


def extract(path: Path) -> tuple[str, str, str]:
    """(format, title, text) for a supported file."""
    fmt = FORMATS[path.suffix.lower()]
    title = path.stem.replace("_", " ").strip()
    if fmt == "epub":
        epub_title, text = _extract_epub(path)
        return fmt, epub_title or title, text
    if fmt == "pdf":
        if not PDF_AVAILABLE:
            raise LibraryError("Leitor de PDF (pypdf) não instalado no motor.", status=503)
        reader = PdfReader(str(path))
        meta_title = (reader.metadata.title if reader.metadata else None) or ""
        parts = []
        total = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            parts.append(text)
            total += len(text)
            if total > MAX_TEXT_CHARS:
                break
        return fmt, meta_title.strip() or title, "\n\n".join(parts)
    text = _read_text_file(path)
    if fmt == "html":
        m = _TITLE.search(text)
        if m and m.group(1).strip():
            title = html.unescape(m.group(1)).strip()
        text = html.unescape(_TAGS.sub(" ", _DROP_BLOCKS.sub(" ", text)))
    elif fmt == "md":
        m = _MD_HEADING.search(text)
        if m:
            title = m.group(1).strip()
    else:  # txt: a short first line followed by a blank line reads as a title
        lines = text.lstrip().splitlines()
        if len(lines) > 1 and 0 < len(lines[0].strip()) <= 100 and not lines[1].strip():
            title = lines[0].strip()
    return fmt, title, text


def find_documents(root: Path, max_depth: int = MAX_SCAN_DEPTH) -> list[Path]:
    found: list[Path] = []
    base = len(Path(root).parts)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).parts) - base
        dirnames[:] = [
            d for d in dirnames if not d.startswith(".") and d.lower() not in SKIP_DIRS and depth < max_depth
        ]
        for name in filenames:
            if Path(name).suffix.lower() in FORMATS and not name.startswith("~$"):
                found.append(Path(dirpath) / name)
    return sorted(found)


# --- search query --------------------------------------------------------------------
def fts_query(text: str) -> str | None:
    """User text → safe FTS5 query: every word must appear; the last one may be a prefix.

    Words are quoted, so FTS5 syntax typed by the user (AND, NEAR, *, ", :) is literal.
    """
    words = _WORD.findall(text)[:12]
    if not words:
        return None
    terms = [f'"{w}"' for w in words[:-1]] + [f'"{words[-1]}"*']
    return " ".join(terms)


def _fold(text: str) -> str:
    """Lowercase, no accents, letters and digits only: "Amanhecer na Colheita " → "amanhecernacolheita"."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if c.isalnum()).lower()


def _same_book(result: dict[str, Any], row: sqlite3.Row) -> bool:
    title, chars = result["_key"]
    if not title or title != _fold(row["title"]):
        return False
    bigger = max(chars, row["chars"]) or 1
    return abs(chars - row["chars"]) / bigger <= 0.10


# --- index ---------------------------------------------------------------------------
class Library:
    def __init__(self, db: sqlite3.Connection, get_volumes: Callable[[], Any], db_path: Path | None = None):
        self.db = db
        self._get_volumes = get_volumes
        # The background indexer uses its own connection, so its transactions never mix
        # with writes made by API requests on the shared one (WAL allows both).
        self._db_path = db_path
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._progress: dict[str, Any] = {"running": False}

    # progress -----------------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        counts = self.db.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(status = 'ok'), 0) AS ok FROM docs"
        ).fetchone()
        with self._lock:
            progress = dict(self._progress)
        return {"documents": counts["n"], "searchable": counts["ok"], **progress}

    def start_indexing(self) -> dict[str, Any]:
        with self._lock:
            if self._progress.get("running"):
                return dict(self._progress)
            self._progress = {"running": True, "done": 0, "total": 0, "current": None, "started_at": now_iso()}
            self._thread = threading.Thread(target=self._run, name="library-index", daemon=True)
            self._thread.start()
            return dict(self._progress)

    def wait(self, timeout: float | None = None) -> None:
        if self._thread:
            self._thread.join(timeout)

    def _set(self, **changes: Any) -> None:
        with self._lock:
            self._progress.update(changes)

    def _run(self) -> None:
        conn = connect(self._db_path) if self._db_path else self.db
        try:
            summary = self.index_now(
                on_progress=lambda done, total, current: self._set(done=done, total=total, current=current),
                conn=conn,
            )
            self._set(running=False, current=None, last_result=summary, finished_at=now_iso())
        except Exception as exc:  # report, never crash the engine
            log.exception("Falha ao indexar a biblioteca")
            self._set(running=False, current=None, error=str(exc), finished_at=now_iso())
        finally:
            if conn is not self.db:
                conn.close()

    def index_now(
        self,
        on_progress: Callable[[int, int, str | None], None] | None = None,
        conn: sqlite3.Connection | None = None,
    ) -> dict[str, int]:
        """Index every supported file on the connected volumes. Returns counters."""
        db = conn or self.db
        volumes = self._get_volumes()
        files: list[tuple[str, Path]] = []
        mounted_ids: list[str] = []
        for vol in volumes.status():
            if vol["available"]:
                mounted_ids.append(vol["id"])
                files.extend((vol["id"], p) for p in find_documents(Path(vol["root"])))

        known = {
            row["uri"]: row
            for row in db.execute("SELECT id, uri, size_bytes, mtime_ns FROM docs").fetchall()
        }
        seen: set[str] = set()
        added = updated = unchanged = failed = 0
        for i, (volume_id, path) in enumerate(files):
            if on_progress:
                on_progress(i, len(files), path.name)
            try:
                uri = volumes.to_uri(path)
                st = path.stat()
            except OSError:
                continue
            seen.add(uri)
            row = known.get(uri)
            if row and row["size_bytes"] == st.st_size and row["mtime_ns"] == st.st_mtime_ns:
                unchanged += 1
                continue
            fmt, title, text, status = FORMATS[path.suffix.lower()], path.stem, "", "ok"
            if st.st_size > MAX_FILE_BYTES:
                status = "erro"
            else:
                try:
                    fmt, title, text = extract(path)
                    text = text[:MAX_TEXT_CHARS]
                    if not text.strip():
                        status = "sem-texto"  # e.g. a scanned PDF: needs OCR (Phase 6)
                except Exception as exc:  # noqa: BLE001 (any damaged file must not stop indexing)
                    log.warning("Não foi possível ler %s: %s", uri, exc)
                    status = "erro"
            if status == "erro":
                failed += 1
            self._upsert(db, row["id"] if row else None, volume_id, uri, title, fmt, st, text, status)
            if row:
                updated += 1
            else:
                added += 1

        # Files gone from a connected volume leave the index; unplugged volumes are untouched.
        removed = 0
        for uri, row in known.items():
            if uri not in seen and parse_uri(uri)[0] in mounted_ids:
                db.execute("DELETE FROM docs_fts WHERE rowid = ?", (row["id"],))
                db.execute("DELETE FROM docs WHERE id = ?", (row["id"],))
                removed += 1
        if on_progress:
            on_progress(len(files), len(files), None)
        summary = {"added": added, "updated": updated, "unchanged": unchanged, "removed": removed, "failed": failed}
        if added or updated or removed:
            log_activity(
                db, "library",
                f"Biblioteca indexada: {added} novos, {updated} atualizados, {removed} removidos",
                summary,
            )
        return summary

    @staticmethod
    def _upsert(db, doc_id, volume_id, uri, title, fmt, st, text, status) -> None:
        now = now_iso()
        db.execute("BEGIN")
        try:
            if doc_id is None:
                cur = db.execute(
                    """INSERT INTO docs (volume_id, uri, title, format, size_bytes, mtime_ns, chars, status, indexed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (volume_id, uri, title, fmt, st.st_size, st.st_mtime_ns, len(text), status, now),
                )
                doc_id = cur.lastrowid
            else:
                db.execute(
                    """UPDATE docs SET volume_id = ?, title = ?, format = ?, size_bytes = ?, mtime_ns = ?,
                       chars = ?, status = ?, indexed_at = ? WHERE id = ?""",
                    (volume_id, title, fmt, st.st_size, st.st_mtime_ns, len(text), status, now, doc_id),
                )
                db.execute("DELETE FROM docs_fts WHERE rowid = ?", (doc_id,))
            db.execute("INSERT INTO docs_fts (rowid, title, body) VALUES (?, ?, ?)", (doc_id, title, text))
            db.execute("COMMIT")
        except BaseException:
            db.execute("ROLLBACK")
            raise

    # search and reading -----------------------------------------------------------------
    def _mounted(self) -> set[str]:
        return {v["id"] for v in self._get_volumes().status() if v["available"]}

    def search(self, text: str, limit: int = 20) -> list[dict[str, Any]]:
        """Best matches first. Copies of the same book (same title, text length within 10%,
        e.g. the EPUB and two PDFs of one novel) are shown once, with the others in `copies`."""
        query = fts_query(text)
        if not query:
            return []
        rows = self.db.execute(
            """
            SELECT d.id, d.uri, d.title, d.format, d.size_bytes, d.chars, d.volume_id,
                   v.label AS volume_label, snippet(docs_fts, 1, '[[', ']]', '…', 14) AS snippet
            FROM docs_fts JOIN docs d ON d.id = docs_fts.rowid JOIN volumes v ON v.id = d.volume_id
            WHERE docs_fts MATCH ?
            ORDER BY bm25(docs_fts, 5.0, 1.0)
            LIMIT ?
            """,
            (query, limit * 3),
        ).fetchall()
        mounted = self._mounted()
        results: list[dict[str, Any]] = []
        for r in rows:
            entry = {
                "id": r["id"], "uri": r["uri"], "title": r["title"], "format": r["format"],
                "size_bytes": r["size_bytes"], "volume_label": r["volume_label"],
                "available": r["volume_id"] in mounted,
            }
            main = next((x for x in results if _same_book(x, r)), None)
            if main is not None:
                main["copies"].append(entry)
                continue
            if len(results) < limit:
                results.append({**entry, "snippet": r["snippet"], "copies": [],
                                "_key": (_fold(r["title"]), r["chars"])})
        for item in results:
            item.pop("_key")
        return results

    def passages(self, words: list[str], limit: int = 2) -> list[dict[str, Any]]:
        """Best passages for an AI answer, one per book (copies grouped), from documents with
        text: those with EVERY keyword first, then (if still short) those with ANY of them."""
        from .retrieve import fts_terms  # retrieve does not import this module back

        terms = fts_terms([w for w in words if _WORD.fullmatch(w)])
        if not terms:
            return []
        sql = """
            SELECT d.id, d.title, d.format, d.chars, v.label AS volume_label,
                   snippet(docs_fts, 1, '', '', '…', 64) AS excerpt
            FROM docs_fts JOIN docs d ON d.id = docs_fts.rowid JOIN volumes v ON v.id = d.volume_id
            WHERE docs_fts MATCH ? AND d.status = 'ok'
            ORDER BY bm25(docs_fts, 5.0, 1.0)
            LIMIT ?
        """
        # Only the text column: a keyword in the book's title ("Jogos Vorazes") must not count,
        # or the passage picked from the text may not mention the rest of the question.
        rows = self.db.execute(sql, (f"body : ({' '.join(terms)})", limit * 4)).fetchall()  # AND
        if len(terms) > 1:
            rows += self.db.execute(sql, (f"body : ({' OR '.join(terms)})", limit * 4)).fetchall()
        picked: list[dict[str, Any]] = []
        for r in rows:
            if any(p["id"] == r["id"] or _same_book(p, r) for p in picked):
                continue
            picked.append({**dict(r), "_key": (_fold(r["title"]), r["chars"])})
            if len(picked) == limit:
                break
        for p in picked:
            p.pop("_key")
        return picked

    def read(self, doc_id: int) -> dict[str, Any]:
        row = self.db.execute(
            """SELECT d.*, v.label AS volume_label, f.body FROM docs d
               JOIN volumes v ON v.id = d.volume_id JOIN docs_fts f ON f.rowid = d.id WHERE d.id = ?""",
            (doc_id,),
        ).fetchone()
        if row is None:
            raise LibraryError("Documento não encontrado na biblioteca.", status=404)
        return {
            "id": row["id"], "uri": row["uri"], "title": row["title"], "format": row["format"],
            "size_bytes": row["size_bytes"], "volume_label": row["volume_label"],
            "available": row["volume_id"] in self._mounted(), "status": row["status"],
            "text": row["body"],
        }
