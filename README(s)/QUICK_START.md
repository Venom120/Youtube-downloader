# Quick Start Guide - YouTube Downloader

Get started with the YouTube Downloader in minutes! Choose your platform:

## 📋 Table of Contents

- [Windows Desktop App](#-windows-desktop-app) (Standalone)
- [Mobile App (Android/iOS)](#-mobile-app-androidios) (Requires Backend Server)
- [Setup Backend Server](#step-1-setup-backend-server)
- [Setup Mobile App](#step-2-setup-mobile-app)

---

## 🖥️ Windows Desktop App

The Windows app is **standalone** - no server required!

### Prerequisites
- Windows 10 or later
- Python 3.10+ (with pip)

### Installation

1. **Install Python** (if not already installed)
   - Download from https://python.org
   - ✅ Check "Add Python to PATH" during installation

2. **Install Dependencies**
   
   Open PowerShell or Command Prompt:
   ```powershell
   cd Windows
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (Optional, for MP3 downloads)
   - Download from https://ffmpeg.org/download.html
   - Extract and add to PATH
   - Or use chocolatey: `choco install ffmpeg`

### Running the App

```powershell
cd Windows
python main.py
```

### Usage

**Search for Videos**:
1. Type search query in the search bar (e.g., "python tutorial")
2. Click 🔍 Search button
3. Browse results as video cards

**Download Video**:
1. Find your video in the search results
2. Click **MP4** button for video download
3. Click **MP3** button for audio-only (requires FFmpeg)
4. Watch progress bar for download status

**Direct URL Download**:
1. Copy YouTube video URL
2. Paste in search bar
3. Video appears as a card
4. Click MP4 or MP3 to download

**Downloads Location**: `C:\Users\YourName\Downloads\`

---

## 📱 Mobile App (Android/iOS)

The mobile app uses a **client-server architecture**:
- **Backend Server**: Handles downloads using yt-dlp
- **Mobile App**: React Native UI connects to backend

### Step 1: Setup Backend Server

You need a running backend server first. Choose an option:

### Step 1: Setup Backend Server

You need a running backend server first. Choose an option:

#### Option A: Docker (Recommended - Easiest)

**Prerequisites**: Docker and Docker Compose installed

```bash
# Navigate to backend directory
cd Android/Python

# Start server with docker-compose
docker-compose up -d

# Check if running
docker ps
```

Server running at: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

#### Option B: Manual Setup (Development)

**Prerequisites**: Python 3.11+, FFmpeg installed

```bash
# Navigate to backend directory
cd Android/Python

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "DOWNLOAD_DIR=/app/downloads" > .env
echo "ALLOWED_APP_ID=com.venom120.ytdownloader" >> .env

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Option C: Cloud Deployment (Production)

Deploy to your preferred cloud platform:

**Heroku**:
```bash
heroku create ytdownloader-api
heroku config:set ALLOWED_APP_ID=com.venom120.ytdownloader
git push heroku main
```

**DigitalOcean/AWS/Other VPS**:
1. Setup VPS with Docker
2. Clone repository
3. Run `docker-compose up -d`
4. Configure firewall for port 8000
5. Setup domain and SSL certificate

### Step 2: Setup Mobile App

#### Prerequisites
- Node.js 20+
- npm or yarn
- Backend server running

#### Installation

1. **Navigate to React Native directory**:
   ```bash
   cd Android/React-Native
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Configure backend connection**:
   
   Create `.env` file in `Android/React-Native/`:
   ```env
   # For local testing (use your computer's IP, not localhost)
   BACKEND_URL=http://192.168.1.100:8000
   WS_URL=ws://192.168.1.100:8000
   APP_ID=com.venom120.ytdownloader
   
   # For production
   # BACKEND_URL=https://your-domain.com
   # WS_URL=wss://your-domain.com
   # APP_ID=com.venom120.ytdownloader
   ```
   
   **Finding your IP**:
   - Windows: `ipconfig` → Look for IPv4 Address
   - Mac/Linux: `ifconfig` or `ip addr` → Look for inet address

4. **Start the app**:
   ```bash
   npx expo start
   ```

5. **Run on device**:
   - Scan QR code with Expo Go app (Android/iOS)
   - Or press `a` for Android emulator
   - Or press `i` for iOS simulator (Mac only)

#### Usage

**Search for Videos**:
1. Open the app
2. Type search query in search bar
3. Tap search button
4. Browse video cards

**Download Video**:
1. Find your video
2. Tap **MP4** for video or **MP3** for audio
3. Watch real-time progress updates
4. File saves to: `/storage/emulated/0/Download/YTDownloader/` (Android)

**Grant Permissions**:
- On first download, allow storage permission
- Required for saving files to device

---

## 🎯 Tips & Tricks

### For All Platforms

**Search Tips**:
- Use specific keywords for better results
- Paste YouTube URLs directly
- Search for playlists too

**Download Tips**:
- MP4 downloads video with audio
- MP3 downloads audio only (requires FFmpeg on backend)
- Check file size before downloading
- Internet connection required throughout download

### For Windows

**Performance**:
- Downloads are single-threaded per video
- Multiple videos can download simultaneously
- Progress updates in real-time

**Troubleshooting**:
- If MP3 doesn't work: Install FFmpeg
- If search fails: Check internet connection
- If app slow: Close and restart

### For Mobile

**Network**:
- Backend must be accessible from your device
- Use local IP for testing, domain for production
- WebSocket connection required for progress

**Battery**:
- Keep app in foreground during downloads
- Background downloads may pause
- Consider downloading on Wi-Fi

**Storage**:
- Check available storage before large downloads
- Grant storage permission when prompted
- Files save to Downloads folder

---

## 🔍 Testing Your Setup

### Test Windows App

1. Run `python main.py`
2. Search for "test video"
3. Try downloading a short video
4. Check downloads folder for file

### Test Backend Server

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test search (with authentication)
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -H "X-App-Id: com.venom120.ytdownloader" \
  -d '{"query": "test", "maxResults": 5}'

# View API documentation
# Open browser: http://localhost:8000/docs
```

### Test Mobile App

1. Ensure backend is running
2. Start Expo app
3. Check connection status in app
4. Try searching for videos
5. Test a small download

---

## 🐛 Common Issues

### Windows Issues

**"python not found"**:
- Install Python and add to PATH
- Restart terminal after installing

**"Module not found"**:
- Run `pip install -r requirements.txt`
- Check you're in the Windows directory

**"FFmpeg not found"**:
- Install FFmpeg from ffmpeg.org
- Add to system PATH
- Restart terminal

### Backend Issues

**"Port 8000 already in use"**:
- Stop other applications using port 8000
- Or change port in docker-compose.yml

**"FFmpeg not found in container"**:
- Dockerfile includes FFmpeg
- Rebuild container: `docker-compose build --no-cache`

**"Database/connection error"**:
- Check Docker is running
- Restart containers: `docker-compose restart`

### Mobile Issues

**"Cannot connect to server"**:
- Check backend is running
- Use IP address, not `localhost`
- Ensure device on same network (for local testing)
- Check firewall settings

**"Authentication failed"**:
- Verify APP_ID matches backend configuration
- Check .env file is properly loaded

**"WebSocket connection failed"**:
- Verify WS_URL is correct  
- Check backend WebSocket endpoint is working
- Try reconnecting

**"Storage permission denied"**:
- Grant storage permission in Android settings
- Restart app after granting permission

---

## 📚 Next Steps

- **Learn More**: Read the [main README](../README.md)
- **Build Apps**: See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)
- **Deploy Backend**: Check [Android/Python/README.md](../Android/Python/README.md)
- **Technical Details**: Read [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

**Need Help?** 
- Check documentation
- Review error messages
- Open GitHub issue with details

**Happy Downloading!** 🎉
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
