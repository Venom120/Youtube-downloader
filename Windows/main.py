import sys
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
import tkinter
import customtkinter as cust
from pytube import YouTube, Playlist
from PIL import Image
from io import BytesIO
import os, requests, threading

# Functions
def url_to_image(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img = img.resize((190,100))
            return img
        else:
            finishLabel.configure(text=f"Failed to retrieve Thumbnail.\nError {response.status_code}!!")
            return None
    except Exception as e:
        finishLabel.configure(text=f"An error occurred: {e}")
        return None
downloads_path = os.path.expanduser("~/Downloads")
def show_details():
    p_percent.configure(text="0%")
    progressbar.set(0)
    mp4button.configure(text="", state="disabled", fg_color="transparent")
    mp3button.configure(text="", state="disabled", fg_color="transparent")
    finishLabel.configure(text="")
    video_label.configure(text="")
    thumbnail_label.configure(text="",image=None)
    try:
        ytLink = link_input.get()
        # check weather the link is playlist link or video link
        if "playlist" in ytLink:
            try:
                yt = Playlist(ytLink)
                temp_img = url_to_image(str(yt.videos[0].thumbnail_url))
                time = str(f"{yt.length} videos in this playlist\nAll will be Downloaded")
                video_label.configure(text=time, text_color="white", justify="left")
            except Exception as ex:
                print(ex)
                p_percent.configure(text="0%")
                progressbar.set(0)
                mp4button.configure(text="", state="disabled", fg_color="transparent")
                mp3button.configure(text="", state="disabled", fg_color="transparent")
                finishLabel.configure(text="Invalid Link", text_color="red")
                video_label.configure(text="")
                thumbnail_label.configure(text="",image=None)
        else:
            try:
                yt = YouTube(ytLink)
                time = str(f"{yt.length//60}m:{(yt.length%60 if yt.length>=10 else ('0'+str(yt.length%60)))}s {yt.streams.get_highest_resolution().resolution}")
                temp_img = url_to_image(yt.thumbnail_url)
                video_label.configure(text=f"{yt.title}\n{time}", text_color="white", justify="left")
            except:
                print(ex)
                p_percent.configure(text="0%")
                progressbar.set(0)
                mp4button.configure(text="", state="disabled", fg_color="transparent")
                mp3button.configure(text="", state="disabled", fg_color="transparent")
                finishLabel.configure(text="Invalid Link", text_color="red")
                video_label.configure(text="")
                thumbnail_label.configure(text="",image=None)
        if temp_img:
            thumbnail = cust.CTkImage(light_image=temp_img,dark_image=temp_img, size=(190,100))
            thumbnail_label.configure(image=thumbnail)
            mp4button.configure(text="MP4", state="normal", fg_color=["#3a7ebf", "#1f538d"], text_color="white")
            mp3button.configure(text="MP3", state="normal", fg_color=["#3a7ebf", "#1f538d"], text_color="white")
        else:
            finishLabel.configure(text="No Internet", text_color="red")
            pass
    except Exception as ex:
        print(ex)
        p_percent.configure(text="0%")
        progressbar.set(0)
        mp4button.configure(text="", state="disabled", fg_color="transparent")
        mp3button.configure(text="", state="disabled", fg_color="transparent")
        finishLabel.configure(text="Invalid Link", text_color="red")
        video_label.configure(text="")
        thumbnail_label.configure(text="",image=None)

def MP4download():
    p_percent.configure(text="0%")
    progressbar.set(0)
    finishLabel.configure(text="")
    mp4button.configure(text="MP4", text_color = "white", state="disabled")
    mp3button.configure(text="MP3", text_color = "white", state="disabled")
    def download_thread(video):
        try:
            yt = YouTube(video, on_progress_callback=progress_check,on_complete_callback=complete)
            stream = yt.streams.filter(progressive=True).get_highest_resolution()
            stream.download(downloads_path, filename=f"{stream.default_filename.replace(' ','_')}")
            mp4button.configure(text="Downloaded", text_color = "lime", state="normal")
            mp3button.configure(text="MP3", text_color = "white", state="normal")
        except Exception as ex:
            finishLabel.configure(text=f"{ex}",text_color="red")
    ytLink = link_input.get()
    if "playlist" in ytLink:
        videos=Playlist(ytLink).video_urls
    else:
        videos=[str(ytLink)]
    for video in videos:
        threading.Thread(target=download_thread(video)).start()

def MP3download():
    p_percent.configure(text="0%")
    progressbar.set(0)
    finishLabel.configure(text="")
    mp4button.configure(text="MP4", text_color = "white", state="disabled")
    mp3button.configure(text="MP3", text_color = "white", state="disabled")
    def download_thread(video33):
        try:
            yt = YouTube(video33, on_progress_callback=progress_check,on_complete_callback=complete)
            stream = yt.streams.filter(only_audio=True).first()
            stream.download(downloads_path, filename=f"{stream.default_filename.replace(' ','_')}.mp3")
            mp4button.configure(text="MP4", text_color = "white", state="normal")
            mp3button.configure(text="Downloaded", text_color = "lime", state="normal")
        except Exception as ex:
            finishLabel.configure(text=f"{ex}")
    ytLink = link_input.get()
    if "playlist" in ytLink:
        videos3=Playlist(ytLink).video_urls
    else:
        videos3=[str(ytLink)]
    for video3 in videos3:
        threading.Thread(target=download_thread(video3)).start()
def progress_check(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    # update progress bar
    progressbar.set(percentage_of_completion/100)
    # update percentage label
    p_percent.configure(text=f"{int(percentage_of_completion)}%")
    p_percent.update()
def complete(downloaded_stream, path_stream):
    progressbar.set(1)
    p_percent.configure(text="100%")

# system settings
cust.set_appearance_mode("System")
cust.set_default_color_theme("blue")

# app frame
app = cust.CTk()
app.title("Youtube Downloader")
app.geometry("720x480")
app.iconbitmap(resource_path("assets/Youtube_icon.ico"))

# Adding title
title = cust.CTkLabel(app, text="Link to the video")
title.pack()

# Link input
url_var = tkinter.StringVar()
link_input = cust.CTkEntry(app, width=350, height=60, textvariable=url_var)
link_input.pack()

# Status
finishLabel = cust.CTkLabel(app,text="")
finishLabel.pack()

# Download Button
download = cust.CTkButton(app, text="Download", command=show_details)
download.pack()

# Download Frame
download_frame = cust.CTkFrame(app, fg_color = "transparent")
download_frame.pack(pady=20)
# Thumbnail image
thumbnail_label = cust.CTkLabel(download_frame, text="")
thumbnail_label.grid(row=0, column=0, padx=20, pady=20)
# video frame
video_frame = cust.CTkFrame(download_frame, fg_color="transparent")
video_frame.grid(row=0, column=1, columnspan=1)
# Video Title
video_label = cust.CTkLabel(video_frame, text="")
video_label.grid(row=0, column=1)
# MP4 Button
mp4button = cust.CTkButton(video_frame, text="", command=MP4download, state="disabled", fg_color="transparent")
mp4button.grid(row=1, column=1, padx=0, pady=9, sticky="w")
# MP3 Button
mp3button = cust.CTkButton(video_frame, text="", command=MP3download, state="disabled", fg_color="transparent")
mp3button.grid(row=1,padx=2,pady=2,column=2, sticky="w")

# Progress percentage
p_percent = cust.CTkLabel(app, text="0%")
p_percent.pack()
# Progressbar
progressbar = cust.CTkProgressBar(app, mode="determinate", width=400)
progressbar.set(0)
progressbar.pack()


app.resizable(False, False)
if __name__ == "__main__":
    app.mainloop()
