# Build all components (Windows EXE and Android APK) for YouTube Downloader
# Usage (from PowerShell in root directory):
#   .\build_all.ps1

$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "YouTube Downloader Build Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# ===== SETUP ENVIRONMENT =====
Write-Host "[1/5] Setting up environment..." -ForegroundColor Yellow

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip --quiet
Write-Host "[OK] Environment ready" -ForegroundColor Green
Write-Host ""

# ===== BUILD WINDOWS EXE =====
Write-Host "[2/5] Building Windows EXE..." -ForegroundColor Yellow

try {
    Set-Location (Join-Path $root "Windows")

    Write-Host "Installing Windows dependencies..."
    python -m pip install -r requirements.txt --quiet
    python -m pip install pyinstaller --quiet

    Write-Host "Building Windows executable..."
    pyinstaller --noconfirm --clean main.spec

    if ((Test-Path "dist\YTDownloader") -or (Test-Path "dist\YTDownloader.exe")) {
        Write-Host "[OK] Windows build successful" -ForegroundColor Green
    } else {
        throw "Windows executable not found"
    }
}
catch {
    Write-Host "[FAIL] Windows build failed: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# ===== COLLECT OUTPUT FILES =====
Write-Host "[3/4] Collecting output files..." -ForegroundColor Yellow

Set-Location $root

$outputDir = Join-Path $root "build_output_$timestamp"
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

Write-Host "Output directory: $outputDir"

$winExePath = Join-Path $root "Windows\dist\YTDownloader.exe"
if ((Test-Path $winExePath) -or (Test-Path (Join-Path $root "Windows\dist\YTDownloader"))) {
    Write-Host "Moving Windows build..."
    if (Test-Path $winExePath) {
        Copy-Item -Path $winExePath -Destination (Join-Path $outputDir "YTDownloader.exe") -Force
    } else {
        Move-Item -Path (Join-Path $root "Windows\dist\YTDownloader") -Destination (Join-Path $outputDir "YTDownloader_Windows") -Force
    }
    Write-Host "[OK] Windows files moved" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Windows build not found" -ForegroundColor Red
}

Write-Host ""

# ===== CLEANUP BUILD ARTIFACTS =====
Write-Host "[4/4] Cleaning up build artifacts..." -ForegroundColor Yellow

$cleanupDirs = @(
    (Join-Path $root "Windows\dist"),
    (Join-Path $root "Windows\build")
)

foreach ($dir in $cleanupDirs) {
    if (Test-Path $dir) {
        Write-Host "Removing $([System.IO.Path]::GetFileName($dir))..."
        Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "[OK] Cleanup complete" -ForegroundColor Green
Write-Host ""

# ===== SUMMARY =====
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Output files are in: $outputDir" -ForegroundColor Green
Write-Host ""

Get-ChildItem -Path $outputDir -Recurse | ForEach-Object {
    if ($_.PSIsContainer) {
        Write-Host "  [FOLDER] $($_.Name)"
    } else {
        Write-Host "  [FILE] $($_.Name)"
    }
}

Write-Host ""
Write-Host "Ready for distribution!" -ForegroundColor Green
deactivate
