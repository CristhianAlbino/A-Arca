# STATUS da ARCA

**Última atualização:** 2026-11-17 · **Fase atual:** 1 — ARCA CORE (compila e roda no notebook; faltam Wi-Fi desligado, pendrive e instalador) · **Adiantado:** Fase 2A — IA local, no branch `feat/fase-2-ai`

## O que existe

- Fase 0 concluída: arquitetura, ADRs 0001–0008, estrutura do repositório e do Drive, protótipos (ver [DESIGN.md](arquitetura/DESIGN.md)).
- Fase 1 (branch `feat/fase-1-core`):
  - **Motor** (`engine/`): pastas, configurações, SQLite com migrações, volumes por UUID, guarda de rede, dados do sistema (RAM/VRAM/disco), histórico, API HTTP local com token, ponto de entrada `python -m arca_engine`.
  - **Interface** (`apps/desktop/src`): barra superior com 8 seções (inclui Entretenimento), tela inicial com dados reais, registro de volumes, histórico; telas "em construção" para o que vem depois.
  - **Shell** (`apps/desktop/src-tauri`): inicia e encerra o motor, CSP restrita, instalador NSIS.
  - **Scripts** Windows (`setup.ps1`, `dev.ps1`, `build.ps1`) e CI no GitHub Actions.
- Fase 2A (branch `feat/fase-2-ai`, empilhado sobre a Fase 1): conversa com modelos locais pelo Ollama, streaming, um modelo por vez, checagem de memória, conversas salvas, tela de conversa no padrão ChatGPT. Testada com um Ollama falso ([relatório](testes/2026-11-17-fase2a-ia-local.md)).

## O que funciona (testado)

- Fase 1: [testes/2026-11-17-fase1-core.md](testes/2026-11-17-fase1-core.md).
- Fase 2A: [testes/2026-11-17-fase2a-ia-local.md](testes/2026-11-17-fase2a-ia-local.md) — 49 testes do motor e 2 testes ponta a ponta no Chromium passaram na sessão de IA (Linux), com Ollama falso.

- **Notebook (Windows 11), 2026-11-17:** 55 testes do motor (inclui FastAPI), `tsc`, `vite build`, `cargo build` do Tauri, app aberto pelo `dev.ps1`, motor encerrado ao fechar a janela, VRAM real da RTX 5060 lida, requisição sem token recusada ([relatório](testes/2026-11-17-notebook-primeira-compilacao.md)).

## O que não foi testado

- App com Wi-Fi desligado, volume em pendrive, instalador (`scripts\build.ps1`), IA com modelo real (Ollama não instalado).

## Próximos passos

1. **Usuário:** abrir o PR de `feat/fase-1-core` no GitHub (https://github.com/CristhianAlbino/A-Arca/pull/new/feat/fase-1-core).
2. **No notebook:** abrir o app com Wi-Fi desligado, testar um pendrive, rodar `scripts\build.ps1` e instalar o `.exe` gerado.
3. Fazer merge da Fase 1 → release `v0.1.0`.
4. Depois do merge da Fase 1: revisar e mergear `feat/fase-2-ai` (https://github.com/CristhianAlbino/A-Arca/pull/new/feat/fase-2-ai).
5. Testar a IA com modelo real: instalar o Ollama, baixar um modelo pequeno (3–4B) enquanto a RAM é 8 GB; 7–9B depois do upgrade para 24 GB.
6. Próximo a adiantar: etapa 2C (Claude/GPT/Gemini opcionais, chaves no Cofre do Windows) e 2B (baixar/remover modelos).

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
