#!/usr/bin/env python3

# import qtmodern.styles
# import qtmodern.windows

import yt_dlp, sys, toml, os, urllib, requests
from PIL import Image
from io import BytesIO
from MyLogger import MyLogger
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import pyqtSignal, QThread, QDir
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QMainWindow, QFileDialog, QLabel, QWidget
from PyQt5 import uic

class YoutubeDownload(QThread):

    progress = pyqtSignal(int)
    message = pyqtSignal(str, str)  # Format and message
    thumbnailFetched = pyqtSignal(QPixmap)


    def __init__(self, url, ydl_opts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.ydl_opts = ydl_opts
        
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

            if d['status'] == 'finished':
                self.message.emit(
                    '<span style="color:#b8bb26;">{}</span>', 
                    "Download completed successfully."
                )

            with open('./logs.txt', 'w') as log:
                log.write(str(d))
          
        self.ydl_opts['progress_hooks'] = [my_hook]
        
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                # print((ydl.extract_info(self.url, download=False)))
                ydl.download([self.url])

                # self.message.emit('<span style="color:green;">{}</span>', "Download completed successfully.")
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

                # Convert PIL Image to QImage
                qimage = QImage(image.tobytes(), image.width, image.height, QImage.Format_RGBA8888)

                # Convert QImage to QPixmap and emit it
                pixmap = QPixmap.fromImage(qimage)
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



class MainWindow(QMainWindow):

    ydl_opts = {
        'quiet': False,
        'verbose': True,
        'yt_search': False,
        'progress_hooks': [],
        'outtmpl': None,
        'logger': None,
        'format': None,
        'nocheckcertificate' : True,
        'geobypass': True,
        'listformats' : False,
    }

    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/main_v2.ui', self)

        #default output directory
        # self.curr_dir = QDir.currentPath()
        with open('./config/config.toml', 'r') as f:
            config = toml.load(f)

        self.curr_dir = config['output']['directory']
        self.file_path_label.setText(self.curr_dir)

        self.ydl_opts.update({'outtmpl': self.curr_dir + '/%(title)s.%(ext)s'})
        self.file_dialog = QFileDialog(self, options=QFileDialog.DontUseNativeDialog)

        self.errorFormat = '<span style="color:#fb4934;">{}</span>'
        self.warningFormat = '<span style="color:#fabd2f;">{}</span>'
        self.validFormat = '<span style="color:#b8bb26;">{}</span>'
        self.normalFormat = '<span style="color:#;">{}</span>'

        # buttons
        self.format_audio_Rbtn.toggled.connect(lambda: self.ydl_opts.update({
                'format': 'm4a/bestaudio/best',
                'postprocessors': [{  # Extract audio using ffmpeg
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }]
        }))

        self.format_video_Rbtn.toggled.connect(
            lambda: self.ydl_opts.update({
                'format': 'bestvideo/best'})
        )

        self.clear_edit_txt_btn.clicked.connect(self.textEdit.clear)
        self.ydl_opts_btn.clicked.connect(self.check_ydl_opts)
        self.start_download_button.clicked.connect(self.onEditingFinished)
        # self.check_url_button.clicked.connect(self.on_check_url_click)
        self.toolButton.clicked.connect(self.show_file_dialog)

        # adding widget programatically
        self.thumbnail_label = QLabel(self)
        self.central_widget = self.centralWidget()
        self.central_widget.layout().addWidget(self.thumbnail_label)  # Add the label to the central widget.

        self.yt_search_chkbx.stateChanged.connect(
            lambda: self.ydl_opts.update({
                'yt_search': self.yt_search_chkbx.isChecked()
            })
        )
    

    def display_thumbnail(self, pixmap):
        self.thumbnail_label.setPixmap(pixmap)

    def show_file_dialog(self):
        file_path= self.file_dialog.getExistingDirectory(self, "Select Directory") 
        if file_path:
            with open('./config/config.toml', 'r') as f:
                config = toml.load(f)
            config['output']['directory'] = file_path 
            with open('./config/config.toml', 'w') as f: 
                toml.dump(config, f)
            self.file_path_label.setText(file_path)
            self.ydl_opts.update({'outtmpl': file_path + '/%(title)s.%(ext)s'})

    # def on_check_url_click(self):
    #     url = self.url_line_edit.text()
        # logger = MyLogger()
        # if self.is_valid_url(url, logger):
        #     self.textEdit.append(self.validFormat.format("'"+url+"' is a valid URL."))
        # else:
        #     self.textEdit.append(self.errorFormat.format("'"+url+"' is not a valid URL."))



    def onEditingFinished(self):
        url = self.url_line_edit.text()
        logger = MyLogger()

        # if self.is_valid_url(url, logger):
        logger.messageSignal.connect(self.textEdit.append)
        self.ydl_opts.update({'logger': logger})

        self.thread = YoutubeDownload(url, self.ydl_opts)
        self.thread.progress.connect(self.update_progress)
        self.thread.message.connect(self.display_message)
        self.thread.thumbnailFetched.connect(self.display_thumbnail)
        self.thread.start()
        # else:
        #     self.textEdit.append(self.errorFormat.format("Cannot download invalid URL."))



    def is_valid_url(self, url, logger):
        self.ydl_opts.update({
            'quiet': True,
            'logger': logger,
            
            # 'listformats' : True
        })

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                ydl.extract_info(url, download=False)

                # self.ydl_opts.update({
                #     'listformats' : False
                # }) 
                return True
            except Exception:
                return False

    def check_ydl_opts(self):
        self.textEdit.append("\n".join("{}\t{}".format(k, v) for k, v in self.ydl_opts.items()))

    def update_progress(self, value):
        self.progressBar.setValue(value)
        if self.progressBar.value == 100:
            self.progressBar.setValue(0)
        
    def display_message(self, format_str, message):
        self.textEdit.append(format_str.format(message))



if __name__ == "__main__":
    app = QApplication(sys.argv)

    config = toml.load('./config/config.toml')
    file = open('./config/' + config['themes']['directory'], 'r')
    with file:
        qss = file.read()
        app.setStyleSheet(qss)

    window = MainWindow()
    window.show()


    # for qtdark
    # app.setStyleSheet(qdarkstyle.load_stylesheet())

    # for qtmodern
    # qtmodern.styles.dark(app)
    # mw = qtmodern.windows.ModernWindow(window)
    # mw.show()


    sys.exit(app.exec_())

