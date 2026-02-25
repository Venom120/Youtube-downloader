import os
import sys
import types
import shutil
import importlib
import importlib.util
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
import pytest

ROOT = Path(__file__).resolve().parents[1]
WINDOWS_DIR = ROOT / "Windows"
ANDROID_DIR = ROOT / "Android"


def _purge_modules(prefixes):
    for name in list(sys.modules.keys()):
        for prefix in prefixes:
            if name == prefix or name.startswith(prefix + "."):
                sys.modules.pop(name, None)
                break


def _load_module(module_name, file_path, extra_sys_path):
    _purge_modules(["models", "controllers", "views"])
    sys.path.insert(0, str(extra_sys_path))
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Failed to load {file_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def _import_windows_module(module_name):
    _purge_modules(["models", "controllers", "views"])
    sys.path.insert(0, str(WINDOWS_DIR))
    try:
        return importlib.import_module(module_name)
    finally:
        sys.path.pop(0)


@pytest.mark.gui
@pytest.mark.timeout(10)
def test_windows_search_click_triggers_controller(monkeypatch, tk_cleanup):
    pytest.importorskip("customtkinter")
    win_main = _load_module("windows_main", WINDOWS_DIR / "main.py", WINDOWS_DIR)

    class FakeSearchController:
        def __init__(self):
            self.search_called = False
            self.url_called = False

        def search_videos(self, query, max_results=20, callback=None, error_callback=None):
            self.search_called = True
            if callback:
                callback(win_main.SearchResult(videos=[], query=query))

        def get_video_info(self, url, callback=None, error_callback=None):
            self.url_called = True
            if callback:
                callback(
                    win_main.VideoInfo(
                        video_id="v1",
                        title="Test Video",
                        thumbnail_url="",
                        duration=10,
                        channel="Test",
                        url=url,
                        is_playlist=False
                    )
                )

    app = win_main.MainWindow()
    tk_cleanup(app)
    try:
        fake = FakeSearchController()
        app.search_controller = fake

        app.search_entry.delete(0, "end")
        app.search_entry.insert(0, "lofi mix")
        app._on_search()
        assert fake.search_called is True

        app.search_entry.delete(0, "end")
        app.search_entry.insert(0, "https://youtube.com/watch?v=abc")
        app._on_search()
        assert fake.url_called is True
    finally:
        if hasattr(app.app, 'quit'):
            app.app.quit()
        app.app.destroy()


@pytest.mark.gui
@pytest.mark.timeout(10)
def test_windows_playlist_expand_click(monkeypatch, tk_cleanup):
    pytest.importorskip("customtkinter")
    win_main = _load_module("windows_main", WINDOWS_DIR / "main.py", WINDOWS_DIR)

    class FakeSearchController:
        def __init__(self):
            self.playlist_called = False

        def get_playlist_videos(self, url, callback=None, error_callback=None):
            self.playlist_called = True
            if callback:
                callback([])

    app = win_main.MainWindow()
    tk_cleanup(app)
    try:
        fake = FakeSearchController()
        app.search_controller = fake

        playlist = win_main.VideoInfo(
            video_id="pl1",
            title="Test Playlist",
            thumbnail_url="",
            duration=-1,
            channel="Test",
            url="https://youtube.com/playlist?list=abc",
            is_playlist=True,
            playlist_count=2
        )

        app._on_playlist_click(playlist)
        assert fake.playlist_called is True
    finally:
        if hasattr(app.app, 'quit'):
            app.app.quit()
        app.app.destroy()


@pytest.mark.gui
@pytest.mark.timeout(10)
def test_windows_download_clicks_trigger_controller(tk_cleanup):
    pytest.importorskip("customtkinter")
    win_main = _load_module("windows_main", WINDOWS_DIR / "main.py", WINDOWS_DIR)

    class FakeDownloadController:
        def __init__(self):
            self.calls = []

        def download_video(self, video, format_type="mp4", progress_callback=None, complete_callback=None, error_callback=None):
            self.calls.append(("video", format_type, video.video_id))

        def download_playlist(self, playlist, format_type="mp4", progress_callback=None, complete_callback=None, error_callback=None):
            self.calls.append(("playlist", format_type, playlist.video_id))

    app = win_main.MainWindow()
    tk_cleanup(app)
    try:
        app.download_controller = FakeDownloadController()

        video = win_main.VideoInfo(
            video_id="v1",
            title="Test Video",
            thumbnail_url="",
            duration=10,
            channel="Test",
            url="https://youtube.com/watch?v=abc",
            is_playlist=False
        )
        playlist = win_main.VideoInfo(
            video_id="pl1",
            title="Test Playlist",
            thumbnail_url="",
            duration=-1,
            channel="Test",
            url="https://youtube.com/playlist?list=abc",
            is_playlist=True,
            playlist_count=2
        )

        card = types.SimpleNamespace(
            update_progress=lambda p: None,
            download_complete=lambda f: None,
            download_error=lambda e: None
        )

        app._on_download_mp4(video, card)
        app._on_download_mp3(video, card)
        app._on_download_mp4(playlist, card)
        app._on_download_mp3(playlist, card)

        assert ("video", "mp4", "v1") in app.download_controller.calls
        assert ("video", "mp3", "v1") in app.download_controller.calls
        assert ("playlist", "mp4", "pl1") in app.download_controller.calls
        assert ("playlist", "mp3", "pl1") in app.download_controller.calls
    finally:
        if hasattr(app.app, 'quit'):
            app.app.quit()
        app.app.destroy()


@pytest.mark.gui
@pytest.mark.timeout(10)
def test_windows_login_error_opens_browser(monkeypatch, tk_cleanup):
    pytest.importorskip("customtkinter")
    win_main = _load_module("windows_main", WINDOWS_DIR / "main.py", WINDOWS_DIR)

    app = win_main.MainWindow()
    tk_cleanup(app)
    try:
        opened = {"called": False}

        def fake_open():
            opened["called"] = True

        monkeypatch.setattr(app, "_open_login_page", fake_open)
        app._on_search_error("Sign in to confirm your age")

        assert opened["called"] is True
    finally:
        if hasattr(app.app, 'quit'):
            app.app.quit()
        app.app.destroy()


@pytest.mark.gui
@pytest.mark.timeout(10)
def test_android_search_click_triggers_controller(monkeypatch):
    pytest.importorskip("kivy")
    android_main = _load_module("android_main", ANDROID_DIR / "main.py", ANDROID_DIR)

    class DummyInput:
        def __init__(self):
            self.text = ""

    class DummyLabel:
        def __init__(self):
            self.text = ""

    class DummyGrid:
        def __init__(self):
            self.items = []

        def add_widget(self, widget):
            self.items.append(widget)

        def clear_widgets(self):
            self.items = []

    class DummyButton:
        def __init__(self):
            self.opacity = 0
            self.disabled = True

    class DummyMainWidget:
        def __init__(self):
            self.ids = types.SimpleNamespace(
                search_input=DummyInput(),
                status_label=DummyLabel(),
                video_grid=DummyGrid(),
                back_btn=DummyButton()
            )
            self.current_mode = "search"
            self.current_playlist = None

    class FakeSearchController:
        def __init__(self):
            self.search_called = False
            self.url_called = False

        def search_videos(self, query, max_results=20, callback=None, error_callback=None):
            self.search_called = True
            if callback:
                callback(android_main.SearchResult(videos=[], query=query))

        def get_video_info(self, url, callback=None, error_callback=None):
            self.url_called = True
            if callback:
                callback(
                    android_main.VideoInfo(
                        video_id="v1",
                        title="Test Video",
                        thumbnail_url="",
                        duration=10,
                        channel="Test",
                        url=url,
                        is_playlist=False
                    )
                )

    app = android_main.YoutubeDownloaderApp()
    app.main_widget = DummyMainWidget()
    app.search_controller = FakeSearchController()

    monkeypatch.setattr(android_main.Clock, "schedule_once", lambda cb, *args, **kwargs: cb(0))

    app.main_widget.ids.search_input.text = "lofi mix"
    app.on_search()
    assert app.search_controller.search_called is True

    app.main_widget.ids.search_input.text = "https://youtube.com/watch?v=abc"
    app.on_search()
    assert app.search_controller.url_called is True


@pytest.mark.gui
@pytest.mark.timeout(10)
def test_android_playlist_expand_click(monkeypatch):
    pytest.importorskip("kivy")
    android_main = _load_module("android_main", ANDROID_DIR / "main.py", ANDROID_DIR)

    class DummyLabel:
        def __init__(self):
            self.text = ""

    class DummyGrid:
        def __init__(self):
            self.items = []

        def add_widget(self, widget):
            self.items.append(widget)

        def clear_widgets(self):
            self.items = []

    class DummyButton:
        def __init__(self):
            self.opacity = 0
            self.disabled = True

    class DummyMainWidget:
        def __init__(self):
            self.ids = types.SimpleNamespace(
                status_label=DummyLabel(),
                video_grid=DummyGrid(),
                back_btn=DummyButton()
            )
            self.current_mode = "search"
            self.current_playlist = None

    class FakeSearchController:
        def __init__(self):
            self.playlist_called = False

        def get_playlist_videos(self, url, callback=None, error_callback=None):
            self.playlist_called = True
            if callback:
                callback([])

    app = android_main.YoutubeDownloaderApp()
    app.main_widget = DummyMainWidget()
    app.search_controller = FakeSearchController()

    monkeypatch.setattr(android_main.Clock, "schedule_once", lambda cb, *args, **kwargs: cb(0))

    playlist = android_main.VideoInfo(
        video_id="pl1",
        title="Test Playlist",
        thumbnail_url="",
        duration=-1,
        channel="Test",
        url="https://youtube.com/playlist?list=abc",
        is_playlist=True,
        playlist_count=2
    )

    app.show_playlist_videos(playlist)
    assert app.search_controller.playlist_called is True
    assert app.main_widget.current_mode == "playlist"


@pytest.mark.gui
@pytest.mark.timeout(10)
def test_android_video_card_download_clicks(monkeypatch):
    pytest.importorskip("kivy")
    android_main = _load_module("android_main", ANDROID_DIR / "main.py", ANDROID_DIR)

    class DummyButton:
        def __init__(self, text=""):
            self.text = text
            self.disabled = False
            self.bg_color = None

    class DummyProgressBox:
        def __init__(self):
            self.height = 0
            self.opacity = 0

    class DummyProgressBar:
        def __init__(self):
            self.value = 0

    class DummyLabel:
        def __init__(self):
            self.text = ""

    class FakeDownloadController:
        def __init__(self):
            self.calls = []

        def download_video(self, video, format_type="mp4", progress_callback=None, complete_callback=None, error_callback=None):
            self.calls.append(("video", format_type, video.video_id))

        def download_playlist(self, playlist, format_type="mp4", progress_callback=None, complete_callback=None, error_callback=None):
            self.calls.append(("playlist", format_type, playlist.video_id))

    app = android_main.YoutubeDownloaderApp()
    app.download_controller = FakeDownloadController()

    monkeypatch.setattr(android_main.Clock, "schedule_once", lambda cb, *args, **kwargs: cb(0))

    video = android_main.VideoInfo(
        video_id="v1",
        title="Test Video",
        thumbnail_url="",
        duration=10,
        channel="Test",
        url="https://youtube.com/watch?v=abc",
        is_playlist=False
    )

    card = android_main.VideoCard(video, app)
    card.ids["mp4_btn"] = DummyButton("MP4")
    card.ids["mp3_btn"] = DummyButton("MP3")
    card.ids["progress_box"] = DummyProgressBox()
    card.ids["progress_bar"] = DummyProgressBar()
    card.ids["progress_label"] = DummyLabel()

    card.on_mp4_click()
    card.on_mp3_click()

    assert ("video", "mp4", "v1") in app.download_controller.calls
    assert ("video", "mp3", "v1") in app.download_controller.calls
    assert card.ids["mp4_btn"].disabled is True
    assert card.ids["mp3_btn"].disabled is True


@pytest.mark.gui
@pytest.mark.timeout(10)
def test_android_login_error_opens_app(monkeypatch):
    pytest.importorskip("kivy")
    android_main = _load_module("android_main", ANDROID_DIR / "main.py", ANDROID_DIR)

    class DummyLabel:
        def __init__(self):
            self.text = ""

    class DummyMainWidget:
        def __init__(self):
            self.ids = types.SimpleNamespace(status_label=DummyLabel())
            self.current_mode = "search"
            self.current_playlist = None

    app = android_main.YoutubeDownloaderApp()
    app.main_widget = DummyMainWidget()

    opened = {"called": False}

    def fake_open():
        opened["called"] = True

    monkeypatch.setattr(app, "_open_youtube_login", fake_open)
    app.on_error("Please sign in to confirm your age")

    assert opened["called"] is True


@pytest.mark.live
def test_live_mp4_download(tmp_path):
    video_url = os.getenv("TEST_VIDEO_URL") or "https://youtu.be/R6DiFlAXrS0?si=urdAIRLhOxX8Of8w"
    if os.getenv("RUN_LIVE_DOWNLOADS") != "1" or not video_url:
        pytest.skip("Set RUN_LIVE_DOWNLOADS=1 and TEST_VIDEO_URL to run live downloads")

    ytdlp = _import_windows_module("models.ytdlp_wrapper")
    wrapper = ytdlp.YTDLPWrapper(str(tmp_path))

    assert wrapper.download_video(video_url, "mp4") is True
    assert any(tmp_path.iterdir())


@pytest.mark.live
def test_live_mp3_download(tmp_path):
    video_url = os.getenv("TEST_VIDEO_URL") or "https://youtu.be/R6DiFlAXrS0?si=urdAIRLhOxX8Of8w"
    if os.getenv("RUN_LIVE_DOWNLOADS") != "1" or not video_url:
        pytest.skip("Set RUN_LIVE_DOWNLOADS=1 and TEST_VIDEO_URL to run live downloads")
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not found in PATH; required for mp3 conversion")

    ytdlp = _import_windows_module("models.ytdlp_wrapper")
    wrapper = ytdlp.YTDLPWrapper(str(tmp_path))

    assert wrapper.download_video(video_url, "mp3") is True
    assert any(tmp_path.iterdir())


@pytest.mark.live
def test_live_playlist_download(tmp_path):
    playlist_url = os.getenv("TEST_PLAYLIST_URL") or "https://youtube.com/playlist?list=PLdfO7XSwwy73bU9q114akyPe2LKwJA7W8&si=zXvnFZa2ylK2XUfz"
    if os.getenv("RUN_LIVE_DOWNLOADS") != "1" or not playlist_url:
        pytest.skip("Set RUN_LIVE_DOWNLOADS=1 and TEST_PLAYLIST_URL to run live downloads")

    ytdlp = _import_windows_module("models.ytdlp_wrapper")
    wrapper = ytdlp.YTDLPWrapper(str(tmp_path))

    assert wrapper.download_playlist(playlist_url, "mp4") is True
    assert any(tmp_path.iterdir())
