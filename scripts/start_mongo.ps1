# Start MongoDB
$dataDir = "G:\Wyatt\cucumber-irrigation\mongodb_data_fresh"
$mongod = "G:\Wyatt\cucumber-irrigation\mongodb\bin\mongod.exe"

Write-Host "============================================"
Write-Host "Starting MongoDB 7.0.15"
Write-Host "============================================"

# Create fresh data directory
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
    Write-Host "Created data directory: $dataDir"
}

Write-Host "Starting mongod..."
Write-Host "  Data: $dataDir"
Write-Host "  Port: 27017"

# Run MongoDB
& $mongod --dbpath $dataDir --bind_ip 127.0.0.1 --port 27017
