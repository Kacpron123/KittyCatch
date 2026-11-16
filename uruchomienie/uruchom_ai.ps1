$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $projectRoot 'kod/python_ai')
try { python -m src.serwer --strategy ../../modele/best_strategy.json --host 127.0.0.1 --port 8080 } finally { Pop-Location }
