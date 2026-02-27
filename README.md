# YouTube Downloader - Enhanced Version

A modern YouTube video and audio downloader for Windows and React Native (Expo) with search capabilities and a YouTube-like interface.

## ✨ New Features

- **🔍 Search Functionality**: Search for videos directly without needing URLs
- **🎨 Modern Card-Based UI**: YouTube-like interface with video thumbnails
- **📑 Playlist Support**: Download entire playlists or individual videos from playlists
- **⚡ yt-dlp Integration**: More reliable and feature-rich than pytube
- **🏗️ MVC Architecture**: Clean, organized code structure for easy maintenance
- **📱 Cross-Platform**: Windows desktop + React Native (Android/iOS)

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
└── Android/React-Native/
     ├── src/
     │   ├── models/          # VideoInfo + SearchResult
     │   ├── controllers/     # Search + download controllers
     │   ├── services/        # youtubei.js wrapper
     │   ├── views/           # React Native UI components
     │   └── utils/           # Formatting helpers
     ├── App.tsx          # Main Expo app
     ├── app.json
     └── package.json
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

### React Native (Expo)

1. **Install Dependencies**:
     ```bash
     cd Android/React-Native
     yarn install
     ```

2. **Run the Expo App**:
     ```bash
     npx expo start
     ```

3. **Download Locations**:
     - Final files: `/storage/emulated/0/Download/YTDownloader/`
     - Temporary files: app cache directory

4. **Android Storage Note (Android 11+)**:
     - Writing to `/storage/emulated/0/Download/` can be restricted by scoped storage.
     - If saving fails, grant storage permission or use a release build with the required permissions.

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

### React Native (Expo)
- Node.js 20+
- Expo SDK 54
- youtubei.js 16.x
- expo-file-system 19.x
- expo-linking 8.x

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
- **MP3**: Download audio-only stream (may be m4a/webm unless an actual mp3 stream exists)
- Progress tracking with percentage
- Download status indicators
- Error handling with user feedback

## 📥 Download Flow Diagrams

These diagrams show the internal download strategies for each platform and format. Understanding these flows helps explain why certain downloads succeed or fail, and what formats you'll get.

### React Native MP3 Download Strategy

```
User clicks "Download as MP3" on React Native
                    ↓
     youtubei.js selects best audio stream
                    ↓
           Download to cache folder
                    ↓
      Move to Download/YTDownloader
                    ↓
✅ Saved as M4A/WebM (or MP3 if stream is mp3)
```

### React Native MP4 Download Strategy

```
User clicks "Download as MP4" on React Native
                    ↓
     youtubei.js selects MP4 stream
                    ↓
      Download to cache folder
                    ↓
      Move to Download/YTDownloader
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
- **React Native MP3**: Saves best available audio (M4A/WebM) without FFmpeg
- **Windows MP3**: Requires FFmpeg, fails if not installed
- **React Native MP4**: Saves best MP4 stream available
- **Windows MP4**: Uses yt-dlp's advanced merging capabilities

**What You'll Actually Get**:

| Platform | Format Requested | FFmpeg Installed | What You Get |
|----------|------------------|------------------|--------------|
| React Native | MP3          | N/A              | `.m4a` or `.webm` audio |
| React Native | MP4          | N/A              | `.mp4` file (best quality) |
| Windows  | MP3              | ✅ Yes           | `.mp3` file (192kbps) |
| Windows  | MP3              | ❌ No            | ❌ Error message |
| Windows  | MP4              | Either           | `.mp4` file (best quality) |

**Tips**:
- React Native MP3 downloads are M4A/WebM; convert externally if you need true MP3

## 🏗️ Architecture

### MVC Pattern

**Models** (`models/`):
- `video_model.py`: Data structures for videos and search results
- `ytdlp_wrapper.py`: Unified wrapper for yt-dlp (Windows)
- `Android/React-Native/src/services/ytdlpWrapper.ts`: youtubei.js wrapper for Expo

**Controllers** (`controllers/`):
- `search_controller.py`: Handles search and video info retrieval
- `download_controller.py`: Manages download operations and progress

**Views** (`views/`):
- Windows: `video_card.py` - CustomTkinter video card widget
- React Native: `VideoCard.tsx` - Expo UI component

### Key Design Decisions

1. **Dual Download Libraries**: yt-dlp for Windows, youtubei.js for React Native
2. **MVC architecture**: Separates concerns, easier to maintain and test
3. **Card-based UI**: Modern, familiar YouTube-like interface
4. **Async operations**: Threading for downloads and searches to avoid blocking UI
5. **Cross-platform models**: Same business logic for Windows and React Native
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


## 🐛 Known Issues & Limitations

1. **Platform-Specific Dependencies**: 
   - **Windows**: Uses yt-dlp (more features, latest updates)
   - **React Native**: Uses youtubei.js (pure JS, Expo compatible)
   - The models handle both libraries transparently

2. **Audio Download (MP3) on React Native**: 
   - Uses the best available audio stream without FFmpeg
   - Saves M4A/WebM audio depending on the stream
   - Convert externally if you need true MP3 files

3. **Windows MP3 Downloads**: 
   - Requires FFmpeg to be installed: https://ffmpeg.org/
   - Download and add to PATH for best results

4. **Large Playlists**: May take time to load all video information
   - Progress indication provided

## 🔧 Build Automation & CI/CD

### GitHub Actions Workflows

The project includes automated build pipelines:

- **[.github/workflows/build-windows.yml](.github/workflows/build-windows.yml)**: Builds Windows EXE on push/PR
  - Runs on Windows Server (latest)
  - Builds standalone executable with PyInstaller
  - Artifacts uploaded for release

- **[.github/workflows/build-android.yml](.github/workflows/build-android.yml)**: Expo checks for the React Native app
     - Runs on Ubuntu (latest)
     - Installs Yarn dependencies
     - Runs Expo diagnostics and TypeScript checks

### Local Build Scripts

Run the build script to create distribution packages:

```bash
# Windows - PowerShell
.\build_all.ps1

# Or build individually:
.\Windows\build_windows.ps1
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
- **youtubei.js**: YouTube data API wrapper for React Native

---

## 📖 API Documentation

### YTDLPWrapper

Unified wrapper for YouTube download operations. Uses yt-dlp for Windows and youtubei.js for React Native.

**Methods**:
- `get_video_info(url)`: Get video/playlist information
- `search_videos(query, max_results)`: Search YouTube with pagination support
- `get_playlist_videos(url)`: Get all videos in a playlist
- `download_video(url, format_type, callbacks)`: Download a video or playlist
- `download_playlist(url, format_type, callbacks)`: Download entire playlist

**Features**:
- Automatic library selection per platform
- **Smart Audio Download** (React Native):
     - Saves best available audio stream (M4A/WebM)
     - No FFmpeg required in Expo
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

**Audio Format Selection** (React Native audio downloads):
When you request MP3 in the Expo app, the wrapper:
1. Picks the best available audio stream
2. Saves the stream as M4A/WebM (no FFmpeg)
3. You can convert the file externally if you need true MP3

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
