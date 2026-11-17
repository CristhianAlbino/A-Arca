# Fase 1 — ARCA CORE

**Status:** código pronto em `feat/fase-1-core`; falta teste no notebook · **Release alvo:** v0.1.0 · Pode ser desenvolvida com 8 GB de RAM.

## Objetivos
Um `ARCA.exe` de desenvolvimento que abre sem internet, inicia e encerra o motor local, mostra a tela inicial com estado real do sistema e já tem banco, volumes e guarda de rede funcionando. Nada de IA ainda.

## Tarefas

### Shell desktop (`apps/desktop`)
- [x] Projeto Tauri 2 + React + TypeScript + Vite
- [x] Estilos com os tokens de [DESIGN.md](../arquitetura/DESIGN.md) em CSS próprio ([ADR 0008](../adr/0008-estilos-css-tokens.md))
- [ ] Fontes Inter e Space Grotesk empacotadas (hoje usa Segoe UI/sistema)
- [x] Iniciar o motor como sidecar, passar porta e token ao frontend, encerrar ao fechar
- [x] CSP bloqueando qualquer URL externa
- [x] Barra superior e tela HOME com destaque, fileiras vazias ("Nada aqui ainda") e faixa de estado do sistema
- [x] Telas dos outros módulos como "Em construção — Fase N" (marcadas, sem funcionalidade fictícia)

### Motor (`engine`)
- [x] FastAPI em `127.0.0.1`, porta aleatória, middleware de token
- [x] `GET /health`, `GET /system` (RAM, VRAM via NVML quando disponível, disco por volume)
- [x] `netguard`: cliente HTTP único, modo padrão bloqueado, log de tentativas
- [x] SQLite em `%LOCALAPPDATA%\ARCA\data\arca.db`, modo WAL, migrações versionadas
- [x] Tabelas iniciais: `volumes`, `items` (catálogo), `activity_log` (configurações ficam em `settings.json`)
- [x] Camada de volumes: criar/ler `.arca-volume.json`, resolver `vol://<uuid>/...`, detectar volume ausente
- [x] Configuração em `%APPDATA%\ARCA\config\settings.json` com caminhos configuráveis
- [x] Logs locais rotativos
- [ ] Contrato OpenAPI exportado e tipos TS gerados em `packages/shared` (tipos escritos à mão em `api/engine.ts` por enquanto)

### Projeto
- [x] Comandos de setup, dev, teste e build documentados no `AGENTS.md`
- [x] GitHub Actions: lint + testes do motor e do frontend
- [ ] Issues da fase e quadro no GitHub Project (sessão sem acesso à API do GitHub)

## Critérios de conclusão
1. `ARCA.exe` de desenvolvimento abre com Wi-Fi desligado e mostra a HOME com RAM, VRAM e disco reais.
2. Fechar o app encerra o motor (nenhum processo órfão).
3. Requisição ao motor sem token é recusada.
4. Com `netguard` bloqueado, qualquer tentativa de saída falha e fica registrada.
5. Um volume criado num pendrive aparece como disponível; ao remover o pendrive, aparece como indisponível sem erro.
6. Testes automatizados passando, com saída colada em `docs/testes/`.

## Testes
- Motor: `pytest` (volumes, resolução de caminhos, token, netguard, migrações do banco).
- Frontend: testes de componentes da HOME.
- Manual: roteiro dos critérios 1, 2 e 5 no notebook, com data e evidência.

## Documentação
Atualizar `AGENTS.md` (comandos), `STATUS.md`, este arquivo, `CHANGELOG.md`; ADR se alguma decisão mudar.

## Resultado dos testes
Ver [2026-11-17-fase1-core.md](../testes/2026-11-17-fase1-core.md). Critérios 4 e 6 verificados na sessão; 1, 2, 3 e 5 dependem do notebook.

## Registro de alterações
- 2026-11-17: plano criado na Fase 0.
- 2026-11-17: motor, interface, shell Tauri, scripts e CI implementados (branch `feat/fase-1-core`).
