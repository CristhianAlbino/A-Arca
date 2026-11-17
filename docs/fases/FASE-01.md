# Fase 1 — ARCA CORE

**Status:** não iniciada · **Release alvo:** v0.1.0 · Pode ser desenvolvida com 8 GB de RAM.

## Objetivos
Um `ARCA.exe` de desenvolvimento que abre sem internet, inicia e encerra o motor local, mostra a tela inicial com estado real do sistema e já tem banco, volumes e guarda de rede funcionando. Nada de IA ainda.

## Tarefas

### Shell desktop (`apps/desktop`)
- [ ] Projeto Tauri 2 + React + TypeScript + Vite
- [ ] Tailwind com os tokens de [DESIGN.md](../arquitetura/DESIGN.md); fontes Inter e Space Grotesk empacotadas
- [ ] Iniciar o motor como sidecar, passar porta e token ao frontend, encerrar ao fechar
- [ ] CSP bloqueando qualquer URL externa
- [ ] Barra superior e tela HOME com destaque, fileiras vazias ("Nada aqui ainda") e faixa de estado do sistema
- [ ] Telas dos outros módulos como "Em construção — Fase N" (marcadas, sem funcionalidade fictícia)

### Motor (`engine`)
- [ ] FastAPI em `127.0.0.1`, porta aleatória, middleware de token
- [ ] `GET /health`, `GET /system` (RAM, VRAM via NVML quando disponível, disco por volume)
- [ ] `netguard`: cliente HTTP único, modo padrão bloqueado, log de tentativas
- [ ] SQLite em `%LOCALAPPDATA%\ARCA\data\arca.db`, modo WAL, migrações versionadas
- [ ] Tabelas iniciais: `volumes`, `items` (catálogo), `settings`, `activity_log`
- [ ] Camada de volumes: criar/ler `.arca-volume.json`, resolver `vol://<uuid>/...`, detectar volume ausente
- [ ] Configuração em `%APPDATA%\ARCA\config\settings.json` com caminhos configuráveis
- [ ] Logs locais rotativos
- [ ] Contrato OpenAPI exportado e tipos TS gerados em `packages/shared`

### Projeto
- [ ] Comandos de setup, dev, teste e build documentados no `AGENTS.md`
- [ ] GitHub Actions: lint + testes do motor e do frontend
- [ ] Issues da fase e quadro no GitHub Project

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

## Registro de alterações
- 2026-11-17: plano criado na Fase 0.
