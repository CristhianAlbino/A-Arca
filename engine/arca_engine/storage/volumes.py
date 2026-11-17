"""Storage volumes identified by UUID, not by drive letter.

Every disk (or folder) the ARCA stores content on gets a `.arca-volume.json`
marker at its root. Files are referenced as `vol://<uuid>/<relative/path>`,
so an external SSD can change letters (E: today, F: tomorrow) or be unplugged
without breaking anything: content on a missing volume is reported as
unavailable, never deleted or forgotten.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import string
import sys
import uuid
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from ..activity import log_activity, now_iso

MARKER_NAME = ".arca-volume.json"
MARKER_SCHEMA = 1
URI_PREFIX = "vol://"


class VolumeError(Exception):
    pass


class InvalidVolumeUri(VolumeError):
    pass


class VolumeUnavailable(VolumeError):
    def __init__(self, volume_id: str, label: str | None = None):
        self.volume_id = volume_id
        self.label = label
        name = label or volume_id
        super().__init__(f"Volume indisponível: {name}. Conecte o disco para acessar este conteúdo.")


@dataclass(frozen=True)
class VolumeMarker:
    volume_id: str
    label: str
    created_at: str
    arca_schema: int = MARKER_SCHEMA


def read_marker(root: Path) -> VolumeMarker | None:
    marker = Path(root) / MARKER_NAME
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        uuid.UUID(data["volume_id"])
        return VolumeMarker(
            volume_id=data["volume_id"],
            label=str(data.get("label") or "ARCA"),
            created_at=str(data.get("created_at") or ""),
            arca_schema=int(data.get("arca_schema", MARKER_SCHEMA)),
        )
    except (OSError, ValueError, KeyError, TypeError):
        return None


def create_marker(root: Path, label: str) -> VolumeMarker:
    """Create the marker if missing. An existing marker is never overwritten."""
    root = Path(root)
    existing = read_marker(root)
    if existing:
        return existing
    if not root.is_dir():
        raise VolumeError(f"A pasta não existe: {root}")
    marker = VolumeMarker(volume_id=str(uuid.uuid4()), label=label, created_at=now_iso())
    target = root / MARKER_NAME
    with target.open("x", encoding="utf-8") as fh:  # "x": fail instead of overwrite
        json.dump(asdict(marker), fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return marker


def parse_uri(uri: str) -> tuple[str, PurePosixPath]:
    if not uri.startswith(URI_PREFIX):
        raise InvalidVolumeUri(f"URI de volume inválida: {uri}")
    rest = uri[len(URI_PREFIX):]
    volume_id, _, rel = rest.partition("/")
    try:
        uuid.UUID(volume_id)
    except ValueError as exc:
        raise InvalidVolumeUri(f"ID de volume inválido em {uri}") from exc
    rel_path = PurePosixPath(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise InvalidVolumeUri(f"Caminho fora do volume em {uri}")
    return volume_id, rel_path


def make_uri(volume_id: str, relative: str | PurePosixPath) -> str:
    rel = PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise InvalidVolumeUri("O caminho precisa ser relativo à raiz do volume")
    return f"{URI_PREFIX}{volume_id}/{rel.as_posix()}" if str(rel) != "." else f"{URI_PREFIX}{volume_id}/"


def windows_drive_roots() -> list[Path]:
    if not sys.platform.startswith("win"):
        return []
    return [Path(f"{letter}:\\") for letter in string.ascii_uppercase[2:]]  # C: to Z:


class VolumeRegistry:
    """Known volumes (in the database) plus where each one is mounted right now."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        search_paths: Callable[[], Iterable[str | Path]] = lambda: (),
        include_drive_roots: bool = True,
    ):
        self.conn = conn
        self._search_paths = search_paths
        self._include_drive_roots = include_drive_roots
        self._mounted: dict[str, Path] = {}

    # --- registration -------------------------------------------------------
    def register(self, root: str | Path, label: str) -> VolumeMarker:
        root = Path(root).resolve()
        marker = create_marker(root, label)
        now = now_iso()
        self.conn.execute(
            """INSERT INTO volumes (id, label, last_root, created_at, last_seen_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET last_root = excluded.last_root,
                                             last_seen_at = excluded.last_seen_at""",
            (marker.volume_id, marker.label, str(root), marker.created_at or now, now),
        )
        self._mounted[marker.volume_id] = root
        log_activity(self.conn, "volume", f"Volume registrado: {marker.label}", {"root": str(root)})
        return marker

    def known(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM volumes ORDER BY label").fetchall()

    # --- discovery ----------------------------------------------------------
    def candidate_roots(self) -> list[Path]:
        seen: set[str] = set()
        out: list[Path] = []
        sources: list[Iterable[str | Path]] = [
            (row["last_root"] for row in self.known() if row["last_root"]),
            self._search_paths(),
        ]
        if self._include_drive_roots:
            sources.append(windows_drive_roots())
        for source in sources:
            for p in source:
                key = os.path.normcase(str(p))
                if key not in seen:
                    seen.add(key)
                    out.append(Path(p))
        return out

    def scan(self) -> dict[str, Path]:
        """Look for markers at every candidate root; update where volumes are now."""
        known_ids = {row["id"] for row in self.known()}
        mounted: dict[str, Path] = {}
        for root in self.candidate_roots():
            marker = read_marker(root)
            if marker and marker.volume_id in known_ids and marker.volume_id not in mounted:
                mounted[marker.volume_id] = root
        now = now_iso()
        for volume_id, root in mounted.items():
            self.conn.execute(
                "UPDATE volumes SET last_root = ?, last_seen_at = ? WHERE id = ?",
                (str(root), now, volume_id),
            )
        self._mounted = mounted
        return dict(mounted)

    # --- queries ------------------------------------------------------------
    def status(self) -> list[dict[str, Any]]:
        out = []
        for row in self.known():
            root = self._mounted.get(row["id"])
            available = root is not None and read_marker(root) is not None
            entry: dict[str, Any] = {
                "id": row["id"],
                "label": row["label"],
                "available": available,
                "root": str(root) if available else None,
                "last_root": row["last_root"],
                "last_seen_at": row["last_seen_at"],
                "total_bytes": None,
                "free_bytes": None,
            }
            if available:
                usage = shutil.disk_usage(root)
                entry["total_bytes"] = usage.total
                entry["free_bytes"] = usage.free
            out.append(entry)
        return out

    def resolve(self, uri: str) -> Path:
        volume_id, rel = parse_uri(uri)
        root = self._mounted.get(volume_id)
        if root is None or read_marker(root) is None:
            row = self.conn.execute("SELECT label FROM volumes WHERE id = ?", (volume_id,)).fetchone()
            raise VolumeUnavailable(volume_id, row["label"] if row else None)
        target = (root / Path(*rel.parts)).resolve() if rel.parts else root.resolve()
        if not target.is_relative_to(root.resolve()):
            raise InvalidVolumeUri(f"Caminho fora do volume em {uri}")
        return target

    def to_uri(self, path: str | Path) -> str:
        path = Path(path).resolve()
        for volume_id, root in self._mounted.items():
            root = root.resolve()
            if path.is_relative_to(root):
                return make_uri(volume_id, PurePosixPath(*path.relative_to(root).parts))
        raise VolumeError(f"O arquivo não está em nenhum volume ARCA conectado: {path}")
