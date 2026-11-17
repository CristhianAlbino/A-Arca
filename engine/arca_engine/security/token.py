"""Session token shared only between the engine and the window that started it.

The engine creates a fresh token at every start and prints it once on stdout,
which only the parent process (the Tauri shell) can read. Every API request
must carry `Authorization: Bearer <token>`.
"""

from __future__ import annotations

import hmac
import secrets


def new_token() -> str:
    return secrets.token_urlsafe(32)


def tokens_match(expected: str, given: str | None) -> bool:
    if not given:
        return False
    return hmac.compare_digest(expected.encode(), given.encode())


def bearer_from_header(value: str | None) -> str | None:
    if not value:
        return None
    scheme, _, token = value.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()
