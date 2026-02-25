# YouTube Downloader - Enhanced Version

A modern YouTube video and audio downloader for Windows and Android with search capabilities and a YouTube-like interface.

## ✨ New Features

- **🔍 Search Functionality**: Search for videos directly without needing URLs
- **🎨 Modern Card-Based UI**: YouTube-like interface with video thumbnails
- **📑 Playlist Support**: Download entire playlists or individual videos from playlists
- **⚡ yt-dlp Integration**: More reliable and feature-rich than pytube
- **🏗️ MVC Architecture**: Clean, organized code structure for easy maintenance
- **📱 Cross-Platform**: Works on both Windows and Android

## 📁 New Project Structure

```
Youtube-downloader/
├── Windows/
│   ├── models/              # Data models and business logic
│   │   ├── __init__.py
│   │   ├── video_model.py   # VideoInfo and SearchResult classes
│   │   └── ytdlp_wrapper.py # yt-dlp integration wrapper
│   ├── controllers/         # Application controllers
│   │   ├── __init__.py
│   │   ├── download_controller.py
│   │   └── search_controller.py
│   ├── views/               # UI components
│   │   ├── __init__.py
│   │   └── video_card.py    # Video card widget
│   ├── assets/              # Images and icons
│   ├── main.py          # Main application (NEW VERSION)
│   ├── main.py              # Old version (for reference)
│   └── requirements.txt # Updated dependencies
│
└── Android/
    ├── models/              # Shared models with Windows
    ├── controllers/         # Android controllers
    ├── views/               # Kivy-specific views
    ├── assets/              # Images and icons
    ├── main.py          # Main Kivy app (NEW VERSION)
    ├── main.kv          # Kivy UI layout
    ├── main.py              # Old version (for reference)
    └── requirements.txt # Updated dependencies
```

## 🚀 Quick Start

### Windows

1. **Install Dependencies**:
   ```bash
   cd Windows
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python main.py
   ```

3. **Build Standalone EXE** (distributable):
   ```bash
   python -m PyInstaller main.spec
   ```

### Android

1. **Install Dependencies**:
   ```bash
   cd Android
   pip install -r requirements.txt
   ```

2. **Install Build Dependencies** (Ubuntu/Debian):
   ```bash
   sudo apt-get install build-essential libffi-dev libssl-dev libjpeg-dev zlib1g-dev openjdk-11-jdk
   ```

3. **Run on Desktop (for testing)**:
   ```bash
   python main.py
   ```

4. **Build APK with Buildozer**:
   ```bash
   buildozer android debug    # Debug APK
   buildozer android release  # Release APK (requires keystore)
   ```

## 📋 Requirements

### Windows
- Python 3.10+ (recommended)
- yt-dlp 2026.2.21
- customtkinter 5.2.2
- pillow 12.1.1
- requests 2.32.5
- certifi 2026.2.25
- pyinstaller 6.19.0 (for building EXE)
- FFmpeg (for MP3 downloads)

### Android
- Python 3.9+
- Kivy 2.3.1
- youtube-dl 2021.12.17 (pure Python, for Android compatibility)
- certifi 2026.2.25
- pillow 12.1.1
- requests 2.32.5
- Buildozer 1.5.0+ (for building APK)
- Java 11+ (for Android SDK)

## 🎯 Features Breakdown

### Search Functionality
- Search YouTube videos by keywords
- Paste direct YouTube URLs (videos or playlists)
- Display search results in a grid of cards
- Pagination support for large result sets

### Video Cards
- Thumbnail preview
- Video title (clickable for playlists)
- Channel name and view count
- Duration badge
- Playlist indicator with video count
- MP4 and MP3 download buttons
- Real-time download progress

### Playlist Handling
- View playlists as a single card
- Click "Download" to download entire playlist
- Click title to expand and view all videos
- Download individual videos from playlist
- Navigate back to search results

### Download Options
- **MP4**: Download video in highest quality
- **MP3**: Extract audio only
- Progress tracking with percentage
- Download status indicators
- Error handling with user feedback

## 📥 Download Flow Diagrams

These diagrams show the internal download strategies for each platform and format. Understanding these flows helps explain why certain downloads succeed or fail, and what formats you'll get.

### Android MP3 Download Strategy

```
User clicks "Download as MP3" on Android
                    ↓
   _download_audio() checks if FFmpeg available
                    ↓
         ┌─────────────────────────┐
         │                         │
    FFmpeg found?           FFmpeg not found?
         │                         │
         ↓                         ↓
    Try MP3                    Try M4A (AAC)
    (192kbps)                  (No conversion)
         │                         │
    Success? → Return        Success? → Return
         │                         │
         ↓                         ↓
    Try M4A                     Try WAV
         │                         │
    Success? → Return      Success? → Return
         │                         │
         ↓                         ↓
    Try WAV                     Best Audio
         │                      (Generic)
    Success? → Return              │
         │                 Success? → Return
         ↓
    Best Audio
    (Generic)
         ↓
    ✅ Success (or error)
```

