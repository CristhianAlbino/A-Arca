# 0004 — IA local com Ollama atrás da interface ModelProvider

- Status: Aceito
- Data: 2026-11-17

## Contexto
A ARCA deve rodar Llama, Qwen, Gemma, Mistral e outros localmente numa RTX 5060 (8 GB VRAM), e opcionalmente usar GPT, Claude e Gemini online.

## Opções consideradas
- **Ollama**: instalador Windows, usa GPU, gerencia downloads, descarrega modelos ociosos (`keep_alive`), API HTTP estável.
- **llama.cpp server** direto: mais controle e empacotável, mas exige mais código de gestão.
- LM Studio: interface própria, menos adequado como dependência.

## Decisão
Interface `ModelProvider` no motor com implementações `OllamaProvider` (padrão), `OpenAIProvider`, `AnthropicProvider` e `GeminiProvider`. llama.cpp fica como reserva com a mesma interface.

## Consequências
- Online desligado por padrão; chaves no Cofre do Windows; confirmação antes de enviar documentos.
- Um modelo de chat carregado por vez; orçamento de VRAM/RAM antes de carregar; descarga após ociosidade.
- O instalador do Ollama fica guardado em `ARCA/14_INSTALADORES` para instalação offline.
- Modelos específicos escolhidos na Fase 2, com medições no notebook.
