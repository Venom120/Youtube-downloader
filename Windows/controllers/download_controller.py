"""
Download Controller - Manages download operations
"""
import threading
import uuid
import queue
from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, List, Union
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
    custom_path: Optional[str] = None


class DownloadController:
    """Controller for handling download operations"""

    def __init__(self, download_path: str = ""):
        """Initialize download controller"""
        self.ytdlp = YTDLPWrapper(download_path)
        self.downloads: Dict[str, DownloadTask] = {}
        self.active_downloads: Dict[str, DownloadTask] = {}
        self.download_history: List[Dict[str, Union[str, VideoInfo]]] = []
        
        # Download queue for sequential processing
        self.download_queue: queue.Queue = queue.Queue()
        self.queue_processor_thread: Optional[threading.Thread] = None
        self.queue_lock = threading.Lock()
        self.is_processing = False
        self._start_queue_processor()

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
                    if error_callback and not task.cancel_event.is_set():
                        error_callback(task.error)
            except Exception as e:
                if task.cancel_event.is_set():
                    task.status = "canceled"
                    task.error = "Canceled"
                else:
                    task.status = "error"
                    task.error = str(e)
                if error_callback and not task.cancel_event.is_set():
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
                    if error_callback and not task.cancel_event.is_set():
                        error_callback(task.error)
            except Exception as e:
                if task.cancel_event.is_set():
                    task.status = "canceled"
                    task.error = "Canceled"
                else:
                    task.status = "error"
                    task.error = str(e)
                if error_callback and not task.cancel_event.is_set():
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
    
    def _start_queue_processor(self):
        """Start the queue processor thread that handles sequential downloads"""
        if self.queue_processor_thread is not None and self.queue_processor_thread.is_alive():
            return
        
        def process_queue():
            while True:
                try:
                    # Get next task from queue (blocks until available)
                    task_data = self.download_queue.get(timeout=1)
                    
                    if task_data is None:  # Poison pill to stop thread
                        break
                    
                    # Process the download
                    task, progress_cb, complete_cb, error_cb = task_data
                    
                    with self.queue_lock:
                        self.is_processing = True
                    
                    # Execute the download synchronously
                    self._execute_download(task, progress_cb, complete_cb, error_cb)
                    
                    with self.queue_lock:
                        self.is_processing = False
                    
                    # Mark task as done
                    self.download_queue.task_done()
                    
                except queue.Empty:
                    continue
                except Exception:
                    with self.queue_lock:
                        self.is_processing = False
        
        self.queue_processor_thread = threading.Thread(target=process_queue, daemon=True)
        self.queue_processor_thread.start()
    
    def _execute_download(self, task: DownloadTask, progress_callback, complete_callback, error_callback):
        """Execute a single download task"""
        try:
            task.status = "downloading"
            self.active_downloads[task.download_id] = task
            
            # Use custom download path if specified
            original_path = self.ytdlp.download_path
            if hasattr(task, 'custom_path') and task.custom_path:
                self.ytdlp.download_path = task.custom_path

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
                task.video.url,
                task.format_type,
                on_progress,
                on_complete,
                should_cancel=task.cancel_event.is_set,
                should_pause=lambda: not task.pause_event.is_set()
            )
            
            # Restore original path
            self.ytdlp.download_path = original_path

            if success:
                self.download_history.append({
                    'video': task.video,
                    'format': task.format_type,
                    'status': 'completed'
                })
            else:
                if task.cancel_event.is_set():
                    task.status = "canceled"
                    task.error = "Canceled"
                else:
                    task.status = "error"
                    task.error = "Download failed"
                if error_callback and not task.cancel_event.is_set():
                    error_callback(task.error)
        except Exception as e:
            # Restore original path on error
            if hasattr(task, 'custom_path') and task.custom_path:
                self.ytdlp.download_path = original_path
            
            if task.cancel_event.is_set():
                task.status = "canceled"
                task.error = "Canceled"
            else:
                task.status = "error"
                task.error = str(e)
            if error_callback and not task.cancel_event.is_set():
                error_callback(task.error or "Download failed")
        finally:
            if task.download_id in self.active_downloads:
                del self.active_downloads[task.download_id]
    
    def queue_download(
        self,
        video: VideoInfo,
        format_type: str = 'mp4',
        progress_callback: Optional[Callable[[float], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        custom_download_path: Optional[str] = None
    ) -> str:
        """Queue a video download to be processed sequentially"""
        task = self._create_task(video, format_type, is_playlist=False)
        
        # Store custom download path in task if provided
        if custom_download_path:
            task.custom_path = custom_download_path
        
        # Add to queue
        self.download_queue.put((task, progress_callback, complete_callback, error_callback))
        
        return task.download_id
