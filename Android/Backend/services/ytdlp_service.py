import yt_dlp
import os
import uuid
import subprocess
from typing import Dict, List, Optional, Callable
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "/app/downloads")
COOKIES_FILE = os.getenv("COOKIES_FILE", "/app/cookies/cookies.txt")
Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

def _extract_thumbnail_url(entry) -> str:
    """Extract the best thumbnail URL from yt-dlp entry."""
    thumbnails = entry.get("thumbnails", [])
    if thumbnails and isinstance(thumbnails, list):
        first_thumbnail = thumbnails[0]
        if isinstance(first_thumbnail, dict):
            return first_thumbnail.get("url", "")
    return entry.get("thumbnail", "")

# Validate cookies file format
def validate_cookie_file(cookie_path: str) -> tuple[bool, str]:
    """
    Validate if cookie file exists and is in correct Netscape format.
    Returns: (is_valid, message)
    """
    if not os.path.exists(cookie_path):
        return False, "Cookie file not found"
    
    try:
        with open(cookie_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            # Netscape format should start with # Netscape HTTP Cookie File or have tab-separated values
            if first_line.startswith('#') or '\t' in first_line:
                return True, "Cookie file format looks valid"
            else:
                return False, "Cookie file may not be in Netscape format. Export cookies using browser extension in Netscape format."
    except Exception as e:
        return False, f"Error reading cookie file: {e}"

# Debug: Check if cookies file exists and validate format
print("\\n" + "="*60)
print("COOKIE VALIDATION")
print("="*60)
if os.path.exists(COOKIES_FILE):
    file_size = os.path.getsize(COOKIES_FILE)
    print(f"[✓] Cookies file found: {COOKIES_FILE} ({file_size} bytes)")
    
    is_valid, msg = validate_cookie_file(COOKIES_FILE)
    if is_valid:
        print(f"[✓] {msg}")
    else:
        print(f"[!] WARNING: {msg}")
        print(f"[!] Cookie file must be in Netscape format (not Chrome JSON)")
        print(f"[!] Use browser extension like 'Get cookies.txt' or 'cookies.txt'")
        print(f"[!] Export from your browser AFTER logging into YouTube")
else:
    print(f"[✗] Cookies file NOT found: {COOKIES_FILE}")
    print(f"[!] yt-dlp will run WITHOUT authentication (guest mode)")
    print(f"[!] Some videos may be age-restricted or unavailable")
    print(f"[!] To fix: Export YouTube cookies in Netscape format to {COOKIES_FILE}")
print("="*60 + "\\n")

# Debug: Check if Deno (JavaScript runtime) is available
print("="*60)
print("JAVASCRIPT RUNTIME CHECK")
print("="*60)
try:
    deno_version = subprocess.check_output(["deno", "--version"], text=True).strip()
    print(f"[✓] Deno JavaScript runtime found:")
    for line in deno_version.split('\\n'):
        print(f"    {line}")
except (subprocess.CalledProcessError, FileNotFoundError):
    print(f"[✗] Deno NOT found - yt-dlp cannot solve YouTube JavaScript challenges")
    print(f"[!] Install Deno: curl -fsSL https://deno.land/install.sh | sh")
    print(f"[!] This is required for modern YouTube access")
print("="*60 + "\\n")


class YTDLPService:
    """
    Service for handling YouTube video operations using yt-dlp
    """

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.active_downloads: Dict[str, dict] = {}

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        try:
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get("id")
        except Exception as e:
            print(f"Error extracting video ID: {e}")
            return None

    async def search_videos(self, query: str, max_results: int = 20) -> List[dict]:
        """
        Search for YouTube videos
        """
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                # Add YouTube-specific extractor arguments for better compatibility
                "extractor_args": {
                    "youtube": {
                        "player_client": ["ios", "web"],  # Use iOS and web clients for better compatibility
                        "skip": ["hls", "dash"],  # Skip unnecessary formats for faster extraction
                    }
                },
            }
            
            # Add cookies if file exists
            if os.path.exists(COOKIES_FILE):
                print(f"[✓] Using cookies for search: {COOKIES_FILE}")
                ydl_opts["cookiefile"] = COOKIES_FILE  # type: ignore
            else:
                print(f"[!] No cookies file found for search - running in guest mode")

            def _search():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                    search_url = f"ytsearch{max_results}:{query}"
                    info = ydl.extract_info(search_url, download=False)  # type: ignore
                    
                    if not info or "entries" not in info:
                        return []
                    
                    videos = []
                    for entry in info["entries"]:  # type: ignore
                        if entry:
                            video_id = entry.get("id", "")
                            thumbnail_url = _extract_thumbnail_url(entry)
                            
                            videos.append({
                                "videoId": video_id,
                                "title": entry.get("title", "Unknown"),
                                "thumbnailUrl": thumbnail_url,
                                "duration": entry.get("duration", 0),
                                "channel": entry.get("channel", "Unknown"),
                                "viewCount": entry.get("view_count", 0),
                                "uploadDate": entry.get("upload_date", ""),
                                "url": f"https://youtube.com/watch?v={video_id}",
                            })
                    return videos

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            videos = await loop.run_in_executor(self.executor, _search)
            return videos

        except Exception as e:
            print(f"Error searching videos: {e}")
            return []

    async def get_video_info(self, url: str) -> Optional[dict]:
        """
        Get video information without downloading
        """
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                # Add YouTube-specific extractor arguments
                "extractor_args": {
                    "youtube": {
                        "player_client": ["ios", "web"],  # iOS client is most reliable with cookies
                        "skip": ["dash"],  # Skip DASH for faster extraction
                    }
                },
            }
            
            # Add cookies if file exists
            if os.path.exists(COOKIES_FILE):
                print(f"[✓] Using cookies for video info: {COOKIES_FILE}")
                ydl_opts["cookiefile"] = COOKIES_FILE  # type: ignore
            else:
                print(f"[!] No cookies file found for video info - running in guest mode")

            def _get_info():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        return None
                    
                    video_id = info.get("id", "")
                    thumbnail_url = _extract_thumbnail_url(info)
                    
                    return {
                        "videoId": video_id,
                        "title": info.get("title", "Unknown"),
                        "thumbnailUrl": thumbnail_url,
                        "duration": info.get("duration", 0),
                        "channel": info.get("channel", "Unknown"),
                        "viewCount": info.get("view_count", 0),
                        "uploadDate": info.get("upload_date", ""),
                        "url": url,
                    }

            loop = asyncio.get_event_loop()
            video_info = await loop.run_in_executor(self.executor, _get_info)
            return video_info

        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

    def _progress_hook(self, d: dict, download_id: str, progress_callback: Optional[Callable] = None):
        """Progress hook for yt-dlp"""
        if d["status"] == "downloading":
            progress_data = {
                "downloadId": download_id,
                "status": "downloading",
                "progress": 0.0,
                "downloadedBytes": d.get("downloaded_bytes", 0),
                "totalBytes": d.get("total_bytes") or d.get("total_bytes_estimate", 0),
                "speed": d.get("speed_str", "N/A"),
                "eta": d.get("eta_str", "N/A"),
            }
            
            if progress_data["totalBytes"] > 0:
                progress_data["progress"] = (
                    progress_data["downloadedBytes"] / progress_data["totalBytes"]
                ) * 100
            
            # Update active download status
            if download_id in self.active_downloads:
                self.active_downloads[download_id].update(progress_data)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(progress_data)

        elif d["status"] == "finished":
            if download_id in self.active_downloads:
                self.active_downloads[download_id]["status"] = "completed"
                self.active_downloads[download_id]["progress"] = 100.0

    async def download_video(
        self,
        url: str,
        format_type: str = "mp4",
        progress_callback: Optional[Callable] = None,
    ) -> dict:
        """
        Download video and prepare for client download
        """
        try:
            download_id = str(uuid.uuid4())
            video_id = self.extract_video_id(url)
            
            if not video_id:
                raise ValueError("Invalid YouTube URL")

            # Get video info first
            video_info = await self.get_video_info(url)
            if not video_info:
                raise ValueError("Could not fetch video information")

            # Sanitize filename
            safe_title = "".join(c for c in video_info["title"] if c.isalnum() or c in (' ', '-', '_')).strip()
            file_extension = "mp4" if format_type == "mp4" else "m4a"
            filename = f"{safe_title}.{file_extension}"
            filepath = os.path.join(DOWNLOAD_DIR, filename)

            # Configure yt-dlp options
            if format_type == "mp3":
                ydl_opts = {
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                    "outtmpl": filepath,
                    "quiet": True,
                    "no_warnings": True,
                    # Add YouTube-specific extractor arguments
                    "extractor_args": {
                        "youtube": {
                            "player_client": ["ios", "web"],  # iOS client most reliable with cookies
                        }
                    },
                    "progress_hooks": [lambda d: self._progress_hook(d, download_id, progress_callback)],
                }
            else:  # mp4
                ydl_opts = {
                    "format": "best[ext=mp4][height<=720]/best[ext=mp4]/best",
                    "outtmpl": filepath,
                    "quiet": True,
                    "no_warnings": True,
                    # Add YouTube-specific extractor arguments
                    "extractor_args": {
                        "youtube": {
                            "player_client": ["ios", "web"],  # iOS client most reliable with cookies
                        }
                    },
                    "progress_hooks": [lambda d: self._progress_hook(d, download_id, progress_callback)],
                }
            
            # Add cookies if file exists
            if os.path.exists(COOKIES_FILE):
                print(f"[✓] Using cookies for download: {COOKIES_FILE}")
                ydl_opts["cookiefile"] = COOKIES_FILE  # type: ignore
            else:
                print(f"[!] No cookies file found for download - running in guest mode")

            # Initialize download status
            self.active_downloads[download_id] = {
                "downloadId": download_id,
                "videoId": video_id,
                "status": "pending",
                "progress": 0.0,
                "downloadedBytes": 0,
                "totalBytes": 0,
                "filepath": filepath,
                "filename": filename,
            }

            # Download in thread pool
            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                    ydl.download([url])
                    return filepath

            loop = asyncio.get_event_loop()
            downloaded_path = await loop.run_in_executor(self.executor, _download)

            # Get file size
            file_size = os.path.getsize(downloaded_path) if os.path.exists(downloaded_path) else 0

            return {
                "downloadId": download_id,
                "videoId": video_id,
                "downloadUrl": f"/api/download-file/{download_id}",
                "fileName": filename,
                "fileSize": file_size,
                "format": format_type,
            }

        except Exception as e:
            print(f"Error downloading video: {e}")
            if download_id in self.active_downloads:
                self.active_downloads[download_id]["status"] = "failed"
                self.active_downloads[download_id]["error"] = str(e)
            raise

    def get_download_status(self, download_id: str) -> Optional[dict]:
        """Get status of a download"""
        return self.active_downloads.get(download_id)

    def cancel_download(self, download_id: str) -> bool:
        """Cancel an active download"""
        if download_id in self.active_downloads:
            self.active_downloads[download_id]["status"] = "cancelled"
            # Note: Actual cancellation of yt-dlp download would require more complex implementation
            return True
        return False

    def get_download_file(self, download_id: str) -> Optional[str]:
        """Get file path for a completed download"""
        download = self.active_downloads.get(download_id)
        if download and download["status"] == "completed":
            return download.get("filepath")
        return None


# Singleton instance
ytdlp_service = YTDLPService()
