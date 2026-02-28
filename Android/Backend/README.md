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
- ✅ **Rate Limiting** - Per-IP throttling to prevent abuse (SlowAPI)
- ✅ **Cookie Authentication** - Support for authenticated YouTube sessions
- ✅ **Background Downloads** - Async processing with threading
- ✅ **Resume/Cancel** - Download control capabilities
- ✅ **Docker Support** - Easy containerized deployment with persistent volumes
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

## 🍪 Cookie Authentication Setup (Recommended)

For improved download reliability and access to age-restricted or member-only content, you can configure the backend to use your YouTube session cookies.

### Why Use Cookies?

- ✅ **Access Age-Restricted Content** - Download videos requiring age verification
- ✅ **Member-Only Content** - Access channel memberships and private videos
- ✅ **Higher Rate Limits** - ~2000 videos/hour vs ~300 videos/hour without auth
- ✅ **Better Reliability** - Reduces throttling and temporary blocks

### ⚠️ Important Security Notes

1. **Never share your cookies publicly** - They contain your session credentials
2. **Cookies expire** - Refresh every 1-2 weeks by re-exporting
3. **Use dedicated account** - Consider using a separate YouTube account
4. **Cookie rotation** - YouTube may invalidate cookies if detected; use fresh sessions

### Step-by-Step Cookie Export Guide

#### Option 1: Export from Windows (Edge/Chrome)

**1. Install Browser Extension**

For **Microsoft Edge** or **Google Chrome**:
- Install extension: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- Or search "Get cookies.txt" in Edge/Chrome Web Store

For **Firefox**:
- Install extension: [cookies.txt](https://addons.mozilla.org/firefox/addon/cookies-txt/)

**2. Create Fresh Session (Important!)**

```powershell
# On Windows, open Edge in InPrivate mode
msedge.exe -inprivate https://www.youtube.com/robots.txt
```

Or use Incognito/Private browsing:
- **Edge**: Ctrl+Shift+N
- **Chrome**: Ctrl+Shift+N  
- **Firefox**: Ctrl+Shift+P

**3. Login to YouTube**

- Navigate to `https://www.youtube.com`
- Log in with your account
- Visit a video page to ensure session is active

**4. Export Cookies**

- Click the "Get cookies.txt" extension icon
- Select "Export" or "Export as cookies.txt"
- Save as `cookies.txt`

**5. Verify Cookie Format**

Open `cookies.txt` and ensure first line is:
```
# Netscape HTTP Cookie File
```

Or:
```
# HTTP Cookie File
```

#### Option 2: Export Using PowerShell Script

**⚠️ Windows Only** - This method extracts cookies from Edge browser data:

```powershell
# Install cookie export tool
pip install browser-cookie3

# Export cookies to file
python -c "import browser_cookie3; import json; cj = browser_cookie3.edge(); cookies = list(cj); print('\\n'.join(['# Netscape HTTP Cookie File'] + [f'{c.domain}\\tTRUE\\t{c.path}\\tFALSE\\t{c.expires}\\t{c.name}\\t{c.value}' for c in cookies if 'youtube' in c.domain]))" > cookies.txt
```

**Note**: This may fail due to DPAPI encryption. Use browser extension method instead.

### Upload Cookies to EC2 Server

**1. Copy cookies.txt to your local project**

```powershell
# On Windows
Copy-Item cookies.txt D:\Github\Youtube-downloader\Android\Backend\cookies\
```

**2. Upload to EC2 using SCP**

```powershell
# From Windows PowerShell
scp D:\Github\Youtube-downloader\Android\Backend\cookies\cookies.txt ubuntu@YOUR_EC2_IP:/home/ubuntu/YTDownloader/Android/Backend/cookies/
```

**3. Or upload directly via SSH**

```bash
# SSH into EC2
ssh ubuntu@YOUR_EC2_IP

# Create cookies directory
cd /home/ubuntu/YTDownloader/Android/Backend
mkdir -p cookies

# Paste cookies content (use nano or vim)
nano cookies/cookies.txt
# Paste cookie content, Ctrl+X, Y, Enter
```

**4. Set proper permissions**

```bash
# On EC2
chmod 600 /home/ubuntu/YTDownloader/Android/Backend/cookies/cookies.txt
chown ubuntu:ubuntu /home/ubuntu/YTDownloader/Android/Backend/cookies/cookies.txt
```

### Docker Volume Configuration

The cookies are automatically mounted via Docker volume. No additional configuration needed if using `docker-compose.yml`:

```yaml
volumes:
  - ytdownloader_cookies:/app/cookies    # ← Cookies persisted here
  - ytdownloader_downloads:/app/downloads
```

The backend automatically detects `cookies.txt` at `/app/cookies/cookies.txt` and uses it for all yt-dlp operations.

### Verify Cookies Are Working

**1. Check backend logs**

```bash
docker logs -f ytdownloader
```

Look for yt-dlp output showing authenticated session.

**2. Test with age-restricted video**

Use the mobile app to download an age-restricted video. If cookies are working, it should download successfully.

### Cookie Refresh Schedule

Set up a cron job or reminder to refresh cookies every 1-2 weeks:

```bash
# Add to crontab (check cookies warning)
0 0 */14 * * echo "REMINDER: Refresh YouTube cookies" | mail -s "Cookie Refresh" your@email.com
```

Or use a scheduled script:

```bash
#!/bin/bash
# refresh_cookies.sh
# Run this every 2 weeks

# 1. Export new cookies using browser extension
# 2. Upload to server
scp ~/Downloads/cookies.txt ubuntu@YOUR_EC2_IP:/home/ubuntu/YTDownloader/Android/Backend/cookies/

# 3. Restart Docker container
ssh ubuntu@YOUR_EC2_IP "cd /home/ubuntu/server-files && docker-compose restart ytdownloader"

echo "Cookies refreshed successfully!"
```

### Troubleshooting Cookies

**Problem**: Downloads failing with "Sign in to confirm you're not a bot"

**Solution**: 
1. Cookies expired - re-export fresh cookies
2. YouTube detected automation - wait 24h and use new session
3. Use incognito session next time

**Problem**: "HTTP Error 403: Forbidden"

**Solution**:
1. Verify cookies.txt format (must start with `# Netscape HTTP Cookie File`)
2. Ensure cookies are from `youtube.com` domain
3. Re-export cookies from fresh private/incognito session

**Problem**: Cookies not being used by backend

**Solution**:
1. Check file path: `/app/cookies/cookies.txt` inside container
2. Verify Docker volume mount
3. Check file permissions (should be readable)

```bash
# Debug inside container
docker exec -it ytdownloader bash
ls -la /app/cookies/
cat /app/cookies/cookies.txt | head -n 5
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
- ✅ **Rate Limiting** - Implemented using SlowAPI (100 requests/minute, 2000/hour per IP)
  - Search endpoint: 30 requests/minute
  - Video info: 50 requests/minute  
  - Downloads: 20 requests/minute
- ✅ **Request Validation** - Pydantic models validate all input
- ✅ **Monitor Usage** - Track download patterns
- ✅ **Auto Cleanup** - Implement cron job to delete old downloads
  ```bash
  # Crontab: Delete files older than 1 day
  0 */6 * * * find /app/downloads -type f -mtime +1 -delete
  ```
- ✅ **Firewall Rules** - Restrict access to necessary ports only
- ✅ **Environment Variables** - Never hardcode sensitive data
- ✅ **Cookie Security** - Store cookies with restricted permissions (chmod 600)

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
