"""
Download Controller - Manages download operations
"""
import threading
from typing import Callable, Optional
from models.ytdlp_wrapper import YTDLPWrapper
from models.video_model import VideoInfo


class DownloadController:
    """Controller for handling download operations"""
    
    def __init__(self, download_path: str):
        """Initialize download controller"""
        self.ytdlp = YTDLPWrapper(download_path)
        self.active_downloads = {}
        self.download_history = []
    
    def download_video(
        self,
        video: VideoInfo,
        format_type: str = 'mp4',
        progress_callback: Optional[Callable[[float], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ):
        """Start downloading a video in a separate thread"""
        def download_thread():
            try:
                success = self.ytdlp.download_video(
                    video.url,
                    format_type,
                    progress_callback,
                    complete_callback
                )
                
                if success:
                    self.download_history.append({
                        'video': video,
                        'format': format_type,
                        'status': 'completed'
                    })
                else:
                    if error_callback:
                        error_callback("Download failed")
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
            finally:
                if video.video_id in self.active_downloads:
                    del self.active_downloads[video.video_id]
        
        thread = threading.Thread(target=download_thread, daemon=True)
        self.active_downloads[video.video_id] = thread
        thread.start()
    
    def download_playlist(
        self,
        playlist: VideoInfo,
        format_type: str = 'mp4',
        progress_callback: Optional[Callable[[float], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ):
        """Start downloading a playlist in a separate thread"""
        def download_thread():
            try:
                success = self.ytdlp.download_playlist(
                    playlist.url,
                    format_type,
                    progress_callback,
                    complete_callback
                )
                
                if success:
                    self.download_history.append({
                        'video': playlist,
                        'format': format_type,
                        'status': 'completed'
                    })
                else:
                    if error_callback:
                        error_callback("Playlist download failed")
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
            finally:
                if playlist.video_id in self.active_downloads:
                    del self.active_downloads[playlist.video_id]
        
        thread = threading.Thread(target=download_thread, daemon=True)
        self.active_downloads[playlist.video_id] = thread
        thread.start()
    
    def is_downloading(self, video_id: str) -> bool:
        """Check if a video is currently being downloaded"""
        return video_id in self.active_downloads
