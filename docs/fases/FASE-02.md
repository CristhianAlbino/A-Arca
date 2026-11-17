# Fase 2 — ARCA AI

**Status:** etapa 2A concluída (testada com Ollama falso); 2B em andamento (baixar/remover feito); 2C pendente; em andamento no branch `feat/fase-2-ai` (empilhado sobre `feat/fase-1-core`) · **Release alvo:** v0.2.0
**Portão:** testes com modelos reais só depois do upgrade de RAM para 24 GB.

## Objetivos
Conversar com modelos locais (Ollama) numa tela no padrão ChatGPT, com conversas salvas no computador, um modelo carregado por vez e checagem de memória antes de carregar. Integrações online (GPT, Claude, Gemini) opcionais, desligadas por padrão.

## Etapas

### 2A — IA local (pode ser feita e testada antes do notebook, com um Ollama falso)
- [x] Interface `ModelProvider` e `OllamaProvider` (via `netguard`, só loopback)
- [x] Streaming de respostas (NDJSON) do Ollama até a interface
- [x] Orçamento de memória: um modelo de chat por vez; recusar com explicação quando não cabe em VRAM + RAM
- [x] Conversas e mensagens salvas no SQLite (migração 2)
- [x] Rotas `/ai/status` (inclui a lista de modelos), `/ai/models/{nome}/unload`, `/ai/conversations`, `/ai/chat`
- [x] Tela de conversa: lateral com histórico, coluna central, caixa de mensagem, parar geração, seletor de modelo com selo LOCAL
- [x] Mensagem clara quando o Ollama não está instalado ou aberto

- [ ] Markdown completo nas respostas (react-markdown) — hoje: parágrafos e blocos de código

### 2B — Gestão de modelos (precisa do notebook e de internet para baixar)
- [x] Baixar modelos (`ollama pull`) só com modo online ligado; remover modelos — rotas `POST /ai/models/pull` (NDJSON com progresso) e `DELETE /ai/models/{nome}`; painel "Gerenciar modelos" na tela de IA; testado com Ollama falso (branch `feat/fase-2-modelos`). Falta testar com o Ollama real.
- [ ] Perfis Rápido / Padrão / Profundo / Embeddings com modelos escolhidos por medição real na RTX 5060
- [ ] Descarga por ociosidade configurável (padrão 5 min)

### 2C — IA online opcional
- [ ] `AnthropicProvider`, `OpenAIProvider`, `GeminiProvider` pela mesma interface, só via `netguard`
- [ ] Chaves no Cofre do Windows (`keyring`); tela para cadastrar/remover
- [ ] Confirmação explícita antes de enviar qualquer documento a um modelo online

## Critérios de conclusão
1. Com Ollama instalado e um modelo 7–9B, a conversa responde em streaming, offline, e fica salva.
2. Pedir um segundo modelo descarrega o primeiro.
3. Um modelo que não cabe é recusado com explicação e sugestão de modelo menor.
4. Sem Ollama, a tela explica o que fazer, sem travar.
5. Com rede bloqueada, nenhuma integração online sai do computador (netguard).
6. Testes automatizados com saída registrada em `docs/testes/`.

## Testes
- Motor: `pytest` com Ollama falso (`engine/tests/fakes/fake_ollama.py`), que imita `/api/version`, `/api/tags`, `/api/ps`, `/api/chat` e `/api/generate`.
- Interface: Playwright no Chromium com o mesmo Ollama falso.
- Notebook: modelos reais (após RAM de 24 GB).

## Registro de alterações
- 2026-11-17: plano criado; início da etapa 2A.
- 2026-11-17: etapa 2A implementada e testada com Ollama falso ([relatório](../testes/2026-11-17-fase2a-ia-local.md)).
