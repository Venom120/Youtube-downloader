"""
Download Controller - Manages download operations
"""
import threading
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, List
from models.ytdlp_wrapper import YTDLPWrapper
from models.video_model import VideoInfo


@dataclass
class DownloadTask:
    download_id: str
    video: VideoInfo
    format_type: str
    is_playlist: bool
    status: str = "queued"
    progress: float = 0.0
    error: Optional[str] = None
    thread: Optional[threading.Thread] = None
    pause_event: threading.Event = field(default_factory=threading.Event)
    cancel_event: threading.Event = field(default_factory=threading.Event)


class DownloadController:
    """Controller for handling download operations"""

    def __init__(self, download_path: str = ""):
        """Initialize download controller"""
        self.ytdlp = YTDLPWrapper(download_path)
        self.downloads: Dict[str, DownloadTask] = {}
        self.active_downloads: Dict[str, DownloadTask] = {}
        self.download_history: List[Dict[str, str]] = []

    def download_video(
        self,
        video: VideoInfo,
        format_type: str = 'mp4',
        progress_callback: Optional[Callable[[float], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Start downloading a video in a separate thread"""
        task = self._create_task(video, format_type, is_playlist=False)

        def download_thread():
            try:
                task.status = "downloading"

                def on_progress(p: float) -> None:
                    task.progress = p
                    if progress_callback:
                        progress_callback(p)

                def on_complete(filename: str) -> None:
                    task.progress = 100
                    task.status = "completed"
                    if complete_callback:
                        complete_callback(filename)

                success = self.ytdlp.download_video(
                    video.url,
                    format_type,
                    on_progress,
                    on_complete,
                    should_cancel=task.cancel_event.is_set,
                    should_pause=lambda: not task.pause_event.is_set()
                )

                if success:
                    self.download_history.append({
                        'video': video,
                        'format': format_type,
                        'status': 'completed'
                    })
                else:
                    if task.cancel_event.is_set():
                        task.status = "canceled"
                        task.error = "Canceled"
                    else:
                        task.status = "error"
                        task.error = "Download failed"
                    if error_callback:
                        error_callback(task.error)
            except Exception as e:
                if task.cancel_event.is_set():
                    task.status = "canceled"
                    task.error = "Canceled"
                else:
                    task.status = "error"
                    task.error = str(e)
                if error_callback:
                    error_callback(task.error or "Download failed")
            finally:
                if task.download_id in self.active_downloads:
                    del self.active_downloads[task.download_id]

        thread = threading.Thread(target=download_thread, daemon=True)
        task.thread = thread
        self.active_downloads[task.download_id] = task
        thread.start()
        return task.download_id

    def download_playlist(
        self,
        playlist: VideoInfo,
        format_type: str = 'mp4',
        progress_callback: Optional[Callable[[float], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Start downloading a playlist in a separate thread"""
        task = self._create_task(playlist, format_type, is_playlist=True)

        def download_thread():
            try:
                task.status = "downloading"

                def on_progress(p: float) -> None:
                    task.progress = p
                    if progress_callback:
                        progress_callback(p)

                def on_complete(filename: str) -> None:
                    task.progress = 100
                    task.status = "completed"
                    if complete_callback:
                        complete_callback(filename)

                success = self.ytdlp.download_playlist(
                    playlist.url,
                    format_type,
                    on_progress,
                    on_complete,
                    should_cancel=task.cancel_event.is_set,
                    should_pause=lambda: not task.pause_event.is_set()
                )

                if success:
                    self.download_history.append({
                        'video': playlist,
                        'format': format_type,
                        'status': 'completed'
                    })
                else:
                    if task.cancel_event.is_set():
                        task.status = "canceled"
                        task.error = "Canceled"
                    else:
                        task.status = "error"
                        task.error = "Playlist download failed"
                    if error_callback:
                        error_callback(task.error)
            except Exception as e:
                if task.cancel_event.is_set():
                    task.status = "canceled"
                    task.error = "Canceled"
                else:
                    task.status = "error"
                    task.error = str(e)
                if error_callback:
                    error_callback(task.error or "Playlist download failed")
            finally:
                if task.download_id in self.active_downloads:
                    del self.active_downloads[task.download_id]

        thread = threading.Thread(target=download_thread, daemon=True)
        task.thread = thread
        self.active_downloads[task.download_id] = task
        thread.start()
        return task.download_id

    def pause_download(self, download_id: str) -> bool:
        task = self.downloads.get(download_id)
        if not task or task.status not in {"downloading", "queued"}:
            return False
        task.pause_event.clear()
        task.status = "paused"
        return True

    def resume_download(self, download_id: str) -> bool:
        task = self.downloads.get(download_id)
        if not task or task.status != "paused":
            return False
        task.pause_event.set()
        task.status = "downloading"
        return True

    def cancel_download(self, download_id: str) -> bool:
        task = self.downloads.get(download_id)
        if not task or task.status in {"completed", "canceled", "error"}:
            return False
        task.cancel_event.set()
        task.pause_event.set()
        task.status = "canceled"
        task.error = "Canceled"
        return True

    def get_download(self, download_id: str) -> Optional[DownloadTask]:
        return self.downloads.get(download_id)

    def get_downloads(self) -> List[DownloadTask]:
        return list(self.downloads.values())

    def is_downloading(self, download_id: str) -> bool:
        """Check if a download is currently active"""
        return download_id in self.active_downloads

    def _create_task(self, video: VideoInfo, format_type: str, is_playlist: bool) -> DownloadTask:
        download_id = uuid.uuid4().hex
        task = DownloadTask(
            download_id=download_id,
            video=video,
            format_type=format_type,
            is_playlist=is_playlist
        )
        task.pause_event.set()
        self.downloads[download_id] = task
        return task
