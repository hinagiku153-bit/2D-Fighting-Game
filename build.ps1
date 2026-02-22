$ErrorActionPreference = 'Stop'

# Build settings
$distPath = Join-Path $PSScriptRoot 'build'
$workPath = Join-Path $PSScriptRoot 'build\temp'

# Ensure folders exist
New-Item -ItemType Directory -Force -Path $distPath | Out-Null
New-Item -ItemType Directory -Force -Path $workPath | Out-Null

# Build using spec (preferred)
python -m PyInstaller --noconfirm --clean --distpath "$distPath" --workpath "$workPath" main.spec

Write-Host "Built: $distPath\main.exe"
