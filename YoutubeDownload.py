import yt_dlp, requests
from PyQt5 import QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
from io import BytesIO

class YoutubeDownload(QThread):

    progress = pyqtSignal(int)
    message = pyqtSignal(str, str)  # Format and message
    thumbnailFetched = pyqtSignal(QPixmap)
    clear_thumbnail = pyqtSignal()


    def __init__(self, url, ydl_opts, window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.ydl_opts = ydl_opts
        self.main_window = window 
        

    def run(self):

        video_id = self.extract_video_id(self.url)

        if video_id:
            thumbnail_url = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
            print(thumbnail_url)
            self.fetch_thumbnail(thumbnail_url)

        def my_hook(d):
            if d['status'] == 'downloading' and d.get('total_bytes'):
                progress = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
                self.progress.emit(progress)
 

            # if d['status'] == 'finished':
            #     self.message.emit(
            #         '<span style="color:#b8bb26;">{}</span>', 
            #         "Download completed successfully."
            #     )

            with open('./logs.txt', 'w') as log:
                log.write(str(d))
          
        self.ydl_opts['progress_hooks'] = [my_hook]
        
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                ydl.download([self.url])
                self.message.emit('<span style="color:#b8bb26;">{}</span>',
                                  "Download completed successfully."
                )
                self.main_window.progressBar.setValue(0)
                self.clear_thumbnail.emit()  # Emit the signal when progress is 0
                
            except Exception as e:

                self.message.emit(
                    '<span style="color:red;">{}</span>', 
                    f"Error: {str(e)}"
                )
                

    def stop(self):
        self.terminate()


    def extract_video_id(self, url):
        if "youtube.com/watch?v=" in url:
            return url.split("v=")[-1]

        elif "youtu.be/" in url:
            return url.split("/")[-1]

        else:
            return None


    def fetch_thumbnail(self, thumbnail_url):
        try:
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                image_data = response.content
                image = Image.open(BytesIO(image_data))
                image = image.convert("RGBA")  # Ensure image has alpha channel
                qimage = QImage(image.tobytes(), image.width, image.height, QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimage)
                pixmap = pixmap.scaled(128, 128, QtCore.Qt.KeepAspectRatio)
                self.thumbnailFetched.emit(pixmap)

            else:
                self.message.emit(
                    '<span style="color:red;">{}</span>', 
                    "Failed to fetch thumbnail"
                )

        except Exception as e:
            print(e)
            self.message.emit(
                '<span style="color:red;">{}</span>', 
                f"Error fetching thumbnail: {str(e)}"
            )


