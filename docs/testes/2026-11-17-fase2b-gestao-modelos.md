# 2026-11-17 — Fase 2B (baixar e remover modelos) — testes

- **Máquina:** notebook do Cris (Windows 11 Pro 10.0.26300), Python 3.12.10, Node 20.20.2
- **Branch:** `feat/fase-2-modelos` (sobre `feat/fase-2-ai`)
- **Ollama:** falso (`engine/tests/fakes/fake_ollama.py`), sem download real. O Ollama real não está instalado.

## 1. Motor — `cd engine; .\.venv\Scripts\python -m pytest -q`

```
69 passed, 1 warning in 27.40s
```

14 testes novos em `tests/test_models.py`:

- baixar com modo offline é recusado (403) e nenhuma chamada chega ao Ollama;
- nomes inválidos (`../etc`, espaços, `;`, vazio, longo demais) são recusados (400);
- download envia progresso, termina com `done`, o modelo aparece na lista e fica no histórico;
- erro do Ollama no meio do download chega como evento `error`;
- remover descarrega o modelo da memória antes e limpa o modelo padrão;
- remover funciona offline; modelo inexistente dá 404;
- rotas HTTP: 401 sem token, 403 offline, nomes com barra (`library/llama3.2:1b`).

## 2. Interface — `npx tsc --noEmit` e `npx vite build`

Sem erros (`index-BScDy3jc.js 251.07 kB`).

## 3. Ponta a ponta no navegador (motor + Vite + Ollama falso, pasta de dados temporária)

1. Aba IA → "Gerenciar modelos": lista os 3 modelos falsos; em modo offline mostra a explicação e "Ligar modo online".
2. "Ligar modo online" → aparece o campo de download e o selo ONLINE.
3. Baixar `llama3.2:1b` → o modelo aparece na lista (1B · Q4_K_M · 1,5 GB).
4. Remover `llama3.2:1b` (confirmação aceita) → "Modelo llama3.2:1b removido." e some da lista.
5. "Voltar ao modo offline" → `GET /settings` retorna `network_mode: blocked`.

## Não testado

- Download real pelo Ollama (precisa instalar o Ollama e ter internet).
- Cancelar um download real no meio (com o falso, o download termina rápido demais).
