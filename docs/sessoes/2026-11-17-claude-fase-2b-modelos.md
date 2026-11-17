# 2026-11-17 — Claude — Fase 2B: baixar e remover modelos

- Fase: 2 (etapa 2B, parte 1)
- Branch / PR: `feat/fase-2-modelos` (sobre `feat/fase-2-ai`); PR precisa ser aberto pelo usuário
- Papel nesta sessão: implementação e testes

## Feito

- `OllamaProvider.pull` (stream de progresso de `/api/pull`) e `OllamaProvider.delete` (`/api/delete`).
- `service.pull_model`: valida o nome, exige `network_mode == "online"` (403 caso contrário), registra no histórico. `service.delete_model`: descarrega da memória antes, limpa o modelo padrão se for ele, funciona offline.
- Rotas `POST /ai/models/pull` (NDJSON) e `DELETE /ai/models/{nome}` (aceita barra no nome). `/ai/status` passa a informar `network_mode`.
- Interface: painel "Gerenciar modelos" na tela de IA (lista com Remover, download com barra de progresso e cancelar, ligar/desligar modo online); selo da lateral mostra ONLINE quando ligado.
- Ollama falso ganhou `/api/pull` e `/api/delete`.
- Relatório: [testes/2026-11-17-fase2b-gestao-modelos.md](../testes/2026-11-17-fase2b-gestao-modelos.md).

## Pendente

- Teste com o Ollama real (instalar o Ollama; baixar um modelo de 3–4B).
- Resto da 2B: perfis Rápido/Padrão/Profundo/Embeddings (precisa de medição real), descarga por ociosidade configurável na interface.

## Não testado (e por quê)

- Download real e cancelamento no meio: Ollama não instalado.

## Decisões tomadas

- O motor não baixa nada sozinho: quem baixa é o Ollama local. Mesmo assim, o download só é liberado com o modo online ligado, para manter a regra "offline primeiro" visível ao usuário.

## Continuação (mesma sessão)

- Decisão do usuário delegada: terminar 2A/2B antes da 2C (uma etapa por vez; 2C é opcional e online).
- Markdown completo nas respostas (pendência da 2A) com react-markdown + remark-gfm, seguro por padrão.
- Descarga por ociosidade configurável no painel de modelos; validação 1–1440 min no motor.
- Perfis Rápido/Padrão/Profundo ficam para quando houver Ollama real para medir na RTX 5060.
