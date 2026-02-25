"""
Main Application Window - YouTube-like interface with search and downloads
"""
import sys
import os
import webbrowser
import customtkinter as cust
import tkinter as tk
from typing import List, Optional, Callable
from models.video_model import VideoInfo, SearchResult
from controllers.search_controller import SearchController
from controllers.download_controller import DownloadController
from views.video_card import VideoCard


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class VerticalListFrame(cust.CTkScrollableFrame):
    """Scrollable frame for displaying videos in a vertical list"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.cards = []
        self.pagination_frame = None
        
        # Configure single column
        self.grid_columnconfigure(0, weight=1)
    
    def add_card(self, card: VideoCard, position: Optional[int] = None):
        """Add a card to the list"""
        if position is None:
            position = len(self.cards)
        
        self.cards.append(card)
        
        # Place card in vertical list with full width
        card.grid(
            row=position,
            column=0,
            padx=8,
            pady=8,
            sticky="ew"
        )
    
    def clear_cards(self):
        """Remove all cards from the list"""
        for card in self.cards:
            card.destroy()
        
        self.cards = []
        
        # Remove pagination frame if exists
        if self.pagination_frame and self.pagination_frame.winfo_exists():
            self.pagination_frame.destroy()
            self.pagination_frame = None
    
    def add_pagination_controls(self, page_info: str, on_prev_click: Callable, on_next_click: Callable, show_prev: bool, show_next: bool):
        """Add pagination controls with prev/next buttons"""
        # Remove old pagination frame if exists
        if self.pagination_frame and self.pagination_frame.winfo_exists():
            self.pagination_frame.destroy()
        
        # Create new pagination frame
        self.pagination_frame = cust.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.grid(
            row=len(self.cards),
            column=0,
            padx=8,
            pady=16,
            sticky="ew"
        )
        self.pagination_frame.grid_columnconfigure(0, weight=1)
        self.pagination_frame.grid_columnconfigure(1, weight=0)
        self.pagination_frame.grid_columnconfigure(2, weight=0)
        self.pagination_frame.grid_columnconfigure(3, weight=0)
        
        # Previous button
        if show_prev:
            prev_btn = cust.CTkButton(
                self.pagination_frame,
                text="← Previous",
                width=100,
                height=35,
                font=cust.CTkFont(size=11),
                fg_color=("#0066cc", "#0080ff"),
                hover_color=("#0052a3", "#0066cc"),
                text_color="white",
                command=on_prev_click
            )
            prev_btn.grid(row=0, column=1, padx=5)
        
        # Page info label (centered)
        page_label = cust.CTkLabel(
            self.pagination_frame,
            text=page_info,
            font=cust.CTkFont(size=12),
            text_color=("#666666", "#999999")
        )
        page_label.grid(row=0, column=2, padx=5)
        
        # Next button
        if show_next:
            next_btn = cust.CTkButton(
                self.pagination_frame,
                text="Next →",
                width=100,
                height=35,
                font=cust.CTkFont(size=11),
                fg_color=("#0066cc", "#0080ff"),
                hover_color=("#0052a3", "#0066cc"),
                text_color="white",
                command=on_next_click
            )
            next_btn.grid(row=0, column=3, padx=5)


class MainWindow:
    """Main application window"""
    
    def __init__(self):
        """Initialize main window"""
        # Setup download path
        import os
        self.download_path = os.path.expanduser("~/Downloads/YTDownloader")
        
        # Create download directory if it doesn't exist
        try:
            os.makedirs(self.download_path, exist_ok=True)
        except Exception:
            pass
        
        # Initialize controllers with download path
        self.search_controller = SearchController()
        self.download_controller = DownloadController(self.download_path)
        
        # Current state
        self.current_mode = "search"  # "search", "playlist", or "url"
        self.current_playlist = None
        self.card_references = {}  # Map video_id to card for progress updates
        
        # Pagination state
        self.current_search_result = None  # Store all search results
        self.current_page = 1
        self.items_per_page = 10
        self.total_pages = 1
        
        # Setup UI
        self._setup_window()
        self._create_widgets()
    
    def _setup_window(self):
        """Setup main window properties"""
        cust.set_appearance_mode("dark")
        cust.set_default_color_theme("blue")
        
        self.app = cust.CTk()
        self.app.title("YouTube Downloader")
        self.app.geometry("1200x800")
        
        # Set icon
        try:
            self.app.iconbitmap(resource_path("assets/Youtube_icon.ico"))
        except:
            pass
        
        # Configure grid weights
        self.app.grid_rowconfigure(3, weight=1)  # Only scrollable frame expands
        self.app.grid_columnconfigure(0, weight=1)
        
        # Set minimum size - prevent UI breakage on resize
        self.app.minsize(960, 720)
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # ===== HEADER SECTION =====
        header_frame = cust.CTkFrame(self.app, fg_color=("#ffffff", "#1a1a1a"), height=90)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)
        
        # Logo/Title and Search in same area
        left_container = cust.CTkFrame(header_frame, fg_color="transparent")
        left_container.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        
        title_label = cust.CTkLabel(
            left_container,
            text="▶ YouTube Downloader",
            font=cust.CTkFont(size=22, weight="bold"),
            text_color=("#cc0000", "#ff0000")
        )
        title_label.pack(side="left", padx=(0, 20))
        
        # Search section
        search_frame = cust.CTkFrame(left_container, fg_color="transparent")
        search_frame.pack(side="left", fill="x", expand=True)
        
        # Search input with rounded style
        self.search_entry = cust.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search videos or paste YouTube URL...",
            height=45,
            font=cust.CTkFont(size=13),
            bg_color="transparent",
            border_color=("#cccccc", "#404040"),
            border_width=2
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._on_search())
        
        # Search button with better styling
        search_btn = cust.CTkButton(
            search_frame,
            text="Search",
            width=100,
            height=45,
            font=cust.CTkFont(size=13, weight="bold"),
            fg_color=("#cc0000", "#ff0000"),
            hover_color=("#990000", "#cc0000"),
            text_color="white"
        )
        search_btn.pack(side="left")
        search_btn.configure(command=self._on_search)
        
        # ===== ERROR/INFO BANNER =====
        self.info_frame = cust.CTkFrame(self.app, fg_color=("#ffe6e6", "#4a1a1a"), height=45)
        self.info_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0, columnspan=10)
        self.info_frame.grid_propagate(False)
        self.info_frame.grid_remove()  # Hide initially until error occurs
        self.info_frame.lift()  # Bring to front (z-index)
        
        self.error_label = cust.CTkLabel(
            self.info_frame,
            text="",
            font=cust.CTkFont(size=12),
            text_color=("#cc0000", "#ff6666"),
            wraplength=800
        )
        self.error_label.pack(padx=15, pady=8)
        
        # ===== NAVIGATION BAR =====
        nav_frame = cust.CTkFrame(self.app, fg_color=("#f0f0f0", "#262626"), height=50)
        nav_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        nav_frame.grid_propagate(False)
        
        # Back button (for playlist view)
        self.back_button = cust.CTkButton(
            nav_frame,
            text="← Back",
            width=100,
            height=35,
            font=cust.CTkFont(size=12, weight="bold"),
            fg_color=("#cc0000", "#ff0000"),
            hover_color=("#990000", "#cc0000"),
            text_color="white",
            command=self._back_to_search
        )
        self.back_button.pack(side="left", padx=15, pady=7)
        self.back_button.pack_forget()  # Hide initially
        
        # Status/Title label
        self.status_label = cust.CTkLabel(
            nav_frame,
            text="Search for videos to get started",
            font=cust.CTkFont(size=13, weight="bold"),
            text_color=("#333333", "#e0e0e0")
        )
        self.status_label.pack(side="left", padx=15)
        
        # ===== MAIN CONTENT AREA =====
        self.scrollable_frame = VerticalListFrame(
            self.app,
            fg_color=("#f5f5f5", "#0f0f0f")
        )
        self.scrollable_frame.grid(row=3, column=0, sticky="nsew", padx=0, pady=0)
        
        # ===== WELCOME MESSAGE =====
        self._show_welcome_message()
    
    def _show_error(self, error_message: str):
        """Show error in the info banner"""
        self.info_frame.grid()  # Show the frame
        self.info_frame.configure(height=45)
        self.error_label.configure(text=error_message)
    
    def _hide_error(self):
        """Hide the error banner"""
        self.info_frame.grid_remove()  # Completely remove from layout
        self.error_label.configure(text="")
    
    def _show_welcome_message(self):
        """Show welcome message when no search results"""
        self.welcome_frame = cust.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent"
        )
        self.welcome_frame.grid(row=0, column=0, pady=80, padx=20)
        
        welcome_label = cust.CTkLabel(
            self.welcome_frame,
            text="▶ Welcome to YouTube Downloader",
            font=cust.CTkFont(size=32, weight="bold"),
            text_color=("#cc0000", "#ff0000")
        )
        welcome_label.pack(pady=10)
        
        instruction_label = cust.CTkLabel(
            self.welcome_frame,
            text="Search for videos or paste a YouTube URL to download",
            font=cust.CTkFont(size=16),
            text_color=("#555555", "#aaaaaa")
        )
        instruction_label.pack()
        
        sub_instruction = cust.CTkLabel(
            self.welcome_frame,
            text="Download videos in MP4 or MP3 format · No sign-up required",
            font=cust.CTkFont(size=13),
            text_color=("#888888", "#777777")
        )
        sub_instruction.pack(pady=(10, 0))
    
    def _hide_welcome_message(self):
        """Hide welcome message"""
        if hasattr(self, 'welcome_frame') and self.welcome_frame.winfo_exists():
            self.welcome_frame.destroy()
    
    def _on_search(self):
        """Handle search button click or Enter key"""
        query = self.search_entry.get().strip()
        
        if not query:
            return
        
        # Clear any previous errors
        self._hide_error()
        
        # Show loading
        self.status_label.configure(text="🔍 Searching...")
        self.scrollable_frame.clear_cards()
        self._hide_welcome_message()
        
        # Check if it's a URL
        if "youtube.com" in query or "youtu.be" in query:
            # It's a URL - get video info
            self.search_controller.get_video_info(
                query,
                callback=self._on_url_info_received,
                error_callback=self._on_search_error
            )
        else:
            # It's a search query
            self.search_controller.search_videos(
                query,
                max_results=20,
                callback=self._on_search_complete,
                error_callback=self._on_search_error
            )
    
    def _on_url_info_received(self, video: Optional[VideoInfo]):
        """Handle video info from URL"""
        self.scrollable_frame.clear_cards()
        
        if video is not None:
            self.current_mode = "url"
            self.current_search_result = None
            self.current_page = 1
            self.total_pages = 1
            self.status_label.configure(text=f"Video: {video.title[:50]}")
            
            # Create card for the video/playlist
            card = self._create_video_card(video)
            self.scrollable_frame.add_card(card)
        else:
            self.status_label.configure(text="❌ Invalid YouTube URL")
    
    def _on_search_complete(self, result: SearchResult):
        """Handle search results"""
        self.scrollable_frame.clear_cards()
        
        if result.videos:
            self.current_mode = "search"
            self.current_search_result = result  # Store all results in memory
            self.current_page = 1
            self.total_pages = (len(result.videos) + self.items_per_page - 1) // self.items_per_page
            
            self.status_label.configure(
                text=f"Found {len(result.videos)} results for '{result.query}'"
            )
            
            # Display first page of results
            self._display_search_page(1)
        else:
            self.status_label.configure(text=f"No results found for '{result.query}'")
            
            no_results_label = cust.CTkLabel(
                self.scrollable_frame,
                text="😕 No videos found\nTry a different search term",
                font=cust.CTkFont(size=18),
                text_color=("#666666", "#999999")
            )
            no_results_label.grid(row=0, column=0, columnspan=3, pady=100)
    
    def _display_search_page(self, page: int):
        """Display a specific page of search results"""
        if not self.current_search_result or page < 1 or page > self.total_pages:
            return
        
        self.current_page = page
        self.scrollable_frame.clear_cards()
        
        # Calculate start and end indices
        start_idx = (page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.current_search_result.videos))
        
        # Display videos for this page
        for i, video in enumerate(self.current_search_result.videos[start_idx:end_idx]):
            card = self._create_video_card(video)
            self.scrollable_frame.add_card(card)
        
        # Add pagination controls if there are more pages
        if self.total_pages > 1:
            page_info = f"Page {self.current_page} of {self.total_pages}"
            show_prev = self.current_page > 1
            show_next = self.current_page < self.total_pages
            self.scrollable_frame.add_pagination_controls(
                page_info,
                self._on_load_prev_page,
                self._on_load_next_page,
                show_prev,
                show_next
            )
    
    def _on_load_prev_page(self):
        """Load previous page of search results"""
        if self.current_page > 1:
            self._display_search_page(self.current_page - 1)
            # Scroll to top of results
            self.scrollable_frame._parent_canvas.yview_moveto(0)
    
    def _on_load_next_page(self):
        """Load next page of search results"""
        if self.current_page < self.total_pages:
            self._display_search_page(self.current_page + 1)
            # Scroll to top of results
            self.scrollable_frame._parent_canvas.yview_moveto(0)
    
    def _on_search_error(self, error: str):
        """Handle search error"""
        if self._handle_login_required(error):
            self._show_error("⚠️ Login required. Opening YouTube for sign-in...")
            self.status_label.configure(text="Please sign in to your YouTube account")
            self.scrollable_frame.clear_cards()
            return

        self._show_error(f"Error: {error[:100]}")
        self.status_label.configure(text="Search failed. Please try again.")
        self.scrollable_frame.clear_cards()
        self.current_search_result = None
    
    def _create_video_card(self, video: VideoInfo) -> VideoCard:
        """Create a video card with download callbacks"""
        card = VideoCard(
            self.scrollable_frame,
            video=video,
            on_mp4_click=lambda v: self._on_download_mp4(v, card),
            on_mp3_click=lambda v: self._on_download_mp3(v, card),
            on_title_click=self._on_playlist_click if video.is_playlist else None
        )
        
        # Store reference for progress updates
        self.card_references[video.video_id] = card
        
        return card
    
    def _on_download_mp4(self, video: VideoInfo, card: VideoCard):
        """Handle MP4 download"""
        if video.is_playlist:
            # Download entire playlist
            self.download_controller.download_playlist(
                video,
                format_type='mp4',
                progress_callback=lambda p: card.update_progress(p),
                complete_callback=lambda f: card.download_complete('mp4'),
                error_callback=lambda e: self._on_download_error(e, card)
            )
        else:
            # Download single video
            self.download_controller.download_video(
                video,
                format_type='mp4',
                progress_callback=lambda p: card.update_progress(p),
                complete_callback=lambda f: card.download_complete('mp4'),
                error_callback=lambda e: self._on_download_error(e, card)
            )
    
    def _on_download_mp3(self, video: VideoInfo, card: VideoCard):
        """Handle MP3 download"""
        if video.is_playlist:
            # Download entire playlist as MP3
            self.download_controller.download_playlist(
                video,
                format_type='mp3',
                progress_callback=lambda p: card.update_progress(p),
                complete_callback=lambda f: card.download_complete('mp3'),
                error_callback=lambda e: self._on_download_error(e, card)
            )
        else:
            # Download single video as MP3
            self.download_controller.download_video(
                video,
                format_type='mp3',
                progress_callback=lambda p: card.update_progress(p),
                complete_callback=lambda f: card.download_complete('mp3'),
                error_callback=lambda e: self._on_download_error(e, card)
            )

    def _on_download_error(self, error: str, card: VideoCard):
        """Handle download errors and check for login requirements"""
        if self._handle_login_required(error):
            self._show_error("⚠️ Login required. Opening YouTube for sign-in...")
        else:
            self._show_error(f"Download error: {error[:80]}")
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
            self._open_login_page()
            return True

        return False

    def _open_login_page(self):
        """Open YouTube login page in the default browser"""
        try:
            webbrowser.open("https://youtube.com")
        except Exception:
            pass
    
    def _on_playlist_click(self, playlist: VideoInfo):
        """Handle playlist title click - show all videos in playlist"""
        if not playlist.is_playlist:
            return
        
        # Show loading
        self.status_label.configure(text=f"📑 Loading playlist: {playlist.title[:40]}...")
        self.scrollable_frame.clear_cards()
        self.current_mode = "playlist"
        self.current_playlist = playlist
        
        # Show back button
        self.back_button.pack(side="left", padx=15, pady=7)
        
        loading_label = cust.CTkLabel(
            self.scrollable_frame,
            text="Loading playlist videos...",
            font=cust.CTkFont(size=18),
            text_color=("#666666", "#999999")
        )
        loading_label.grid(row=0, column=0, columnspan=3, pady=100)
        
        # Get playlist videos
        self.search_controller.get_playlist_videos(
            playlist.url,
            callback=self._on_playlist_videos_loaded,
            error_callback=self._on_search_error
        )
    
    def _on_playlist_videos_loaded(self, videos: List[VideoInfo]):
        """Handle playlist videos loaded"""
        self.scrollable_frame.clear_cards()
        
        if videos and self.current_playlist is not None:
            self.status_label.configure(
                text=f"📑 Playlist: {self.current_playlist.title[:40]} ({len(videos)} videos)"
            )
            
            # Create cards for each video in playlist
            for video in videos:
                card = self._create_video_card(video)
                self.scrollable_frame.add_card(card)
        else:
            self.status_label.configure(text="❌ Failed to load playlist videos")
    
    def _back_to_search(self):
        """Return to search results from playlist view"""
        self.current_mode = "search"
        self.current_playlist = None
        self.current_search_result = None
        self.current_page = 1
        self.total_pages = 1
        self.back_button.pack_forget()
        
        # Clear and show welcome
        self.scrollable_frame.clear_cards()
        self.status_label.configure(text="Search for videos or paste a YouTube URL")
        self._show_welcome_message()
    
    def run(self):
        """Start the application"""
        self.app.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()
