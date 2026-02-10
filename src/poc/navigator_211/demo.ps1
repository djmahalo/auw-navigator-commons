# demo.ps1
# Run from project root: navigator_211
# Usage:
#   .\demo.ps1
# Optional:
#   .\demo.ps1 -BaseUrl "http://127.0.0.1:8000"

param(
  [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

function Write-Section($title) {
  Write-Host ""
  Write-Host "===================================================="
  Write-Host $title
  Write-Host "===================================================="
}

function Invoke-Json($method, $url, $bodyObj = $null) {
  if ($null -ne $bodyObj) {
    $json = ($bodyObj | ConvertTo-Json -Depth 10)
    return Invoke-RestMethod -Method $method -Uri $url -ContentType "application/json" -Body $json
  } else {
    return Invoke-RestMethod -Method $method -Uri $url
  }
}

# --- Preflight checks ---
Write-Section "Preflight: Validate project folder"
if (-not (Test-Path ".\api")) {
  throw "I don't see an .\api folder. Run this script from the navigator_211 project root."
}
if (-not (Test-Path ".\data")) {
  Write-Host "Note: .\data folder not found (it may be created on first run)."
}

Write-Section "Step 1: Health check"
try {
  $health = Invoke-Json "GET" "$BaseUrl/health"
  $health | ConvertTo-Json -Depth 6
} catch {
  Write-Host ""
  Write-Host "❌ Cannot reach API at $BaseUrl."
  Write-Host "Make sure the server is running in a separate PowerShell window:"
  Write-Host "  cd <project-root>"
  Write-Host "  .\.venv\Scripts\Activate.ps1"
  Write-Host "  python -m uvicorn api.app:app --host 127.0.0.1 --port 8000"
  throw
}

# --- Demo creates ---
Write-Section "Step 2: Create demo intakes (General/Food, Priority, Crisis)"

$demo1 = @{
  caller_id     = "DEMO-FOOD-01"
  channel       = "chat"
  domain_module = "Food"
  priority      = "Low"
  crisis        = $false
  narrative     = "Demo: Food benefits info request (expected route: Food/default_domain)"
  attributes    = @{ language = "en" }
}

$demo2 = @{
  caller_id     = "DEMO-HOUSING-PRIORITY-01"
  channel       = "phone"
  domain_module = "Housing"
  priority      = "High"
  crisis        = $false
  narrative     = "Demo: High priority housing intake (expected route: Priority)"
  attributes    = @{ risk_eviction_days = 7 }
}

$demo3 = @{
  caller_id     = "DEMO-HOUSING-CRISIS-01"
  channel       = "phone"
  domain_module = "Housing"
  priority      = "Low"
  crisis        = $true
  narrative     = "Demo: Crisis housing intake (expected route: Crisis)"
  attributes    = @{ risk_eviction_days = 1 }
}

$response1 = Invoke-Json "POST" "$BaseUrl/intakes" $demo1
$response2 = Invoke-Json "POST" "$BaseUrl/intakes" $demo2
$response3 = Invoke-Json "POST" "$BaseUrl/intakes" $demo3

Write-Host "`n--- Created Intake 1 ---"
$response1 | ConvertTo-Json -Depth 10

Write-Host "`n--- Created Intake 2 ---"
$response2 | ConvertTo-Json -Depth 10

Write-Host "`n--- Created Intake 3 ---"
$response3 | ConvertTo-Json -Depth 10

# --- Lists ---
Write-Section "Step 3: List intakes (top 20)"
$intakes = Invoke-Json "GET" "$BaseUrl/intakes?limit=20"
$intakes | ConvertTo-Json -Depth 10

Write-Section "Step 4: List queues"
$queues = Invoke-Json "GET" "$BaseUrl/queues"
$queues | ConvertTo-Json -Depth 10

Write-Section "Step 5: Fetch intake details for the 3 new records"
foreach ($id in @($response1.intake_id, $response2.intake_id, $response3.intake_id)) {
  Write-Host "`n--- Intake Detail: $id ---"
  $detail = Invoke-Json "GET" "$BaseUrl/intakes/$id"
  $detail | ConvertTo-Json -Depth 10
}

Write-Section "DONE ✅"
Write-Host "Tip: For a visual demo, open: $BaseUrl/docs"
