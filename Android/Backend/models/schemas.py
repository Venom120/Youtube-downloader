from pydantic import BaseModel, Field
from typing import List, Optional


class VideoInfo(BaseModel):
    videoId: str
    title: str
    thumbnailUrl: str
    duration: int  # in seconds
    channel: str
    viewCount: int
    uploadDate: Optional[str] = None
    url: str


class SearchRequest(BaseModel):
    query: str
    maxResults: int = Field(default=20, ge=1, le=50)


class SearchResult(BaseModel):
    videos: List[VideoInfo]
    query: str
    page: int = 1
    hasMore: bool = False


class VideoInfoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format: str = Field(..., pattern="^(mp4|mp3)$")  # "mp4" or "mp3"


class DownloadResponse(BaseModel):
    downloadId: str
    videoId: str
    downloadUrl: str
    fileName: str
    fileSize: Optional[int] = None
    format: str
    message: str = "Download initiated successfully"


class DownloadStatus(BaseModel):
    downloadId: str
    status: str  # "pending", "downloading", "completed", "failed", "cancelled"
    progress: float = 0.0  # 0-100
    downloadedBytes: int = 0
    totalBytes: int = 0
    error: Optional[str] = None


class CancelDownloadRequest(BaseModel):
    downloadId: str


# WebSocket message schemas
class WSMessage(BaseModel):
    type: str
    data: dict


class WSDownloadProgress(BaseModel):
    downloadId: str
    videoId: str
    progress: float  # 0-100
    downloadedBytes: int
    totalBytes: int
    speed: str
    eta: str


class WSDownloadComplete(BaseModel):
    downloadId: str
    videoId: str
    filePath: str
    fileName: str


class WSDownloadError(BaseModel):
    downloadId: str
    videoId: str
    error: str
