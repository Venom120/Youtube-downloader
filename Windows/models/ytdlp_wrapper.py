"""
yt-dlp wrapper - handles all yt-dlp operations
"""
import yt_dlp
from typing import List, Optional, Dict, Any, Callable
from .video_model import VideoInfo, SearchResult
import os
import threading


class YTDLPWrapper:
    """Wrapper class for yt-dlp operations"""
    
    def __init__(self, download_path: Optional[str] = None):
        """Initialize wrapper with download path"""
        if download_path is None:
            self.download_path = os.path.expanduser("~/Downloads/YTDownloader")
        else:
            self.download_path = download_path
        
        self.current_progress = 0
        self._progress_callback = None
        self._complete_callback = None
    
    @staticmethod
    def _extract_thumbnail_url(entry: Any) -> str:
        """Extract thumbnail URL from entry, handling both thumbnail and thumbnails fields"""
        # Try direct thumbnail field first
        if entry.get('thumbnail'):
            return str(entry.get('thumbnail', ''))
        
        # Try thumbnails list (plural)
        if entry.get('thumbnails') and len(entry.get('thumbnails', [])) > 0:
            thumbnails = entry.get('thumbnails', [])
            # Get the last (highest quality) thumbnail
            return str(thumbnails[-1].get('url', ''))
        
        return ''
    
    def _progress_hook(self, d: Dict[str, Any]):
        """Internal progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            # Calculate percentage
            if 'total_bytes' in d:
                total = d['total_bytes']
            elif 'total_bytes_estimate' in d:
                total = d['total_bytes_estimate']
            else:
                total = None
            
            if total and 'downloaded_bytes' in d:
                downloaded = d['downloaded_bytes']
                percentage = (downloaded / total) * 100
                self.current_progress = percentage
                
                if self._progress_callback:
                    self._progress_callback(percentage)
        
        elif d['status'] == 'finished':
            self.current_progress = 100
            if self._complete_callback:
                self._complete_callback(d.get('filename', ''))
    
    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """
        Extract video information from URL
        
        Args:
            url: YouTube video or playlist URL
            
        Returns:
            VideoInfo object or None if failed
        """
        ydl_opts: Any = {
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
            print(f"Error getting video info: {e}")
            return None
    
    def get_playlist_videos(self, url: str) -> List[VideoInfo]:
        """
        Get all videos from a playlist
        
        Args:
            url: YouTube playlist URL
            
        Returns:
            List of VideoInfo objects
        """
        ydl_opts: Any = {
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
            print(f"Error getting playlist videos: {e}")
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
        ydl_opts: Any = {
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
            print(f"Error searching videos: {e}")
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
            ydl_opts: Any = {
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
            ydl_opts: Any = {
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
            print(f"Error downloading video: {e}")
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
