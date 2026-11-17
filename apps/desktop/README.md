# apps/desktop — interface e shell da ARCA

- `src/` — interface React + TypeScript (estilos em `src/styles/tokens.css`, ADR 0008).
- `src-tauri/` — shell Tauri 2: abre a janela, inicia e encerra o motor, gera o instalador.

Comandos (a partir da raiz do repositório): `scripts\setup.ps1`, `scripts\dev.ps1`, `scripts\build.ps1`.
Só a interface no navegador: `npm run dev` com o motor rodando em `--port 8765 --token dev` (veja `.env.example`).
