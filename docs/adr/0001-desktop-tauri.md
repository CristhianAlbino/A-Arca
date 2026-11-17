# 0001 — Desktop com Tauri 2 + React/TypeScript

- Status: Aceito
- Data: 2026-11-17

## Contexto
A ARCA precisa ser um executável Windows (`ARCA.exe`) com instalador, ícone, atalho e desinstalador, leve o bastante para um notebook com 8–24 GB de RAM que também roda modelos de IA.

## Opções consideradas
- **Tauri 2**: usa o WebView2 já presente no Windows 11; instalador pequeno; bundler NSIS/MSI; updater com assinatura; suporta sidecars.
- **Electron**: maduro, mas empacota um Chromium inteiro (instalador e uso de RAM bem maiores).
- **App nativo (WinUI/.NET)**: bom desempenho, mas ecossistema de UI menos flexível para o visual desejado e menos familiar ao usuário.

## Decisão
Tauri 2 com React + TypeScript + Vite. UI com Tailwind CSS, Radix/shadcn e Framer Motion.

## Consequências
- O shell Rust fica fino: janela, ciclo de vida dos sidecars, updater. A lógica fica no motor (ADR 0002).
- Toda fonte, ícone e estilo precisa ser empacotado (CSP bloqueia URLs externas).
- Requer toolchain Rust no ambiente de build.
