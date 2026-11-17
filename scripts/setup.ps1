# Prepara o ambiente de desenvolvimento da ARCA no Windows 11.
# Uso (PowerShell, na raiz do repositório):  .\scripts\setup.ps1
#
# Pré-requisitos instalados uma vez (precisam de internet):
#   - Python 3.12+   https://www.python.org/downloads/
#   - Node.js 20+    https://nodejs.org/
#   - Rust (rustup)  https://rustup.rs/   + "Desktop development with C++" do Visual Studio Build Tools
#   - WebView2 já vem no Windows 11.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "==> Motor (Python): criando engine\.venv e instalando dependências" -ForegroundColor Cyan
Push-Location "$root\engine"
if (-not (Test-Path ".venv")) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev,gpu]"
Pop-Location

# O Tauri exige que a pasta do motor empacotado exista mesmo em modo desenvolvimento.
# build.ps1 a preenche de verdade; aqui só garantimos que ela existe.
$engineDist = "$root\engine\dist\arca-engine"
if (-not (Test-Path $engineDist)) {
    New-Item -ItemType Directory -Force $engineDist | Out-Null
    Set-Content "$engineDist\LEIA-ME.txt" "Gerado por scripts\build.ps1 (PyInstaller)."
}

Write-Host "==> Interface (Node): instalando pacotes de apps\desktop" -ForegroundColor Cyan
Push-Location "$root\apps\desktop"
npm install
Pop-Location

Write-Host "==> Testes do motor" -ForegroundColor Cyan
Push-Location "$root\engine"
& .\.venv\Scripts\python.exe -m pytest -q
Pop-Location

Write-Host ""
Write-Host "Pronto. Para abrir a ARCA em modo desenvolvimento:  .\scripts\dev.ps1" -ForegroundColor Green
