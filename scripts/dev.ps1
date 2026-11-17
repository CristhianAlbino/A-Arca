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
    # A terminal opened before installing Rust keeps the old PATH (VS Code keeps it
    # until fully restarted). Reload PATH from the registry and add rustup's default dir.
    if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
        $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                    [Environment]::GetEnvironmentVariable("Path", "User")
        $cargoHome = if ($env:CARGO_HOME) { $env:CARGO_HOME } else { "$env:USERPROFILE\.cargo" }
        if (Test-Path "$cargoHome\bin\cargo.exe") { $env:Path = "$cargoHome\bin;$env:Path" }
    }
    if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
        Write-Host "Rust (cargo) não encontrado." -ForegroundColor Red
        Write-Host "1. Instale pelo rustup-init.exe em https://rustup.rs (aceite a instalação do Visual Studio Build Tools com C++)."
        Write-Host "2. Feche TODAS as janelas do PowerShell/VS Code, abra de novo e confira com: cargo --version"
        Write-Host "Enquanto isso, dá para usar só no navegador:  .\scripts\dev.ps1 -Browser"
        exit 1
    }
    Push-Location "$root\apps\desktop"
    npm run tauri dev
    Pop-Location
}
