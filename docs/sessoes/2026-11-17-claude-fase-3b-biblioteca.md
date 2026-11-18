# 2026-11-17 — Claude — Fase 3B: biblioteca própria

- Fase: 3 (adiantada a pedido do usuário)
- Branch / PR: `feat/fase-3-biblioteca` (sobre `feat/fase-3-kiwix`); PR precisa ser aberto pelo usuário
- Papel nesta sessão: implementação e testes

## Feito

- Migração 4: tabela `docs` + índice FTS5 `docs_fts` (sem acentos).
- `arca_engine/knowledge/library.py`: encontrar documentos nos volumes, extrair texto (txt/md/html/pdf), indexação incremental em segundo plano com conexão própria, busca segura com trechos, leitura.
- Rotas `/library/status`, `/library/index`, `/library/search`, `/library/docs/{id}`; dependência `pypdf`; `--check-deps` inclui `pypdf`.
- Tela Conhecimento: seção Biblioteca, busca unificada, leitor de documento.
- Relatório: [testes/2026-11-17-fase3b-biblioteca.md](../testes/2026-11-17-fase3b-biblioteca.md).

## Pendente

- EPUB/DOCX/OCR (Fase 6), teste com o acervo real, novo instalador com `pypdf`.

## Decisões tomadas

- O texto extraído fica no índice FTS5 (não em arquivos à parte): permite ler o documento mesmo com o disco desconectado. Custo: o banco cresce com o acervo; o limite por arquivo é 5 milhões de caracteres.
- A indexação não segue a ordem "importar → catalogar" da Fase 6: só lê o que já está nos volumes, sem copiar nem mover nada.
