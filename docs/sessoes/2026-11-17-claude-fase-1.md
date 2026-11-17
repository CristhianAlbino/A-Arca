# 2026-11-17 — Claude — Fase 1 (CORE) + ajustes da Fase 0

- Fase: 0 (ajuste) e 1
- Branch: ajuste da Fase 0 direto em `main` (`71bfe77`); Fase 1 em `feat/fase-1-core`
- PR: **não aberto** — a sessão não tem acesso à API do GitHub (token do `gh` inválido). O usuário abre pelo link em `docs/STATUS.md`.
- Papel nesta sessão: implementação e testes

## Feito

1. Aba **Entretenimento** (Bíblia, literatura, jogos leves, quadrinhos, música; sem filmes): Drive (`12_JOGOS` → `12_ENTRETENIMENTO` com 5 subpastas, LEIA-ME refeito), protótipo, DESIGN.md, catálogo com a Bíblia Livre (CC BY 4.0).
2. Motor: núcleo (pastas, configurações, SQLite), volumes por UUID, guarda de rede, sistema, token, serviço, API FastAPI, ponto de entrada.
3. Interface React: tela inicial com dados reais, volumes, histórico, telas "em construção".
4. ADR 0008: CSS próprio com tokens no lugar de Tailwind.
5. Shell Tauri, ícone, scripts PowerShell, CI.
6. Relatório de testes, STATUS, FASE-01, AGENTS (comandos).

Commits do branch, em ordem: `7379e77` núcleo do motor · `e24517b` volumes/rede/sistema/token · `17faefc` API · `db6382a` interface · `eb658d4` Tauri/scripts/CI · (este) documentação.

## Pendente

- Rodar no notebook: `scripts\setup.ps1`, `scripts\dev.ps1`, critérios 1, 2, 3 e 5.
- Primeira compilação real do Tauri e da interface (`tsc`, `vite build`): pode exigir pequenos ajustes.
- Fontes empacotadas; issues e GitHub Project.

## Não testado (e por quê)

- `test_api.py`, Tauri, Vite/tsc, PowerShell, VRAM real: pacotes não instaláveis no ambiente da sessão e ambiente Linux.

## Decisões tomadas

- [ADR 0008](../adr/0008-estilos-css-tokens.md).
- Fase de Entretenimento: leitura na Fase 6 (Arquivos), jogos na Fase 7 (Módulos).
- Motor empacotado como recurso (pasta onedir) e iniciado pelo próprio shell com `std::process`, sem o plugin shell do Tauri: menos permissões e o token não aparece na linha de comando.
