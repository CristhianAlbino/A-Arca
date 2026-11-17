# 2026-11-17 — Primeira compilação real no notebook (Fases 1 e 2A)

- **Máquina:** notebook do Cris (Acer Nitro V16, RTX 5060 8 GB, 8 GB de RAM), Windows 11 Pro 10.0.26300
- **Ferramentas:** Python 3.12.10 (`engine\.venv`), Node 20.20.2 / npm 10.8.2, rustc/cargo 1.100.0 (`stable-x86_64-pc-windows-msvc`), Visual Studio 2022 Build Tools (C++)
- **Branch:** `feat/fase-2-ai` (inclui a Fase 1)
- **Executado por:** Claude (sessão no próprio notebook)

## Problema relatado: "Rust não encontrado" depois de instalar

O Rust estava instalado corretamente (`C:\Users\<usuário>\.cargo\bin` no PATH do usuário). O terminal usado tinha sido aberto **antes** da instalação e guardava o PATH antigo (o terminal do VS Code só recarrega o PATH quando o VS Code inteiro é fechado). Correção: `scripts\dev.ps1` agora recarrega o PATH do registro e procura `cargo` em `%CARGO_HOME%\bin` / `%USERPROFILE%\.cargo\bin` antes de desistir.

## 1. Motor — `cd engine; .\.venv\Scripts\python -m pytest -q`

```
.......................................................                  [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
55 passed, 1 warning in 20.19s
```

Inclui `test_api.py` (camada HTTP com FastAPI), que nunca tinha rodado.

## 2. Interface — `npx tsc --noEmit` e `npx vite build`

```
tsc: exit 0 (sem erros)
vite v7.3.8 building client environment for production...
✓ 46 modules transformed.
dist/index.html                   0.39 kB │ gzip:  0.26 kB
dist/assets/index-DgbVamx8.css   11.04 kB │ gzip:  2.92 kB
dist/assets/core-DV6XEvTN.js      0.10 kB │ gzip:  0.11 kB
dist/assets/index-Dwv_Yhkn.js   246.00 kB │ gzip: 77.55 kB
✓ built in 971ms
```

## 3. Shell Tauri — `cd apps\desktop\src-tauri; cargo build`

```
   Compiling arca v0.1.0 (...\A-Arca\apps\desktop\src-tauri)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 2m 21s
```

Sem avisos do compilador.

## 4. App aberto com `npm run tauri dev`

- `target\debug\arca.exe` iniciou o motor: `engine\.venv\Scripts\python.exe -m arca_engine --sidecar`. No Windows o `python.exe` do venv é um lançador e cria um segundo processo Python (o motor real), filho do lançador.
- O motor escutou só em `127.0.0.1` (porta aleatória, 58191 nesta execução).
- **Fechar a janela encerrou o motor:** após `CloseMainWindow()`, nenhum processo `arca_engine` (lançador ou filho) ficou ativo, e o Vite (porta 5173) também parou. → **Critério 2 da Fase 1: passou.**
- A janela em si não foi capturada em imagem (a ferramenta de automação não alcança o app de desenvolvimento); a interface foi conferida no modo navegador abaixo.

## 5. Modo navegador (`motor --port 8765 --token dev` + Vite)

- `GET /health` com token: `{"status":"ok","version":"0.1.0.dev0","db_schema":2,"network_mode":"blocked"}`
- `GET /system` sem token: **401**. → **Critério 3: passou.**
- Tela inicial com dados reais: RAM 6,8 GB / 8 GB, VRAM 0,2 GB / 8 GB (RTX 5060 detectada), disco 211 GB livres, selo "OFFLINE · tudo local".
- Aba IA: "Nenhum modelo instalado" e "IA local indisponível" — correto, o Ollama ainda não está instalado neste notebook.
- Todas as requisições foram para `127.0.0.1` (5173 e 8765).

## Ainda não testado no notebook

| Item | Motivo |
| --- | --- |
| App com Wi-Fi desligado (critério 1) | Rodou com rede ligada; o motor já indica `network_mode: blocked`. Repetir com Wi-Fi desligado. |
| Volume em pendrive (critério 5) | Precisa de um pendrive conectado. |
| Instalador (`scripts\build.ps1`, PyInstaller + NSIS) | Não executado nesta sessão. |
| IA com modelo real (Fase 2A) | Ollama não instalado; RAM de 8 GB. |
