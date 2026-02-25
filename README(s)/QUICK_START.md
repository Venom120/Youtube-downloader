# Quick Start Guide - New YouTube Downloader

This guide will get you up and running with the new YouTube Downloader in minutes.

## 🚀 Windows Quick Start

### 1. Install Python (if not already installed)
- Download Python 3.8+ from https://python.org
- During installation, check "Add Python to PATH"

### 2. Install Dependencies
Open Command Prompt or PowerShell in the `Windows` folder:

```powershell
cd Windows
pip install -r requirements.txt
```

### 3. Run the Application
```powershell
python main.py
```

### 4. Start Using

**To Search for Videos**:
1. Type a search query in the top search bar (e.g., "python tutorial")
2. Click 🔍 Search
3. Browse video cards and click MP4 or MP3 to download

**To Download from URL**:
1. Copy a YouTube video or playlist URL
2. Paste in the search bar
3. The video will appear as a card
4. Click MP4 or MP3 to download

**To Browse a Playlist**:
1. Search for or paste a playlist URL
2. Click the playlist title to see all videos
3. Download individual videos or use the playlist card to download all

Downloads go to: `C:\Users\YourName\Downloads\`

---

## 📱 Android Quick Start

### 1. Prerequisites
- Linux or WSL2 (for building APK)
- Python 3.8+
- Java JDK 8 or 11
- Android SDK

### 2. Install Buildozer
```bash
pip install buildozer
pip install cython
```

### 3. Navigate to Android Folder
```bash
cd Android
```

### 4. Build APK

**First time** (downloads dependencies, takes 30+ minutes):
```bash
buildozer android debug
```

**Subsequent builds**:
```bash
buildozer android debug
```

### 5. Install on Device

Connect your Android device via USB and enable USB debugging:

```bash
adb install bin/YTDownloader-*.apk
```

Or transfer the APK file from `Android/bin/` folder to your phone and install manually.

### 6. Grant Permissions

On first launch:
- Allow **Storage** permission (to save downloads)
- Allow **Internet** permission (automatic)

Downloads go to: `/storage/emulated/0/Download/`

---

## 🎨 UI Overview

### Main Screen

```
┌─────────────────────────────────────────┐
│  📺 YouTube Downloader                  │  ← Header
├─────────────────────────────────────────┤
│  [Search YouTube or paste URL...] [🔍] │  ← Search Bar
├─────────────────────────────────────────┤
│  ← Back    |  Status: Found 10 results  │  ← Navigation
├─────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Video 1 │  │ Video 2 │  │ Video 3 │  │  ← Video Cards
│  │  [MP4]  │  │  [MP4]  │  │  [MP4]  │  │    (responsive grid)
│  │  [MP3]  │  │  [MP3]  │  │  [MP3]  │  │
│  └─────────┘  └─────────┘  └─────────┘  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Video 4 │  │ Video 5 │  │ Video 6 │  │
│  └─────────┘  └─────────┘  └─────────┘  │
└─────────────────────────────────────────┘
```

### Video Card Detail

```
┌──────────────────────────────┐
│      [Thumbnail Image]       │  ← Video thumbnail
│         📑 5 videos           │  ← Badge (playlist/duration)
├──────────────────────────────┤
│  Video Title Goes Here...    │  ← Clickable title (if playlist)
│  Channel Name • 1.2M views   │  ← Channel & views
├──────────────────────────────┤
│   [📥 MP4]     [🎵 MP3]      │  ← Download buttons
│   ▓▓▓▓▓░░░░░░░░░░   45%     │  ← Progress (when downloading)
└──────────────────────────────┘
```

---

## 💡 Common Use Cases

### Download a Single Video

1. **Copy YouTube URL**:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

2. **Paste in search bar**

3. **Click MP4 (video) or MP3 (audio only)**

4. **Wait for download to complete** (progress shown)

### Search and Download

1. **Type search query**: "how to make a game"

2. **Click 🔍 Search**

3. **Browse results** in card grid

4. **Click MP4/MP3** on desired video

### Download Entire Playlist

1. **Paste playlist URL**:
   ```
   https://www.youtube.com/playlist?list=...
   ```

2. **Playlist appears as one card** with "📑 X videos" badge

3. **Click MP4 or MP3 on the playlist card**

4. **All videos download sequentially**

### Download Individual Videos from Playlist

1. **Paste or search for playlist**

2. **Click the playlist TITLE** (blue, clickable)

3. **View all videos** in the playlist

4. **Click MP4/MP3** on individual videos you want

5. **Click ← Back** to return to search

---

## ⚙️ Settings & Configuration

### Change Download Location

**Windows**: Edit `main.py`
```python
# Line ~38
self.download_controller = DownloadController()

# Change to:
self.download_controller = DownloadController("D:/MyDownloads/")
```

**Android**: Downloads always go to `/Download/` folder (system default)

### Adjust Number of Search Results

Edit `main.py`:
```python
# Windows: Line ~203
# Android: Line ~184
self.search_controller.search_videos(
    query,
    max_results=20,  # Change this number
    ...
)
```

### Change Video Quality

Edit `Windows/models/ytdlp_wrapper.py` or `Android/models/ytdlp_wrapper.py`:

```python
# Line ~170 (MP4 download)
'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',

# For specific quality, use:
'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',  # 720p max
```

---

## 🆘 Troubleshooting

### "No module named 'yt_dlp'"
```bash
pip install yt-dlp
```

### MP3 downloads fail
Install FFmpeg:
- **Windows**: Download from https://ffmpeg.org/ and add to PATH
- **Android**: Included automatically in APK build

### "Permission denied" on Android
- Go to Settings > Apps > YTDownloader > Permissions
- Enable Storage permission

### Videos not playing after download
The file is fine! Some players don't support all formats. Try:
- **Windows**: VLC Media Player
- **Android**: VLC for Android or MX Player

### Search returns no results
- Check internet connection
- Try different search terms
- Make sure query isn't too specific

### Download is very slow
- Check your internet speed
- Large videos (1080p, 4K) take longer
- Try closing other downloads

---

## 🎓 Tips & Tricks

### Keyboard Shortcuts

**Windows**:
- `Enter` in search bar = Start search
- `Ctrl+V` in search bar = Paste URL

### Batch Downloads

To download multiple videos:
1. Search for videos
2. Click MP4/MP3 on multiple cards
3. Downloads run concurrently

### Best Practices

✅ **Do**:
- Use specific search terms
- Check video duration before downloading
- Download during off-peak hours for faster speeds
- Keep the app updated

❌ **Don't**:
- Download copyrighted content without permission
- Download hundreds of videos at once (may get rate limited)
- Close app while downloads are in progress

---

## 📊 Feature Comparison: Old vs New

| Action | Old Version | New Version |
|--------|-------------|-------------|
| Download video | Paste URL → Click button | Same + Can search |
| Find videos | Manual search on YouTube | Built-in search |
| Playlists | All or nothing | Individual or all |
| UI | Simple list | Modern cards with thumbnails |
| Progress | Basic bar | Detailed percentage |

---

## 🔗 Useful Links

- **yt-dlp**: https://github.com/yt-dlp/yt-dlp
- **Report Issues**: [Your GitHub/Issues Page]
- **FFmpeg Download**: https://ffmpeg.org/download.html
- **Kivy Documentation**: https://kivy.org/doc/stable/

---

## ✅ You're All Set!

The new YouTube Downloader is ready to use. Enjoy the enhanced features and modern interface!

For more detailed information, see:
- `README.md` - Complete documentation
- `MIGRATION_GUIDE.md` - Migrating from old version
- Code comments - Inline documentation

Happy downloading! 🎉
