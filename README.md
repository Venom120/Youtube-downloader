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

### Android

1. **Install Dependencies**:
   ```bash
   cd Android
   pip install -r requirements.txt
   ```

2. **Run on Desktop (for testing)**:
   ```bash
   python main.py
   ```

3. **Build APK with Buildozer**:
   ```bash
   buildozer android debug
   ```

## 📋 Requirements

### Windows
- Python 3.8+
- yt-dlp
- customtkinter
- pillow
- requests

### Android
- Python 3.8+
- Kivy 2.0+
- yt-dlp
- certifi
- pillow
- requests
- Buildozer (for building APK)

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

## 🏗️ Architecture

### MVC Pattern

**Models** (`models/`):
- `video_model.py`: Data structures for videos and search results
- `ytdlp_wrapper.py`: Wrapper around yt-dlp for all download operations

**Controllers** (`controllers/`):
- `search_controller.py`: Handles search and video info retrieval
- `download_controller.py`: Manages download operations and progress

**Views** (`views/`):
- Windows: `video_card.py` - CustomTkinter video card widget
- Android: `main.kv` - Kivy layout definitions

### Key Design Decisions

1. **yt-dlp over pytube**: More reliable, better maintained, works on Android
2. **MVC architecture**: Separates concerns, easier to maintain and test
3. **Card-based UI**: Modern, familiar YouTube-like interface
4. **Async operations**: Threading for downloads and searches to avoid blocking UI
5. **Cross-platform models**: Same business logic for Windows and Android

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

1. **FFmpeg Required**: MP3 downloads require FFmpeg to be installed
   - Windows: Download from https://ffmpeg.org/
   - Android: Included in buildozer build

2. **Android Permissions**: Requires storage and internet permissions
   - Automatically requested on app start

3. **Large Playlists**: May take time to load all video information
   - Progress indication provided

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

Main wrapper for yt-dlp operations.

**Methods**:
- `get_video_info(url)`: Get video/playlist information
- `search_videos(query, max_results)`: Search YouTube
- `get_playlist_videos(url)`: Get all videos in a playlist
- `download_video(url, format_type, callbacks)`: Download a video
- `download_playlist(url, format_type, callbacks)`: Download a playlist

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
