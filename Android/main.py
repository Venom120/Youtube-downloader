from kivy.config import Config
Config.set('kivy', 'window_icon', 'assets/Youtube_icon.ico')
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()

from kivy.app import App, StringProperty
from kivy import platform
from pathlib import Path
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window 
from pytube import YouTube,Playlist
import os.path, threading, pytube
from kivy.properties import StringProperty
class YtDownloader(ScrollView):
    thumbnail_image_link = StringProperty()
    if platform == 'win':
        output_path = f'{str(os.path.expanduser("~/Downloads/"))}'
    elif platform == 'android':
        from android.storage import primary_external_storage_path
        output_path = f'{str(primary_external_storage_path())}/Download/'
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
    def show_details(self):
        ytLink = self.ids.link.text
        Clock.schedule_once(lambda dt: self.update_details(ytLink), 0)


    def update_details(self, yt):
        try:
            self.ids.mp4.text = "MP4"
            self.ids.mp3.text = "MP3"
            self.ids.buttons.color = (1,1,1,1)
            self.ids.buttons.disabled = True
            self.ids.Youtube_details.opacity = 0
            self.ids.progress_details.opacity = 0
            self.ids.progressbar.value = 0
            self.ids.p_percent.text = "0%"
            self.ids.error_display.text = ""
        except:
            self.show_error("Update details failed")
        try:
            ytLink = self.ids.link.text
            yt = YouTube(ytLink)
            yt.title = f"{yt.title[0:30]} ..."
            time = f"{yt.length // 60}m:{(yt.length % 60 if yt.length >= 10 else ('0' + str(yt.length % 60)))}s   {yt.streams.get_highest_resolution().resolution}    {yt.streams.get_highest_resolution().filesize / 1024.0 // 1024}Mb"
            self.ids.progress_details.opacity = 1
            self.thumbnail_image_link = str(yt.thumbnail_url)
            self.ids.Youtube_details.opacity = 1
            self.ids.yt_title.text = f"{yt.title}"
            self.ids.yt_details.text = f"{time}"
            self.ids.thumbnail_image.opacity: 1
            self.ids.buttons.disabled = False
            self.ids.mp4.text = "MP4"
            self.ids.mp3.text = "MP3"
        except pytube.exceptions.RegexMatchError as reg_error:
            self.show_error("Invalid Link")
        except Exception as ex:
            self.show_error(f"{str(ex)[0:50]}\n{str(ex)[50:]}")


    def show_error(self, message):
        self.ids.error_display.text = message
        self.ids.error_display.color = (1, 0, 0, 0.85)

    def progress_check(self, stream, chunk, bytes_remaining):
        try:
            value = round((1 - bytes_remaining / stream.filesize) * 100, 1)
            self.ids.progressbar.value = value
            self.ids.p_percent.text = f"{int(value)}%"
        except Exception as ex:
            self.show_error("progress_check error")

    def complete_func(self, *args):
        try:
            self.ids.progressbar.value = 100
            self.ids.p_percent.text = "100%"
            self.ids.Youtube_details.opacity = 1
        except Exception as ex:
            self.show_error("progress_check error")
        

    def MP4download(self):
        self.ids.progressbar.value = 0
        self.ids.p_percent.text = "0%"
        self.ids.error_display.text = ""
        self.ids.mp3.text = "MP3"
        self.ids.mp4.text = "MP4"
        self.ids.buttons.disabled = True
        self.ids.buttons.color = (1,1,1,1)
        app = App.get_running_app()

        def download_thread(video4):
            try:
                yt = YouTube(video4, on_progress_callback=self.progress_check, on_complete_callback=self.complete_func)
                stream = yt.streams.filter(progressive=True).get_highest_resolution()
                stream.download(self.output_path, filename=f"{stream.default_filename.replace(' ','_')}")
                self.ids.mp4.text = "Downloaded"
                self.ids.mp4.color = (0,1,0,0.8)
                self.ids.mp3.text = "MP3"
                self.ids.mp3.color = (1,1,1,1)
                self.ids.buttons.disabled = False
            except Exception as ex:
                self.show_error(f"{ex}")
        ytLink = self.ids.link.text
        if "playlist" in ytLink:
            videos=Playlist(ytLink).video_urls
        else:
            videos=[str(ytLink)]
        for video in videos:
            threading.Thread(target=download_thread(video)).start()

    def MP3download(self):
        self.ids.progressbar.value = 0
        self.ids.p_percent.text = "0%"
        self.ids.error_display.text = ""
        self.ids.mp4.text = "MP4"
        self.ids.mp3.text = "MP3"
        self.ids.buttons.disabled = True

        def download_thread(video33):
            try:
                yt = YouTube(video33, on_progress_callback=self.progress_check, on_complete_callback=self.complete_func)
                stream = yt.streams.filter(only_audio=True).first()
                stream.download(self.output_path, filename=f"{stream.default_filename.replace(' ','_')}.mp3")
                self.ids.mp3.text = "Downloaded"
                self.ids.mp3.color = (0,1,0,0.8)
                self.ids.mp4.text = "MP4"
                self.ids.mp4.color = (1,1,1,1)
                self.ids.buttons.disabled = False
            except Exception as ex:
                self.show_error(f"{ex}")

        ytLink = self.ids.link.text
        if "playlist" in ytLink:
            videos3=Playlist(ytLink).video_urls
        else:
            videos3=[str(ytLink)]
        for video3 in videos3:
            threading.Thread(target=download_thread(video3)).start()


class YoutubeDownloader(App):
    def build(self):
        self.icon = r"assets/Youtube_icon.png"
        root = Builder.load_file("main.kv")
        Window.clearcolor = (36/255, 36/255, 36/255, 1)
        return YtDownloader()
    def on_start(self):
        try:
            os.mkdir(self.output_path)
        except:
            pass


if __name__ == "__main__":
    YoutubeDownloader().run()
