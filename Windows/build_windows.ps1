# Build Windows EXE only for YouTube Downloader
# Usage (from PowerShell in Windows directory):
#   .\build_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Building Windows EXE" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Setup environment
if (-not (Test-Path "..\\.venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv ..\.venv
}

. ..\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip --quiet

Set-Location $PSScriptRoot

Write-Host "Installing dependencies..."
python -m pip install -r requirements.txt --quiet
python -m pip install pyinstaller --quiet

Write-Host "Building executable (PyInstaller)..."
pyinstaller --noconfirm --clean main.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

# Verify output
if ((Test-Path "dist\YTDownloader") -or (Test-Path "dist\YTDownloader.exe")) {
    Write-Host ""
    Write-Host "[OK] Build successful!" -ForegroundColor Green
    if (Test-Path "dist\YTDownloader.exe") {
        Write-Host "Output: dist\YTDownloader.exe" -ForegroundColor Green
        $size = (Get-Item "dist\YTDownloader.exe" | Measure-Object -Property Length -Sum).Sum / 1MB
    } else {
        Write-Host "Output: dist\YTDownloader\" -ForegroundColor Green
        $size = (Get-ChildItem "dist\YTDownloader\YTDownloader.exe" | Measure-Object -Property Length -Sum).Sum / 1MB
    }
    Write-Host ""
    Write-Host "Executable size: $([math]::Round($size, 2)) MB"
} else {
    Write-Host "[FAIL] Build failed - executable not found" -ForegroundColor Red
    exit 1
}
