# YouTube Downloader - Client-Server Architecture

A modern YouTube video and audio downloader with multiple deployment options:
- **Windows Desktop** - Standalone application with CustomTkinter UI
- **Backend API Server** - FastAPI server with yt-dlp for mobile clients
- **React Native Mobile** - Cross-platform mobile app (Android/iOS)

## 🏗️ Architecture Overview

### Client-Server Model (Mobile)
```
React Native App (Client)
        ↓ REST API + WebSocket
FastAPI Backend (Server)
        ↓ yt-dlp
    YouTube
```

### Standalone (Desktop)
```
Windows App (CustomTkinter)
        ↓ yt-dlp
    YouTube
```

## ✨ Features

- **🔍 Video Search** - Search YouTube videos without URLs
- **🎨 Modern UI** - YouTube-like card interface with thumbnails
- **📑 Playlist Support** - Download entire playlists or individual videos
- **⚡ Real-time Progress** - WebSocket updates for mobile downloads
- **🔐 App Authentication** - Secure backend API with app ID validation
- **🎯 Dual Architecture** - Standalone desktop or client-server for mobile
- **📥 Multiple Formats** - MP4 video and MP3 audio downloads

## 📁 Project Structure

```
Youtube-downloader/
├── Windows/                      # 🖥️ Standalone Desktop Application
│   ├── models/                   # Data models and business logic
│   │   ├── video_model.py        # VideoInfo and SearchResult classes
│   │   └── ytdlp_wrapper.py      # yt-dlp integration wrapper
│   ├── controllers/              # Application controllers
│   │   ├── download_controller.py
│   │   └── search_controller.py
│   ├── views/                    # CustomTkinter UI components
│   │   └── video_card.py         # Video card widget
│   ├── main.py                   # Main application entry point
│   └── requirements.txt          # Python dependencies
│
├── Android/
│   ├── Backend/                   # 🔧 Backend API Server
│   │   ├── app/
│   │   │   ├── main.py           # FastAPI application
│   │   │   ├── models/
│   │   │   │   └── schemas.py    # Pydantic models
│   │   │   ├── routes/
│   │   │   │   ├── youtube.py    # REST API endpoints
│   │   │   │   └── websocket.py  # WebSocket for progress
│   │   │   ├── services/
│   │   │   │   └── ytdlp_service.py  # yt-dlp wrapper
│   │   │   └── middleware/
│   │   │       └── auth.py       # App ID authentication
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── requirements.txt
│   │
│   └── React-Native/             # 📱 Mobile Client Application
│       ├── src/
│       │   ├── api/              # Backend API client
│       │   │   ├── backendClient.ts  # HTTP client
│       │   │   ├── websocket.ts      # WebSocket client
│       │   │   ├── youtube.ts        # YouTube API calls
│       │   │   └── config.ts         # API configuration
│       │   ├── controllers/      # Business logic
│       │   │   ├── downloadController.ts
│       │   │   └── searchController.ts
│       │   ├── models/
│       │   │   └── videoModel.ts # Video data models
│       │   ├── services/
│       │   │   └── ytdlWrapper-server.ts  # Backend wrapper
│       │   ├── views/            # React Native UI
│       │   │   ├── VideoCard.tsx
│       │   │   └── DownloadsList.tsx
│       │   └── utils/
│       │       └── format.ts     # Formatting helpers
│       ├── App.tsx               # Main React Native app
│       ├── app.json
│       └── package.json
│
└── README(s)/                     # 📚 Documentation
    ├── BUILD_INSTRUCTIONS.md
    ├── IMPLEMENTATION_SUMMARY.md
    └── QUICK_START.md
```

## 🚀 Quick Start

### Option 1: Windows Standalone Desktop App

The Windows app runs independently without needing a backend server.

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

### Option 2: Mobile App with Backend Server

The React Native mobile app requires a backend server to handle downloads.

#### Step 1: Start the Backend Server

**Using Docker (Recommended)**:
```bash
cd Android/Python
docker-compose up --build
```

