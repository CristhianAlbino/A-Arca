# 2026-11-18 — Fase 3C (respostas da IA com fontes do acervo) — testes

- **Máquina:** notebook do Cris, RTX 5060 8 GB, 8 GB de RAM; Ollama 0.40.16 + `qwen3.5:4b`
- **Branch:** `feat/fase-3-biblioteca`
- **Acervo real** (`G:\Meu Drive\ARCA`): 6 documentos (5 livros de Jogos Vorazes, Bíblia Livre) e 4 ZIMs (Wikipédia Medicina, Wikcionário, Wikilivros, Wikivoyage). Pasta de dados temporária (o banco do app instalado não foi usado).

## Como funciona (primeira versão, sem embeddings)

"Buscar e depois ler" (ADR 0005): palavras-chave da pergunta (sem palavras vazias; números contam) → até 2 trechos da biblioteca (FTS5 só no texto, todas as palavras primeiro, radical para palavras longas, palavras curtas exatas) + até 2 artigos de enciclopédia (índice do ZIM; o parágrafo que mais combina com a pergunta). Os trechos vão numerados junto com a pergunta; a instrução pede português do Brasil, citação [n] e dizer quando o acervo não responde. A conversa salva guarda só a pergunta do usuário; as fontes ficam salvas com a resposta.

## 1. Motor — `cd engine; .\.venv\Scripts\python -m pytest -q`

```
110 passed, 1 warning in 36.86s
```

`ruff`: `All checks passed!`. Novos (`tests/test_retrieve.py`): palavras-chave; biblioteca antes de enciclopédia; trechos enviados ao modelo e pergunta salva sem eles; fontes salvas na resposta; `use_sources=false`; sem resultado → sem fontes; radical ("tratar" ↔ "tratamento") e nomes curtos exatos ("Prim" ≠ "primeira").

## 2. Perguntas reais (motor + Ollama real)

| Pergunta | 1ª versão | Depois dos ajustes |
| --- | --- | --- |
| Como tratar uma queimadura leve em casa? | trechos de ficção + começo dos artigos "Queimadura"; modelo citou [4] para conhecimento próprio | [4] = parágrafo de **tratamento** da Wikipédia Medicina (água corrente fresca, analgésicos, curativo, bolhas), citado em cada ponto |
| Quem é Prim na história de Jogos Vorazes? | trechos sem a Prim; modelo inventou | trecho do livro do começo da Trilogia (inclui a primeira cena com Prim); ainda há artigos soltos ("Lista de filmes…") e o modelo de 4B ainda erra detalhes |
| O que diz o Salmo 23? | "23" ignorado; trecho do sumário | trecho = o próprio **Salmo 23** da Bíblia Livre; resposta correta citando [1] |

Tempos: fontes em 1–10 s (a primeira busca em cada ZIM é a mais lenta), primeira palavra em ~2–11 s, ~50 tokens/s.

## 3. Interface (navegador, motor + Vite com o acervo real)

- "Consultar acervo" ligado por padrão (preferência guardada no navegador).
- "O que diz o Salmo 23?" → resposta citando [1] e lista "Fontes do acervo": [1] Bíblia Livre · EPUB · DRIVE, [2] Amanhecer na Colheita, [3] Placebo, [4] Preocupação.
- Reabrir a conversa salva → as fontes voltam.
- Clicar em [1] → tela Conhecimento com a Bíblia Livre aberta e **"Trecho citado pela IA"** marcando "23 Salmo de Davi: 1 O SENHOR é meu pastor, nada me faltará…".
- Uma aba oculta do navegador travou ao renderizar a Bíblia inteira (4 milhões de caracteres) enquanto scripts de teste esperavam; numa aba nova o mesmo fluxo funcionou. Observar no app instalado.

## Limitações conhecidas

- Fontes irrelevantes ainda entram ([3]/[4] no Salmo 23); o modelo de 4B às vezes cita uma fonte para algo que veio do conhecimento próprio. Próximos passos: limiar de relevância, busca semântica (embeddings), testar `qwen3.5:9b` com 24 GB de RAM.
- Saúde e segurança: a regra "só com fonte A/B" da Fase 4 ainda não está aplicada; as respostas mostram as fontes, mas o modelo pode completar com conhecimento próprio.
