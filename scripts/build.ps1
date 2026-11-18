# Gera o instalador da ARCA (NSIS) com o motor empacotado.
# Uso:  .\scripts\build.ps1
# Saída: apps\desktop\src-tauri\target\release\bundle\nsis\ARCA_<versão>_x64-setup.exe

# "Continue", not "Stop": in Windows PowerShell 5.1, "Stop" turns any line a native tool
# writes to stderr (PyInstaller logs INFO there) into a fatal error when output is
# redirected. Failures are caught by checking $LASTEXITCODE after each step instead.
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot

function Step([string]$failMessage) {
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Host $failMessage -ForegroundColor Red
        exit 1
    }
}

Write-Host "==> Empacotando o motor com PyInstaller (onedir)" -ForegroundColor Cyan
Push-Location "$root\engine"
& .\.venv\Scripts\python.exe -m PyInstaller packaging\entry.py `
    --name arca-engine --onedir --noconfirm --clean `
    --collect-submodules uvicorn `
    --collect-all libzim `
    --distpath dist --workpath build
Step "PyInstaller falhou."

# The ZIM reader is imported inside try/except, so a missing module would only show up
# at runtime as "leitor de ZIM não instalado". Fail the build here instead.
& .\dist\arca-engine\arca-engine.exe --check-deps
Step "O motor empacotado está sem dependências (veja acima)."
Pop-Location

Write-Host "==> Gerando o instalador com Tauri" -ForegroundColor Cyan
Push-Location "$root\apps\desktop"
npm run tauri build
Step "A geração do instalador (Tauri) falhou."
Pop-Location

Write-Host "Instalador em apps\desktop\src-tauri\target\release\bundle\nsis\" -ForegroundColor Green
