# Build Instructions

This directory contains PowerShell build scripts for creating Windows EXE and Android APK distributions of the YouTube Downloader application.

## Quick Start

### Build Everything (Windows + Android)

```powershell
# From the root directory
.\build_all.ps1
```

This will:
1. Build Windows EXE with PyInstaller
2. Build Android APK with Buildozer
3. Clean up build artifacts
4. Move all output files to a new `build_output_YYYY-MM-DD_HH-MM-SS` folder

### Build Windows Only

```powershell
# From the Windows directory
cd Windows
.\build_windows.ps1
```

Output: `Windows\dist\YTDownloader\`

### Build Android Only

```powershell
# From the Android directory
cd Android
.\build_android.ps1
```

Output: `Android\bin\*.apk`

## Prerequisites

### Windows Build
- Python 3.8+ with pip
- Virtual environment (created automatically)
- Dependencies from `Windows/requirements.txt` (installed automatically)
- PyInstaller (installed automatically)

### Android Build
- Python 3.8+
- Java JDK 11+ (in PATH)
- Android SDK (configured in buildozer.spec)
- Windows or Linux with buildozer support

For Windows users: Android building is challenging due to Java/Android SDK setup. Consider using Linux (WSL2) or macOS for Android builds.

## Output Structure

When running `build_all.ps1`, the output directory structure will be:

```
build_output_YYYY-MM-DD_HH-MM-SS/
├── YTDownloader_Windows/          # Windows application folder
│   ├── YTDownloader.exe           # Main executable
│   ├── _internal/                 # Python runtime and libraries
│   └── assets/                    # Icons and resources
└── youtube_downloader-*.apk       # Android APK file
```

## Troubleshooting

### Windows Build Issues
- **PyInstaller errors**: Run `pip install --upgrade pyinstaller`
- **Missing dependencies**: Run `pip install -r Windows/requirements.txt`
- **Icon not found**: Ensure `Windows/assets/Youtube_icon.ico` exists

### Android Build Issues
- **Java not found**: Install Java JDK 11+ and add to PATH
  ```powershell
  # Verify Java is in PATH
  java -version
  ```
- **Build hangs**: Check `.buildozer/android/platform/build-*/build.log`
- **NDK/SDK errors**: Update buildozer:
  ```powershell
  pip install --upgrade buildozer cython
  ```

### For WSL2 Users (Linux on Windows)
Android builds work better on Linux. Install WSL2 and run:
```bash
cd /mnt/d/Github/Youtube-downloader
./build_all.sh  # (create a similar .sh script)
```

## Distribution

After building:

### Windows
1. The `YTDownloader_Windows` folder contains the complete application
2. Users can run `YTDownloader.exe` directly (no installation needed)
3. Package as ZIP for distribution

### Android
1. Sign the APK if needed before distribution:
   ```powershell
   jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore my-release-key.keystore *.apk alias_name
   ```
2. Upload to Google Play Store or distribute directly

## Cleanup

The scripts automatically clean up build artifacts (dist/, build/, .buildozer/) to save space.

To manually clean:
```powershell
# Windows
Remove-Item Windows/dist -Recurse -Force
Remove-Item Windows/build -Recurse -Force

# Android
Remove-Item Android/.buildozer -Recurse -Force
Remove-Item Android/bin -Recurse -Force
Remove-Item Android/dist -Recurse -Force
```

## Environment Variables

You can customize builds with environment variables:

```powershell
# For Android builds, specify API level
$env:ANDROID_API_LEVEL = "31"

# For Windows, specify output name
# (inherited from main.spec)
```

## Dependencies Versions

See the latest versions in:
- `Windows/requirements.txt` - Windows app dependencies
- `Android/requirements.txt` - Android app dependencies
- Windows/main.spec - PyInstaller configuration
- Android/buildozer.spec - Buildozer configuration

## Notes

- First build takes longer (downloading SDKs, building dependencies)
- Subsequent builds are faster for Windows (cached deps)
- Android builds each time may take 10-30 minutes depending on system
- Output files can be large (~200MB+ for Android)
