# Build Android APK for YouTube Downloader
# Usage (from PowerShell in Android directory):
#   .\build_android.ps1
#
# Prerequisites:
#   - Java JDK 11+ installed and configured
#   - Android SDK installed and configured
#   - buildozer.spec configured properly

$ErrorActionPreference = "Continue"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Building Android APK" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
    Write-Host "[FAIL] Java not found in PATH" -ForegroundColor Red
    Write-Host "Please install Java JDK 11+ and add it to PATH" -ForegroundColor Yellow
    exit 1
}

$javaInfo = cmd /c java -version 2>&1
if ($LASTEXITCODE -eq 0 -or $javaInfo) {
    $versionLine = $javaInfo | Select-String "version" | Select-Object -First 1
    Write-Host "[OK] Java found: $versionLine" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Could not verify Java installation" -ForegroundColor Red
    exit 1
}

# Setup environment
if (-not (Test-Path "..\\.venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv ..\.venv
}

. ..\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip --quiet

Set-Location $PSScriptRoot

Write-Host "Installing Android build dependencies..."
python -m pip install buildozer cython --quiet

# Check if buildozer has Android target available
Write-Host "Checking buildozer configuration..."
$buildozerHelp = buildozer --help 2>&1
if ($buildozerHelp -match "android") {
    Write-Host "[OK] Android target is available" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Building Android APK (this may take 10-30 minutes)..." -ForegroundColor Yellow
    Write-Host "This will:"
    Write-Host "  1. Download Android SDK components"
    Write-Host "  2. Compile Python code with Cython"
    Write-Host "  3. Build APK package"
    Write-Host ""

    buildozer android release

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build failed!" -ForegroundColor Red
        exit 1
    }

    # Verify output
    $apkFile = Get-ChildItem "bin\*.apk" -ErrorAction SilentlyContinue | Select-Object -First 1

    if ($apkFile) {
        Write-Host ""
        Write-Host "[OK] Build successful!" -ForegroundColor Green
        Write-Host "Output: bin\$($apkFile.Name)" -ForegroundColor Green
        Write-Host ""

        $size = $apkFile.Length / 1MB
        Write-Host "APK size: $([math]::Round($size, 2)) MB"
        Write-Host ""
        Write-Host "Installation instructions:" -ForegroundColor Cyan
        Write-Host "  1. Transfer APK to Android device"
        Write-Host "  2. Enable 'Unknown Sources' in settings"
        Write-Host "  3. Install the APK"
        Write-Host ""
        Write-Host "Or use adb:"
        Write-Host "  adb install -r bin\$($apkFile.Name)"
    } else {
        Write-Host "[FAIL] Build failed - APK not found" -ForegroundColor Red
    }
} else {
    Write-Host "[WARN] Android target not available in buildozer" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Note: Buildozer Android support is not available on Windows." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To build the Android APK, you have these options:" -ForegroundColor Cyan
    Write-Host "  1. Use WSL 2 (Windows Subsystem for Linux):" -ForegroundColor White
    Write-Host "     - Install Ubuntu in WSL 2" -ForegroundColor White
    Write-Host "     - Install Android SDK and buildozer in the Linux environment" -ForegroundColor White
    Write-Host "     - Run 'buildozer android release' from WSL" -ForegroundColor White
    Write-Host "" -ForegroundColor White
    Write-Host "  2. Use a Linux or macOS system:" -ForegroundColor White
    Write-Host "     - Transfer the Android folder to a Linux/macOS machine" -ForegroundColor White
    Write-Host "     - Install buildozer, Android SDK, and NDK" -ForegroundColor White
    Write-Host "     - Run the build there" -ForegroundColor White
    Write-Host "" -ForegroundColor White
    Write-Host "  3. Use GitHub Actions CI/CD:" -ForegroundColor White
    Write-Host "     - Create a .github/workflows/build-android.yml file" -ForegroundColor White
    Write-Host "     - GitHub will build the APK in a Linux environment" -ForegroundColor White
    Write-Host "" -ForegroundColor White
    exit 1
}
