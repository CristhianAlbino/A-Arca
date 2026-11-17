# STATUS da ARCA

**Última atualização:** 2026-11-17 · **Fase atual:** 1 — ARCA CORE · **Situação:** código pronto no branch `feat/fase-1-core`, aguardando teste no notebook e revisão (PR)

## O que existe

- Fase 0 concluída: arquitetura, ADRs 0001–0008, estrutura do repositório e do Drive, protótipos (ver [DESIGN.md](arquitetura/DESIGN.md)).
- Fase 1 (branch `feat/fase-1-core`):
  - **Motor** (`engine/`): pastas, configurações, SQLite com migrações, volumes por UUID, guarda de rede, dados do sistema (RAM/VRAM/disco), histórico, API HTTP local com token, ponto de entrada `python -m arca_engine`.
  - **Interface** (`apps/desktop/src`): barra superior com 8 seções (inclui Entretenimento), tela inicial com dados reais, registro de volumes, histórico; telas "em construção" para o que vem depois.
  - **Shell** (`apps/desktop/src-tauri`): inicia e encerra o motor, CSP restrita, instalador NSIS.
  - **Scripts** Windows (`setup.ps1`, `dev.ps1`, `build.ps1`) e CI no GitHub Actions.

## O que funciona (testado)

Ver [testes/2026-11-17-fase1-core.md](testes/2026-11-17-fase1-core.md): 34 testes do motor e 1 teste ponta a ponta da interface no Chromium passaram na sessão de IA (Linux).

## O que não foi testado

- Camada HTTP com FastAPI (`test_api.py`), compilação do Tauri, `vite build`/`tsc`, scripts PowerShell, VRAM real, letras de unidade do Windows. Motivo: o ambiente da sessão não permite instalar pacotes. Tudo isso roda no notebook com `scripts\setup.ps1` e `scripts\dev.ps1`.

## Próximos passos

1. **Usuário:** abrir o PR de `feat/fase-1-core` no GitHub (https://github.com/CristhianAlbino/A-Arca/pull/new/feat/fase-1-core).
2. **Usuário, no notebook:** instalar Python 3.12, Node 20, Rust e Build Tools; rodar `scripts\setup.ps1` e `scripts\dev.ps1`; conferir os critérios da Fase 1 (tabela no relatório de testes).
3. Corrigir o que falhar na primeira compilação real e fazer merge → release `v0.1.0`.
4. Fase 2 (IA) começa depois do merge e do upgrade de RAM para 24 GB.

## Pendências da Fase 1

- Empacotar as fontes Inter e Space Grotesk (hoje usa Segoe UI/sistema como reserva).
- Issues e GitHub Project (não foi possível criar pela sessão: sem acesso à API do GitHub).

## Bloqueios

- Fase 2 depende do upgrade de RAM (8 → 24 GB) para os testes com modelos locais.

## Decisões do usuário (2026-11-17)

| Tema | Decisão |
| --- | --- |
| Motor | Python + FastAPI como sidecar |
| Drive | Google Drive para computador; conta de 5 TB guarda todo o acervo na Etapa 1 |
| Repositório | Público, `CristhianAlbino/A-Arca`, Apache 2.0 |
| Wikipédia | Português e inglês |
| SSD externo | 2 TB, compra futura |
| Design | Navegação inspirada em streaming (Netflix), chat no padrão ChatGPT, identidade própria (grafite, âmbar, verde) |
| Acervo extra | Artes e aba **Entretenimento** (Bíblia, literatura, jogos leves, quadrinhos, música; sem filmes). Jogos somente próprios ou livres |
| Acompanhamento | Cada passo registrado no Git com commits detalhados |
