$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PgBin = Join-Path $ProjectRoot ".tools\scoop\apps\postgresql\18.3\bin"
$PgData = Join-Path $ProjectRoot "data\postgres"
$PgLog = Join-Path $ProjectRoot "logs\postgres.log"
$BackendLog = Join-Path $ProjectRoot "backend_server.log"
$BackendErr = Join-Path $ProjectRoot "backend_server.err.log"
$FrontendLog = Join-Path $ProjectRoot "frontend_server.log"
$FrontendErr = Join-Path $ProjectRoot "frontend_server.err.log"
$CacheHome = Join-Path $ProjectRoot "data\cache\chroma_home"

New-Item -ItemType Directory -Force -Path `
  (Join-Path $ProjectRoot "logs"), `
  $PgData, `
  $CacheHome, `
  (Join-Path $ProjectRoot "data\docker\redis"), `
  (Join-Path $ProjectRoot "data\docker\chroma"), `
  (Join-Path $ProjectRoot "data\docker\prometheus"), `
  (Join-Path $ProjectRoot "data\docker\grafana"), `
  (Join-Path $ProjectRoot ".tools\pdf_parsers\cache\huggingface"), `
  (Join-Path $ProjectRoot ".tools\pdf_parsers\cache\torch"), `
  (Join-Path $ProjectRoot ".tools\pdf_parsers\cache\ultralytics") | Out-Null

$env:UV_CACHE_DIR = Join-Path $ProjectRoot ".uv-cache"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $ProjectRoot ".uv-python"
$env:HOME = $CacheHome
$env:USERPROFILE = $CacheHome
$env:XDG_CACHE_HOME = Join-Path $ProjectRoot "data\cache"
$env:HF_HOME = Join-Path $ProjectRoot ".tools\pdf_parsers\cache\huggingface"
$env:HUGGINGFACE_HUB_CACHE = Join-Path $ProjectRoot ".tools\pdf_parsers\cache\huggingface\hub"
$env:TORCH_HOME = Join-Path $ProjectRoot ".tools\pdf_parsers\cache\torch"
$env:YOLO_CONFIG_DIR = Join-Path $ProjectRoot ".tools\pdf_parsers\cache\ultralytics"
$env:PYTHONPATH = "$ProjectRoot\src;$ProjectRoot\backend"
$env:npm_config_cache = Join-Path $ProjectRoot ".npm-cache"

if (-not (Test-Path (Join-Path $PgData "PG_VERSION"))) {
  $PwFile = Join-Path $ProjectRoot "data\postgres_pw.tmp"
  Set-Content -LiteralPath $PwFile -Value "agriagent" -NoNewline -Encoding ASCII
  & (Join-Path $PgBin "initdb.exe") -D $PgData -U agriagent -A scram-sha-256 --pwfile=$PwFile --encoding=UTF8 --locale=C
  Remove-Item -LiteralPath $PwFile -Force
}

try {
  & (Join-Path $PgBin "pg_ctl.exe") -D $PgData status | Out-Null
} catch {
  & (Join-Path $PgBin "pg_ctl.exe") -D $PgData -l $PgLog -o '"-p" "5432"' start
}

$env:PGPASSWORD = "agriagent"
$ExistingDb = & (Join-Path $PgBin "psql.exe") -h 127.0.0.1 -p 5432 -U agriagent -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='agriagent';"
if ($ExistingDb -ne "1") {
  & (Join-Path $PgBin "createdb.exe") -h 127.0.0.1 -p 5432 -U agriagent agriagent
}

docker compose -f (Join-Path $ProjectRoot "docker-compose.yml") -f (Join-Path $ProjectRoot "docker-compose.gdrive.yml") up -d redis chromadb prometheus grafana

$ExistingBackendPids = @(Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
foreach ($PidValue in $ExistingBackendPids) {
  if ($PidValue) {
    Stop-Process -Id $PidValue -Force -ErrorAction SilentlyContinue
  }
}

$ExistingFrontendPids = @(Get-NetTCPConnection -LocalPort 3003 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
foreach ($PidValue in $ExistingFrontendPids) {
  if ($PidValue) {
    Stop-Process -Id $PidValue -Force -ErrorAction SilentlyContinue
  }
}

for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
  $OpenPorts = @(Get-NetTCPConnection -LocalPort 8000,3003 -State Listen -ErrorAction SilentlyContinue)
  if ($OpenPorts.Count -eq 0) {
    break
  }
  Start-Sleep -Milliseconds 500
}

if (Test-Path $BackendLog) { Remove-Item -LiteralPath $BackendLog -Force }
if (Test-Path $BackendErr) { Remove-Item -LiteralPath $BackendErr -Force }

Start-Process -FilePath (Join-Path $ProjectRoot ".venv\Scripts\python.exe") `
  -ArgumentList @("-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8000", "--loop", "app.core.uvicorn_loop:selector_event_loop") `
  -WorkingDirectory $ProjectRoot `
  -RedirectStandardOutput $BackendLog `
  -RedirectStandardError $BackendErr `
  -WindowStyle Hidden

if (Test-Path $FrontendLog) { Remove-Item -LiteralPath $FrontendLog -Force }
if (Test-Path $FrontendErr) { Remove-Item -LiteralPath $FrontendErr -Force }

Start-Process -FilePath "npm.cmd" `
  -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1") `
  -WorkingDirectory (Join-Path $ProjectRoot "frontend") `
  -RedirectStandardOutput $FrontendLog `
  -RedirectStandardError $FrontendErr `
  -WindowStyle Hidden

Start-Sleep -Seconds 3
Write-Host "AgriAgent backend is starting on http://127.0.0.1:8000"
Write-Host "AgriAgent frontend is starting on http://127.0.0.1:3003"
Write-Host "Prometheus is starting on http://127.0.0.1:9090"
Write-Host "Grafana is starting on http://127.0.0.1:3000"
