# Fase 3 — ARCA KNOWLEDGE

**Status:** 3A (enciclopédias ZIM) feita no branch `feat/fase-3-kiwix`; 3B (biblioteca própria, busca textual) feita no branch `feat/fase-3-biblioteca` (sobre `feat/fase-3-kiwix`); 3C (semântica/RAG) espera a IA local · **Release alvo:** v0.3.0

> Adiantada a pedido do usuário (2026-11-17) enquanto a IA local espera o Ollama e o upgrade de RAM. A parte que depende de IA (3C) continua esperando a Fase 2.

## Objetivos
Ler e buscar enciclopédias offline (Wikipédia PT/EN, WikiMed, Wikibooks…) e a biblioteca própria, sem internet; depois, respostas da IA com referências a esses textos (RAG).

## Etapas

### 3A — Enciclopédias ZIM (não depende de IA)
- [x] Encontrar arquivos `.zim` nos volumes ARCA conectados (sem letras de unidade: `vol://<uuid>/...`), pulando pastas ocultas e de sistema
- [x] Ler metadados (título, idioma, número de itens, tamanho, se tem índice de texto completo)
- [x] Busca no índice do próprio ZIM (texto completo) com reserva por título; trecho de texto em cada resultado
- [x] Ler artigos: segue redirecionamentos, página inicial do ZIM
- [x] HTML limpo no motor (sem scripts, iframes, formulários, eventos, estilos inline, recursos externos; imagens do ZIM embutidas como `data:`) e de novo no navegador
- [x] Links internos navegam dentro da ARCA (com Voltar); links externos só mostram o endereço
- [x] Tela Conhecimento: lista de enciclopédias, filtro por enciclopédia, busca, leitor
- [ ] Teste com ZIMs reais (Wikipédia PT/EN) do Drive
- [x] Empacotamento do `libzim` no PyInstaller: faltava (`--collect-all libzim`); o build agora roda `arca-engine --check-deps` e falha se faltar biblioteca
- [x] Catálogo persistente no SQLite (migração 3, tabela `zims`): enciclopédias de discos desconectados continuam na lista, marcadas como indisponíveis

Decisão de implementação: em vez de rodar o `kiwix-serve` (ADR 0005), a primeira versão lê os ZIMs direto com `python-libzim`, que já traz busca e leitura; evita mais um processo e uma porta. O `kiwix-serve` continua opção se for preciso navegar ZIMs com JavaScript (ex.: PhET).

### 3B — Biblioteca própria (busca textual)
- [x] Indexar `.txt`, `.md`, `.html` e `.pdf` (texto, via `pypdf`) dos volumes ARCA com FTS5 (`unicode61 remove_diacritics 2`), migração 4 — branch `feat/fase-3-biblioteca`
- [x] Reindexação incremental (tamanho + data de modificação); arquivos apagados saem do índice; disco desconectado mantém os documentos (marcados como indisponíveis)
- [x] Indexação em segundo plano com progresso; conexão própria ao SQLite
- [x] Busca sem acentos, todas as palavras, prefixo na última; trechos com destaque; título pesa mais (bm25)
- [x] Tela Conhecimento: seção Biblioteca (Indexar, progresso, contagem), resultados separados de Biblioteca e Enciclopédias, leitor de documento
- [ ] EPUB, DOCX e OCR de PDFs escaneados — ficam para a Fase 6 (FILES), que traz importação e catálogo de verdade
- [ ] Teste com o acervo real do Drive (desempenho com milhares de PDFs)

### 3C — Busca semântica e RAG (depende da IA local)
- [ ] Embeddings pelo Ollama, `sqlite-vec` atrás de `VectorStore`
- [ ] "Buscar e depois ler" na Wikipédia para a IA; respostas citando artigo e enciclopédia
