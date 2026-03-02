"""
Main Application Window - YouTube-like interface with search and downloads
"""
import sys
import os
import webbrowser
import customtkinter as cust
import tkinter as tk
import subprocess
from tkinter import messagebox
from typing import List, Optional, Callable, Dict
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
        
        # Download dropdown state
        self.download_items = {}
        self.downloads_visible = False
        self.downloads_panel = None
        self.downloads_list = None
        self.downloads_button = None
        self.search_button = None  # Store reference for disabling
        
        # Operation tracking for disabling navigation
        self.active_operations = 0  # Track active downloads/loading operations
        
        # Playlist download tracking
        self.active_playlist_downloads = {}  # playlist_id -> {total, completed, failed, format_type, card}
        self.video_download_state = {}  # video_id -> {status: 'downloading'/'completed'/'failed', format: 'mp4'/'mp3'}
        self.download_id_to_video_id = {}  # download_id -> video_id for tracking
        self.playlist_individual_downloads = {}  # playlist_id -> set of video_ids that were downloaded individually
        
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
        self.search_button = cust.CTkButton(
            search_frame,
            text="Search",
            width=100,
            height=45,
            font=cust.CTkFont(size=13, weight="bold"),
            fg_color=("#cc0000", "#ff0000"),
            hover_color=("#990000", "#cc0000"),
            text_color="white"
        )
        self.search_button.pack(side="left")
        self.search_button.configure(command=self._on_search)
        
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
        self.nav_frame = cust.CTkFrame(self.app, fg_color=("#f0f0f0", "#262626"), height=50)
        self.nav_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.nav_frame.grid_propagate(False)
        
        # Back button (for playlist view)
        self.back_button = cust.CTkButton(
            self.nav_frame,
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
            self.nav_frame,
            text="Search for videos to get started",
            font=cust.CTkFont(size=13, weight="bold"),
            text_color=("#333333", "#e0e0e0")
        )
        self.status_label.pack(side="left", padx=15)
        
        # Right navbar area
        right_nav = cust.CTkFrame(self.nav_frame, fg_color="transparent")
        right_nav.pack(side="right", padx=15)
        
        self.downloads_button = cust.CTkButton(
            right_nav,
            text="Downloads (0)",
            width=140,
            height=32,
            font=cust.CTkFont(size=12, weight="bold"),
            fg_color=("#0066cc", "#0080ff"),
            hover_color=("#0052a3", "#0066cc"),
            text_color="white",
            command=self._toggle_downloads_panel
        )
        self.downloads_button.pack()
        
        # ===== MAIN CONTENT AREA =====
        self.scrollable_frame = VerticalListFrame(
            self.app,
            fg_color=("#f5f5f5", "#0f0f0f")
        )
        self.scrollable_frame.grid(row=3, column=0, sticky="nsew", padx=0, pady=0)
        
        # ===== WELCOME MESSAGE =====
        self._show_welcome_message()
        
        # Downloads dropdown panel
        self._create_downloads_panel()
    
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
    
    def _create_downloads_panel(self):
        """Create downloads dropdown panel"""
        self.downloads_panel = cust.CTkFrame(
            self.app,
            fg_color=("#ffffff", "#1a1a1a"),
            corner_radius=10,
            border_width=1,
            border_color=("#cccccc", "#333333"),
            width=550,
            height=420
        )
        self.downloads_panel.place_forget()
        self.downloads_panel.grid_propagate(False)
        self.downloads_panel.pack_propagate(False)
        
        header = cust.CTkFrame(self.downloads_panel, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 6))
        
        title = cust.CTkLabel(
            header,
            text="Downloads",
            font=cust.CTkFont(size=14, weight="bold"),
            text_color=("#333333", "#e0e0e0")
        )
        title.pack(side="left")
        
        close_btn = cust.CTkButton(
            header,
            text="✕",
            width=28,
            height=28,
            fg_color=("#eeeeee", "#333333"),
            hover_color=("#dddddd", "#444444"),
            text_color=("#333333", "#e0e0e0"),
            command=self._toggle_downloads_panel
        )
        close_btn.pack(side="right")
        
        # Folder button to open downloads directory
        folder_btn = cust.CTkButton(
            header,
            text="📁",
            width=28,
            height=28,
            fg_color=("#eeeeee", "#333333"),
            hover_color=("#dddddd", "#444444"),
            text_color=("#333333", "#e0e0e0"),
            command=self._open_downloads_folder
        )
        folder_btn.pack(side="right", padx=(0, 5))
        
        # Tooltip for folder button
        self._create_tooltip(folder_btn, "Open downloads folder")
        
        self.downloads_list = cust.CTkScrollableFrame(
            self.downloads_panel,
            fg_color="transparent",
            width=540
        )
        self.downloads_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.downloads_list.pack_propagate(False)
        
        self.downloads_empty_label = cust.CTkLabel(
            self.downloads_list,
            text="No active downloads",
            font=cust.CTkFont(size=12),
            text_color=("#666666", "#999999")
        )
        self.downloads_empty_label.pack(pady=20)
    
    def _toggle_downloads_panel(self):
        """Show or hide the downloads dropdown panel"""
        if not self.downloads_panel:
            return
        
        if self.downloads_visible:
            self.downloads_panel.place_forget()
            self.downloads_visible = False
            return
        
        self._position_downloads_panel()
        self.downloads_panel.lift()
        self.downloads_visible = True
    
    def _position_downloads_panel(self):
        if not self.downloads_panel:
            return
        self.app.update_idletasks()
        margin_right = 20
        y = self.nav_frame.winfo_y() + self.nav_frame.winfo_height() -15

        self.downloads_panel.place(relx=1.0, x=-margin_right, y=y, anchor="ne")
    
    def _open_downloads_folder(self):
        """Open the downloads folder in file explorer"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.download_path, exist_ok=True)
            
            # Open folder based on OS
            if sys.platform == 'win32':
                subprocess.Popen(['explorer', os.path.normpath(self.download_path)])
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', self.download_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', self.download_path])
        except Exception as e:
            self._show_error(f"Could not open folder: {str(e)}")
    
    def _create_tooltip(self, widget, text: str):
        """Create a tooltip for a widget on hover"""
        tooltip_window = None
        
        def on_enter(event):
            nonlocal tooltip_window
            if tooltip_window:
                return
            
            # Create tooltip window
            tooltip_window = tk.Toplevel(self.app)
            tooltip_window.wm_overrideredirect(True)
            tooltip_window.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            
            label = tk.Label(
                tooltip_window,
                text=text,
                background="#333333",
                foreground="#e0e0e0",
                font=("Arial", 9),
                padx=5,
                pady=3
            )
            label.pack()
        
        def on_leave(event):
            nonlocal tooltip_window
            if tooltip_window:
                tooltip_window.destroy()
                tooltip_window = None
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _update_downloads_button(self):
        """Update downloads button text with active count"""
        # Count active downloads from the UI items
        active_count = len(self.download_items)
        
        if self.downloads_button:
            self.downloads_button.configure(text=f"Downloads ({active_count})")
    
    def _add_download_item(self, download_id: Optional[str], video: VideoInfo, format_type: str, is_playlist: bool):
        try:
            if not download_id:
                print("_add_download_item: download_id is None")
                return
            if not self.downloads_list:
                print("_add_download_item: downloads_list does not exist")
                return
            if not self.downloads_list.winfo_exists():
                print("_add_download_item: downloads_list widget does not exist")
                return
            
            print(f"_add_download_item: Adding item for {video.title[:30]}... (ID: {download_id})")
            
            if hasattr(self, 'downloads_empty_label') and self.downloads_empty_label.winfo_exists():
                self.downloads_empty_label.pack_forget()
                # Force layout update after hiding empty label
                self.downloads_list.update_idletasks()
            
            item = cust.CTkFrame(
                self.downloads_list,
                fg_color=("#f7f7f7", "#222222"),
                corner_radius=8,
                border_width=1,
                border_color=("#dddddd", "#333333"),
                width=530
            )
            item.pack(fill="x", padx=6, pady=6)
            item.grid_columnconfigure(0, weight=1)
            item.grid_propagate(False)
            
            # Force scrollable frame to update its scroll region
            self.downloads_list.update_idletasks()
            
            title_text = video.title if len(video.title) <= 45 else f"{video.title[:42]}..."
            format_label = "Playlist" if is_playlist else format_type.upper()
            
            title = cust.CTkLabel(
                item,
                text=title_text,
                font=cust.CTkFont(size=12, weight="bold"),
                text_color=("#222222", "#e0e0e0"),
                wraplength=420
            )
            title.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
            
            meta = cust.CTkLabel(
                item,
                text=f"{format_label} · Queued",
                font=cust.CTkFont(size=11),
                text_color=("#666666", "#999999"),
                wraplength=420
            )
            meta.grid(row=1, column=0, sticky="w", padx=10)
            
            progress = cust.CTkProgressBar(item, height=6)
            progress.set(0)
            progress.grid(row=2, column=0, sticky="ew", padx=10, pady=(6, 8))
            
            actions = cust.CTkFrame(item, fg_color="transparent")
            actions.grid(row=0, column=1, rowspan=3, padx=10, pady=10)
            
            pause_btn = cust.CTkButton(
                actions,
                text="Pause",
                width=80,
                height=26,
                font=cust.CTkFont(size=11),
                fg_color=("#555555", "#444444"),
                hover_color=("#666666", "#555555"),
                text_color="white",
                command=lambda: self._on_pause_resume_clicked(download_id)
            )
            pause_btn.pack(pady=(0, 6))
            
            cancel_btn = cust.CTkButton(
                actions,
                text="Cancel",
                width=80,
                height=26,
                font=cust.CTkFont(size=11),
                fg_color=("#cc0000", "#ff0000"),
                hover_color=("#990000", "#cc0000"),
                text_color="white",
                command=lambda: self._on_cancel_clicked(download_id)
            )
            cancel_btn.pack()
            
            self.download_items[download_id] = {
                "frame": item,
                "title": title,
                "meta": meta,
                "progress": progress,
                "pause_btn": pause_btn,
                "cancel_btn": cancel_btn
            }
            
            self._update_downloads_button()
        except Exception as e:
            print(f"Error adding download item: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_download_item_progress(self, download_id: Optional[str], percentage: float):
        item = self.download_items.get(download_id)
        if not item:
            return
        
        item["progress"].set(percentage / 100)
        status = "Downloading" if percentage < 100 else "Complete"
        meta_text = item["meta"].cget("text").split("·")[0].strip()
        item["meta"].configure(text=f"{meta_text} · {status} {int(percentage)}%")
    
    def _set_download_item_status(self, download_id: Optional[str], status: str, error_msg: Optional[str] = None):
        item = self.download_items.get(download_id)
        if not item:
            return
        
        meta_prefix = item["meta"].cget("text").split("·")[0].strip()
        status_text = status
        if error_msg:
            status_text = f"{status}: {error_msg[:30]}"
        item["meta"].configure(text=f"{meta_prefix} · {status_text}")
        
        if status in {"Completed", "Canceled", "Error"}:
            item["pause_btn"].configure(state="disabled")
            item["cancel_btn"].configure(state="disabled")
            # Remove the item immediately after a very short delay
            def remove_item():
                if download_id in self.download_items:
                    item_frame = self.download_items[download_id]["frame"]
                    item_frame.pack_forget()
                    item_frame.destroy()
                    del self.download_items[download_id]
                    
                    # Show empty label if no downloads left
                    if not self.download_items and hasattr(self, 'downloads_empty_label'):
                        self.downloads_empty_label.pack(pady=20)
                    
                    # Update downloads button after removal
                    self._update_downloads_button()
            
            self.app.after(100, remove_item)
        else:
            self._update_downloads_button()
    
    def _on_pause_resume_clicked(self, download_id: Optional[str]):
        if not download_id:
            return
        task = self.download_controller.get_download(download_id)
        if not task:
            return
        
        if task.status == "paused":
            if self.download_controller.resume_download(download_id):
                self.download_items[download_id]["pause_btn"].configure(text="Pause")
                self._set_download_item_status(download_id, "Downloading")
        else:
            if self.download_controller.pause_download(download_id):
                self.download_items[download_id]["pause_btn"].configure(text="Resume")
                self._set_download_item_status(download_id, "Paused")
    
    def _on_cancel_clicked(self, download_id: Optional[str]):
        if not download_id:
            return
        
        # Get video_id for this download
        video_id = self.download_id_to_video_id.get(download_id)
        
        if self.download_controller.cancel_download(download_id):
            self._set_download_item_status(download_id, "Canceled")
            
            # Update video state to canceled
            if video_id and video_id in self.video_download_state:
                format_type = self.video_download_state[video_id].get('format')
                self.video_download_state[video_id] = {
                    'status': 'canceled',
                    'format': format_type,
                    'error': 'Canceled by user'
                }
                
                # Check if this video is part of any active playlist download
                for playlist_id, playlist_info in list(self.active_playlist_downloads.items()):
                    if playlist_info['format_type'] == format_type:
                        # Increment failed count for the playlist
                        playlist_info['failed'] += 1
                        
                        # Update playlist button progress
                        playlist_card = playlist_info['card']
                        total = playlist_info['total']
                        completed = playlist_info['completed']
                        failed = playlist_info['failed']
                        
                        def update_playlist_btn():
                            try:
                                if not playlist_card.winfo_exists():
                                    return
                                if format_type == "mp4":
                                    playlist_card.mp4_button.configure(
                                        state="disabled",
                                        text=f"Downloading... ({completed + failed}/{total})"
                                    )
                                else:
                                    playlist_card.mp3_button.configure(
                                        state="disabled",
                                        text=f"Downloading... ({completed + failed}/{total})"
                                    )
                            except:
                                pass
                        
                        self._run_ui(update_playlist_btn)
                        
                        # If all videos are done (completed or failed), reset playlist buttons
                        if completed + failed >= total:
                            del self.active_playlist_downloads[playlist_id]
                            
                            def reset_playlist_btn():
                                try:
                                    if not playlist_card.winfo_exists():
                                        return
                                    if format_type == "mp4":
                                        playlist_card.mp4_button.configure(
                                            state="normal",
                                            text="📥 MP4",
                                            fg_color=("#cc0000", "#ff0000")
                                        )
                                        playlist_card.mp3_button.configure(state="normal")
                                    else:
                                        playlist_card.mp3_button.configure(
                                            state="normal",
                                            text="🎵 MP3",
                                            fg_color=("#0066cc", "#0080ff")
                                        )
                                        playlist_card.mp4_button.configure(state="normal")
                                except:
                                    pass
                            
                            self._run_ui(reset_playlist_btn)
                        
                        break  # Found the playlist, no need to continue
                
                # Reset button state for the individual video card if it exists
                if video_id in self.card_references:
                    card = self.card_references[video_id]
                    
                    def reset_video_btn():
                        try:
                            if not card.winfo_exists():
                                return
                            # Reset both buttons to allow retry
                            card.mp4_button.configure(state="normal", text="📥 MP4", fg_color=("#cc0000", "#ff0000"))
                            card.mp3_button.configure(state="normal", text="🎵 MP3", fg_color=("#0066cc", "#0080ff"))
                        except:
                            pass
                    
                    self._run_ui(reset_video_btn)
            
            # Clean up mapping
            if download_id in self.download_id_to_video_id:
                del self.download_id_to_video_id[download_id]
    
    def _run_ui(self, callback: Callable[[], None]):
        self.app.after(0, callback)
    
    def _start_operation(self):
        """Increment operation counter and disable navigation"""
        self.active_operations += 1
        if self.active_operations > 0:
            self._disable_navigation()
    
    def _end_operation(self):
        """Decrement operation counter and enable navigation if no operations active"""
        self.active_operations = max(0, self.active_operations - 1)
        if self.active_operations == 0:
            self._enable_navigation()
    
    def _disable_navigation(self):
        """Disable search and back buttons"""
        try:
            self.search_entry.configure(state="disabled")
            if self.search_button:
                self.search_button.configure(state="disabled")
            if self.back_button:
                self.back_button.configure(state="disabled")
        except:
            pass
    
    def _enable_navigation(self):
        """Enable search and back buttons"""
        try:
            self.search_entry.configure(state="normal")
            if self.search_button:
                self.search_button.configure(state="normal")
            if self.back_button:
                self.back_button.configure(state="normal")
        except:
            pass
    
    def _normalize_playlist_title(self, title: str) -> str:
        """Normalize playlist title for use as directory name"""
        import re
        import unicodedata
        
        # Remove emojis and special characters
        # Keep only alphanumeric, spaces, hyphens, and underscores
        cleaned = ''.join(char for char in title if unicodedata.category(char)[0] != 'C' and (char.isalnum() or char in ' -_'))
        
        # Remove emojis more aggressively
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        cleaned = emoji_pattern.sub('', cleaned)
        
        # Replace spaces with underscores
        cleaned = cleaned.replace(' ', '_')
        
        # Replace pipes with hyphens
        cleaned = cleaned.replace('|', '-')
        
        # Remove multiple consecutive underscores
        cleaned = re.sub(r'_+', '_', cleaned)
        
        # Remove leading/trailing underscores
        cleaned = cleaned.strip('_')
        
        # Limit length to avoid filesystem issues
        if len(cleaned) > 100:
            cleaned = cleaned[:100]
        
        # If empty after cleaning, use a default name with increasing number if old nummber already exists `playlist (i)`

        if not cleaned:
            cleaned = 'playlist'
            i = 1
            if cleaned not in os.listdir(self.download_path):
                return cleaned
            while f"{cleaned} ({i})" in os.listdir(self.download_path):
                i += 1
            cleaned = f"{cleaned} ({i})"
        
        return cleaned
    
    def _start_download(self, video: VideoInfo, format_type: str, card: VideoCard, is_playlist: bool):
        # If it's a playlist, show confirmation and download all videos
        if is_playlist:
            # Check if any video in this playlist is CURRENTLY being downloaded individually
            playlist_id = video.video_id
            if playlist_id in self.playlist_individual_downloads:
                # Check if any of those videos are actively downloading
                active_individual_downloads = False
                for video_id in self.playlist_individual_downloads[playlist_id]:
                    if video_id in self.video_download_state:
                        state = self.video_download_state[video_id]
                        if state.get('status') == 'downloading':
                            active_individual_downloads = True
                            break
                
                if active_individual_downloads:
                    self._show_error("Some videos in this playlist are currently downloading individually. Please wait for them to complete.")
                    return
            
            # Disable both buttons and title immediately for playlist
            try:
                card.mp4_button.configure(state="disabled")
                card.mp3_button.configure(state="disabled")
                # Disable title click while preserving text color
                card.disable_title()
            except:
                pass
            
            # Start operation (disable navigation) before fetching playlist
            self._start_operation()
            
            self._download_playlist_confirmation(video, format_type, card)
            return
        
        # Check if already downloaded
        if video.video_id in self.video_download_state:
            state = self.video_download_state[video.video_id]
            if state.get('status') == 'completed' and state.get('format') == format_type:
                self._show_error("This video has already been downloaded in this format")
                return
            # Check if other format is downloading or completed
            if state.get('status') in ('downloading', 'completed'):
                other_format = 'mp3' if format_type == 'mp4' else 'mp4'
                if state.get('format') == other_format:
                    self._show_error(f"This video is already downloading/downloaded as {other_format.upper()}")
                    return
        
        # Disable both buttons immediately
        try:
            card.mp4_button.configure(state="disabled")
            card.mp3_button.configure(state="disabled")
        except:
            pass
        
        # Start operation (disable navigation)
        self._start_operation()
        
        # Regular single video download
        download_id: Optional[str] = None
        
        # Track video state
        self.video_download_state[video.video_id] = {
            'status': 'downloading',
            'format': format_type,
            'progress': 0
        }
        
        def on_progress(p: float):
            if download_id is None:
                return
            self._run_ui(lambda: self._update_download_item_progress(download_id, p))
            # Update video state progress
            if video.video_id in self.video_download_state:
                self.video_download_state[video.video_id]['progress'] = p
        
        def on_complete(_filename: str):
            if download_id is None:
                return
            self._run_ui(lambda: self._set_download_item_status(download_id, "Completed"))
            
            # Update video state
            self.video_download_state[video.video_id] = {
                'status': 'completed',
                'format': format_type
            }
            
            # Mark this video as individually downloaded if it belongs to a playlist
            # Check all playlists to see if this video belongs to any
            for pl_id in self.card_references:
                card_ref = self.card_references[pl_id]
                if hasattr(card_ref.video, 'is_playlist') and card_ref.video.is_playlist:
                    # This is a playlist card, we need to check if our video belongs to it
                    # We'll mark it when we're in playlist view
                    pass
            
            # If we're in playlist mode, track this as individual download
            if self.current_mode == "playlist" and self.current_playlist:
                playlist_id = self.current_playlist.video_id
                if playlist_id not in self.playlist_individual_downloads:
                    self.playlist_individual_downloads[playlist_id] = set()
                self.playlist_individual_downloads[playlist_id].add(video.video_id)
            
            # Show downloaded state - only enable the downloaded format button
            def update_complete_state():
                try:
                    if not card.winfo_exists():
                        return
                    if format_type == "mp4":
                        card.mp4_button.configure(state="normal", text="✓ Downloaded", fg_color=("#00aa00", "#00cc00"))
                        # Keep MP3 disabled
                    else:
                        card.mp3_button.configure(state="normal", text="✓ Downloaded", fg_color=("#00aa00", "#00cc00"))
                        # Keep MP4 disabled
                except:
                    pass
            
            self._run_ui(update_complete_state)
            
            # End operation (re-enable navigation)
            self._end_operation()
        
        def on_error(error: str):
            if download_id is None:
                return
            self._run_ui(lambda: self._set_download_item_status(download_id, "Error", error))
            self._run_ui(lambda: self._on_download_error(error, card))
            
            # Update video state
            self.video_download_state[video.video_id] = {
                'status': 'failed',
                'format': format_type,
                'error': error
            }
            
            # Reset both buttons to original state on error (allow retry of either format)
            def reset_error_state():
                try:
                    if not card.winfo_exists():
                        return
                    card.mp4_button.configure(state="normal", text="📥 MP4", fg_color=("#cc0000", "#ff0000"))
                    card.mp3_button.configure(state="normal", text="🎵 MP3", fg_color=("#0066cc", "#0080ff"))
                except:
                    pass
            
            self._run_ui(reset_error_state)
            
            # End operation (re-enable navigation)
            self._end_operation()
        
        # Use queue_download for sequential processing
        download_id = self.download_controller.queue_download(
            video,
            format_type=format_type,
            progress_callback=on_progress,
            complete_callback=on_complete,
            error_callback=on_error
        )
        
        if not download_id:
            return
        
        # Add download item via UI thread for consistency
        self._run_ui(lambda: self._add_download_item(download_id, video, format_type, is_playlist=False))
        
        # Track download_id to video_id mapping
        self.download_id_to_video_id[download_id] = video.video_id
    
    def _download_playlist_confirmation(self, playlist: VideoInfo, format_type: str, card: VideoCard):
        """Show confirmation dialog and download all videos from playlist"""
        # First, fetch all videos in the playlist
        def on_videos_fetched(videos: List[VideoInfo]):
            if not videos:
                self._run_ui(lambda: self._show_error("Failed to fetch playlist videos"))
                self._run_ui(lambda: card.download_error("Failed to fetch playlist"))
                
                # End operation (re-enable navigation) on error
                self._end_operation()
                
                # Reset buttons
                def reset_buttons():
                    try:
                        if card.winfo_exists():
                            if format_type == "mp4":
                                card.mp4_button.configure(state="normal", text="📥 MP4", fg_color=("#cc0000", "#ff0000"))
                                card.mp3_button.configure(state="normal")
                            else:
                                card.mp3_button.configure(state="normal", text="🎵 MP3", fg_color=("#0066cc", "#0080ff"))
                                card.mp4_button.configure(state="normal")
                            # Re-enable title
                            card.enable_title()
                    except:
                        pass
                self._run_ui(reset_buttons)
                return
            
            # Show confirmation dialog in UI thread
            def show_confirmation():
                result = messagebox.askyesno(
                    "Download Playlist",
                    f"You are about to download {len(videos)} video(s) from this playlist.\n\n"
                    f"All videos will be downloaded one by one.\n\n"
                    f"Do you want to proceed?",
                    icon='warning'
                )
                
                if result:
                    # User confirmed, start downloading all videos
                    self._download_all_playlist_videos(videos, format_type, card)
                else:
                    # User canceled - re-enable navigation
                    self._end_operation()
                    
                    # Reset buttons
                    playlist_id = playlist.video_id
                    if playlist_id not in self.active_playlist_downloads:
                        # Only reset if no active playlist download
                        try:
                            if card.winfo_exists():
                                if format_type == "mp4":
                                    card.mp4_button.configure(state="normal", text="📥 MP4", fg_color=("#cc0000", "#ff0000"))
                                    card.mp3_button.configure(state="normal")
                                else:
                                    card.mp3_button.configure(state="normal", text="🎵 MP3", fg_color=("#0066cc", "#0080ff"))
                                    card.mp4_button.configure(state="normal")
                                # Re-enable title
                                card.enable_title()
                        except:
                            pass
            
            self._run_ui(show_confirmation)
        
        def on_error(error: str):
            self._run_ui(lambda: self._show_error(f"Failed to fetch playlist: {error}"))
            
            # End operation (re-enable navigation) on error
            self._end_operation()
            
            # Reset buttons
            playlist_id = playlist.video_id
            if playlist_id not in self.active_playlist_downloads:
                # Only reset if no active playlist download
                def reset_on_error():
                    try:
                        if not card.winfo_exists():
                            return
                        if format_type == "mp4":
                            card.mp4_button.configure(state="normal", text="📥 MP4", fg_color=("#cc0000", "#ff0000"))
                            card.mp3_button.configure(state="normal")
                        else:
                            card.mp3_button.configure(state="normal", text="🎵 MP3", fg_color=("#0066cc", "#0080ff"))
                            card.mp4_button.configure(state="normal")
                        # Re-enable title
                        card.enable_title()
                    except:
                        pass
                
                self._run_ui(reset_on_error)
        
        # Fetch playlist videos
        self.search_controller.get_playlist_videos(
            playlist.url,
            callback=on_videos_fetched,
            error_callback=on_error
        )
    
    def _download_all_playlist_videos(self, videos: List[VideoInfo], format_type: str, card: VideoCard):
        """Download all videos from a playlist sequentially"""
        total_videos = len(videos)
        completed_count = 0
        failed_count = 0
        
        # Get playlist info for tracking
        playlist_id = card.video.video_id
        playlist_title = card.video.title
        
        # Create normalized subdirectory for playlist
        normalized_title = self._normalize_playlist_title(playlist_title)
        playlist_download_path = os.path.join(self.download_path, normalized_title)
        
        # Create the directory
        try:
            os.makedirs(playlist_download_path, exist_ok=True)
        except Exception as e:
            self._run_ui(lambda: self._show_error(f"Failed to create playlist directory: {str(e)}"))
            return
        
        # Track this playlist download
        self.active_playlist_downloads[playlist_id] = {
            'total': total_videos,
            'completed': 0,
            'failed': 0,
            'format_type': format_type,
            'card': card,
            'video_ids': [v.video_id for v in videos]  # Track all video IDs in this playlist
        }
        
        # Update the playlist card to show overall progress (wrap in _run_ui)
        def initial_update():
            try:
                if card.winfo_exists():
                    card.mp4_button.configure(state="disabled", text=f"Downloading... (0/{total_videos})")
                    card.mp3_button.configure(state="disabled", text=f"Downloading... (0/{total_videos})")
            except:
                pass
        self._run_ui(initial_update)
        
        def update_playlist_progress():
            """Update the playlist card with overall progress"""
            try:
                if not card.winfo_exists():
                    return
                
                if format_type == "mp4":
                    card.mp4_button.configure(
                        state="disabled",
                        text=f"Downloading... ({completed_count + failed_count}/{total_videos})"
                    )
                else:
                    card.mp3_button.configure(
                        state="disabled",
                        text=f"Downloading... ({completed_count + failed_count}/{total_videos})"
                    )
            except:
                pass
        
        # Queue all videos for download
        for idx, video in enumerate(videos):
            def create_callbacks(video_obj, video_idx):
                # Create a container for download_id that will be set after queue_download returns
                dl_id_container: Dict[str, Optional[str]] = {'id': None}
                
                def on_progress(p: float):
                    if dl_id_container['id'] is None:
                        return
                    dl_id = dl_id_container['id']
                    self._run_ui(lambda: self._update_download_item_progress(dl_id, p))
                    
                    # Update video state
                    self.video_download_state[video_obj.video_id] = {
                        'status': 'downloading',
                        'format': format_type,
                        'progress': p
                    }
                
                def on_complete(_filename: str):
                    nonlocal completed_count
                    if dl_id_container['id'] is None:
                        return
                    completed_count += 1
                    dl_id = dl_id_container['id']
                    self._run_ui(lambda: self._set_download_item_status(dl_id, "Completed"))
                    self._run_ui(update_playlist_progress)
                    
                    # Update video state
                    self.video_download_state[video_obj.video_id] = {
                        'status': 'completed',
                        'format': format_type
                    }
                    
                    # Update playlist tracking
                    if playlist_id in self.active_playlist_downloads:
                        self.active_playlist_downloads[playlist_id]['completed'] = completed_count
                    
                    # Sync card state if it exists in card_references
                    if video_obj.video_id in self.card_references:
                        video_card = self.card_references[video_obj.video_id]
                        # For bulk playlist downloads, disable both buttons and DON'T sync state
                        # until the entire playlist is done (to prevent re-enabling buttons)
                        def disable_video_buttons():
                            try:
                                if video_card.winfo_exists():
                                    if video_card.mp4_button.winfo_exists():
                                        video_card.mp4_button.configure(state="disabled")
                                    if video_card.mp3_button.winfo_exists():
                                        video_card.mp3_button.configure(state="disabled")
                                    # Only sync state if this playlist download is complete
                                    if playlist_id not in self.active_playlist_downloads:
                                        self._sync_video_card_state(video_card, video_obj.video_id)
                            except:
                                pass
                        self._run_ui(disable_video_buttons)
                    
                    # If this is the last video, reset playlist card buttons to original state
                    if completed_count + failed_count >= total_videos:
                        if playlist_id in self.active_playlist_downloads:
                            del self.active_playlist_downloads[playlist_id]
                        
                        # End operation (re-enable navigation) when playlist fully completes
                        self._end_operation()
                        
                        if format_type == "mp4":
                            self._run_ui(lambda: card.mp4_button.configure(
                                state="normal",
                                text="📥 MP4",
                                fg_color=("#cc0000", "#ff0000")
                            ))
                            self._run_ui(lambda: card.mp3_button.configure(state="normal"))
                        else:
                            self._run_ui(lambda: card.mp3_button.configure(
                                state="normal",
                                text="🎵 MP3",
                                fg_color=("#0066cc", "#0080ff")
                            ))
                            self._run_ui(lambda: card.mp4_button.configure(state="normal"))
                        
                        # Re-enable title click
                        def enable_title():
                            try:
                                if card.winfo_exists():
                                    card.enable_title()
                            except:
                                pass
                        self._run_ui(enable_title)
                
                def on_error(error: str):
                    nonlocal failed_count
                    if dl_id_container['id'] is None:
                        return
                    failed_count += 1
                    dl_id = dl_id_container['id']
                    self._run_ui(lambda: self._set_download_item_status(dl_id, "Error", error))
                    self._run_ui(update_playlist_progress)
                    
                    # Update video state
                    self.video_download_state[video_obj.video_id] = {
                        'status': 'failed',
                        'format': format_type,
                        'error': error
                    }
                    
                    # Update playlist tracking
                    if playlist_id in self.active_playlist_downloads:
                        self.active_playlist_downloads[playlist_id]['failed'] = failed_count
                    
                    # Sync card state if it exists in card_references
                    if video_obj.video_id in self.card_references:
                        video_card = self.card_references[video_obj.video_id]
                        # For bulk playlist downloads, keep both buttons disabled until entire playlist is done
                        def disable_error_buttons():
                            try:
                                if video_card.winfo_exists():
                                    if video_card.mp4_button.winfo_exists():
                                        video_card.mp4_button.configure(state="disabled")
                                    if video_card.mp3_button.winfo_exists():
                                        video_card.mp3_button.configure(state="disabled")
                                    # Only sync state if this playlist download is complete
                                    if playlist_id not in self.active_playlist_downloads:
                                        self._sync_video_card_state(video_card, video_obj.video_id)
                            except:
                                pass
                        self._run_ui(disable_error_buttons)
                    
                    # If this is the last video, reset playlist card buttons to original state
                    if completed_count + failed_count >= total_videos:
                        if playlist_id in self.active_playlist_downloads:
                            del self.active_playlist_downloads[playlist_id]
                        
                        # End operation (re-enable navigation) when playlist fully completes
                        self._end_operation()
                        
                        def reset_playlist_buttons():
                            try:
                                if not card.winfo_exists():
                                    return
                                if format_type == "mp4":
                                    card.mp4_button.configure(
                                        state="normal",
                                        text="📥 MP4",
                                        fg_color=("#cc0000", "#ff0000")
                                    )
                                    card.mp3_button.configure(state="normal")
                                else:
                                    card.mp3_button.configure(
                                        state="normal",
                                        text="🎵 MP3",
                                        fg_color=("#0066cc", "#0080ff")
                                    )
                                    card.mp4_button.configure(state="normal")
                                # Re-enable title
                                card.enable_title()
                            except:
                                pass
                        
                        self._run_ui(reset_playlist_buttons)
                
                return on_progress, on_complete, on_error, dl_id_container
            
            on_progress, on_complete, on_error, dl_id_container = create_callbacks(video, idx)
            
            # Queue the download with custom path for playlist subdirectory
            download_id = self.download_controller.queue_download(
                video,
                format_type=format_type,
                progress_callback=on_progress,
                complete_callback=on_complete,
                error_callback=on_error,
                custom_download_path=playlist_download_path
            )
            
            # Store the download_id in the container so callbacks can use it
            dl_id_container['id'] = download_id
            
            if download_id:
                # Add to download list UI with playlist indicator
                video_title_with_index = f"[{idx + 1}/{total_videos}] {video.title}"
                temp_video = VideoInfo(
                    video_id=video.video_id,
                    title=video_title_with_index,
                    channel=video.channel,
                    duration=video.duration,
                    view_count=video.view_count,
                    thumbnail_url=video.thumbnail_url,
                    url=video.url,
                    is_playlist=False
                )
                # Capture variables explicitly to avoid closure issues
                self._run_ui(lambda did=download_id, vid=temp_video, fmt=format_type: 
                            self._add_download_item(did, vid, fmt, is_playlist=False))
                
                # Track download_id to video_id mapping
                self.download_id_to_video_id[download_id] = video.video_id
        
        self._run_ui(self._update_downloads_button)
    
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
        
        # Sync state with any existing downloads
        self._sync_video_card_state(card, video.video_id)
        
        return card
    
    def _sync_video_card_state(self, card: VideoCard, video_id: str):
        """Sync video card button states with current download state"""
        try:
            if not card.winfo_exists():
                return
            
            if video_id in self.video_download_state:
                state = self.video_download_state[video_id]
                status = state.get('status')
                format_type = state.get('format')
                
                if status == 'completed':
                    # Show as completed and disable the other format
                    if format_type == 'mp4':
                        if card.mp4_button.winfo_exists():
                            card.mp4_button.configure(
                                state="normal",
                                text="✓ Downloaded",
                                fg_color=("#00aa00", "#00cc00")
                            )
                        if card.mp3_button.winfo_exists():
                            card.mp3_button.configure(state="disabled", text="🎵 MP3")
                    elif format_type == 'mp3':
                        if card.mp3_button.winfo_exists():
                            card.mp3_button.configure(
                                state="normal",
                                text="✓ Downloaded",
                                fg_color=("#00aa00", "#00cc00")
                            )
                        if card.mp4_button.winfo_exists():
                            card.mp4_button.configure(state="disabled", text="📥 MP4")
                elif status == 'downloading':
                    # Show as downloading and disable both buttons
                    progress = state.get('progress', 0)
                    if format_type == 'mp4':
                        if card.mp4_button.winfo_exists():
                            card.mp4_button.configure(
                                state="disabled",
                                text=f"Downloading... {int(progress)}%"
                            )
                        if card.mp3_button.winfo_exists():
                            card.mp3_button.configure(state="disabled", text="🎵 MP3")
                    elif format_type == 'mp3':
                        if card.mp3_button.winfo_exists():
                            card.mp3_button.configure(
                                state="disabled",
                                text=f"Downloading... {int(progress)}%"
                            )
                        if card.mp4_button.winfo_exists():
                            card.mp4_button.configure(state="disabled", text="📥 MP4")
                elif status in ('failed', 'canceled'):
                    # Show normal state for failed/canceled (allow retry of either format)
                    pass
            else:
                # Check if this video is part of an active bulk playlist download
                for playlist_id, playlist_info in self.active_playlist_downloads.items():
                    # We need to check if this video is in that playlist
                    # For now, we'll disable both buttons if ANY bulk download is active
                    # This is a conservative approach
                    pass
        except:
            pass
    
    def _on_download_mp4(self, video: VideoInfo, card: VideoCard):
        """Handle MP4 download"""
        self._start_download(video, "mp4", card, is_playlist=video.is_playlist)
    
    def _on_download_mp3(self, video: VideoInfo, card: VideoCard):
        """Handle MP3 download"""
        self._start_download(video, "mp3", card, is_playlist=video.is_playlist)

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
        
        # Start operation (disable navigation)
        self._start_operation()
        
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
            error_callback=self._on_playlist_load_error
        )
    
    def _on_playlist_videos_loaded(self, videos: List[VideoInfo]):
        """Handle playlist videos loaded"""
        # End operation (re-enable navigation)
        self._end_operation()
        
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
    
    def _on_playlist_load_error(self, error: str):
        """Handle playlist loading error"""
        # End operation (re-enable navigation)
        self._end_operation()
        
        # Show error
        self._on_search_error(error)
    
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
