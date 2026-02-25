"""
YouTube downloader wrapper - handles youtube-dl operations for Android
Uses youtube-dl (pure Python) for Android compatibility
Uses yt-dlp (if available) with fallback to youtube-dl
"""
import os
import sys
import tempfile
import shutil
from typing import List, Optional, Dict, Any, Callable
from .video_model import VideoInfo, SearchResult

# Try to import yt-dlp first (for Windows), fall back to youtube-dl (for Android)
try:
    import yt_dlp as ydl_module  # type: ignore
    YDL_LIB = 'yt-dlp'
except ImportError:
    try:
        import youtube_dl as ydl_module  # type: ignore
        YDL_LIB = 'youtube-dl'
    except ImportError:
        raise ImportError("Neither yt-dlp nor youtube-dl is installed. Please install one of them.")


class YTDLPWrapper:
    """
    Wrapper class for YouTube download operations
    Supports both yt-dlp (Windows) and youtube-dl (Android)
    """
    
    def __init__(self, download_path: Optional[str] = None):
        """Initialize wrapper with download path"""
        self.download_path = download_path
        self.current_progress = 0
        self._progress_callback: Optional[Callable[[float], None]] = None
        self._complete_callback: Optional[Callable[[str], None]] = None
        self.lib_name = YDL_LIB
    
    @staticmethod
    def _extract_thumbnail_url(entry: Any) -> str:
        """Extract thumbnail URL from entry, handling both thumbnail and thumbnails fields"""
        try:
            # Try direct thumbnail field first
            if entry.get('thumbnail'):
                return str(entry.get('thumbnail', ''))
            
            # Try thumbnails list (plural)
            if entry.get('thumbnails') and len(entry.get('thumbnails', [])) > 0:
                thumbnails = entry.get('thumbnails', [])
                # Get the last (highest quality) thumbnail
                return str(thumbnails[-1].get('url', ''))
            
            return ''
        except Exception as e:
            print(f"Warning: Error extracting thumbnail: {e}")
            return ''
    
    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """Internal progress hook for download operations"""
        try:
            if d.get('status') == 'downloading':
                # Calculate percentage
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                
                if total and 'downloaded_bytes' in d:
                    downloaded = d['downloaded_bytes']
                    percentage = min(100, (downloaded / total) * 100)
                    self.current_progress = percentage
                    
                    if self._progress_callback:
                        self._progress_callback(percentage)
            
            elif d.get('status') == 'finished':
                self.current_progress = 100
                if self._complete_callback:
                    filename = d.get('filename', 'Unknown')
                    self._complete_callback(filename)
        except Exception as e:
            print(f"Warning: Progress hook error: {e}")
    
    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """
        Extract video information from URL
        
        Args:
            url: YouTube video or playlist URL
            
        Returns:
            VideoInfo object or None if failed
        """
        ydl_opts: Dict[str, Any] = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
        }
        
        try:
            with ydl_module.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                # Check if it's a playlist
                if 'entries' in info:
                    entries = list(info.get('entries', []))
                    first_video = next((e for e in entries if e), None)
                    
                    if not first_video:
                        return None
                    
                    thumb_url = self._extract_thumbnail_url(first_video)
                    
                    return VideoInfo(
                        video_id=str(info.get('id', '')),
                        title=str(info.get('title') or 'Unknown Playlist'),
                        thumbnail_url=thumb_url,
                        duration=-1,  # Playlists don't have single duration
                        channel=str(info.get('uploader') or info.get('channel') or 'Unknown'),
                        view_count=None,
                        url=url,
                        is_playlist=True,
                        playlist_count=len(entries)
                    )
                else:
                    # Single video
                    thumb_url = self._extract_thumbnail_url(info)
                    
                    return VideoInfo(
                        video_id=str(info.get('id', '')),
                        title=str(info.get('title') or 'Unknown'),
                        thumbnail_url=thumb_url,
                        duration=int(info.get('duration', 0) or 0),
                        channel=str(info.get('uploader') or info.get('channel') or 'Unknown'),
                        view_count=info.get('view_count'),
                        upload_date=info.get('upload_date'),
                        url=url,
                        is_playlist=False
                    )
        except Exception as e:
            error_msg = f"Error getting video info: {str(e)}"
            if 'private' in str(e).lower():
                error_msg = "This video is private or restricted"
            elif 'unavailable' in str(e).lower():
                error_msg = "This video is unavailable"
            elif 'age' in str(e).lower():
                error_msg = "This video requires age verification"
            print(error_msg)
            return None
    
    def get_playlist_videos(self, url: str) -> List[VideoInfo]:
        """Get all videos from a playlist"""
        ydl_opts: Dict[str, Any] = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with ydl_module.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info = ydl.extract_info(url, download=False)
                
                if 'entries' not in info:
                    return []
                
                videos = []
                for entry in info.get('entries', []):
                    if entry:
                        try:
                            thumb_url = self._extract_thumbnail_url(entry)
                            
                            video = VideoInfo(
                                video_id=entry.get('id', ''),
                                title=entry.get('title', 'Unknown'),
                                thumbnail_url=thumb_url,
                                duration=int(entry.get('duration', 0) or 0),
                                channel=entry.get('uploader', entry.get('channel', 'Unknown')),
                                view_count=entry.get('view_count'),
                                upload_date=entry.get('upload_date'),
                                url=entry.get('webpage_url', f"https://youtube.com/watch?v={entry.get('id', '')}"),
                                is_playlist=False
                            )
                            videos.append(video)
                        except Exception as e:
                            print(f"Warning: Could not process playlist entry: {e}")
                
                return videos
        except Exception as e:
            error_msg = f"Error getting playlist videos: {str(e)}"
            if 'private' in str(e).lower():
                error_msg = "This playlist is private"
            print(error_msg)
            return []
    
    def search_videos(self, query: str, max_results: int = 20) -> SearchResult:
        """Search for videos on YouTube"""
        ydl_opts: Dict[str, Any] = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
        }
        
        search_url = f"ytsearch{max_results}:{query}"
        
        try:
            with ydl_module.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info = ydl.extract_info(search_url, download=False)
                
                videos = []
                if 'entries' in info:
                    for entry in info.get('entries', []):
                        if entry:
                            try:
                                is_playlist = entry.get('_type') == 'playlist'
                                thumb_url = self._extract_thumbnail_url(entry)
                                
                                video = VideoInfo(
                                    video_id=entry.get('id', ''),
                                    title=entry.get('title', 'Unknown'),
                                    thumbnail_url=thumb_url,
                                    duration=int(entry.get('duration', 0) or 0) if not is_playlist else -1,
                                    channel=entry.get('uploader', entry.get('channel', 'Unknown')),
                                    view_count=entry.get('view_count'),
                                    url=entry.get('url', f"https://youtube.com/watch?v={entry.get('id', '')}"),
                                    is_playlist=is_playlist,
                                    playlist_count=entry.get('playlist_count') if is_playlist else None
                                )
                                videos.append(video)
                            except Exception as e:
                                print(f"Warning: Could not process search result: {e}")
                
                return SearchResult(
                    videos=videos,
                    query=query,
                    page=1,
                    has_more=len(videos) >= max_results
                )
        except Exception as e:
            error_msg = f"Error searching videos: {str(e)}"
            if 'no internet' in str(e).lower() or 'parse error' in str(e).lower():
                error_msg = "Network error - check your internet connection"
            print(error_msg)
            return SearchResult(videos=[], query=query, page=1, has_more=False)
    
    def download_video(
        self,
        url: str,
        format_type: str = 'mp4',
        progress_callback: Optional[Callable[[float], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Download video in specified format
        
        Args:
            url: YouTube video or playlist URL
            format_type: 'mp4' for video or 'mp3' for audio
            progress_callback: Function to call with progress (0-100)
            complete_callback: Function to call when complete with filename
            
        Returns:
            True if successful, False otherwise
            
        Notes:
            - MP3: Tries FFmpeg first, falls back to M4A (AAC audio)
            - MP4: Downloads video with audio
        """
        self._progress_callback = progress_callback
        self._complete_callback = complete_callback
        
        # Ensure download directory exists
        download_path = self.download_path or os.path.expanduser('~/Downloads/YTDownloader')
        os.makedirs(download_path, exist_ok=True)
        
        try:
            if format_type == 'mp3':
                # Try multiple audio extraction methods for better Android compatibility
                return self._download_audio(url, download_path)
            else:
                # MP4 format - download video with audio
                ydl_opts: Dict[str, Any] = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'progress_hooks': [self._progress_hook],
                }
                
                # Only set merge_output_format if using yt-dlp
                if self.lib_name == 'yt-dlp':
                    ydl_opts['merge_output_format'] = 'mp4'
                
                with ydl_module.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                    ydl.download([url])
                return True
        
        except Exception as e:
            error_msg = f"Download error: {str(e)}"
            
            # Provide specific error messages
            error_str = str(e).lower()
            if 'permission' in error_str or 'access' in error_str:
                error_msg = "Permission denied: Check download folder permissions"
            elif 'space' in error_str or 'disk' in error_str:
                error_msg = "Not enough storage space"
            elif 'private' in error_str:
                error_msg = "This video is private"
            elif 'unavailable' in error_str or 'deleted' in error_str:
                error_msg = "This video is no longer available"
            elif 'age' in error_str:
                error_msg = "Video requires age verification"
            elif 'region' in error_str or 'country' in error_str:
                error_msg = "This video is not available in your region"
            elif 'ffmpeg' in error_str:
                error_msg = "FFmpeg not installed (required for MP3 downloads)"
            
            print(error_msg)
            return False
    
    def _download_audio(self, url: str, download_path: str) -> bool:
        """
        Download audio with multiple fallback strategies
        
        Tries in order:
        1. MP3 with FFmpeg (best quality)
        2. M4A (AAC - native YouTube audio format)
        3. WAV (if available)
        4. Best audio stream (generic format)
        
        Args:
            url: YouTube URL
            download_path: Path to save audio
            
        Returns:
            True if successful, False otherwise
        """
        # Strategy 1: Try MP3 with FFmpeg (best quality)
        print("Attempting to download as MP3...")
        ffmpeg_available = self._check_ffmpeg_available()
        
        if ffmpeg_available:
            # Use temp directory for MP3 conversion to avoid deleting existing MP4 files
            temp_dir = tempfile.mkdtemp(prefix='ytdl_mp3_')
            try:
                ydl_opts: Dict[str, Any] = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [self._progress_hook],
                    'quiet': True,
                    'no_warnings': True,
                }
                
                with ydl_module.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                    ydl.download([url])
                
                # Find the MP3 file in temp directory and move it to final location
                mp3_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp3')]
                if mp3_files:
                    temp_mp3_path = os.path.join(temp_dir, mp3_files[0])
                    final_mp3_path = os.path.join(download_path, mp3_files[0])
                    shutil.move(temp_mp3_path, final_mp3_path)
                    print("Successfully downloaded as MP3")
                    return True
                else:
                    print("Error: MP3 file not found after conversion. Trying alternative formats...")
            except Exception as e:
                print(f"MP3 with FFmpeg failed: {e}. Trying alternative formats...")
            finally:
                # Clean up temp directory
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"Warning: Failed to clean up temp directory: {e}")
        
        # Strategy 2: Try M4A (AAC - native YouTube format, no conversion needed)
        print("Attempting to download as M4A (AAC audio)...")
        try:
            ydl_opts: Dict[str, Any] = {
                'format': 'bestaudio[ext=m4a]/bestaudio',
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [],  # No post-processing needed
            }
            
            with ydl_module.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                ydl.download([url])
            print("Successfully downloaded as M4A (AAC audio format)")
            return True
        except Exception as e:
            print(f"M4A download failed: {e}. Trying WAV format...")
        
        # Strategy 3: Try WAV format (if available)
        print("Attempting to download as WAV...")
        try:
            ydl_opts: Dict[str, Any] = {
                'format': 'bestaudio[ext=wav]/bestaudio',
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
            }
            
            with ydl_module.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                ydl.download([url])
            print("Successfully downloaded as WAV (uncompressed audio)")
            return True
        except Exception as e:
            print(f"WAV download failed: {e}. Trying best audio stream...")
        
        # Strategy 4: Download best audio available (fallback)
        print("Attempting to download best available audio...")
        try:
            ydl_opts: Dict[str, Any] = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
            }
            
            with ydl_module.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                ydl.download([url])
            print("Successfully downloaded best available audio format")
            return True
        except Exception as e:
            error_msg = f"All audio download strategies failed: {str(e)}"
            print(error_msg)
            return False
    
    @staticmethod
    def _check_ffmpeg_available() -> bool:
        """
        Check if FFmpeg is available on the system
        
        Returns:
            True if FFmpeg is available, False otherwise
        """
        try:
            import subprocess
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def download_playlist(
        self,
        url: str,
        format_type: str = 'mp4',
        progress_callback: Optional[Callable[[float], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Download entire playlist
        
        Args:
            url: YouTube playlist URL
            format_type: 'mp4' for video or 'mp3' for audio
            progress_callback: Function to call with progress (0-100)
            complete_callback: Function to call when complete
            
        Returns:
            True if successful, False otherwise
        """
        # Delegate to download_video - the library handles playlists automatically
        return self.download_video(url, format_type, progress_callback, complete_callback)