**Or Manual Setup**:
```bash
cd Android/Python
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

#### Step 1.5: Setup Cookie Authentication (Optional but Recommended)

For better reliability and access to restricted content, configure YouTube cookies:

**Quick Setup**:
1. Export cookies from your browser using a browser extension:
   - **Edge/Chrome**: Install "Get cookies.txt LOCALLY" extension
   - **Firefox**: Install "cookies.txt" extension

2. Open browser in **Incognito/Private mode** and login to YouTube

3. Export cookies as `cookies.txt` (Netscape format)

4. Copy to backend cookies folder:
   ```bash
   # Local development
   cp cookies.txt Android/Backend/cookies/
   
   # Production (EC2)
   scp cookies.txt ubuntu@YOUR_EC2_IP:/home/ubuntu/YTDownloader/Android/Backend/cookies/
   ```

5. Restart the backend server

**Benefits**:
- ✅ Access age-restricted and member-only content  
- ✅ Higher rate limits (~2000 vs ~300 videos/hour)
- ✅ Reduced throttling and better reliability

**Detailed guide**: See [Backend Cookie Authentication](Android/Backend/README.md#-cookie-authentication-setup-recommended)

#### Step 2: Configure & Run React Native App

1. **Create `.env` file** in `Android/React-Native/`:
   ```env
   BACKEND_URL=http://YOUR_SERVER_IP:8000
   WS_URL=ws://YOUR_SERVER_IP:8000
   APP_ID=com.venom120.ytdownloader
   ```

2. **Install Dependencies**:
   ```bash
   cd Android/React-Native
   npm install
   ```

3. **Run the App**:
   ```bash
   npx expo start
   ```

4. **Build for Production**:
   ```bash
   # Android APK
   eas build --platform android --profile production
   
   # iOS
   eas build --platform ios --profile production
   ```

## 📋 Requirements

### Windows Desktop App (Standalone)
- Python 3.10+
- yt-dlp 2024.x+
- customtkinter 5.2.2+
- pillow 12.1.1+
- requests 2.32.5+
- FFmpeg (for MP3 downloads)

### Backend Server (FastAPI)
- Python 3.11+
- FastAPI 0.115.x
- yt-dlp 2024.x+
- uvicorn 0.34.x
- python-dotenv 1.0.x
- FFmpeg (for audio extraction)
- Docker (optional, recommended)

### React Native Mobile App
- Node.js 20+
- Expo SDK 52
- React Native 0.76.x
- TypeScript 5.x
- Axios 1.7.x
- Backend server running and accessible

## 🔧 Backend API Documentation

The FastAPI backend provides RESTful endpoints and WebSocket support for real-time updates.

### REST Endpoints

**POST `/api/search`** - Search for YouTube videos
```json
Request:
{
  "query": "python tutorial",
  "maxResults": 20
}

Response:
{
  "videos": [
    {
      "videoId": "xxx",
      "title": "...",
      "thumbnailUrl": "...",
      "duration": 600,
      "channel": "...",
      "viewCount": 12345,
      "url": "..."
    }
  ],
  "query": "python tutorial",
  "page": 1,
  "hasMore": false
}
```

**POST `/api/video-info`** - Get video information
```json
Request:
{
  "url": "https://youtube.com/watch?v=VIDEO_ID"
}

Response: VideoInfo object
```

**POST `/api/download`** - Initiate download
```json
Request:
{
  "url": "https://youtube.com/watch?v=VIDEO_ID",
  "format": "mp4"  // or "mp3"
}

Response:
{
  "downloadId": "uuid",
  "videoId": "xxx",
  "downloadUrl": "/api/download-file/{downloadId}",
  "fileName": "video.mp4",
  "fileSize": 12345678,
  "format": "mp4"
}
```

**GET `/api/download-status/{downloadId}`** - Check download status

**GET `/api/download-file/{downloadId}`** - Download completed file

**POST `/api/cancel-download`** - Cancel active download

### WebSocket Endpoint

**WS `/ws`** - Real-time download progress

Connected clients receive progress updates:
```json
{
  "type": "download_progress",
  "downloadId": "uuid",
  "status": "downloading",
  "progress": 45.5,
  "downloadedBytes": 5000000,
  "totalBytes": 11000000,
  "speed": "1.2 MB/s",
  "eta": "5s"
}
```

### Authentication

All API requests require an `X-App-Id` header with a valid app identifier:
```
X-App-Id: com.venom120.ytdownloader
```

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

### React Native (Client-Server Architecture)

**Search & Video Info:**
```
React Native App
        ↓ HTTP POST /api/search
Backend Server (FastAPI)
        ↓ yt-dlp
    YouTube API
        ↓ Video metadata
Backend Server
        ↓ JSON Response
React Native App (displays cards)
```

**Download Flow:**
```
User clicks "Download as MP4/MP3"
        ↓
React Native sends POST /api/download
        ↓
Backend Server initiates yt-dlp download
        ↓
WebSocket sends progress updates
        ↓
React Native displays real-time progress
        ↓
Backend completes download
        ↓
WebSocket sends completion event
        ↓
React Native downloads file from /api/download-file/{id}
        ↓
File saved to device storage
        ↓
✅ Complete
```

**Download Strategy (Server-Side with yt-dlp):**
- **MP4**: Downloads best quality video+audio streams and merges
- **MP3**: Uses FFmpeg to extract audio and convert to 192kbps MP3
- All processing happens on the server
- Client receives the completed file via HTTP download

### Windows (Standalone Architecture)

**Direct yt-dlp Integration:**
```
User clicks "Download as MP4/MP3"
        ↓
Windows App calls yt-dlp directly
        ↓ (threading for non-blocking UI)
yt-dlp downloads from YouTube
        ↓ Progress callbacks
Windows App updates UI in real-time
        ↓
File saved to local Downloads folder
        ↓
