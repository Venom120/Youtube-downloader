# Android APK Build Guide

## Current Status

❌ **Android builds are NOT supported on Windows** with the current buildozer setup.

Buildozer's Android support is only available on **Linux** and **macOS**. Windows users need to use an alternative approach.

## Why Windows Doesn't Work

Buildozer relies on the Android SDK and NDK, which don't have native Windows support in the buildozer ecosystem. While Java is available on Windows, the build tools chain (esp. the compilation toolchain) requires a Linux/Unix environment.

## Solution Options

### Option 1: Use WSL 2 (Windows Subsystem for Linux) ⭐ RECOMMENDED

This is the easiest option if you're on Windows 10/11.

**Setup:**
```bash
# 1. Install WSL 2 with Ubuntu
wsl --install -d Ubuntu-22.04

# 2. Enter WSL and install dependencies
wsl
sudo apt-get update
sudo apt-get install -y python3 python3-venv openjdk-11-jdk git

# 3. Clone/navigate to your project
cd /mnt/d/Github/Youtube-downloader  # Adjust drive letter

# 4. Create virtual environment in WSL
python3 -m venv venv
source venv/bin/activate

# 5. Install build dependencies
pip install --upgrade pip
pip install buildozer cython kivy

# 6. Build the APK
cd Android
buildozer android release
```

The APK will be created in `Android/bin/YTDownloader-2.0.0-release-unsigned.apk`

**Advantages:**
- Native Linux environment
- Full buildozer support
- Easy access to Windows files via `/mnt/d/`

### Option 2: Use GitHub Actions (CI/CD) ⭐ AUTOMATED

Let GitHub's servers build the APK for you.

**Setup:**
1. Create folder: `.github/workflows/`
2. Create file: `.github/workflows/build-android.yml`

```yaml
name: Build Android APK

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install buildozer cython kivy
      
      - name: Build APK
        working-directory: ./Android
        run: buildozer android release
      
      - name: Upload APK
        uses: actions/upload-artifact@v3
        with:
          name: youtube-downloader-apk
          path: Android/bin/*.apk
```

**Advantages:**
- Runs on GitHub's servers (you don't need to do anything locally)
- APK automatically uploaded as artifact
- Works for any OS

**Usage:**
1. Push code to GitHub (or manually trigger workflow)
2. Wait for build to complete (~15 minutes)
3. Download APK from "Actions" tab

### Option 3: Use a Linux/macOS Machine

If you have access to a Linux or macOS system:

```bash
# On Linux/macOS:
cd /path/to/Youtube-downloader
cd Android

# Install dependencies (Linux example)
sudo apt-get install python3-pip openjdk-11-jdk
pip install buildozer cython kivy

# Build
buildozer android release
```

### Option 4: Use Docker

```bash
docker run -v $(pwd):/app -w /app/Android buildpack-deps:focal bash -c "
apt-get update && \
apt-get install -y python3-pip openjdk-11-jdk && \
pip install buildozer cython kivy && \
buildozer android release
"
```

## Buildozer Configuration

The [buildozer.spec](buildozer.spec) file is already configured with:

- **App name**: YTDownloader
- **Package**: org.Venom120.YTDownloader
- **Python version**: 3.10.11
- **Kivy version**: 2.1.0
- **Dependencies**: yt-dlp, pillow, certifi, requests
- **Permissions**: INTERNET, READ/WRITE_EXTERNAL_STORAGE
- **Target APIs**: Android 21-31
- **Architectures**: arm64-v8a, armeabi-v7a

No additional configuration is needed before building.

## Building the APK

### Once You Have a Linux/macOS/WSL Environment:

```bash
cd Android
buildozer android release
```

**First build will take 10-30 minutes** (downloads SDK, NDK, compiles everything)

**Output:**
```
bin/YTDownloader-2.0.0-release-unsigned.apk
```

## Signing the APK

For release, you need to sign the APK:

```bash
# Generate keystore (do this once)
keytool -genkey -v -keystore youtube-downloader.keystore \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias youtube-downloader

# Update buildozer.spec with keystore details
# Then rebuild
buildozer android release
```

## Installing on Device

### Via File Transfer:
1. Enable "Unknown Sources" in Android settings
2. Transfer APK to device
3. Open file manager and tap APK to install

### Via ADB:
```bash
adb install -r bin/YTDownloader-2.0.0-release-unsigned.apk
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| `buildozer: command not found` | Install: `pip install buildozer` |
| `cython: command not found` | Install: `pip install cython` |
| `java: command not found` | Install Java JDK (11 or higher) |
| `Android SDK not found` | Buildozer will download on first build (10GB+) |
| `Permission denied` | Ensure `buildozer.spec` is in Android directory |
| `Build failed` | Check `.buildozer/android/platform/build-*/build.log` |

## Next Steps

1. **Choose a build method** from the options above
2. **Follow the setup instructions** for your chosen method
3. **Run the build** and wait for completion
4. **Test the APK** on an Android device
5. **Sign the APK** if releasing on Play Store

---

**For Windows users**: WSL 2 (Option 1) is the quickest path to building APKs locally.
**For CI/CD**: GitHub Actions (Option 2) requires zero local setup.
