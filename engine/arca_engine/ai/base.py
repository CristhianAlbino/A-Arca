"""Common shapes for every model provider (local or online)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol


class ProviderUnavailable(Exception):
    """The provider cannot be reached (not installed, not running, offline)."""


class ProviderError(Exception):
    """The provider answered with an error."""


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass(frozen=True)
class ModelInfo:
    name: str
    size_bytes: int
    family: str | None = None
    parameter_size: str | None = None
    quantization: str | None = None
    local: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "size_bytes": self.size_bytes,
            "family": self.family,
            "parameter_size": self.parameter_size,
            "quantization": self.quantization,
            "local": self.local,
        }


@dataclass(frozen=True)
class LoadedModel:
    name: str
    size_bytes: int
    vram_bytes: int
    expires_at: str | None = None


@dataclass
class ChatChunk:
    text: str = ""
    done: bool = False
    stats: dict[str, Any] = field(default_factory=dict)


class ModelProvider(Protocol):
    name: str
    local: bool

    def status(self) -> dict[str, Any]: ...

    def list_models(self) -> list[ModelInfo]: ...

    def loaded(self) -> list[LoadedModel]: ...

    def unload(self, model: str) -> None: ...

    def chat(
        self, model: str, messages: list[ChatMessage], *, keep_alive_minutes: int = 5
    ) -> Iterator[ChatChunk]: ...
