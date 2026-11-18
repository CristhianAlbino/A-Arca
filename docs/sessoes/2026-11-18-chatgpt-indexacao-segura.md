# 2026-11-18 — ChatGPT — segurança de indexação do acervo

- **Fase:** 3B/3C (biblioteca e RAG)
- **Branch:** `fix/library-ignore-private-and-curation` derivada de `feat/fase-3-biblioteca`
- **Papel:** revisão de segurança e testes de regressão, durante curadoria do Google Drive

## Contexto e feito

A pasta `ARCA/` no Google Drive contém `90_PESSOAL`, `00_CATALOGO`, `01_ENTRADA` e `99_BACKUPS`.
A função `find_documents` indexava qualquer `.txt/.md/.html/.pdf/.epub` sem excluir essas pastas reservadas.
Isso permitiria que dados pessoais e listas bibliográficas (URLs de materiais ainda não baixados)
aparecessem na busca e fossem fornecidos indevidamente ao modelo como se fossem evidência.

- Excluídas essas quatro pastas por nome (sem diferenciar maiúsculas).
- Excluídos arquivos terminados em `__FONTES_E_PRIORIDADES.txt`, gerados na curadoria.
- Mantida a indexação dos arquivos editoriais `__GUIA_BASE.txt` em pastas de conhecimento público.
- Criados 2 testes para validar exclusões e preservar arquivos técnicos normais.
- Issue [#3](https://github.com/CristhianAlbino/A-Arca/issues/3) com diagnóstico.

## Não testado

- **Não executei o `pytest`/lint do repositório** neste ambiente: o trabalho foi enviado
  pelo conector GitHub; o GitHub Actions atualmente falha antes de executar etapas.
- Não verifiquei o comportamento no notebook Windows ou com a sincronização real do Drive.

## Pendente

1. Executar no notebook: `cd engine; .\\.venv\\Scripts\\python -m pytest -q` e `ruff`.
2. Verificar se um índice já existente remove entradas privadas após a reindexação e se
   nenhuma fonte do catálogo é citada.
3. Revisar o PR antes de merge; nenhum merge automático.
4. Considerar mais adiante uma política de allowlist por coleções, uma vez que algumas pastas
   não reservadas também podem receber dados sensíveis.

## Decisão

Mudança apenas na seleção de arquivos; não move, apaga ou envia documentos pessoais.
A pasta `90_PESSOAL` **não foi lida** durante a auditoria.
