import tkinter
import customtkinter as cust
from pytube import YouTube
from PIL import Image, ImageTk
from io import BytesIO
import os, time, pytube, numpy as np, requests

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
    try:
        ytLink = link_input.get()
        yt = YouTube(ytLink)
        time = str(f"{yt.length//60}m:{(yt.length%60 if yt.length>=10 else ("0"+str(yt.length%60)))}s   {yt.streams.get_highest_resolution().resolution}")
        video_label.configure(text=f"{yt.title}\n{time}", text_color="white", justify="left")
        progressbar.set(0)
        p_percent.configure(text="0%")
        finishLabel.configure(text="")
        temp_img = url_to_image(yt.thumbnail_url)
        if temp_img:
            thumbnail = cust.CTkImage(light_image=temp_img,dark_image=temp_img, size=(190,100))
            thumbnail_label.configure(image=thumbnail)
            mp4button.configure(text="MP4", state="normal", fg_color=["#3a7ebf", "#1f538d"], text_color="white")
            mp3button.configure(text="MP3", state="normal", fg_color=["#3a7ebf", "#1f538d"], text_color="white")
        else:
            finishLabel.configure(text="No Internet", text_color="red")
    except Exception as ex:
        print(ex.with_traceback)
        mp4button.configure(text="", state="disabled", fg_color="transparent")
        mp3button.configure(text="", state="disabled", fg_color="transparent")
        finishLabel.configure(text="Invalid Link", text_color="red")
        video_label.configure(text="")
        thumbnail_label.configure(text="",image=None)
def MP4download():
    p_percent.configure(text="0%")
    try:
        ytLink = link_input.get()
        yt = YouTube(ytLink, on_progress_callback=progress_check,on_complete_callback=complete)
        finishLabel.configure(text="")
        stream = yt.streams.filter(progressive=True).get_highest_resolution()
        stream.download(downloads_path, filename=f"{stream.default_filename}")
        mp4button.configure(text="Downloaded", text_color = "lime")
    except:
        finishLabel.configure(text="Invalid link", text_color = "red")
def MP3download():
    p_percent.configure(text="0%")
    try:
        ytLink = link_input.get()
        yt = YouTube(ytLink, on_progress_callback=progress_check,on_complete_callback=complete)
        finishLabel.configure(text="")
        try:
            stream = yt.streams.filter(only_audio=True).first()
            stream = stream.download(downloads_path, filename=f"{stream.default_filename[:-4]}.mp3")
            mp3button.configure(text="Downloaded", text_color="lime")
        except:
            finishLabel.configure(text="Invalid link", text_color="red")
    except Exception as err:
        print(err)
        finishLabel.configure(text="Invalid link", text_color = "red")
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
