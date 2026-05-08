$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PgBin = Join-Path $ProjectRoot ".tools\scoop\apps\postgresql\18.3\bin"
$PgData = Join-Path $ProjectRoot "data\postgres"

$BackendPids = @(Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
foreach ($PidValue in $BackendPids) {
  if ($PidValue) {
    Stop-Process -Id $PidValue -Force -ErrorAction SilentlyContinue
  }
}

$FrontendPids = @(Get-NetTCPConnection -LocalPort 3003 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
foreach ($PidValue in $FrontendPids) {
  if ($PidValue) {
    Stop-Process -Id $PidValue -Force -ErrorAction SilentlyContinue
  }
}

if (Test-Path (Join-Path $PgData "PG_VERSION")) {
  & (Join-Path $PgBin "pg_ctl.exe") -D $PgData stop -m fast
}

docker compose -f (Join-Path $ProjectRoot "docker-compose.yml") -f (Join-Path $ProjectRoot "docker-compose.gdrive.yml") stop redis chromadb prometheus grafana

Write-Host "AgriAgent stack stopped."
