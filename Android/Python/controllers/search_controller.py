"""
Search Controller - Manages search and video info operations
"""
import threading
from typing import Callable, Optional, List
from models.ytdlp_wrapper import YTDLPWrapper
from models.video_model import VideoInfo, SearchResult


class SearchController:
    """Controller for handling search and video info retrieval"""
    
    def __init__(self):
        """Initialize search controller"""
        self.ytdlp = YTDLPWrapper()
        self.current_search_result = None
        self.current_playlist_videos = []
    
    def search_videos(
        self,
        query: str,
        max_results: int = 20,
        callback: Optional[Callable[[SearchResult], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ):
        """Search for videos asynchronously"""
        def search_thread():
            try:
                result = self.ytdlp.search_videos(query, max_results)
                self.current_search_result = result
                
                if callback:
                    callback(result)
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
        
        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()
    
    def get_video_info(
        self,
        url: str,
        callback: Optional[Callable[[Optional[VideoInfo]], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ):
        """Get video info from URL asynchronously"""
        def info_thread():
            try:
                video_info = self.ytdlp.get_video_info(url)
                
                if callback:
                    callback(video_info)
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
        
        thread = threading.Thread(target=info_thread, daemon=True)
        thread.start()
    
    def get_playlist_videos(
        self,
        url: str,
        callback: Optional[Callable[[List[VideoInfo]], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ):
        """Get all videos from a playlist asynchronously"""
        def playlist_thread():
            try:
                videos = self.ytdlp.get_playlist_videos(url)
                self.current_playlist_videos = videos
                
                if callback:
                    callback(videos)
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
        
        thread = threading.Thread(target=playlist_thread, daemon=True)
        thread.start()
