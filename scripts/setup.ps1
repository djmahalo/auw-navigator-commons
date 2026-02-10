# Creates venv and installs deps for the 211 POC API
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv"

python -m venv $venv

& "$venv\Scripts\python.exe" -m pip install --upgrade pip
& "$venv\Scripts\pip.exe" install -r (Join-Path $root "api\requirements.txt")

Write-Host "✅ Setup complete."
Write-Host "Next:"
Write-Host "  1) Copy config\.env.example to config\.env and fill values"
Write-Host "  2) Run: scripts\deploy.ps1"
