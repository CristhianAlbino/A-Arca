# 0003 — SQLite + FTS5 + sqlite-vec

- Status: Aceito
- Data: 2026-11-17

## Contexto
Precisamos de catálogo, histórico, configuração, busca textual e busca vetorial, tudo offline e sem servidores extras.

## Opções consideradas
- **SQLite** (WAL) com **FTS5** e a extensão **sqlite-vec** (MIT/Apache, binários para Windows x64).
- PostgreSQL + pgvector: servidor desnecessário para uso pessoal.
- Qdrant (usado pelo Project N.O.M.A.D.): mais um serviço para gerenciar.
- LanceDB: bom candidato embutido; fica como reserva.

## Decisão
Um arquivo SQLite principal no SSD interno, FTS5 com tokenizador `unicode61` (remove acentos) e sqlite-vec para vetores, atrás de uma interface `VectorStore`.

## Consequências
- sqlite-vec ainda é versão 0.x: a interface `VectorStore` permite trocar por LanceDB sem mudar o resto.
- O banco nunca fica no SSD externo, para evitar corrupção ao desconectar.
- Backup simples via API de backup online do SQLite.
