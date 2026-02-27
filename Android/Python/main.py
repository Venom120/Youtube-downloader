"""
Main Android Application - YouTube Downloader with Kivy

This is the new version using yt-dlp with MVC architecture
"""
from kivy.config import Config
Config.set('kivy', 'window_icon', 'assets/Youtube_icon.ico')

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()
import webbrowser

from kivy.app import App
from kivy import platform
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.network.urlrequest import UrlRequest
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex as hex

from models.video_model import VideoInfo, SearchResult
from controllers.search_controller import SearchController
from controllers.download_controller import DownloadController
from typing import Optional


class VideoCard(BoxLayout):
    """Card widget for displaying individual video with download buttons"""
    
    video_thumbnail = StringProperty('')
    video_title = StringProperty('')
    video_info = StringProperty('')
    badge_text = StringProperty('')
    
    def __init__(self, video: VideoInfo, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.video = video
        self.app = app_instance
        
        # Set properties from video info
        self.video_thumbnail = video.thumbnail_url
        # Truncate title similar to Windows version
        self.video_title = video.title if len(video.title) <= 80 else video.title[:77] + "..."
        
        # Build info text
        info_parts = [video.channel]
        if video.view_count:
            info_parts.append(f"{video.formatted_views} views")
        self.video_info = ' • '.join(info_parts)
        
        # Set badge text
        if video.is_playlist:
            playlist_count = int(video.playlist_count) if isinstance(video.playlist_count, (int, float)) else video.playlist_count
            self.badge_text = f"📑 {playlist_count}"
        elif video.duration > 0:
            self.badge_text = video.formatted_duration
        else:
            self.badge_text = ""
    
    def on_title_click(self):
        """Handle title click - open playlist if it's a playlist"""
        if self.video.is_playlist:
            self.app.show_playlist_videos(self.video)
    
    def on_mp4_click(self):
        """Handle MP4 download button click"""
        self.ids.mp4_btn.disabled = True
        self.ids.mp4_btn.text = "Downloading..."
        self.show_progress()
        
        self.app.start_download(self.video, 'mp4', self)
    
    def on_mp3_click(self):
        """Handle MP3 download button click"""
        self.ids.mp3_btn.disabled = True
        self.ids.mp3_btn.text = "Downloading..."
        self.show_progress()
        
        self.app.start_download(self.video, 'mp3', self)
    
    def show_progress(self):
        """Show progress bar"""
        self.ids.progress_box.height = dp(30)
        self.ids.progress_box.opacity = 1
    
    def update_progress(self, percentage: float):
        """Update download progress"""
        self.ids.progress_bar.value = percentage
        self.ids.progress_label.text = f"{int(percentage)}%"
    
    def download_complete(self, format_type: str):
        """Mark download as complete"""
        if format_type == 'mp4':
            self.ids.mp4_btn.text = "✓ Downloaded"
            self.ids.mp4_btn.disabled = False
            self.ids.mp4_btn.bg_color = (0, 0.8, 0, 1)
        else:
            self.ids.mp3_btn.text = "✓ Downloaded"
            self.ids.mp3_btn.disabled = False
            self.ids.mp3_btn.bg_color = (0, 0.8, 0, 1)
        
        self.ids.progress_label.text = "Complete!"
    
    def download_error(self, error_msg: str):
        """Show download error"""
        self.ids.mp4_btn.disabled = False
        self.ids.mp3_btn.disabled = False
        self.ids.mp4_btn.text = "📥 MP4"
        self.ids.mp3_btn.text = "🎵 MP3"
        self.ids.progress_label.text = f"❌ {error_msg[:30]}"


class YTDownloaderApp(BoxLayout):
    """Main application widget"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance
        self.current_mode = "search"  # "search" or "playlist"
        self.current_playlist: Optional[VideoInfo] = None
        
        # Pagination state
        self.current_search_result: Optional[SearchResult] = None
        self.current_page = 1
        self.items_per_page = 10
        self.total_pages = 1


class YoutubeDownloaderApp(App):
    """Main Kivy Application"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Setup download path based on platform
        if platform == 'android':
            from android.storage import primary_external_storage_path  # type: ignore
            self.download_path = f'{str(primary_external_storage_path())}/Download/YTDownloader/'
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.INTERNET
            ])
        else:
            self.download_path = os.path.expanduser("~/Downloads/YTDownloader/")
        
        # Initialize controllers
        self.search_controller = SearchController()
        self.download_controller = DownloadController(self.download_path)
        
        # Download dropdown state
        self.download_items = {}
        self.downloads_modal = None
        self.downloads_list = None
        self.downloads_empty_label = None
        
        # Create download directory if it doesn't exist
        try:
            os.makedirs(self.download_path, exist_ok=True)
        except:
            pass
    
    def build(self):
        """Build the application UI"""
        self.icon = "assets/Youtube_icon.png"
        Window.clearcolor = (15/255, 15/255, 15/255, 1)
        
        # Load KV file
        self.root = Builder.load_file("main.kv")
        
        # Create main app widget
        self.main_widget = YTDownloaderApp(app_instance=self)
        
        # Downloads modal
        self._create_downloads_modal()
        
        return self.main_widget
    
    def _create_downloads_modal(self):
        self.downloads_modal = ModalView(
            size_hint=(0.92, None),
            height=dp(420),
            auto_dismiss=True,
            background_color=(0, 0, 0, 0.35)
        )
        
        container = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        
        # Enhanced header with folder button
        header = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        title = Label(text='📥 Downloads', color=hex('#ffffff'), bold=True, font_size=sp(14))
        header.add_widget(title)
        header.add_widget(Widget(size_hint_x=1))
        
        # Folder button to open downloads location
        folder_btn = Button(text='📁', size_hint_x=None, width=dp(36), background_color=hex('#0066cc'))
        folder_btn.bind(on_release=lambda _btn: self._open_downloads_folder())  # type: ignore
        header.add_widget(folder_btn)
        
        close_btn = Button(text='✕', size_hint_x=None, width=dp(36), background_color=hex('#cc0000'))
        close_btn.bind(on_release=lambda _btn: self.downloads_modal.dismiss() if self.downloads_modal else None)  # type: ignore
        header.add_widget(close_btn)
        
        scroll = ScrollView(do_scroll_x=False)
        list_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        list_layout.bind(minimum_height=list_layout.setter('height'))  # type: ignore
        scroll.add_widget(list_layout)
        
        self.downloads_list = list_layout
        self.downloads_empty_label = Label(
            text='No active downloads',
            size_hint_y=None,
            height=dp(40),
            color=hex('#bbbbbb')
        )
        list_layout.add_widget(self.downloads_empty_label)
        
        container.add_widget(header)
        container.add_widget(scroll)
        self.downloads_modal.add_widget(container)
    
    def _open_downloads_folder(self):
        """Open downloads folder in file manager"""
        if platform == 'android':
            try:
                from jnius import autoclass  # type: ignore
                Toast = autoclass('android.widget.Toast')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                
                Toast.makeText(
                    PythonActivity.mActivity,
                    f"Downloads saved to: {self.download_path}",
                    Toast.LENGTH_LONG
                ).show()
                return
            except Exception:
                pass
        
        # Fallback: just show download path
        self.main_widget.ids.status_label.text = f"Downloads: {self.download_path}"
    
    def open_downloads_panel(self):
        if self.downloads_modal:
            self.downloads_modal.open()
    
    def _update_downloads_button(self):
        active_count = 0
        for task in self.download_controller.get_downloads():
            if task.status in {"queued", "downloading", "paused"}:
                active_count += 1
        
        if self.main_widget and 'downloads_btn' in self.main_widget.ids:
            self.main_widget.ids.downloads_btn.text = f"Downloads ({active_count})"
    
    def _add_download_item(self, download_id: str, video: VideoInfo, format_type: str, is_playlist: bool):
        if not self.downloads_list:
            return
        
        if self.downloads_empty_label and self.downloads_empty_label.parent:
            self.downloads_list.remove_widget(self.downloads_empty_label)
        
        # Main container with background styling
        row = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(110),
            padding=dp(8),
            spacing=dp(4),
            canvas_before=None
        )
        
        # Add background color
        from kivy.graphics import Color, RoundedRectangle
        with row.canvas.before:  # type: ignore
            Color(rgba=hex('#2b2b2b') if hex('#2b2b2b') else (0.17, 0.17, 0.17, 1))
            RoundedRectangle(size=row.size, pos=row.pos, radius=[8])
        
        row.bind(pos=self._update_bg, size=self._update_bg)  # type: ignore
        
        # Title
        title_text = video.title if len(video.title) <= 50 else f"{video.title[:47]}..."
        title = Label(
            text=title_text,
            size_hint_y=None,
            height=dp(20),
            color=hex('#ffffff'),
            font_size=sp(12),
            bold=True,
            halign='left',
            valign='top',
            text_size=(None, None)
        )
        
        # Format and status label
        format_label = 'Playlist' if is_playlist else format_type.upper()
        meta = Label(
            text=f"{format_label} · Queued",
            size_hint_y=None,
            height=dp(16),
            color=hex('#bbbbbb'),
            font_size=sp(10),
            halign='left',
            valign='top',
            text_size=(None, None)
        )
        
        # Progress bar
        progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(4)
        )
        
        # Action buttons
        actions = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(6))
        pause_btn = Button(
            text='⏸ Pause',
            size_hint_x=None,
            width=dp(85),
            background_color=hex('#0066cc'),
            font_size=sp(10)
        )
        cancel_btn = Button(
            text='✕ Cancel',
            size_hint_x=None,
            width=dp(85),
            background_color=hex('#cc0000'),
            font_size=sp(10)
        )
        
        pause_btn.bind(on_release=lambda _btn: self._on_pause_resume_clicked(download_id))  # type: ignore
        cancel_btn.bind(on_release=lambda _btn: self._on_cancel_clicked(download_id))  # type: ignore
        
        actions.add_widget(pause_btn)
        actions.add_widget(cancel_btn)
        
        # Add widgets to row
        row.add_widget(title)
        row.add_widget(meta)
        row.add_widget(progress)
        row.add_widget(actions)
        
        self.downloads_list.add_widget(row)
        self.download_items[download_id] = {
            'row': row,
            'meta': meta,
            'progress': progress,
            'pause_btn': pause_btn,
            'cancel_btn': cancel_btn
        }
        
        self._update_downloads_button()
    
    def _update_bg(self, instance, value):
        """Update background rectangle on size/pos change"""
        from kivy.graphics import Color, RoundedRectangle
        if instance.canvas.before:  # type: ignore
            instance.canvas.before.clear()  # type: ignore
        with instance.canvas.before:  # type: ignore
            Color(rgba=hex('#2b2b2b') if hex('#2b2b2b') else (0.17, 0.17, 0.17, 1))
            RoundedRectangle(size=instance.size, pos=instance.pos, radius=[8])
    
    def _update_download_item_progress(self, download_id: str, percentage: float):
        item = self.download_items.get(download_id)
        if not item:
            return
        
        item['progress'].value = percentage
        meta_prefix = item['meta'].text.split('·')[0].strip()
        item['meta'].text = f"{meta_prefix} · Downloading {int(percentage)}%"
    
    def _set_download_item_status(self, download_id: str, status: str, error_msg: Optional[str] = None):
        item = self.download_items.get(download_id)
        if not item:
            return
        
        meta_prefix = item['meta'].text.split('·')[0].strip()
        
        # Format status text
        if status == "Completed":
            status_text = "✓ Completed"
        elif status == "Canceled":
            status_text = "⊘ Canceled"
        elif status == "Error":
            status_text = f"❌ {error_msg[:30]}" if error_msg else "❌ Error"
        else:
            status_text = status
            
        item['meta'].text = f"{meta_prefix} · {status_text}"
        
        # Disable buttons for terminal states
        if status in {"Completed", "Canceled", "Error"}:
            item['pause_btn'].disabled = True
            item['cancel_btn'].disabled = True
            
            # Auto-remove item after 2 seconds
            Clock.schedule_once(
                lambda _dt: self._remove_download_item(download_id),
                2.0
            )
        
        self._update_downloads_button()
    
    def _remove_download_item(self, download_id: str):
        """Remove a download item from the list"""
        item = self.download_items.get(download_id)
        if item and item['row'].parent and self.downloads_list:
            self.downloads_list.remove_widget(item['row'])  # type: ignore
        
        if download_id in self.download_items:
            del self.download_items[download_id]
        
        # Show empty label if no more items
        if not self.download_items and self.downloads_empty_label and self.downloads_list:
            if not self.downloads_empty_label.parent:
                self.downloads_list.add_widget(self.downloads_empty_label)  # type: ignore
        
        self._update_downloads_button()
    
    def _on_pause_resume_clicked(self, download_id: str):
        task = self.download_controller.get_download(download_id)
        if not task:
            return
        
        if task.status == 'paused':
            if self.download_controller.resume_download(download_id):
                self.download_items[download_id]['pause_btn'].text = '⏸ Pause'
                self._set_download_item_status(download_id, 'Downloading')
        else:
            if self.download_controller.pause_download(download_id):
                self.download_items[download_id]['pause_btn'].text = '▶ Resume'
                self._set_download_item_status(download_id, 'Paused')
    
    def _on_cancel_clicked(self, download_id: str):
        if self.download_controller.cancel_download(download_id):
            self._set_download_item_status(download_id, 'Canceled')
    
    def start_download(self, video: VideoInfo, format_type: str, card: VideoCard):
        download_id = None
        
        def on_progress(p: float):
            if download_id:
                Clock.schedule_once(lambda _dt: self._update_download_item_progress(download_id, p))  # type: ignore
            Clock.schedule_once(lambda _dt: card.update_progress(p))
        
        def on_complete(_filename: str):
            if download_id:
                Clock.schedule_once(lambda _dt: self._set_download_item_status(download_id, 'Completed'))  # type: ignore
            Clock.schedule_once(lambda _dt: card.download_complete(format_type))
        
        def on_error(error: str):
            if download_id:
                Clock.schedule_once(lambda _dt: self._set_download_item_status(download_id, 'Error', error))  # type: ignore
            Clock.schedule_once(lambda _dt: self.handle_download_error(error, card))
        
        if video.is_playlist:
            download_id = self.download_controller.download_playlist(
                video,
                format_type=format_type,
                progress_callback=on_progress,
                complete_callback=on_complete,
                error_callback=on_error
            )
        else:
            download_id = self.download_controller.download_video(
                video,
                format_type=format_type,
                progress_callback=on_progress,
                complete_callback=on_complete,
                error_callback=on_error
            )
        
        Clock.schedule_once(lambda _dt: self._add_download_item(download_id, video, format_type, video.is_playlist))
        self._update_downloads_button()
    
    def on_search(self):
        """Handle search button click"""
        query = self.main_widget.ids.search_input.text.strip()
        
        if not query:
            return
        
        # Clear grid
        self.clear_video_grid()
        
        # Show loading
        self.main_widget.ids.status_label.text = "🔍 Searching..."
        
        # Check if it's a URL
        if "youtube.com" in query or "youtu.be" in query:
            # Get video info from URL
            self.search_controller.get_video_info(
                query,
                callback=lambda v: Clock.schedule_once(lambda dt: self.on_url_info_received(v)) if v is not None else None,
                error_callback=lambda e: Clock.schedule_once(lambda dt: self.on_error(e))
            )
        else:
            # Search for videos
            self.search_controller.search_videos(
                query,
                max_results=20,
                callback=lambda r: Clock.schedule_once(lambda dt: self.on_search_complete(r)),
                error_callback=lambda e: Clock.schedule_once(lambda dt: self.on_error(e))
            )
    
    def on_url_info_received(self, video: Optional[VideoInfo]):
        """Handle video info from URL"""
        if video is not None:
            self.main_widget.ids.status_label.text = f"Video: {video.title[:40]}"
            self.add_video_card(video)
        else:
            self.main_widget.ids.status_label.text = "❌ Invalid YouTube URL"
    
    def on_search_complete(self, result: SearchResult):
        """Handle search results with pagination"""
        if result.videos:
            self.current_search_result = result
            self.current_page = 1
            self.total_pages = (len(result.videos) + self.items_per_page - 1) // self.items_per_page
            self.display_search_page(1)
        else:
            self.main_widget.ids.status_label.text = f"No results found for '{result.query}'"
    
    def display_search_page(self, page: int):
        """Display a specific page of search results"""
        if not self.current_search_result or page < 1 or page > self.total_pages:
            return
        
        self.current_page = page
        self.clear_video_grid()
        
        # Calculate start and end indices
        start_idx = (page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.current_search_result.videos))
        
        # Display videos for this page
        for i, video in enumerate(self.current_search_result.videos[start_idx:end_idx]):
            self.add_video_card(video)
        
        # Update status with pagination info
        page_info = f"Found {len(self.current_search_result.videos)} results - Page {self.current_page} of {self.total_pages}"
        self.main_widget.ids.status_label.text = page_info
        
        # Add pagination controls if there are more pages
        if self.total_pages > 1:
            self.add_pagination_controls()
    
    def add_pagination_controls(self):
        """Add pagination buttons to the bottom of the video grid"""
        grid = self.main_widget.ids.video_grid
        
        # Create pagination button container
        pagination_layout = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10),
            padding=dp(10)
        )
        
        # Previous button
        if self.current_page > 1:
            prev_btn = Button(
                text='← Previous',
                size_hint_x=None,
                width=dp(100),
                background_color=hex('#0066cc')
            )
            prev_btn.bind(on_release=lambda x: Clock.schedule_once(lambda dt: self.on_load_prev_page()))  # type: ignore
            pagination_layout.add_widget(prev_btn)
        
        # Spacer
        pagination_layout.add_widget(BoxLayout(size_hint_x=1))
        
        # Next button  
        if self.current_page < self.total_pages:
            next_btn = Button(
                text='Next →',
                size_hint_x=None,
                width=dp(100),
                background_color=hex('#0066cc')
            )
            next_btn.bind(on_release=lambda x: Clock.schedule_once(lambda dt: self.on_load_next_page()))  # type: ignore
            pagination_layout.add_widget(next_btn)
        
        grid.add_widget(pagination_layout)
    
    def on_load_prev_page(self):
        """Load previous page of search results"""
        if self.current_page > 1:
            self.display_search_page(self.current_page - 1)
    
    def on_load_next_page(self):
        """Load next page of search results"""
        if self.current_page < self.total_pages:
            self.display_search_page(self.current_page + 1)
    
    def on_error(self, error: str):
        """Handle errors"""
        if self._handle_login_required(error):
            self.main_widget.ids.status_label.text = "⚠️ Login required. Opened YouTube for sign-in."
            return

        self.main_widget.ids.status_label.text = f"❌ Error: {error[:40]}"

    def handle_download_error(self, error: str, card: VideoCard):
        """Handle download errors and check for login requirements"""
        if self._handle_login_required(error):
            self.main_widget.ids.status_label.text = "⚠️ Login required. Opened YouTube for sign-in."
        card.download_error(error)

    def _handle_login_required(self, error: str) -> bool:
        """Check if login is required and open YouTube if needed"""
        if not error:
            return False

        lowered = error.lower()
        triggers = [
            "sign in",
            "login",
            "log in",
            "confirm your age",
            "age-restricted",
            "members only",
            "private video",
            "account required"
        ]

        if any(trigger in lowered for trigger in triggers):
            self._open_youtube_login()
            return True

        return False

    def _open_youtube_login(self):
        """Open YouTube login (app if possible, otherwise browser)"""
        if platform == 'android':
            try:
                from jnius import autoclass  # type: ignore
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                intent = Intent(Intent.ACTION_VIEW, Uri.parse("vnd.youtube://"))
                PythonActivity.mActivity.startActivity(intent)
                return
            except Exception:
                pass

        try:
            webbrowser.open("https://youtube.com")
        except Exception:
            pass
    
    def add_video_card(self, video: VideoInfo):
        """Add a video card to the grid"""
        card = VideoCard(video, self)
        self.main_widget.ids.video_grid.add_widget(card)
    
    def clear_video_grid(self):
        """Clear all video cards from the grid"""
        self.main_widget.ids.video_grid.clear_widgets()
    
    def show_playlist_videos(self, playlist: VideoInfo):
        """Show all videos from a playlist"""
        self.main_widget.current_mode = "playlist"
        self.main_widget.current_playlist = playlist
        
        # Show back button
        self.main_widget.ids.back_btn.opacity = 1
        self.main_widget.ids.back_btn.disabled = False
        
        # Clear grid and show loading
        self.clear_video_grid()
        self.main_widget.ids.status_label.text = f"📑 Loading playlist: {playlist.title[:30]}..."
        
        # Get playlist videos
        self.search_controller.get_playlist_videos(
            playlist.url,
            callback=lambda v: Clock.schedule_once(lambda dt: self.on_playlist_loaded(v)),
            error_callback=lambda e: Clock.schedule_once(lambda dt: self.on_error(e))
        )
    
    def on_playlist_loaded(self, videos):
        """Handle playlist videos loaded"""
        if videos and self.main_widget.current_playlist is not None:
            self.main_widget.ids.status_label.text = (
                f"📑 {self.main_widget.current_playlist.title[:30]} ({len(videos)} videos)"
            )
            
            for video in videos:
                self.add_video_card(video)
        else:
            self.main_widget.ids.status_label.text = "❌ Failed to load playlist"
    
    def back_to_search(self):
        """Return to search from playlist view"""
        self.main_widget.current_mode = "search"
        self.main_widget.current_playlist = None
        
        # Hide back button
        self.main_widget.ids.back_btn.opacity = 0
        self.main_widget.ids.back_btn.disabled = True
        
        # Clear grid
        self.clear_video_grid()
        self.main_widget.ids.status_label.text = "Search for videos or paste a YouTube URL"


if __name__ == "__main__":
    YoutubeDownloaderApp().run()
