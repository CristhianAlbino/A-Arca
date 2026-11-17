# STATUS da ARCA

**Última atualização:** 2026-11-17 · **Fase atual:** 0 concluída → próxima: **Fase 1 — ARCA CORE**

## O que existe

- Arquitetura aprovada pelo usuário em 2026-11-17 ([ARQUITETURA.md](arquitetura/ARQUITETURA.md), ADRs 0001–0007).
- Estrutura do repositório e documentação de colaboração entre IAs.
- Pasta `ARCA/` no Google Drive com 17 categorias, 18 subpastas de Sobrevivência, planilha `catalogo_arca` e LEIA-ME.
- Protótipos visuais da tela inicial e da conversa (canvas de design no claude.ai, ver [DESIGN.md](arquitetura/DESIGN.md)).

## O que funciona

Nada executável ainda. Nenhum código foi escrito.

## O que não foi testado

Tudo. Não há código.

## Próximos passos

1. Fase 1 — ver [FASE-01.md](fases/FASE-01.md).
2. Usuário: instalar o upgrade de RAM para 24 GB antes da Fase 2 (portão).
3. Usuário: começar a abastecer o Drive (`ARCA/01_ENTRADA` e categorias) e registrar no catálogo.

## Bloqueios

- Nenhum para a Fase 1.
- Fase 2 depende do upgrade de RAM (8 → 24 GB).

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
