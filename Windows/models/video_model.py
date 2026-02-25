"""
Video Model - Represents a YouTube video or playlist
"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class VideoInfo:
    """Data class for video information"""
    video_id: str
    title: str
    thumbnail_url: str
    duration: int  # in seconds
    channel: str
    view_count: Optional[int] = None
    upload_date: Optional[str] = None
    url: str = ""
    is_playlist: bool = False
    playlist_count: Optional[int] = None
    
    @property
    def formatted_duration(self) -> str:
        """Return formatted duration string (e.g., '3:45' or '1:23:45')"""
        if self.duration < 0:
            return "Unknown"
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    @property
    def formatted_views(self) -> str:
        """Return formatted view count (e.g., '1.2M', '45K')"""
        if self.view_count is None:
            return "Unknown"
        
        if self.view_count >= 1_000_000:
            return f"{self.view_count / 1_000_000:.1f}M"
        elif self.view_count >= 1_000:
            return f"{self.view_count / 1_000:.1f}K"
        else:
            return str(self.view_count)


@dataclass
class SearchResult:
    """Container for search results with pagination info"""
    videos: List[VideoInfo]
    query: str
    page: int = 1
    has_more: bool = False
