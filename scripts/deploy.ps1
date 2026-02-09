# Runs the FastAPI app locally
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv"

if (!(Test-Path $venv)) {
  throw "Virtual env not found. Run scripts\setup.ps1 first."
}

# Load .env if present
$envPath = Join-Path $root "config\.env"
if (Test-Path $envPath) {
  Get-Content $envPath | ForEach-Object {
    if ($_ -match "^\s*#") { return }
    if ($_ -match "^\s*$") { return }
    $parts = $_ -split "=", 2
    if ($parts.Length -eq 2) {
      $name = $parts[0].Trim()
      $value = $parts[1].Trim()
      [System.Environment]::SetEnvironmentVariable($name, $value)
    }
  }
}

$apiPath = Join-Path $root "api"

Push-Location $apiPath
try {
  & "$venv\Scripts\uvicorn.exe" api.app:app --reload --host 127.0.0.1 --port 8000
} finally {
  Pop-Location
}
