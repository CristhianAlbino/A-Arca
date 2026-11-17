# ARCA — Arquivo de Recursos, Conhecimento e Autonomia

Plataforma pessoal de inteligência artificial e conhecimento que funciona **sem internet** depois de instalada e abastecida de conteúdo: IA local, enciclopédias, livros, mapas, documentos e um acervo de sobrevivência, num único aplicativo para Windows.

> **Estado atual:** Fase 0 (arquitetura e planejamento) concluída. Ainda não há código funcional. Veja [`docs/STATUS.md`](docs/STATUS.md).

## O que a ARCA vai ter

| Módulo | O que faz |
| --- | --- |
| **HOME** | Painel inicial no estilo de streaming: destaques, fileiras de conteúdo, estado do sistema (RAM, VRAM, disco) |
| **AI** | Conversa com modelos locais (Ollama) e, opcionalmente, online (GPT, Claude, Gemini), com referências às fontes |
| **KNOWLEDGE** | Biblioteca offline: Wikipédia (PT e EN) via Kiwix, livros, PDFs, EPUBs, busca textual e semântica |
| **SURVIVAL** | Acervo curado em 18 áreas (água, saúde, energia, rádio...), respostas sempre com fonte |
| **MAPS** | Mapas offline (OpenStreetMap / PMTiles), busca de lugares, pontos salvos |
| **FILES** | Importar, organizar, indexar e consultar documentos pela IA |
| **MODULES** | Extensões com permissões declaradas |

## Arquitetura em uma linha

App desktop **Tauri 2 + React/TypeScript** → **motor local em Python (FastAPI)** → **Ollama**, **Kiwix** e **SQLite** (FTS5 + sqlite-vec) → **volumes de armazenamento** identificados por UUID (SSD interno e externo). Nuvem só abastece; nada essencial depende dela.

Detalhes: [`docs/arquitetura/ARQUITETURA.md`](docs/arquitetura/ARQUITETURA.md).

## Estrutura do repositório

```
apps/desktop/      Interface (Tauri + React/TS)          — a partir da Fase 1
engine/            Motor local (Python + FastAPI)          — a partir da Fase 1
modules/           Módulos oficiais                         — Fase 7
packages/shared/   Tipos compartilhados (gerados do OpenAPI)
catalog/           Catálogo de fontes públicas (URL + SHA-256 + licença), sem os arquivos
docs/              Documentação, decisões (ADRs), fases, sessões e testes
scripts/           Utilitários de desenvolvimento e build
tests/             Testes ponta a ponta e de isolamento de rede
```

## Para IAs e colaboradores

Comece por [`AGENTS.md`](AGENTS.md). Ele explica regras, fluxo de trabalho e onde está o estado atual do projeto.

## Licença

Código sob [Apache License 2.0](LICENSE). Conteúdos (livros, enciclopédias, mapas) e modelos de IA **não** fazem parte deste repositório e mantêm suas próprias licenças.
