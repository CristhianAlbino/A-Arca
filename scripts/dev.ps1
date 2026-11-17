# Abre a ARCA em modo desenvolvimento (janela Tauri + motor Python do repositório).
# Uso:  .\scripts\dev.ps1            -> janela do app (Tauri)
#       .\scripts\dev.ps1 -Browser   -> só no navegador (motor na porta 8765, token "dev")

param([switch]$Browser)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if ($Browser) {
    Write-Host "Motor em http://127.0.0.1:8765 (token dev). Feche esta janela para parar." -ForegroundColor Cyan
    Start-Process -FilePath "$root\engine\.venv\Scripts\python.exe" `
        -ArgumentList "-m", "arca_engine", "--port", "8765", "--token", "dev" `
        -WorkingDirectory "$root\engine"
    Push-Location "$root\apps\desktop"
    if (-not (Test-Path ".env.local")) { Copy-Item ".env.example" ".env.local" }
    npm run dev
    Pop-Location
} else {
    Push-Location "$root\apps\desktop"
    npm run tauri dev
    Pop-Location
}
