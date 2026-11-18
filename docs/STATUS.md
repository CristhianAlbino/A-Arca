# STATUS da ARCA

**Última atualização:** 2026-11-17 · **Fase atual:** 1 — ARCA CORE (instalada e funcionando no notebook; faltam Wi-Fi desligado e pendrive) · **Adiantado:** Fase 2A — IA local, no branch `feat/fase-2-ai`

## O que existe

- Fase 0 concluída: arquitetura, ADRs 0001–0008, estrutura do repositório e do Drive, protótipos (ver [DESIGN.md](arquitetura/DESIGN.md)).
- Fase 1 (branch `feat/fase-1-core`):
  - **Motor** (`engine/`): pastas, configurações, SQLite com migrações, volumes por UUID, guarda de rede, dados do sistema (RAM/VRAM/disco), histórico, API HTTP local com token, ponto de entrada `python -m arca_engine`.
  - **Interface** (`apps/desktop/src`): barra superior com 8 seções (inclui Entretenimento), tela inicial com dados reais, registro de volumes, histórico; telas "em construção" para o que vem depois.
  - **Shell** (`apps/desktop/src-tauri`): inicia e encerra o motor, CSP restrita, instalador NSIS.
  - **Scripts** Windows (`setup.ps1`, `dev.ps1`, `build.ps1`) e CI no GitHub Actions.
- Fase 2A (branch `feat/fase-2-ai`, empilhado sobre a Fase 1): conversa com modelos locais pelo Ollama, streaming, um modelo por vez, checagem de memória, conversas salvas, tela de conversa no padrão ChatGPT. Testada com um Ollama falso ([relatório](testes/2026-11-17-fase2a-ia-local.md)).
- Fase 2B (branch `feat/fase-2-modelos`, sobre `feat/fase-2-ai`): baixar modelos (só com modo online ligado), remover modelos e escolher o tempo de descarga, pelo painel "Gerenciar modelos" da tela de IA; respostas em Markdown completo (pendência da 2A). Testada com Ollama falso ([relatório](testes/2026-11-17-fase2b-gestao-modelos.md)).
- Fase 3A, adiantada a pedido do usuário (branch `feat/fase-3-kiwix`, sobre `feat/fase-2-modelos`): tela Conhecimento lê e busca enciclopédias `.zim` (Kiwix) nos volumes, sem internet. Testada com um ZIM gerado nos testes ([relatório](testes/2026-11-17-fase3a-enciclopedias.md); plano em [FASE-03.md](fases/FASE-03.md)).
- Fase 3B (branch `feat/fase-3-biblioteca`, sobre `feat/fase-3-kiwix`): a tela Conhecimento também indexa e busca seus documentos `.txt`, `.md`, `.html` e `.pdf` dos volumes (índice FTS5 sem acentos), junto com as enciclopédias ([relatório](testes/2026-11-17-fase3b-biblioteca.md)).

## O que funciona (testado)

- Fase 1: [testes/2026-11-17-fase1-core.md](testes/2026-11-17-fase1-core.md).
- Fase 2A: [testes/2026-11-17-fase2a-ia-local.md](testes/2026-11-17-fase2a-ia-local.md) — 49 testes do motor e 2 testes ponta a ponta no Chromium passaram na sessão de IA (Linux), com Ollama falso.

- **Notebook (Windows 11), 2026-11-17:** 55 testes do motor (inclui FastAPI), `tsc`, `vite build`, `cargo build` do Tauri, app aberto pelo `dev.ps1`, motor encerrado ao fechar a janela, VRAM real da RTX 5060 lida, requisição sem token recusada ([relatório](testes/2026-11-17-notebook-primeira-compilacao.md)).

## O que não foi testado

- App com Wi-Fi desligado, volume em pendrive, IA com modelo real (Ollama não instalado), enciclopédia ZIM real. O app instalado já foi testado (ver relatório da 3A).
- Atenção: as correções do `build.ps1` (libzim no pacote e stderr no PowerShell 5.1) estão só no branch `feat/fase-3-kiwix`; nos branches anteriores o build falha ou sai sem o leitor de ZIM.

## Próximos passos

1. **Usuário:** abrir o PR de `feat/fase-1-core` no GitHub (https://github.com/CristhianAlbino/A-Arca/pull/new/feat/fase-1-core).
2. **No notebook:** a ARCA está instalada (2026-11-17, instalador de `feat/fase-3-biblioteca`, commit `c579040`) e abre com Início e Conhecimento (enciclopédias e biblioteca) funcionando. Falta abrir com Wi-Fi desligado e testar um pendrive.
3. Fazer merge da Fase 1 → release `v0.1.0`.
4. Depois do merge da Fase 1: revisar e mergear `feat/fase-2-ai` (https://github.com/CristhianAlbino/A-Arca/pull/new/feat/fase-2-ai).
5. Testar a IA com modelo real: instalar o Ollama, baixar um modelo pequeno (3–4B) enquanto a RAM é 8 GB; 7–9B depois do upgrade para 24 GB.
6. Instalar o Ollama e baixar um modelo pequeno pelo painel "Gerenciar modelos" (teste real da 2B).
7. Colocar um ZIM real (ex.: Wikipédia PT `nopic`) e alguns PDFs num volume e testar a tela Conhecimento (Procurar e Indexar).
8. Próximo a adiantar: perfis da 2B (depois de medir com Ollama real), 2C (IA online opcional), 3C (busca semântica e RAG, depende da IA local).

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
