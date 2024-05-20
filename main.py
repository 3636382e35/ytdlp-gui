#!/usr/bin/env python3

import yt_dlp
import sys

import qdarkstyle

# import qtmodern.styles
# import qtmodern.windows

from MyLogger import MyLogger

from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic, QtCore, QtGui


# TODO: valid url search lock
# def if valid url, lock search button and url input


class YoutubeDownload(QThread):
    progress = pyqtSignal(int)
    message = pyqtSignal(str, str)  # Format and message

    def __init__(self, url, ydl_opts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.ydl_opts = MainWindow.ydl_opts
        
        # ydl_opts = self.ydl_opts

    def run(self):
        def my_hook(d):
            if d['status'] == 'downloading' and d.get('total_bytes'):
                progress = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
                self.progress.emit(progress)
            if d['status'] == 'finished':
                self.message.emit('<span style="color:green;">{}</span>', "Download completed successfully.")

        self.ydl_opts['progress_hooks'] = [my_hook]

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                ydl.download([self.url])
                self.message.emit('<span style="color:green;">{}</span>', "Download completed successfully.")
            except Exception as e:
                self.message.emit('<span style="color:red;">{}</span>', f"Error: {str(e)}")

    def stop(self):
        self.terminate()


class MainWindow(QMainWindow):

    ydl_opts = {
        'quiet': False,
        'yt_search': False,
        'progress_hooks': [],
        'outtmpl': None,
        'logger': None,
        'format': None,
    }

    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/main_v2.ui', self)

        self.errorFormat = '<span style="color:red;">{}</span>'
        self.warningFormat = '<span style="color:orange;">{}</span>'
        self.validFormat = '<span style="color:green;">{}</span>'

        # buttons
        self.format_audio_Rbtn.toggled.connect(lambda: self.ydl_opts.update({
                'format': 'm4a/bestaudio/best',
                'postprocessors': [{  # Extract audio using ffmpeg
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }]
        }))


        #font
        # self.fontstd = QFont("JetBrainsMonoNL Nerd Font", 10)
        # self.fontstd.setFamily('Monospace')
        # self.fontstd.setFixedPitch(True)


        self.format_video_Rbtn.toggled.connect(lambda: self.ydl_opts.update({'format': 'bestvideo/best'}))
        self.clear_edit_txt_btn.clicked.connect(self.textEdit.clear)
        self.ydl_opts_btn.clicked.connect(self.check_ydl_opts)
        self.start_download_button.clicked.connect(self.onEditingFinished)
        self.check_url_button.clicked.connect(self.on_check_url_click)
        self.yt_search_chkbx.stateChanged.connect(lambda: self.ydl_opts.update({'yt_search': self.yt_search_chkbx.isChecked()}))

    def on_check_url_click(self):
        url = self.url_line_edit.text()
        logger = MyLogger()

        if self.is_valid_url(url, logger):
            self.textEdit.append(self.validFormat.format("'"+url+"' is a valid URL."))
        else:
            self.textEdit.append(self.errorFormat.format("'"+url+"' is not a valid URL."))

    def onEditingFinished(self):
        url = self.url_line_edit.text()
        logger = MyLogger()

        if self.is_valid_url(url, logger):
            logger.messageSignal.connect(self.textEdit.append)
            self.ydl_opts.update({'logger': logger})
            self.thread = YoutubeDownload(url, self.ydl_opts)
            self.thread.progress.connect(self.update_progress)
            self.thread.message.connect(self.display_message)
            self.thread.start()
        else:
            self.textEdit.append(self.errorFormat.format("Cannot download invalid URL."))

    def is_valid_url(self, url, logger):
        self.ydl_opts.update({
            'quiet': True,
            'logger': logger
        })

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                ydl.extract_info(url, download=False)
                return True
            except Exception:
                return False

    def check_ydl_opts(self):
        self.textEdit.append("\n".join("{}\t{}".format(k, v) for k, v in self.ydl_opts.items()))

    def update_progress(self, value):
        self.progressBar.setValue(value)

    def display_message(self, format_str, message):
        self.textEdit.append(format_str.format(message))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    file = open("./Darkeum.qss",'r')
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

