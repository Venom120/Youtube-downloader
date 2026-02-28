# Check build environment and prerequisites
# Usage:
#   .\check_environment.ps1

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "YouTube Downloader - Build Environment Check" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# ===== PYTHON =====
Write-Host "[1] Python" -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "OK $pythonVersion" -ForegroundColor Green
    
    # Check Python version
    $version = [version] (python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if ($version -ge [version]"3.8") {
        Write-Host "  Version OK (3.8+)" -ForegroundColor Green
    } else {
        Write-Host "  ERROR: Version too old (need 3.8+)" -ForegroundColor Red
        $allGood = $false
    }
} else {
    Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# ===== PIP =====
Write-Host "[2] pip (Python Package Manager)" -ForegroundColor Yellow
if (Get-Command pip -ErrorAction SilentlyContinue) {
    $pipVersion = pip --version
    Write-Host "OK $pipVersion" -ForegroundColor Green
} else {
    Write-Host "ERROR: pip not found in PATH" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# ===== GIT =====
Write-Host "[3] Git" -ForegroundColor Yellow
if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitVersion = git --version
    Write-Host "OK $gitVersion" -ForegroundColor Green
} else {
    Write-Host "WARN: Git not found (optional)" -ForegroundColor Yellow
}
Write-Host ""

# ===== WINDOWS BUILD TOOLS =====
Write-Host "[4] Windows Build Dependencies" -ForegroundColor Yellow

# Check for pyinstaller
if (python -c "import pyinstaller; print('ok')" -ErrorAction SilentlyContinue) {
    Write-Host "OK PyInstaller installed" -ForegroundColor Green
} else {
    Write-Host "WARN PyInstaller not installed (will be installed during build)" -ForegroundColor Yellow
}

# Check for customtkinter
if (python -c "import customtkinter; print('ok')" -ErrorAction SilentlyContinue) {
    Write-Host "OK CustomTkinter installed" -ForegroundColor Green
} else {
    Write-Host "WARN CustomTkinter not installed (will be installed from Windows/requirements.txt)" -ForegroundColor Yellow
}

Write-Host ""

# ===== PROJECT STRUCTURE =====
Write-Host "[6] Project Structure" -ForegroundColor Yellow

$requiredFiles = @(
    "Windows/main.py",
    "Windows/main.spec",
    "Windows/requirements.txt",
    "tests/test_ui_and_core.py"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "OK $file" -ForegroundColor Green
    } else {
        Write-Host "ERROR Missing: $file" -ForegroundColor Red
        $allGood = $false
    }
}

Write-Host ""

# ===== SUMMARY =====
Write-Host "======================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "Status: Ready for Windows builds" -ForegroundColor Green
    Write-Host ""
    Write-Host "Run Windows build:" -ForegroundColor Cyan
    Write-Host "  cd Windows" -ForegroundColor Gray
    Write-Host "  .\build_windows.ps1" -ForegroundColor Gray
} else {
    Write-Host "Status: Some tools missing" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Install missing tools with:" -ForegroundColor Cyan
    Write-Host "  python -m pip install pyinstaller buildozer cython" -ForegroundColor Gray
}

Write-Host ""
Write-Host ""
Write-Host ""
Write-Host "Full documentation: See BUILD_INSTRUCTIONS.md" -ForegroundColor Cyan
