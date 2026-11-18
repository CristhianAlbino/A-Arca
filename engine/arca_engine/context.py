"""Everything the engine needs at runtime, created once at startup."""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass, field

from .activity import log_activity
from .ai.ollama import OllamaProvider
from .config.paths import AppPaths
from .config.settings import Settings, load_settings, save_settings
from .knowledge.kiwix import ZimLibrary
from .knowledge.library import Library
from .netguard import NetGuard, NetPolicy
from .storage.db import open_database
from .storage.volumes import VolumeRegistry


@dataclass
class AppContext:
    paths: AppPaths
    token: str
    db: sqlite3.Connection
    settings: Settings
    netguard: NetGuard = field(init=False)
    volumes: VolumeRegistry = field(init=False)
    _settings_lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    zims: ZimLibrary = field(init=False)
    library: Library = field(init=False)

    def __post_init__(self) -> None:
        self.netguard = NetGuard(self._net_policy, on_blocked=self._log_blocked)
        self.volumes = VolumeRegistry(self.db, search_paths=lambda: self.settings.volume_search_paths)
        # A getter, because create() may swap the registry after construction.
        self.zims = ZimLibrary(lambda: self.volumes, db=self.db)
        self.library = Library(self.db, lambda: self.volumes, db_path=self.paths.database_file)

    @classmethod
    def create(cls, paths: AppPaths, token: str, include_drive_roots: bool = True) -> AppContext:
        paths.ensure()
        ctx = cls(
            paths=paths,
            token=token,
            db=open_database(paths.database_file),
            settings=load_settings(paths.settings_file),
        )
        if not include_drive_roots:
            ctx.volumes = VolumeRegistry(
                ctx.db, search_paths=lambda: ctx.settings.volume_search_paths, include_drive_roots=False
            )
        ctx.volumes.scan()
        return ctx

    def ai_provider(self) -> OllamaProvider:
        return OllamaProvider(self.netguard, self.settings.ollama_url)

    def _net_policy(self) -> NetPolicy:
        s = self.settings
        return NetPolicy(mode=s.network_mode, allowlist=frozenset(s.network_allowlist))

    def _log_blocked(self, record: dict) -> None:
        log_activity(self.db, "network", f"Conexão bloqueada: {record['host']}", record)

    def update_settings(self, changes: dict) -> Settings:
        with self._settings_lock:
            merged = {**self.settings.to_dict(), **changes}
            new = Settings.from_dict(merged)  # validates
            save_settings(self.paths.settings_file, new)
            old_mode = self.settings.network_mode
            self.settings = new
        if new.network_mode != old_mode:
            label = "ONLINE" if new.network_mode == "online" else "OFFLINE"
            log_activity(self.db, "network", f"Modo de rede alterado para {label}")
        return new

    def close(self) -> None:
        self.library.wait(timeout=30)
        self.db.close()
