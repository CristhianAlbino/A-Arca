"""The single door to the network.

Every outbound HTTP request made by the engine goes through NetGuard.
Rules:
- Loopback (localhost, 127.0.0.0/8, ::1) is always allowed: local services
  such as Ollama and kiwix-serve live there.
- Anything else needs network_mode == "online" AND the host in the allowlist.
- Only http and https.
- Redirects are checked again, so an allowed host cannot bounce a request
  to a blocked one.
- Every attempt (allowed or not) is recorded in memory; blocked attempts
  also go to the activity log through the on_blocked callback.
"""

from __future__ import annotations

import ipaddress
import threading
import urllib.error
import urllib.request
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit


class NetworkBlocked(Exception):
    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Conexão bloqueada pela ARCA ({reason}): {url}")


@dataclass(frozen=True)
class NetPolicy:
    mode: str = "blocked"  # "blocked" | "online"
    allowlist: frozenset[str] = field(default_factory=frozenset)


def is_loopback_host(host: str) -> bool:
    host = host.strip("[]").lower()
    if host == "localhost" or host.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def host_allowed(host: str, allowlist: frozenset[str]) -> bool:
    host = host.lower().rstrip(".")
    for entry in allowlist:
        entry = entry.lower().rstrip(".")
        if entry.startswith("*.") and host.endswith(entry[1:]):
            return True
        if host == entry:
            return True
    return False


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes


class NetGuard:
    def __init__(
        self,
        policy: Callable[[], NetPolicy],
        on_blocked: Callable[[dict[str, Any]], None] | None = None,
        history_size: int = 200,
    ):
        self._policy = policy
        self._on_blocked = on_blocked
        self._history: deque[dict[str, Any]] = deque(maxlen=history_size)
        self._lock = threading.Lock()

    # --- decisions ----------------------------------------------------------
    def decide(self, url: str) -> tuple[bool, str]:
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https"):
            return False, f"esquema não permitido: {parts.scheme or 'vazio'}"
        host = parts.hostname or ""
        if not host:
            return False, "endereço sem host"
        if is_loopback_host(host):
            return True, "serviço local"
        policy = self._policy()
        if policy.mode != "online":
            return False, "modo offline"
        if not host_allowed(host, policy.allowlist):
            return False, "host fora da lista permitida"
        return True, "permitido pelo usuário"

    def check(self, url: str) -> None:
        allowed, reason = self.decide(url)
        record = {
            "at": datetime.now(UTC).isoformat(timespec="seconds"),
            "host": urlsplit(url).hostname,
            "url": _redact(url),
            "allowed": allowed,
            "reason": reason,
        }
        with self._lock:
            self._history.append(record)
        if not allowed:
            if self._on_blocked:
                self._on_blocked(record)
            raise NetworkBlocked(_redact(url), reason)

    def attempts(self, only_blocked: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._history)
        if only_blocked:
            items = [i for i in items if not i["allowed"]]
        return list(reversed(items))

    # --- transport ----------------------------------------------------------
    def _opener(self, url: str) -> urllib.request.OpenerDirector:
        guard = self

        class _CheckedRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, hdrs, newurl):  # noqa: N802
                guard.check(newurl)
                return super().redirect_request(req, fp, code, msg, hdrs, newurl)

        handlers: list[Any] = [_CheckedRedirect()]
        if is_loopback_host(urlsplit(url).hostname or ""):
            handlers.append(urllib.request.ProxyHandler({}))  # never send local traffic to a proxy
        return urllib.request.build_opener(*handlers)

    def request(
        self,
        method: str,
        url: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> Response:
        self.check(url)
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method.upper())
        try:
            with self._opener(url).open(req, timeout=timeout) as resp:
                return Response(resp.status, dict(resp.headers.items()), resp.read())
        except urllib.error.HTTPError as err:
            return Response(err.code, dict(err.headers.items()), err.read())
        except urllib.error.URLError as err:
            if isinstance(err.reason, NetworkBlocked):
                raise err.reason from None
            raise

    def get(self, url: str, **kwargs: Any) -> Response:
        return self.request("GET", url, **kwargs)

    def stream_lines(
        self,
        method: str,
        url: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 300.0,
    ) -> Iterator[bytes]:
        """Yield the response body line by line (for NDJSON streams such as Ollama's).

        Raises urllib.error.HTTPError for non-2xx answers. `timeout` applies to each read,
        so a model that takes a while to load does not break the stream.
        """
        self.check(url)
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method.upper())
        try:
            resp = self._opener(url).open(req, timeout=timeout)
        except urllib.error.URLError as err:
            if isinstance(err.reason, NetworkBlocked):
                raise err.reason from None
            raise
        with resp:
            for line in resp:
                if line.strip():
                    yield line


def _redact(url: str) -> str:
    """Drop query strings and credentials from logged URLs."""
    parts = urlsplit(url)
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    return f"{parts.scheme}://{host}{port}{parts.path}"
