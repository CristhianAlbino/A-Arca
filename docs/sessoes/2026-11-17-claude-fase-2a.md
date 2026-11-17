# 2026-11-17 — Claude — Fase 2A (IA local)

- Fase: 2 (etapa 2A), adiantada a pedido do usuário enquanto ele instala o ambiente no notebook
- Branch: `feat/fase-2-ai`, empilhado sobre `feat/fase-1-core` (Fase 1 ainda sem teste no notebook)
- PR: não aberto (sessão sem API do GitHub)
- Papel nesta sessão: implementação e testes

## Feito
- Plano da Fase 2 (FASE-02.md) em etapas 2A, 2B e 2C.
- netguard com streaming; provedor Ollama; orçamento de memória; Ollama falso para testes.
- Migração 2 (conversas e mensagens), serviço de chat com streaming NDJSON, rotas `/ai/*`.
- Tela de conversa no padrão ChatGPT; servidor de pré-visualização com rotas de IA.

Commits: `3a50be0` plano · `7d0175a` provedor/orçamento/falso · `c1d8759` conversas/serviço/rotas · `9a5b2c0` tela de conversa · (este) documentação.

## Pendente
- Teste com Ollama e modelo reais no notebook.
- Etapas 2B (baixar/remover modelos, perfis medidos) e 2C (IA online opcional).
- Markdown completo nas respostas.

## Não testado (e por quê)
- Modelos reais, VRAM real, rota HTTP `/ai/chat` com FastAPI: sem GPU, sem Ollama e sem FastAPI no ambiente da sessão.

## Decisões tomadas
- Protocolo de streaming entre motor e interface: NDJSON (uma linha JSON por evento: meta, notice, delta, done, error).
- Pergunta só é salva depois da checagem de memória: um pedido recusado não cria conversa.
- Resposta interrompida é salva com o texto parcial e status `interrupted`.