✅ Complete
```

**Download Strategy:**
- **MP4**: `bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best`
- **MP3**: Requires FFmpeg, extracts audio and converts to MP3 (192kbps)
- No server required - all processing local
- Direct file system access

## 🔄 Architecture Comparison

| Feature | Windows (Standalone) | React Native + Backend |
|---------|---------------------|------------------------|
| **Architecture** | Monolithic desktop app | Client-server model |
| **Download Engine** | yt-dlp (local) | yt-dlp (server) |
| **Progress Updates** | Threading + callbacks | WebSocket real-time |
| **File Storage** | Local downloads folder | Server → Device transfer |
| **Authentication** | Not required | App ID header required |
| **FFmpeg** | Optional (needed for MP3) | Required on server |
| **Network** | Direct to YouTube | Via backend API |
| **Offline Capability** | Yes (after download) | Requires server connection |

## 🏗️ Architecture

### Client-Server Model (Mobile)

**Backend Server** (`Android/Python/`):
- FastAPI framework with async/await support
- yt-dlp service for YouTube interactions
- WebSocket manager for real-time updates
- Pydantic models for request/response validation
- Middleware for app authentication
- Docker containerization for easy deployment

**React Native Client** (`Android/React-Native/`):
- TypeScript with React Native
- Expo framework for cross-platform support
- Axios for HTTP requests
- WebSocket client for progress updates
- MVC architecture:
  - **Models**: `videoModel.ts` - Data structures
  - **Controllers**: Business logic for search/download
  - **Views**: React components for UI
  - **Services**: `ytdlWrapper-server.ts` - Backend API wrapper

### Standalone Model (Desktop)

**Windows Application** (`Windows/`):
- CustomTkinter for modern UI
- Direct yt-dlp integration (no server)
- Threading for async operations
- MVC architecture:
  - **Models**: Data structures and yt-dlp wrapper
  - **Controllers**: Search and download logic
  - **Views**: UI components and video cards
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

## 🐛 Known Issues & Limitations

1. **Backend Server Required for Mobile**: 
   - React Native app requires a running backend server
   - Server must be accessible over network (not localhost on mobile devices)
   - Use ngrok, your VPS, or local network IP for testing

2. **FFmpeg Requirement**: 
   - Backend server requires FFmpeg for MP3 audio extraction
   - Windows standalone app needs FFmpeg for MP3 downloads
   - Install from https://ffmpeg.org/

3. **WebSocket Connections**: 
   - Mobile devices may disconnect WebSocket on app backgrounding
   - Downloads continue on server, but progress updates may be missed
   - Reconnection logic handles resuming progress updates

4. **File Size Limits**: 
   - Large video downloads may timeout depending on network
   - Server storage capacity determines maximum concurrent downloads

5. **Large Playlists**: 
   - May take time to load all video information
   - Progress indication provided
   - Backend processes playlists sequentially

## 🌐 Deployment

### Backend Server Deployment Options

**1. Docker (Recommended)**
```bash
cd Android/Python
docker-compose up -d
```

**2. Local Server**
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**3. Cloud Deployment (VPS/Cloud Platform)**
- Deploy Docker container to AWS, DigitalOcean, Azure, etc.
- Ensure FFmpeg is installed
- Configure firewall to allow ports 8000 (HTTP) and WebSocket
- Set environment variables in `.env`:
  ```env
  DOWNLOAD_DIR=/app/downloads
  ALLOWED_APP_IDS=com.venom120.ytdownloader
  ```

**4. Reverse Proxy (Production)**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Mobile App Configuration

Update `.env` in React Native app with your backend URL:
```env
BACKEND_URL=https://your-domain.com
WS_URL=wss://your-domain.com
APP_ID=com.venom120.ytdownloader
```

## 🔧 Build Automation & CI/CD

### GitHub Actions Workflows

The project includes automated build pipelines:

- **Build Windows EXE**: Automated PyInstaller builds
- **Build Mobile App**: EAS builds for Android/iOS (when configured)
- **Docker Image**: Backend server containerization

### Local Build Scripts

```bash
# Windows Desktop App
cd Windows
python -m PyInstaller main.spec

# Backend Docker Image
cd Android/Python
docker build -t ytdownloader-backend .

# React Native App
cd Android/React-Native
eas build --platform android --profile production
```

## 🤝 Contributing

Contributions are welcome! The modular architecture makes it easy to add new features:

**Backend Server** (`Android/Python/`):
- Add new API endpoints in `app/routes/`
- Extend services in `app/services/`
- Add data models in `app/models/schemas.py`

**React Native Client** (`Android/React-Native/`):
- Add UI components in `src/views/`
- Extend controllers in `src/controllers/`
- Add API methods in `src/api/`

**Windows App** (`Windows/`):
- Add models in `models/`
- Add controller logic in `controllers/`
- Create UI components in `views/`

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **FastAPI**: Modern Python web framework
- **React Native & Expo**: Cross-platform mobile development
- **CustomTkinter**: Modern UI library for Windows

---

## 📚 More Documentation

For detailed information, see:
- [Quick Start Guide](README(s)/QUICK_START.md) - Get started quickly
- [Build Instructions](README(s)/BUILD_INSTRUCTIONS.md) - Building executables and APKs
- [Implementation Summary](README(s)/IMPLEMENTATION_SUMMARY.md) - Technical implementation details
- [Backend API README](Android/Python/README.md) - FastAPI backend documentation

---

For more information, see the inline documentation in the source code.
