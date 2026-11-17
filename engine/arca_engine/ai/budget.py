"""Will this model fit? Checked before loading, so the notebook never freezes.

Ollama splits a model between GPU and system RAM when VRAM is short. That works
but is slower, and a model larger than VRAM + free RAM can make Windows swap
heavily. The rule here:
- fits in free VRAM (with a safety margin)          -> "gpu"
- fits in free VRAM + part of the free RAM           -> "partial" (allowed, slower)
- otherwise                                         -> refused, with an explanation
"""

from __future__ import annotations

from dataclasses import dataclass

GB = 1024**3
VRAM_MARGIN = 0.90  # leave room for the context (KV cache) and the display
RAM_SHARE = 0.60  # never plan to use more than this share of the free RAM


@dataclass(frozen=True)
class Fit:
    ok: bool
    mode: str  # "gpu" | "partial" | "cpu" | "refused"
    message: str


def _gb(n: int) -> str:
    return f"{n / GB:.1f} GB".replace(".", ",")


def check_fit(model_bytes: int, vram_free_bytes: int | None, ram_free_bytes: int) -> Fit:
    ram_budget = int(ram_free_bytes * RAM_SHARE)
    if vram_free_bytes is None:
        if model_bytes <= ram_budget:
            return Fit(True, "cpu", "Sem GPU detectada: o modelo vai rodar na CPU, mais devagar.")
        return Fit(
            False,
            "refused",
            f"O modelo precisa de cerca de {_gb(model_bytes)} e só há {_gb(ram_budget)} de RAM "
            "disponível para ele. Escolha um modelo menor ou feche outros programas.",
        )

    vram_budget = int(vram_free_bytes * VRAM_MARGIN)
    if model_bytes <= vram_budget:
        return Fit(True, "gpu", "O modelo cabe inteiro na memória da placa de vídeo.")
    if model_bytes <= vram_budget + ram_budget:
        return Fit(
            True,
            "partial",
            "O modelo não cabe inteiro na placa de vídeo; parte vai para a RAM e as respostas "
            "serão mais lentas.",
        )
    return Fit(
        False,
        "refused",
        f"O modelo precisa de cerca de {_gb(model_bytes)}, mas há {_gb(vram_budget)} livres na "
        f"placa de vídeo e {_gb(ram_budget)} de RAM disponível. Escolha um modelo menor "
        "(por exemplo, 7–9B quantizado em 4 bits) ou feche outros programas.",
    )
