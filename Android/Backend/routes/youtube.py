from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

from models.schemas import (
    SearchRequest,
    SearchResult,
    VideoInfoRequest,
    VideoInfo,
    DownloadRequest,
    DownloadResponse,
    DownloadStatus,
    CancelDownloadRequest,
)
from services.ytdlp_service import ytdlp_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/search", response_model=SearchResult)
@limiter.limit("30/minute")
async def search_videos(request_body: SearchRequest, request: Request):
    """
    Search for YouTube videos
    """
    try:
        videos_dict = await ytdlp_service.search_videos(request_body.query, request_body.maxResults)
        videos = [VideoInfo(**video) for video in videos_dict]
        
        return SearchResult(
            videos=videos,
            query=request_body.query,
            page=1,
            hasMore=len(videos) >= request_body.maxResults,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/video-info", response_model=VideoInfo)
@limiter.limit("50/minute")
async def get_video_info(request_body: VideoInfoRequest, request: Request):
    """
    Get information about a specific video
    """
    try:
        video_info = await ytdlp_service.get_video_info(request_body.url)
        
        if not video_info:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return VideoInfo(**video_info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video info: {str(e)}")


@router.post("/download", response_model=DownloadResponse)
@limiter.limit("20/minute")
async def initiate_download(request_body: DownloadRequest, request: Request, background_tasks: BackgroundTasks):
    """
    Initiate video download
    Returns download ID and URL for client to download the file
    """
    try:
        # Start download asynchronously
        download_info = await ytdlp_service.download_video(
            request_body.url,
            request_body.format,
        )
        
        return DownloadResponse(**download_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download initiation failed: {str(e)}")


@router.get("/download-status/{download_id}", response_model=DownloadStatus)
async def get_download_status(download_id: str):
    """
    Get status of a download
    """
    status = ytdlp_service.get_download_status(download_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Download not found")
    
    return DownloadStatus(**status)


@router.get("/download-file/{download_id}")
async def download_file(download_id: str):
    """
    Download the completed file
    """
    filepath = ytdlp_service.get_download_file(download_id)
    
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found or download not completed")
    
    filename = os.path.basename(filepath)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("/cancel-download")
async def cancel_download(request: CancelDownloadRequest):
    """
    Cancel an active download
    """
    success = ytdlp_service.cancel_download(request.downloadId)
    
    if not success:
        raise HTTPException(status_code=404, detail="Download not found")
    
    return {"message": "Download cancelled successfully", "downloadId": request.downloadId}
