# Copy the cBot source from this repo into cTrader's cBot folder.
# Usage (from the repo folder):  powershell -ExecutionPolicy Bypass -File tools\sync-cbot.ps1

$ErrorActionPreference = "Stop"
$docs = [Environment]::GetFolderPath("MyDocuments")
$src  = Join-Path $PSScriptRoot "..\cbot\BacktestLab"
$dst  = Join-Path $docs "cAlgo\Sources\Robots\BacktestLab\BacktestLab"

if (-not (Test-Path $dst)) {
    Write-Host "Not found: $dst" -ForegroundColor Yellow
    Write-Host "Open cTrader > Algo > cBots > New, name it exactly 'BacktestLab', save, then run this script again."
    exit 1
}

Copy-Item -Path (Join-Path $src "*") -Destination $dst -Recurse -Force
Write-Host "Copied cBot source to $dst (V5 standalone — no external Supabase dependencies)" -ForegroundColor Green
Write-Host "Next: run 'ctrader-cli build' or open cTrader and press Build."
