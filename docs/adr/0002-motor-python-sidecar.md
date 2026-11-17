# 0002 — Motor em Python + FastAPI como sidecar

- Status: Aceito (confirmado pelo usuário em 2026-11-17)
- Data: 2026-11-17

## Contexto
O motor faz RAG, leitura de PDF/EPUB, indexação, acesso a ZIM e OSM, gestão de modelos e de volumes. Várias IAs vão colaborar no código.

## Opções consideradas
- **Python + FastAPI** como processo separado, iniciado pelo Tauri.
- **Tudo em Rust** dentro do Tauri: mais rápido e um processo a menos, porém desenvolvimento mais lento e ecossistema de RAG/documentos menor.
- **Node/TypeScript** no backend: ecossistema de IA e documentos inferior ao Python.

## Decisão
Python 3.12 + FastAPI, servindo em `127.0.0.1` porta aleatória, com token gerado a cada inicialização e passado ao frontend pelo Tauri. Empacotado com PyInstaller em modo onedir.

## Consequências
- Contrato HTTP documentado via OpenAPI; tipos TS gerados em `packages/shared`.
- PyInstaller pode gerar falso positivo em antivírus: usar onedir, build reprodutível e, se possível, assinatura de código.
- Evitar dependências AGPL (ex.: PyMuPDF); preferir pypdf/pdfplumber.
