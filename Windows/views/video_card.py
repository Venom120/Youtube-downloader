"""
Video Card Widget - Card-based video display with download buttons
"""
import customtkinter as cust  # type: ignore
from PIL import Image
from io import BytesIO
import requests
from typing import Callable, Optional
from models.video_model import VideoInfo
import threading


class VideoCard(cust.CTkFrame):
    """Card widget for displaying video information with download buttons"""
    
    def __init__(
        self,
        master,
        video: VideoInfo,
        on_mp4_click: Optional[Callable[[VideoInfo], None]] = None,
        on_mp3_click: Optional[Callable[[VideoInfo], None]] = None,
        on_title_click: Optional[Callable[[VideoInfo], None]] = None,
        **kwargs
    ):
        """
        Initialize video card
        
        Args:
            master: Parent widget
            video: VideoInfo object to display
            on_mp4_click: Callback when MP4 button clicked
            on_mp3_click: Callback when MP3 button clicked
            on_title_click: Callback when title is clicked (for playlists)
        """
        super().__init__(master, **kwargs)
        
        self.video = video
        self.on_mp4_click = on_mp4_click
        self.on_mp3_click = on_mp3_click
        self.on_title_click = on_title_click
        self.photo_image = None  # Keep reference to prevent garbage collection
        
        # Configure card styling
        self.configure(
            fg_color=["#f0f0f0", "#2b2b2b"],
            corner_radius=10,
            border_width=1,
            border_color=["#cccccc", "#404040"]
        )
        self.grid_propagate(True)  # Allow frame to expand with content
        
        # Create card layout
        self._create_widgets()
        
        # Defer thumbnail loading until after widget is rendered
        self.after(100, self._load_thumbnail)
    
    def _create_widgets(self):
        """Create all widgets for the card"""
        # Main horizontal container (25% thumbnail, 75% details)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=25)  # Thumbnail - 25% width
        self.grid_columnconfigure(1, weight=75)  # Details - 75% width
        
        # ===== LEFT SIDE: THUMBNAIL =====
        self.thumbnail_container = cust.CTkFrame(self, fg_color="transparent")
        self.thumbnail_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Thumbnail label - fills container width, maintains aspect ratio
        self.thumbnail_label = cust.CTkLabel(
            self.thumbnail_container,
            text="Loading...",
            fg_color=("#e0e0e0", "#1a1a1a"),
            corner_radius=6,
            font=cust.CTkFont(size=10)
        )
        self.thumbnail_label.pack(fill="both", expand=True)
        
        # Add playlist badge if it's a playlist
        if self.video.is_playlist and self.video.playlist_count:
            playlist_count_text = f"{int(self.video.playlist_count)}" if isinstance(self.video.playlist_count, (int, float)) else str(self.video.playlist_count)
            playlist_badge = cust.CTkLabel(
                self.thumbnail_label,
                text=f"📑 {playlist_count_text}",
                fg_color=("#1a1a1a", "#1a1a1a"),
                text_color="white",
                corner_radius=4,
                font=cust.CTkFont(size=9, weight="bold"),
                padx=4,
                pady=2
            )
            playlist_badge.place(relx=0.95, rely=0.05, anchor="ne")
        
        # Duration badge (only for videos, not playlists)
        if not self.video.is_playlist and self.video.duration > 0:
            duration_badge = cust.CTkLabel(
                self.thumbnail_label,
                text=self.video.formatted_duration,
                fg_color=("#1a1a1a", "#1a1a1a"),
                text_color="white",
                corner_radius=3,
                font=cust.CTkFont(size=16, weight="bold"),
                padx=3,
                pady=2
            )
            duration_badge.place(relx=0.95, rely=0.95, anchor="se")
        
        # ===== RIGHT SIDE: DETAILS =====
        details_container = cust.CTkFrame(self, fg_color="transparent")
        details_container.grid(row=0, column=1, sticky="nsew", padx=(10, 10), pady=10)
        details_container.grid_columnconfigure(0, weight=1)
        details_container.grid_rowconfigure(4, weight=1)  # Button frame expands
        
        # Title section
        title_text = self.video.title if len(self.video.title) <= 80 else self.video.title[:77] + "..."
        
        # Make title clickable if it's a playlist
        if self.video.is_playlist and self.on_title_click:
            self.title_label = cust.CTkButton(
                details_container,
                text=title_text,
                font=cust.CTkFont(size=24, weight="bold"),
                text_color=("#0066cc", "#4da6ff"),
                fg_color="transparent",
                hover_color=("#f0f0f0", "#222222"),
                anchor="w",
                command=lambda: self.on_title_click(self.video) if self.on_title_click else None,
                height=30
            )
        else:
            self.title_label = cust.CTkLabel(
                details_container,
                text=title_text,
                font=cust.CTkFont(size=24, weight="bold"),
                text_color=("#1a1a1a", "#e0e0e0"),
                anchor="w",
                wraplength=0,  # Use full available width
                justify="left"
            )
        
        self.title_label.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        
        # Channel and info section
        info_text = f"{self.video.channel}"
        if self.video.view_count:
            info_text += f" • {self.video.formatted_views} views"
        
        info_label = cust.CTkLabel(
            details_container,
            text=info_text,
            font=cust.CTkFont(size=20),
            text_color=("#666666", "#999999"),
            anchor="w",
            wraplength=0,  # Use full available width
        )
        info_label.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        
        # Progress section (hidden by default)
        progress_container = cust.CTkFrame(details_container, fg_color="transparent")
        progress_container.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        progress_container.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = cust.CTkProgressBar(progress_container, height=4)
        self.progress_bar.set(0)
        
        self.progress_label = cust.CTkLabel(
            progress_container,
            text="",
            font=cust.CTkFont(size=20),
            text_color=("#666666", "#999999")
        )
        
        # Download buttons section
        button_frame = cust.CTkFrame(details_container, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        # Configure button frame columns for centered buttons with fixed width
        button_frame.grid_columnconfigure(0, weight=1)  # Spacer
        button_frame.grid_columnconfigure(1, weight=0)  # MP4 button
        button_frame.grid_columnconfigure(2, weight=0)  # MP3 button
        button_frame.grid_columnconfigure(3, weight=1)  # Spacer
        button_frame.grid_rowconfigure(0, weight=1)
        
        # MP4 button - centered within column
        self.mp4_button = cust.CTkButton(
            button_frame,
            text="📥 MP4",
            height=28,
            font=cust.CTkFont(size=20, weight="bold"),
            fg_color=("#cc0000", "#ff0000"),
            hover_color=("#990000", "#cc0000"),
            text_color="white",
            command=self._on_mp4_clicked
        )
        self.mp4_button.grid(row=0, column=1, padx=(0, 3), sticky="nsew")
        
        # MP3 button - centered within column
        self.mp3_button = cust.CTkButton(
            button_frame,
            text="🎵 MP3",
            height=32,
            font=cust.CTkFont(size=20, weight="bold"),
            fg_color=("#0066cc", "#0080ff"),
            hover_color=("#0052a3", "#0066cc"),
            text_color="white",
            command=self._on_mp3_clicked
        )
        self.mp3_button.grid(row=0, column=2, padx=(3, 0), sticky="nsew")
    
    def _load_thumbnail(self):
        """Load thumbnail image from URL"""
        def load_image():
            try:
                if not self.video.thumbnail_url:
                    self.thumbnail_label.configure(text="📹")
                    return
                
                # Get actual container width (25% of card width)
                container_width = self.thumbnail_container.winfo_width()
                
                # Use container width if available, otherwise use reasonable default
                if container_width > 10:
                    img_width = int(container_width * 0.95)  # Slightly smaller for margin
                else:
                    img_width = 180  # Fallback default
                
                # Calculate height to maintain 16:9 aspect ratio
                img_height = int(img_width * 9 / 16)
                
                response = requests.get(self.video.thumbnail_url, timeout=5)
                
                if response.status_code == 200:
                    # Open image from bytes
                    img_data = BytesIO(response.content)
                    img = Image.open(img_data)
                    
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = Image.new('RGB', img.size, (230, 230, 230))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = rgb_img
                    
                    # Resize maintaining aspect ratio - width x height
                    img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
                    
                    # Create CTkImage with the loaded image
                    self.photo_image = cust.CTkImage(
                        light_image=img,
                        dark_image=img,
                        size=(img.width, img.height)
                    )
                    
                    # Update label with image
                    self.thumbnail_label.configure(image=self.photo_image, text="")
                else:
                    self.thumbnail_label.configure(text="📹")
                    
            except Exception as e:
                self.thumbnail_label.configure(text="📹")
        
        # Load in background to avoid blocking UI
        thread = threading.Thread(target=load_image, daemon=True)
        thread.start()
    
    def _on_mp4_clicked(self):
        """Handle MP4 button click"""
        if self.on_mp4_click:
            self.mp4_button.configure(state="disabled", text="Downloading...")
            self.on_mp4_click(self.video)
    
    def _on_mp3_clicked(self):
        """Handle MP3 button click"""
        if self.on_mp3_click:
            self.mp3_button.configure(state="disabled", text="Downloading...")
            self.on_mp3_click(self.video)
    
    def update_progress(self, percentage: float):
        """
        Update download progress
        
        Args:
            percentage: Progress percentage (0-100)
        """
        # Show progress bar if hidden
        if not self.progress_bar.winfo_ismapped():
            self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 5))
            self.progress_label.pack(side="left")
        
        # Update progress
        self.progress_bar.set(percentage / 100)
        self.progress_label.configure(text=f"{int(percentage)}%")
    
    def download_complete(self, format_type: str):
        """
        Mark download as complete
        
        Args:
            format_type: 'mp4' or 'mp3'
        """
        if format_type == 'mp4':
            self.mp4_button.configure(
                state="normal",
                text="✓ MP4",
                fg_color=["#00aa00", "#00cc00"]
            )
        else:
            self.mp3_button.configure(
                state="normal",
                text="✓ MP3",
                fg_color=["#00aa00", "#00cc00"]
            )
        
        self.progress_label.configure(text="Complete!")
    
    def download_error(self, error_msg: str = "Error"):
        """
        Show download error
        
        Args:
            error_msg: Error message to display
        """
        self.mp4_button.configure(state="normal", text="📥 MP4")
        self.mp3_button.configure(state="normal", text="🎵 MP3")
        self.progress_label.configure(text=f"❌ {error_msg}", text_color="red")

