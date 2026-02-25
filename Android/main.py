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
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.network.urlrequest import UrlRequest
from kivy.metrics import dp
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
        
        if self.video.is_playlist:
            self.app.download_controller.download_playlist(
                self.video,
                format_type='mp4',
                progress_callback=lambda p: Clock.schedule_once(lambda dt: self.update_progress(p)),
                complete_callback=lambda f: Clock.schedule_once(lambda dt: self.download_complete('mp4')),
                error_callback=lambda e: Clock.schedule_once(lambda dt: self.app.handle_download_error(e, self))
            )
        else:
            self.app.download_controller.download_video(
                self.video,
                format_type='mp4',
                progress_callback=lambda p: Clock.schedule_once(lambda dt: self.update_progress(p)),
                complete_callback=lambda f: Clock.schedule_once(lambda dt: self.download_complete('mp4')),
                error_callback=lambda e: Clock.schedule_once(lambda dt: self.app.handle_download_error(e, self))
            )
    
    def on_mp3_click(self):
        """Handle MP3 download button click"""
        self.ids.mp3_btn.disabled = True
        self.ids.mp3_btn.text = "Downloading..."
        self.show_progress()
        
        if self.video.is_playlist:
            self.app.download_controller.download_playlist(
                self.video,
                format_type='mp3',
                progress_callback=lambda p: Clock.schedule_once(lambda dt: self.update_progress(p)),
                complete_callback=lambda f: Clock.schedule_once(lambda dt: self.download_complete('mp3')),
                error_callback=lambda e: Clock.schedule_once(lambda dt: self.app.handle_download_error(e, self))
            )
        else:
            self.app.download_controller.download_video(
                self.video,
                format_type='mp3',
                progress_callback=lambda p: Clock.schedule_once(lambda dt: self.update_progress(p)),
                complete_callback=lambda f: Clock.schedule_once(lambda dt: self.download_complete('mp3')),
                error_callback=lambda e: Clock.schedule_once(lambda dt: self.app.handle_download_error(e, self))
            )
    
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
        
        return self.main_widget
    
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