### Android MP4 Download Strategy

```
User clicks "Download as MP4" on Android
                    ↓
    Download video with audio
                    ↓
    Format: bestvideo[ext=mp4]+bestaudio[ext=m4a]
                    ↓
         ┌──────────────────┐
         │                  │
    Format available?   Not available?
         │                  │
         ↓                  ↓
    Download MP4      Try best[ext=mp4]
         │                  │
         ↓                  ↓
    ✅ Success         Try best format
                            │
                            ↓
                       ✅ Success (or error)
```

### Windows MP3 Download Strategy

```
User clicks "Download as MP3" on Windows
                    ↓
    Check FFmpeg availability
                    ↓
         ┌──────────────────┐
         │                  │
    FFmpeg found?      FFmpeg not found?
         │                  │
         ↓                  ↓
    Download Best Audio   ❌ Error Message
         │                "FFmpeg not installed"
         ↓
    Convert to MP3
    (192kbps quality)
         │
         ↓
    ✅ Success
```

### Windows MP4 Download Strategy

```
User clicks "Download as MP4" on Windows
                    ↓
    Download best video + audio
                    ↓
    Format: bestvideo[ext=mp4]+bestaudio[ext=m4a]
                    ↓
    Merge to MP4 (if separate streams)
                    ↓
         ┌──────────────────┐
         │                  │
    Format available?   Not available?
         │                  │
         ↓                  ↓
    Download & Merge    Try best[ext=mp4]
         │                  │
         ↓                  ↓
    ✅ Success         Try best format
                            │
                            ↓
                       ✅ Success (or error)
```

**Key Differences**:
- **Android MP3**: Multiple fallback formats (M4A, WAV, generic audio)
- **Windows MP3**: Requires FFmpeg, fails if not installed
- **Android MP4**: No merge required (youtube-dl handles it)
- **Windows MP4**: Uses yt-dlp's advanced merging capabilities

**What You'll Actually Get**:

| Platform | Format Requested | FFmpeg Installed | What You Get |
|----------|------------------|------------------|--------------|
| Android  | MP3              | ✅ Yes           | `.mp3` file (192kbps) |
| Android  | MP3              | ❌ No            | `.m4a` file (AAC audio) |
| Android  | MP4              | Either           | `.mp4` file (best quality) |
| Windows  | MP3              | ✅ Yes           | `.mp3` file (192kbps) |
| Windows  | MP3              | ❌ No            | ❌ Error message |
| Windows  | MP4              | Either           | `.mp4` file (best quality) |

