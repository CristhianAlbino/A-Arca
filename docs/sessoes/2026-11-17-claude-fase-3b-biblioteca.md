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

## Acervo — lote 1 (2026-11-18)

Aprovado pelo usuário: Bíblia Livre (EPUB, ebible.org), Wikivoyage PT, Wikilivros PT, Wikipédia Medicina PT, Wikcionário PT e Wikipédia PT completa (todos `nopic`, download.kiwix.org) — ~7,1 GB. Script: `scripts/acervo/baixar_lote1.sh` (baixa numa pasta temporária, confere o SHA-256 publicado pelo Kiwix, só então move para `G:\Meu Drive\ARCA`; nunca sobrescreve). Registro em `catalog/fontes-publicas.csv`.

- Já no Drive e conferidos: Bíblia Livre (`12_ENTRETENIMENTO/01_Biblia`), Wikivoyage e Wikilivros (`02_ENCICLOPEDIAS`).
- App instalado: Wikilivros (16.667 itens) e Wikivoyage (4.610) listados; Bíblia indexada na Biblioteca (6 documentos). Busca "pastor" → 42 resultados (Bíblia, Trilogia e Wikilivros).
- A primeira busca no app instalado logo após o Wikilivros chegar ao Drive não trouxe resultados das enciclopédias; a mesma busca minutos depois trouxe 40. Provável causa: o Google Drive ainda baixando o arquivo da nuvem (modo streaming). Recomendação: marcar `02_ENCICLOPEDIAS` como "Disponível off-line".
- Incidentes do script: (1) o `sha256sum` do Git Bash põe `\` antes do hash em caminhos Windows — comparação falhou com hashes iguais; corrigido lendo pela entrada padrão. (2) `TaskStop` não encerrou o script antigo, que continuou em paralelo; encerrado à mão.
- Velocidade varia por espelho (≈140 KB/s em um deles). Medicina, Wikcionário e a Wikipédia completa ainda baixando; entrar no catálogo quando conferidos.
