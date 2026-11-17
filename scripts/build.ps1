# Gera o instalador da ARCA (NSIS) com o motor empacotado.
# Uso:  .\scripts\build.ps1
# Saída: apps\desktop\src-tauri\target\release\bundle\nsis\ARCA_<versão>_x64-setup.exe

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "==> Empacotando o motor com PyInstaller (onedir)" -ForegroundColor Cyan
Push-Location "$root\engine"
& .\.venv\Scripts\python.exe -m PyInstaller packaging\entry.py `
    --name arca-engine --onedir --noconfirm --clean `
    --collect-submodules uvicorn `
    --distpath dist --workpath build
Pop-Location

Write-Host "==> Gerando o instalador com Tauri" -ForegroundColor Cyan
Push-Location "$root\apps\desktop"
npm run tauri build
Pop-Location

Write-Host "Instalador em apps\desktop\src-tauri\target\release\bundle\nsis\" -ForegroundColor Green
