# AGENTS.md — Instruções para qualquer IA que trabalhe na ARCA

Este arquivo é a fonte canônica de instruções para Claude, ChatGPT/Codex, Gemini ou qualquer outra ferramenta. O repositório é a memória compartilhada: não dependa do histórico de conversa de outra IA.

## 1. Antes de qualquer coisa, leia nesta ordem

1. [`docs/STATUS.md`](docs/STATUS.md) — fase atual, o que funciona, o que falta, bloqueios.
2. O arquivo da fase atual em [`docs/fases/`](docs/fases/).
3. [`docs/arquitetura/ARQUITETURA.md`](docs/arquitetura/ARQUITETURA.md) e os ADRs em [`docs/adr/`](docs/adr/).
4. A issue da tarefa no GitHub, se houver.

O documento de origem do projeto é [`docs/00-visao/PROMPT-MESTRE.md`](docs/00-visao/PROMPT-MESTRE.md).

## 2. Regras inegociáveis

- **Offline primeiro.** Nenhuma função essencial pode exigir internet. Toda chamada externa passa pelo guarda de rede do motor (`engine/arca_engine/netguard/`).
- **Nada fictício.** Não implemente funcionalidade de mentira (botão que não faz nada sem estar marcado como tal, dados inventados apresentados como reais).
- **Nada declarado testado sem execução.** Um teste só conta com comando executado, data, máquina e saída colada no PR ou em `docs/testes/`.
- **Nenhuma credencial no Git.** Chaves de API vivem no Cofre do Windows (Credential Manager) via `keyring`. Nunca em `.env` versionado, código ou logs.
- **Nenhum documento pessoal sai do computador** sem confirmação explícita do usuário. A pasta `90_PESSOAL` nunca vai para provedores online.
- **Nada de arquivos grandes no Git.** Modelos (`.gguf`), ZIMs, mapas (`.pmtiles`, `.pbf`), bancos (`.sqlite`) e bibliotecas ficam fora. Não use Git LFS para eles.
- **Migrações nunca apagam.** Copiar, verificar SHA-256, atualizar catálogo; apagar a origem é sempre ação separada do usuário.
- **SURVIVAL não inventa procedimento.** Respostas de saúde e segurança só com trechos citados de fontes A ou B; sem fonte, dizer que não sabe.
- **Uma fase por vez.** Não adiante funcionalidades de fases futuras.

## 3. Stack

| Camada | Tecnologia |
| --- | --- |
| Desktop | Tauri 2 (Rust) + React + TypeScript + Vite |
| UI | CSS próprio com tokens (`apps/desktop/src/styles/tokens.css`, ADR 0008); react-markdown a partir da Fase 2 |
| Motor | Python 3.12 + FastAPI, sidecar em `127.0.0.1` com token por sessão |
| IA local | Ollama (interface `ModelProvider`; llama.cpp como reserva) |
| Banco | SQLite (WAL) + FTS5 + sqlite-vec |
| Enciclopédias | Kiwix (`kiwix-serve` + `python-libzim`) |
| Mapas | PMTiles + MapLibre GL JS |
| Empacotamento | Tauri bundler (NSIS) + PyInstaller (onedir) |

Comandos de instalação, execução e teste serão adicionados aqui na Fase 1, quando houver código.

## 4. Fluxo de cada sessão

1. Ler os arquivos da seção 1.
2. Criar branch `feat/fase-N-tema`, `fix/...` ou `docs/...` (uma IA por branch).
3. Implementar em passos pequenos, com testes.
4. Rodar os testes e colar a saída real no PR.
5. Atualizar `docs/STATUS.md`, o arquivo da fase e, se houve decisão de arquitetura, criar um ADR.
6. Registrar `docs/sessoes/AAAA-MM-DD-<ia>-<tema>.md` (modelo em `docs/sessoes/README.md`).
7. Abrir PR. Merge só após revisão do usuário ou de outra IA.

## 5. Convenções

- Commits no padrão Conventional Commits: `feat(ai): ...`, `fix(storage): ...`, `docs(adr): ...`.
- Uma release por fase concluída: Fase 1 = `v0.1.0` ... Fase 10 = `v1.0.0`.
- Código e comentários em inglês; documentação e textos da interface em português do Brasil.
- Nunca use caminhos fixos de disco: use a camada de volumes (`vol://<uuid>/...`).

## 6. Usuário

Cristhian (Cris), GitHub `CristhianAlbino`. Notebook alvo: Acer Nitro V16, RTX 5060 8 GB VRAM, Windows 11, RAM sendo ampliada para 24 GB. Acervo da Etapa 1 no Google Drive (pasta `ARCA/`).
