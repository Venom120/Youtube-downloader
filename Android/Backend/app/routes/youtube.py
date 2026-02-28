from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
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


@router.post("/search", response_model=SearchResult)
async def search_videos(request: SearchRequest):
    """
    Search for YouTube videos
    """
    try:
        videos_dict = await ytdlp_service.search_videos(request.query, request.maxResults)
        videos = [VideoInfo(**video) for video in videos_dict]
        
        return SearchResult(
            videos=videos,
            query=request.query,
            page=1,
            hasMore=len(videos) >= request.maxResults,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/video-info", response_model=VideoInfo)
async def get_video_info(request: VideoInfoRequest):
    """
    Get information about a specific video
    """
    try:
        video_info = await ytdlp_service.get_video_info(request.url)
        
        if not video_info:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return VideoInfo(**video_info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video info: {str(e)}")


@router.post("/download", response_model=DownloadResponse)
async def initiate_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Initiate video download
    Returns download ID and URL for client to download the file
    """
    try:
        # Start download asynchronously
        download_info = await ytdlp_service.download_video(
            request.url,
            request.format,
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
