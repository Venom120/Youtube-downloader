# Build Instructions

This document provides instructions for building all components of the YouTube Downloader project:
- **Windows Desktop App** - Standalone executable
- **Backend API Server** - Docker container
- **React Native Mobile App** - Android APK and iOS IPA

## Project Architecture

The project uses a dual architecture:
- **Windows**: Standalone desktop app (no server required)
- **Mobile**: Client-server architecture (React Native app + FastAPI backend)

## 📦 Build All Components

### Quick Build Script

```powershell
# From the root directory (Windows)
.\build_all.ps1
```

This will build:
1. Windows EXE with PyInstaller
2. Backend Docker image
3. React Native APK (if EAS configured)

Output will be organized in `build_output_YYYY-MM-DD_HH-MM-SS/`

## Prerequisites

### Windows Desktop App
- Python 3.10+
- pip and virtual environment
- PyInstaller (installed automatically)
- Dependencies from `Windows/requirements.txt`

### Backend Server
- Docker and Docker Compose (recommended)
- OR Python 3.11+ with pip
- FFmpeg installed

### React Native Mobile App
- Node.js 20+
- npm or yarn
- Expo CLI
- EAS CLI (for production builds)
- Expo account for cloud builds

## 🖥️ Build Windows Desktop App

### Using Build Script (Recommended)

```powershell
cd Windows
.\build_windows.ps1
```

### Manual Build

1. **Create Virtual Environment**:
   ```powershell
   cd Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   pip install pyinstaller
   ```

3. **Build Executable**:
   ```powershell
   python -m PyInstaller main.spec
   ```

4. **Output**:
   - Located in `Windows/dist/YTDownloader/`
   - Contains `YTDownloader.exe` and all dependencies
   - Distribute entire folder as ZIP

## 🔧 Build Backend Server

### Using Docker (Recommended)

```bash
cd Android/Python

# Build image
docker build -t ytdownloader-backend:latest .

# Or use docker-compose
docker-compose build
```

### Manual Setup

```bash
cd Android/Python
pip install -r requirements.txt

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Deploy to Registry

```bash
# Tag for registry
docker tag ytdownloader-backend:latest your-registry/ytdownloader-backend:latest

# Push to Docker Hub
docker push your-registry/ytdownloader-backend:latest
```

## 📱 Build React Native Mobile App

### Development Build

```bash
cd Android/React-Native

# Install dependencies
npm install

# Start development server
npx expo start
```

### Production Build with EAS

1. **Setup EAS (First Time)**:
   ```bash
   npm install -g eas-cli
   eas login
   eas build:configure
   ```

2. **Configure `.env`**:
   ```env
   BACKEND_URL=https://your-backend-server.com
   WS_URL=wss://your-backend-server.com
   APP_ID=com.venom120.ytdownloader
   ```

3. **Build Android APK**:
   ```bash
   # Development build
   eas build --platform android --profile development
   
   # Production build
   eas build --platform android --profile production
   ```

4. **Build iOS IPA**:
   ```bash
   eas build --platform ios --profile production
   ```

5. **Download Builds**:
   ```bash
   eas build:list
   # Download from Expo dashboard or CLI
   ```

### Local Build (Android Only)

```bash
# Generate native code
npx expo prebuild

# Build APK locally (requires Android SDK)
cd android
./gradlew assembleRelease

# Output: android/app/build/outputs/apk/release/app-release.apk
```

## Output Structure

After building all components:

```
build_output_YYYY-MM-DD_HH-MM-SS/
├── Windows/
│   └── YTDownloader/              # Windows application folder
│       ├── YTDownloader.exe       # Main executable
│       ├── _internal/             # Python runtime and libraries
│       └── assets/                # Icons and resources
│
├── Backend/
│   └── ytdownloader-backend.tar   # Docker image (if exported)
│
└── Mobile/
    ├── android-*.apk              # Android APK
    └── ios-*.ipa                  # iOS IPA (if built)
```

## 🚀 Distribution

### Windows Desktop App

1. **Package for Distribution**:
   ```powershell
   # Create ZIP archive
   Compress-Archive -Path Windows/dist/YTDownloader -DestinationPath YTDownloader-Windows.zip
   ```

2. **User Installation**:
   - Extract ZIP to any location
   - Run `YTDownloader.exe`
   - No Python installation required

### Backend Server

1. **Docker Image**:
   ```bash
   # Export image
   docker save ytdownloader-backend:latest > ytdownloader-backend.tar
   
   # On target server
   docker load < ytdownloader-backend.tar
   docker-compose up -d
   ```

2. **Cloud Deployment**:
   - Push to Docker Hub/GitHub Container Registry
   - Deploy to VPS, AWS, DigitalOcean, etc.
   - Configure environment variables
   - Setup SSL/HTTPS with reverse proxy

### React Native Mobile App

1. **Android APK**:
   - Direct distribution (sideloading)
   - Or publish to Google Play Store

2. **iOS IPA**:
   - TestFlight for beta testing
   - Or publish to Apple App Store

3. **App Store Submission**:
   ```bash
   # Submit to stores via EAS
   eas submit --platform android
   eas submit --platform ios
   ```

## Troubleshooting

### Windows Build Issues

**PyInstaller Errors**:
```powershell
# Update PyInstaller
pip install --upgrade pyinstaller

