# YouTube Downloader Backend API

FastAPI backend server for YouTube video downloading using yt-dlp with WebSocket support for real-time progress updates.

## 🏗️ Architecture

This backend server is designed to work with the React Native mobile client app, providing a complete client-server architecture for YouTube downloading.

```
React Native Client (Android/React-Native/)
        ↓ HTTP REST API + WebSocket
FastAPI Backend Server (Android/Python/)
        ↓ yt-dlp library
    YouTube
```

## Features

- ✅ **Video Search** - Search YouTube videos using yt-dlp
- ✅ **Video Info** - Get detailed video metadata
- ✅ **Download Videos** - MP4 format with quality selection
- ✅ **Download Audio** - MP3 extraction with FFmpeg
- ✅ **Real-time Progress** - WebSocket updates to clients
- ✅ **App Authentication** - Secure API access with app ID validation
- ✅ **Background Downloads** - Async processing with threading
- ✅ **Resume/Cancel** - Download control capabilities
- ✅ **Docker Support** - Easy containerized deployment
- ✅ **CORS Enabled** - Configured for mobile client access

## Tech Stack

- **FastAPI** - Modern async Python web framework
- **yt-dlp** - Powerful YouTube download library
- **WebSockets** - Real-time bidirectional communication
- **Docker** - Containerization for easy deployment
- **FFmpeg** - Media processing for audio extraction
- **Pydantic** - Request/response validation
- **Uvicorn** - ASGI server

## Quick Start

### Using Docker Compose (Recommended)

```bash
cd backend
docker-compose up --build
```

The server will be available at `http://localhost:8000`

### Manual Installation

1. **Install Python 3.11+**

2. **Install FFmpeg**
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### REST API

#### POST `/api/search`
Search for videos
```json
{
  "query": "music video",
  "maxResults": 20
}
```

#### POST `/api/video-info`
Get video information
```json
{
  "url": "https://youtube.com/watch?v=VIDEO_ID"
}
```

#### POST `/api/download`
Initiate video download
```json
{
  "url": "https://youtube.com/watch?v=VIDEO_ID",
  "format": "mp4"  // or "mp3"
}
```

#### GET `/api/download-status/{download_id}`
Get download status

#### GET `/api/download-file/{download_id}`
Download the completed file

#### POST `/api/cancel-download`
Cancel an active download
```json
{
  "downloadId": "uuid"
}
```

### WebSocket

Connect to `ws://localhost:8000/ws?app_id=com.venom120.ytdownloader`

**Client Messages:**
- `subscribe` - Subscribe to download progress
- `unsubscribe` - Unsubscribe from download
- `resume_download` - Resume a paused download
- `cancel_download` - Cancel a download

**Server Messages:**
- `download_progress` - Progress updates
- `download_complete` - Download finished
- `download_error` - Download failed
- `download_cancelled` - Download cancelled

## Authentication

All requests must include the `X-App-ID` header:

```
X-App-ID: com.venom120.ytdownloader
```

## Environment Variables

- `ALLOWED_APP_ID` - Valid app identifier (default: `com.venom120.ytdownloader`)
- `DOWNLOAD_DIR` - Download directory (default: `/app/downloads`)

## Docker Commands

```bash
# Build image
docker build -t ytdownloader-backend .

# Run container
docker run -p 8000:8000 \
  -e ALLOWED_APP_ID=com.venom120.ytdownloader \
  -v $(pwd)/downloads:/app/downloads \
  ytdownloader-backend

# View logs
docker logs -f ytdownloader-backend

# Stop container
docker stop ytdownloader-backend
```

## Development

### Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── routes/
│   │   ├── youtube.py          # REST endpoints
│   │   └── websocket.py        # WebSocket handler
│   ├── services/
│   │   └── ytdlp_service.py    # yt-dlp wrapper
│   └── middleware/
│       └── auth.py             # Authentication
├── downloads/                  # Downloaded files
├── requirements.txt           # Dependencies
├── Dockerfile                # Docker config
└── docker-compose.yml        # Docker Compose config
```

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Production Deployment

### Prerequisites

- FFmpeg installed on server
- Python 3.11+ 
- Network access for mobile clients
- SSL certificate for HTTPS (recommended)

### Deploy to Cloud

1. **Configure `.env` file**:
   ```env
   ALLOWED_APP_ID=com.venom120.ytdownloader
   DOWNLOAD_DIR=/app/downloads
   ```

2. **Update React Native client** - Set backend URL in `Android/React-Native/.env`:
   ```env
   BACKEND_URL=https://your-server.com
   WS_URL=wss://your-server.com
   APP_ID=com.venom120.ytdownloader
   ```

3. **Deploy Options**:

   **Option A: Docker (Recommended)**
   ```bash
   # Build and push to registry
   docker build -t your-registry/ytdownloader-backend .
   docker push your-registry/ytdownloader-backend
   
   # Deploy on server
   docker pull your-registry/ytdownloader-backend
   docker-compose up -d
   ```

   **Option B: VPS (DigitalOcean, AWS EC2, etc.)**
   ```bash
   # On server
   git clone your-repo
   cd Android/Python
   pip install -r requirements.txt
   
   # Run with systemd or supervisor
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

   **Option C: Platform as a Service**
   - **Heroku**: 
     ```bash
     heroku create ytdownloader-api
     heroku config:set ALLOWED_APP_ID=com.venom120.ytdownloader
     git push heroku main
     ```
   - **Railway.app**: Connect GitHub repo and deploy
   - **Render.com**: Deploy as web service with Docker

4. **Setup Reverse Proxy (Nginx)**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       # Redirect to HTTPS
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl http2;
       server_name your-domain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       # WebSocket support
       location /ws {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_read_timeout 86400;
       }
   }
   ```

### Security Considerations

- ✅ **Use HTTPS** - Encrypt data in transit
- ✅ **Restrict CORS** - Configure allowed origins in `main.py`
- ✅ **Rate Limiting** - Implement request throttling
- ✅ **Request Validation** - Pydantic models validate all input
- ✅ **Monitor Usage** - Track download patterns
- ✅ **Auto Cleanup** - Implement cron job to delete old downloads
  ```bash
  # Crontab: Delete files older than 1 day
  0 */6 * * * find /app/downloads -type f -mtime +1 -delete
  ```
- ✅ **Firewall Rules** - Restrict access to necessary ports only
- ✅ **Environment Variables** - Never hardcode sensitive data

## Troubleshooting

### yt-dlp errors
```bash
# Update yt-dlp
pip install --upgrade yt-dlp
```

### FFmpeg not found
```bash
# Check FFmpeg installation
ffmpeg -version
```

### WebSocket connection fails
- Check firewall settings
- Verify app ID is correct
- Ensure server is running

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open a GitHub issue.