**Tips**:
- On Android without FFmpeg: You'll get M4A files (AAC audio) - these work in all modern music players
- M4A files can be renamed to `.mp3` for compatibility (though they're not true MP3s)
- For true MP3 format on Android: Include FFmpeg in your buildozer build or install it via Termux

## 🏗️ Architecture

### MVC Pattern

**Models** (`models/`):
- `video_model.py`: Data structures for videos and search results
- `ytdlp_wrapper.py`: Unified wrapper for both yt-dlp (Windows) and youtube-dl (Android)
  - Abstracts platform-specific differences
  - Comprehensive error handling with user-friendly messages
  - Automatic library selection based on what's installed

**Controllers** (`controllers/`):
- `search_controller.py`: Handles search and video info retrieval
- `download_controller.py`: Manages download operations and progress

**Views** (`views/`):
- Windows: `video_card.py` - CustomTkinter video card widget
- Android: `main.kv` - Kivy layout definitions

### Key Design Decisions

1. **Dual Download Libraries**: yt-dlp for Windows (advanced features), youtube-dl for Android (pure Python compatibility)
2. **MVC architecture**: Separates concerns, easier to maintain and test
3. **Card-based UI**: Modern, familiar YouTube-like interface
4. **Async operations**: Threading for downloads and searches to avoid blocking UI
5. **Cross-platform models**: Same business logic for Windows and Android
6. **Library Abstraction**: Wrapper class handles library differences transparently

## 🔄 Migrating from Old Version

The new version (`main.py`) can coexist with the old version. To switch:

1. **Install new requirements**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the new version**:
   ```bash
   python main.py  # instead of main.py
   ```

3. **Update buildozer.spec** (Android):
   - Change `requirements` to include `yt-dlp` instead of `pytube`
   - Update source files to use `main.py` and `main.kv`

## 🐛 Known Issues & Limitations

1. **Platform-Specific Dependencies**: 
   - **Windows**: Uses yt-dlp (more features, latest updates)
   - **Android**: Uses youtube-dl (pure Python, avoids native compilation issues)
   - The models handle both libraries transparently

2. **Audio Download (MP3) on Android**: 
   - Automatically tries multiple formats in order of preference:
     1. **MP3** (with FFmpeg if available) - Best quality
     2. **M4A** (AAC - native YouTube audio format) - No conversion needed ✅
     3. **WAV** (if available) - Uncompressed
     4. **Best Audio Stream** (fallback) - Generic format
   - At least one format will always work without FFmpeg
   - Files can be renamed after download if desired

3. **Windows MP3 Downloads**: 
   - Requires FFmpeg to be installed: https://ffmpeg.org/
   - Download and add to PATH for best results

4. **Android Permissions**: Requires storage and internet permissions
   - Automatically requested on app start

5. **Large Playlists**: May take time to load all video information
   - Progress indication provided

## 🔧 Build Automation & CI/CD

### GitHub Actions Workflows

The project includes automated build pipelines:

- **[.github/workflows/build-windows.yml](.github/workflows/build-windows.yml)**: Builds Windows EXE on push/PR
  - Runs on Windows Server (latest)
  - Builds standalone executable with PyInstaller
  - Artifacts uploaded for release

- **[.github/workflows/build-android.yml](.github/workflows/build-android.yml)**: Builds Android APK on push/PR
  - Runs on Ubuntu (latest)
  - Builds both debug and release APKs with Buildozer
  - Automatically accepts SDK licenses
  - Artifacts uploaded for testing

### Local Build Scripts

Run the build script to create distribution packages:

```bash
# Windows - PowerShell
.\build_all.ps1

# Or build individually:
.\Windows\build_windows.ps1
.\Android\build_android.ps1  # Requires Linux/WSL
```

## 🤝 Contributing

Contributions are welcome! The MVC structure makes it easy to add new features:
- Add new models in `models/`
- Add controller logic in `controllers/`
- Create new UI components in `views/`

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

- **yt-dlp**: Excellent YouTube download library
- **CustomTkinter**: Modern UI for Windows
- **Kivy**: Cross-platform Python framework

---

## 📖 API Documentation

### YTDLPWrapper

Unified wrapper for YouTube download operations. Automatically uses yt-dlp for Windows and youtube-dl for Android.

**Methods**:
- `get_video_info(url)`: Get video/playlist information
- `search_videos(query, max_results)`: Search YouTube with pagination support
- `get_playlist_videos(url)`: Get all videos in a playlist
- `download_video(url, format_type, callbacks)`: Download a video or playlist
- `download_playlist(url, format_type, callbacks)`: Download entire playlist

**Features**:
- Automatic library selection (yt-dlp preferred, youtube-dl fallback)
- **Smart Audio Download** (Android):
  - Tries MP3 with FFmpeg (best quality)
  - Falls back to M4A/AAC (native YouTube format, no conversion)
  - Tries WAV (if available)
  - Downloads best audio stream (generic fallback)
  - At least one format always succeeds
  - User-friendly logging of which format was used
- Comprehensive error handling with user-friendly messages:
  - Private/restricted videos
  - Age-restricted content
  - Region-locked videos
  - Storage space issues
  - FFmpeg availability
  - Network errors
- Progress tracking with callbacks (0-100%)
- Thumbnail extraction with fallback handling
- Support for both MP4 and MP3/audio downloads

**Audio Format Selection** (Android MP3 downloads):
When you request MP3 on Android, the library automatically:
1. Checks for FFmpeg availability
2. If FFmpeg found → converts to high-quality 192kbps MP3
3. If not → downloads as M4A (AAC, native YouTube format)
4. If M4A fails → tries WAV (uncompressed, larger file size)
5. If all fail → downloads best available audio stream
6. Files can be renamed afterwards using a file manager

**Error Handling Examples**:
```python
result = wrapper.download_video(
    url,
    format_type='mp4',
    progress_callback=lambda p: print(f"Progress: {p}%"),
    complete_callback=lambda f: print(f"Downloaded: {f}")
)

if not result:
    # Check console for specific error message
    # e.g., "FFmpeg not installed (required for MP3 downloads)"
    pass
```

### Controllers

**SearchController**:
- Manages async search operations
- Caches search results
- Handles video info retrieval

**DownloadController**:
- Manages concurrent downloads
- Tracks download progress
- Maintains download history

---

For more information, see the inline documentation in the source code.