# Clear cache and rebuild
rmdir /s /q build dist
python -m PyInstaller main.spec --clean
```

**Missing Dependencies**:
```powershell
pip install --upgrade -r requirements.txt
```

**Icon Not Found**:
- Ensure `Windows/assets/Youtube_icon.ico` exists
- Check path in `main.spec`

### Backend Build Issues

**Docker Build Fails**:
```bash
# Check Docker is running
docker --version

# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

**FFmpeg Not Found**:
```bash
# In Dockerfile, FFmpeg install is included
# If manual install needed:
# Ubuntu/Debian:
apt-get install ffmpeg

# macOS:
brew install ffmpeg
```

**Port Already in Use**:
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

### React Native Build Issues

**EAS Build Fails**:
```bash
# Check EAS configuration
eas build:configure

# View build logs
eas build:list
eas build:view BUILD_ID

# Clear credentials
eas credentials --clear-provisioning-profile
```

**Environment Variables Not Loading**:
```bash
# Ensure .env file exists in Android/React-Native/
# Check @env import in config.ts
# Rebuild app after changing .env
```

**Expo Prebuild Issues**:
```bash
# Clean and regenerate
rm -rf android ios
npx expo prebuild --clean
```

**Android Gradle Build Fails**:
```bash
cd android

# Clean build
./gradlew clean

# Rebuild
./gradlew assembleRelease

# Check Java version (needs JDK 11 or 17)
java -version
```

### General Issues

**yt-dlp Errors**:
```bash
# Update to latest version
pip install --upgrade yt-dlp
```

**Network/Proxy Issues**:
```bash
# Set proxy in environment
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=https://proxy:port
```

**Disk Space**:
```bash
# Check available space
df -h

# Clean Docker
docker system prune -a --volumes
```

## Cleanup

The build scripts automatically clean up artifacts to save space.

### Manual Cleanup

**Windows**:
```powershell
# Clean build artifacts
Remove-Item Windows/dist -Recurse -Force
Remove-Item Windows/build -Recurse -Force
Remove-Item Windows/__pycache__ -Recurse -Force
```

**Backend**:
```bash
# Clean Docker
docker-compose down
docker system prune -a

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
```

**React Native**:
```bash
cd Android/React-Native

# Clean dependencies
rm -rf node_modules

# Clean native builds
rm -rf android ios

# Clean Expo cache
npx expo start -c
```

## Environment Configuration

### Development Environment Variables

**Backend** (`Android/Python/.env`):
```env
ALLOWED_APP_ID=com.venom120.ytdownloader
DOWNLOAD_DIR=/app/downloads
DEBUG=true
```

**React Native** (`Android/React-Native/.env`):
```env
# Local development
BACKEND_URL=http://192.168.1.xxx:8000  # Your local IP
WS_URL=ws://192.168.1.xxx:8000
APP_ID=com.venom120.ytdownloader

# Production
# BACKEND_URL=https://your-domain.com
# WS_URL=wss://your-domain.com
```

### Production Environment Variables

Update production values before building release versions:
- Use HTTPS/WSS URLs in production
- Configure proper domain names
- Set appropriate security tokens
- Enable production optimizations

## Continuous Integration

### GitHub Actions

The project includes CI/CD workflows:

**.github/workflows/build-windows.yml**:
- Builds Windows EXE on push
- Uploads artifacts
- Creates releases

**.github/workflows/build-backend.yml**:
- Builds Docker image
- Pushes to registry
- Deploys to server

**.github/workflows/build-mobile.yml**:
- Runs EAS builds
- Publishes to app stores (when configured)

## Notes

- **First build takes longer**: Downloads dependencies, SDKs, etc.
- **Subsequent builds faster**: Cached dependencies
- **Backend requires FFmpeg**: Included in Docker image
- **Mobile needs backend running**: Configure BACKEND_URL correctly
- **Windows standalone**: No server required

## Dependencies Versions

Current versions (check files for latest):
- Python: 3.11+
- Node.js: 20+
- Expo SDK: 52
- React Native: 0.76.x
- FastAPI: 0.115.x
- yt-dlp: Latest available

## Support

For build issues:
1. Check this troubleshooting guide
2. Review error messages carefully
3. Check GitHub Issues
4. Create new issue with build logs

---

**Related Documentation**:
- [README.md](../README.md) - Project overview
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details
- Android builds each time may take 10-30 minutes depending on system
- Output files can be large (~200MB+ for Android)
