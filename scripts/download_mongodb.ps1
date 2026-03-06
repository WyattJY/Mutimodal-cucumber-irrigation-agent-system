# MongoDB Windows 下载脚本
# PowerShell 版本

$ErrorActionPreference = 'Stop'
$MONGODB_VERSION = '7.0.15'
$MONGODB_URL = "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-$MONGODB_VERSION.zip"
$DOWNLOAD_DIR = Join-Path $PSScriptRoot '..\mongodb'
$MONGODB_ZIP = Join-Path $DOWNLOAD_DIR 'mongodb.zip'

Write-Host '============================================================'
Write-Host "MongoDB $MONGODB_VERSION Windows Download"
Write-Host '============================================================'

# Create directory
if (-not (Test-Path $DOWNLOAD_DIR)) {
    New-Item -ItemType Directory -Path $DOWNLOAD_DIR | Out-Null
    Write-Host "Created directory: $DOWNLOAD_DIR"
}

# Check if already exists
$mongodPath = Join-Path $DOWNLOAD_DIR 'bin\mongod.exe'
if (Test-Path $mongodPath) {
    Write-Host 'MongoDB already exists!'
    & $mongodPath --version
    exit 0
}

Write-Host ''
Write-Host '[1] Downloading MongoDB...'
Write-Host "    URL: $MONGODB_URL"
Write-Host '    This may take a few minutes...'

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $MONGODB_URL -OutFile $MONGODB_ZIP -UseBasicParsing

Write-Host 'Download complete!'

Write-Host ''
Write-Host '[2] Extracting...'
Expand-Archive -Path $MONGODB_ZIP -DestinationPath $DOWNLOAD_DIR -Force

# Move files from extracted folder to bin
$binDir = Join-Path $DOWNLOAD_DIR 'bin'
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir | Out-Null
}

Get-ChildItem -Path $DOWNLOAD_DIR -Directory -Filter 'mongodb-*' | ForEach-Object {
    $srcBin = Join-Path $_.FullName 'bin'
    if (Test-Path $srcBin) {
        Copy-Item -Path "$srcBin\*" -Destination $binDir -Force
    }
    Remove-Item -Path $_.FullName -Recurse -Force
}

# Delete zip
Remove-Item -Path $MONGODB_ZIP -Force

Write-Host 'Extraction complete!'

Write-Host ''
Write-Host '[3] Verifying...'
& $mongodPath --version

Write-Host ''
Write-Host '============================================================'
Write-Host 'MongoDB installed successfully!'
Write-Host '============================================================'
Write-Host ''
Write-Host 'Start MongoDB with:'
Write-Host "  $mongodPath --dbpath `"$DOWNLOAD_DIR\..\mongodb_data`""
