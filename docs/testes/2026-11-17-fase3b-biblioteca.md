# 2026-11-17 — Fase 3B (biblioteca própria, busca textual) — testes

- **Máquina:** notebook do Cris (Windows 11 Pro 10.0.26300), Python 3.12.10, SQLite 3.49.1 (FTS5), pypdf 6.21.4, Node 20.20.2
- **Branch:** `feat/fase-3-biblioteca`
- **Dados de teste:** arquivos criados na hora: `.txt`, `.md`, `.html` e um PDF real mínimo gerado por `engine/tests/fakes/make_pdf.py` (texto em WinAnsi, com acentos). Nenhum documento pessoal usado.

## 1. Motor — `cd engine; .\.venv\Scripts\python -m pytest -q`

```
98 passed, 1 warning in 34.54s
```

`ruff check arca_engine tests` → `All checks passed!`

8 testes novos em `tests/test_library.py`:

- consulta FTS5 segura: palavras do usuário entre aspas (`NEAR`, `OR`, `*`, `"` viram texto comum), prefixo só na última;
- títulos: primeira linha curta do `.txt`, primeiro `#` do Markdown, `<title>` do HTML (sem o conteúdo de `<script>`), título do PDF;
- indexa 4 arquivos; ignora pasta oculta e `.jpg`; "agua" (sem acento) acha o `.txt` e o PDF; trecho com `[[queimadura]]`; todas as palavras exigidas;
- reindexar: 4 inalterados; arquivo alterado é atualizado, arquivo apagado sai do índice;
- disco desconectado: nada é removido, resultados marcados `available: false`;
- arquivo vazio → `sem-texto`; PDF quebrado → `erro` sem parar a indexação;
- HTTP: 401 sem token, indexação em segundo plano (202) até `running: false`, busca, documento, busca longa → 400.

## 2. Interface — `npx tsc --noEmit` e `npx vite build`

Sem erros (`index-A_c2v6A8.js 430.87 kB`).

## 3. Navegador (motor + Vite, volume temporário com ZIM de teste, .txt, .md e PDF)

1. Conhecimento → Biblioteca: "0 documentos" e a explicação; "Indexar" → "3 documentos · Última indexação: 3 novos, 0 atualizados, 0 removidos".
2. Buscar `agua`: "4 resultados", seções **Biblioteca** (agua.txt, "Manual de primeiros socorros") e **Enciclopédias** ("Água potável", "Filtro de água"); "água" destacado nos trechos.
3. Abrir o PDF: título "Manual de primeiros socorros", "PDF · SSD-TESTE", texto "Primeiros socorros / Em caso de queimadura, resfrie com água corrente por 20 minutos."
4. O título do `.txt` aparecia como "agua" (nome do arquivo); passou a usar a primeira linha ("Purificação de água") — coberto em `test_extracts_titles_and_text`.

Conferido pelo DOM.

## Não testado

- Acervo real (milhares de PDFs do Drive): tempo de indexação e tamanho do banco.
- PDFs escaneados reais (devem aparecer como "sem texto" até o OCR da Fase 6).

## 4. Instalador (`scripts\build.ps1` a partir do commit `c579040`, sem edições durante o build)

- `--check-deps`: `ok` para fastapi, uvicorn, psutil, libzim (3 módulos) e `pypdf`.
- `ARCA_0.1.0_x64-setup.exe` gerado (24.97 MiB).
- Motor empacotado com volume temporário contendo um PDF: indexação `{'added': 1, ... 'failed': 0}`; busca `queimadura` → `('Manual', 'pdf')`.
- Instalada pelo usuário (instalador aberto pelo Explorer). `arca.exe` de 23:32; `--check-deps` do motor instalado: tudo `ok`, inclusive `pypdf`.
- O instalador abriu a ARCA ao concluir; motor escutando em `127.0.0.1:57807`. A tela ficou ~40 s em "Conectando ao motor…" com ~700 MB de RAM livre (de 8 GB) e depois carregou normalmente.
- Conhecimento: seções Enciclopédias e Biblioteca presentes; "Indexar" sem volume registrado → "0 documentos · Última indexação: 0 novos, 0 atualizados, 0 removidos", sem erro.
- Observação: a partida do motor empacotado fica lenta com pouca RAM livre; reavaliar depois do upgrade para 24 GB (se continuar lento, mostrar na tela que o motor está iniciando há X segundos).
