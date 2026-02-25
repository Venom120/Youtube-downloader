"""
yt-dlp wrapper - handles all yt-dlp operations for Windows/Desktop
Uses yt-dlp with advanced features and better maintained
"""
import yt_dlp
from typing import List, Optional, Dict, Any, Callable
from .video_model import VideoInfo, SearchResult
import os


class YTDLPWrapper:
    """Wrapper class for yt-dlp operations (Windows/Desktop)"""
    
    def __init__(self, download_path: Optional[str] = None):
        """
        Initialize wrapper with download path
        
        Args:
            download_path: Directory to save downloads (default: ~/Downloads/YTDownloader)
        """
        if download_path is None:
            self.download_path = os.path.expanduser("~/Downloads/YTDownloader")
        else:
            self.download_path = download_path
        
        # Ensure directory exists
        os.makedirs(self.download_path, exist_ok=True)
        
        self.current_progress = 0
        self._progress_callback: Optional[Callable[[float], None]] = None
        self._complete_callback: Optional[Callable[[str], None]] = None
        self.lib_name = 'yt-dlp'
    
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
        """Internal progress hook for yt-dlp"""
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
            'extract_flat': 'in_playlist',  # Don't download, just extract info
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info = ydl.extract_info(url, download=False)
                
                # Check if it's a playlist
                if 'entries' in info:
                    # It's a playlist
                    first_video = next((e for e in info.get('entries', []) if e), None)  # type: ignore
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
                        playlist_count=int(len(list(info['entries'])))
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
        """
        Get all videos from a playlist
        
        Args:
            url: YouTube playlist URL
            
        Returns:
            List of VideoInfo objects
        """
        ydl_opts: Dict[str, Any] = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,  # Extract full info for each video
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info = ydl.extract_info(url, download=False)
                
                if 'entries' not in info:
                    return []
                
                videos = []
                for entry in info.get('entries', []):  # type: ignore
                    if entry:  # Some entries might be None
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
                
                return videos
        except Exception as e:
            error_msg = f"Error getting playlist videos: {str(e)}"
            if 'private' in str(e).lower():
                error_msg = "This playlist is private"
            print(error_msg)
            return []
    
    def search_videos(self, query: str, max_results: int = 20) -> SearchResult:
        """
        Search for videos on YouTube
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            SearchResult object
        """
        ydl_opts: Dict[str, Any] = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
        }
        
        search_url = f"ytsearch{max_results}:{query}"
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info = ydl.extract_info(search_url, download=False)
                
                videos = []
                if 'entries' in info:
                    for entry in info.get('entries', []):  # type: ignore
                        if entry:
                            # Extract thumbnail URL using helper method
                            thumbnail_url = self._extract_thumbnail_url(entry)
                            
                            # Determine if it's a playlist
                            is_playlist = entry.get('_type') == 'playlist'
                            
                            video = VideoInfo(
                                video_id=entry.get('id', ''),
                                title=entry.get('title', 'Unknown'),
                                thumbnail_url=thumbnail_url,
                                duration=int(entry.get('duration', 0) or 0) if not is_playlist else -1,
                                channel=entry.get('uploader', entry.get('channel', 'Unknown')),
                                view_count=entry.get('view_count'),
                                url=entry.get('url', f"https://youtube.com/watch?v={entry.get('id', '')}"),
                                is_playlist=is_playlist,
                                playlist_count=int(float(entry.get('playlist_count', 0))) if is_playlist and entry.get('playlist_count') else None
                            )
                            videos.append(video)
                
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
            url: YouTube video URL
            format_type: 'mp4' for video or 'mp3' for audio only
            progress_callback: Function to call with progress percentage
            complete_callback: Function to call when download completes
            
        Returns:
            True if successful, False otherwise
        """
        self._progress_callback = progress_callback
        self._complete_callback = complete_callback
        
        if format_type == 'mp3':
            ydl_opts: Dict[str, Any] = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
            }
        else:  # mp4
            ydl_opts: Dict[str, Any] = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
            }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
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
            format_type: 'mp4' for video or 'mp3' for audio only
            progress_callback: Function to call with progress percentage
            complete_callback: Function to call when download completes
            
        Returns:
            True if successful, False otherwise
        """
        # Same as download_video but yt-dlp handles playlists automatically
        return self.download_video(url, format_type, progress_callback, complete_callback)
