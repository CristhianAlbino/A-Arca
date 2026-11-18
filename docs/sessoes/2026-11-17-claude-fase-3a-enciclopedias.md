# 2026-11-17 — Claude — Fase 3A: enciclopédias ZIM

- Fase: 3 (adiantada a pedido do usuário, enquanto a IA local espera o Ollama)
- Branch / PR: `feat/fase-3-kiwix` (sobre `feat/fase-2-modelos`); PR precisa ser aberto pelo usuário
- Papel nesta sessão: planejamento da fase, implementação e testes

## Feito

- `docs/fases/FASE-03.md` com as etapas 3A/3B/3C.
- Motor: `arca_engine/knowledge/kiwix.py` (`ZimLibrary`: encontrar ZIMs nos volumes, metadados, busca texto completo/título, leitura com redirecionamentos, limpeza de HTML com imagens embutidas). Rotas `/knowledge/zims`, `/knowledge/search`, `/knowledge/article`. Dependência `libzim>=3.4,<4`.
- Testes com ZIM real gerado na hora (`tests/fakes/make_zim.py`).
- Interface: tela Conhecimento (lista, filtro, busca, leitor com Voltar; links externos não navegam; segunda limpeza de HTML no navegador).
- Relatório: [testes/2026-11-17-fase3a-enciclopedias.md](../testes/2026-11-17-fase3a-enciclopedias.md).

## Continuação

- PyInstaller não levava o `libzim`: corrigido com `--collect-all libzim` e checagem `--check-deps` no build.
- `build.ps1` não aborta mais por saída em stderr no PowerShell 5.1.
- Catálogo persistente de ZIMs (migração 3).
- `ruff` limpo.

## Pendente

- Testar com ZIMs reais do Drive.
- 3B (busca na biblioteca própria) e 3C (semântica/RAG, depende da IA).

## Não testado (e por quê)

- ZIMs grandes: nenhum disponível nesta sessão.

## Decisões tomadas

- Ler ZIMs com `python-libzim` direto em vez de `kiwix-serve` (detalhe registrado em FASE-03.md; o ADR 0005 continua valendo: Kiwix/ZIM, sem vetorizar a Wikipédia).
- Artigos mostrados num `div` com HTML limpo duas vezes (motor e navegador), não num iframe: a CSP do app já bloqueia scripts inline e assim os links internos ficam fáceis de interceptar.
