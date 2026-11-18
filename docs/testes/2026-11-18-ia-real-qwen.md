# 2026-11-18 — Primeiro teste com IA local real (Ollama + qwen3.5:4b)

- **Máquina:** notebook do Cris, RTX 5060 Laptop 8 GB, 8 GB de RAM (~500–800 MB livres durante o teste), Windows 11
- **Ollama:** 0.40.16; modelo `qwen3.5:4b` (Q4_K_M, 3,3 GB) baixado pelo usuário com `ollama pull`
- **Branch:** `feat/fase-3-biblioteca` (inclui toda a Fase 2)

## Escolha do modelo

Conferido em ollama.com/library/qwen3.5/tags (2026-11-18): `qwen3.5:4b` = 3,3 GB, cabe inteiro nos 8 GB de VRAM. `qwen3.5:9b` (6,6 GB) fica no limite da VRAM; testar depois do upgrade de RAM.

## 1. App instalado (antes da correção)

- Aba IA listou "qwen3.5:4b · 4.2B · 3,1 GB · LOCAL" sozinha (o modelo veio do Ollama, sem configuração).
- Pergunta: "Responda em portugues, em 3 frases curtas: como deixar agua segura para beber sem filtro?" → mais de 1 minuto em "Pensando…".
- Log do Ollama: carregamento lento (aquecimento com a RAM quase cheia), depois 100% GPU; a requisição gerou **1.500+ tokens de raciocínio** (campo `thinking`, que a ARCA não mostra) antes de qualquer palavra visível.
- Pergunta direta ao Ollama com `"think": false`: avaliação do prompt 0,11 s, geração 0,03 s (o resto do tempo foi fila atrás da pergunta da ARCA).

## 2. Correção (commit `4144642`)

O chat da ARCA pede `think: false`; se o Ollama/modelo recusar a opção, repete sem ela. Testes: `104 passed`, `ruff` ok (2 novos: `think` enviado como `false`; repetição sem `think` quando recusado).

## 3. Motor da ARCA (código corrigido) com o Ollama real

`POST /ai/chat` com a mesma pergunta (com acentos), modelo `qwen3.5:4b`:

```
primeira palavra: 1.0s | total: 2.5s
fim: {"type": "done", "stats": {"total_seconds": 2.4, "load_seconds": 0.28, "output_tokens": 70, "tokens_per_second": 51.4}}
```

Resposta em português, 3 frases, coerente: ferver até a fervura completa, deixar esfriar, e o aviso de que a fervura não remove contaminantes químicos nem metais pesados.

## Observações

- Primeira medição real para os perfis da 2B: `qwen3.5:4b` ≈ 51 tokens/s na RTX 5060 com contexto de 4096.
- Com a RAM quase cheia, o **primeiro** carregamento do modelo demorou bem mais que a geração. O upgrade para 24 GB deve resolver; enquanto isso, fechar programas antes de usar a IA.
- A resposta usa algumas palavras de Portugal ("arrefecer"); avaliar um prompt de sistema pedindo português do Brasil.
- Ainda não testado no app instalado com a correção (instalador sendo gerado).

## 4. App instalado com a correção (instalador do `4144642`)

- `arca.exe` de 00:52; um app e um motor; `qwen3.5:4b` carregado 100% na GPU; ~600 MB de RAM livre.
- Aba IA: modelo "carregado na memória"; a conversa do teste anterior aparece no histórico ("Hoje").
- A mensagem enviada acabou sendo o conteúdo da área de transferência do usuário (`ollama pull qwen3.5:4b`), por causa da automação de tela. A resposta completa chegou em **menos de 5 s**, em português, com Markdown renderizado (negrito, lista, dois blocos de código com "Copiar").
- Conteúdo da resposta: dizia que o modelo "pode não existir oficialmente ainda" — erro factual do próprio modelo (não conhece versões posteriores ao seu treino). Reforça a regra do projeto: respostas de saúde/segurança só com fontes (etapa 3C / Fase 4).

**Resultado:** a correção do `think` resolve a espera no app instalado. → IA local **funcionando** no notebook.
