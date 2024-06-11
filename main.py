#!/usr/bin/env python3

import sys, toml, os, urllib
from YoutubeDownload import YoutubeDownload
from io import BytesIO
from MyLogger import MyLogger
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDir, QSettings 
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QMainWindow, QFileDialog, QLabel, QWidget
from PyQt5 import uic, QtCore

# exec on exit
def appExec(window):
    app = QApplication(sys.argv)
    app.exec_()
    window.write_settings()

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
        self.toolButton.clicked.connect(self.show_file_dialog)

        # adding widget programatically
        self.thumbnail_label = QLabel(self)
        self.central_widget = self.centralWidget()
        self.central_widget.layout().addWidget(self.thumbnail_label)  
        self.thumbnail_label.setContentsMargins(10, 6, 10, 6)
        

        self.yt_search_chkbx.stateChanged.connect(
            lambda: self.ydl_opts.update({
                'yt_search': self.yt_search_chkbx.isChecked()
            })
        )
    

    def display_thumbnail(self, pixmap):
        # self.thumbnail_label.setVisible(False)
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


    def check_button_flags(self):
        return self.format_audio_Rbtn.isChecked() or self.format_video_Rbtn.isChecked()


    def onEditingFinished(self):
        if self.check_button_flags():

            url = self.url_line_edit.text()
            logger = MyLogger()

            logger.messageSignal.connect(self.textEdit.append)
            self.ydl_opts.update({'logger': logger})

            self.thread = YoutubeDownload(url, self.ydl_opts, self)
            self.thread.progress.connect(self.update_progress)
            self.thread.message.connect(self.display_message)
            self.thread.thumbnailFetched.connect(self.display_thumbnail)
            self.thread.clear_thumbnail.connect(self.clear_thumbnail_label)
            self.thread.start()
        else:
            self.textEdit.append(self.warningFormat.format("Please select format."))

    def clear_thumbnail_label(self):
        self.thumbnail_label.clear()

    def check_ydl_opts(self):
        self.textEdit.append("\n".join("{}\t{}".format(k, v) for k, v in self.ydl_opts.items()))


    def update_progress(self, value):
        self.progressBar.setValue(value)
        if self.progressBar.value == 100:
            self.progressBar.setValue(0)

        
    def display_message(self, format_str, message):
        self.textEdit.append(format_str.format(message))


    def read_settings(self):
        settings = QSettings("./config/config.ini", QSettings.IniFormat)

        audio_btn_state = settings.value("audio_btn_state", False, type=bool)
        video_btn_state = settings.value("video_btn_state", False, type=bool)
        yt_search_chkbx_state = settings.value("yt_search_chkbx_state", False, type=bool)
        
        self.format_audio_Rbtn.setChecked(audio_btn_state)
        self.format_video_Rbtn.setChecked(video_btn_state)
        self.yt_search_chkbx.setChecked(yt_search_chkbx_state)

        pos = settings.value("pos", self.pos())
        size = settings.value("size", self.size())
        self.move(pos)
        self.resize(size)


    def write_settings(self):
        settings = QSettings("./config/config.ini", QSettings.IniFormat)
        #to boolean
        settings.setValue("audio_btn_state", self.format_audio_Rbtn.isChecked())
        settings.setValue("video_btn_state", self.format_video_Rbtn.isChecked())
        settings.setValue("yt_search_chkbx_state", self.yt_search_chkbx.isChecked())
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    config = toml.load('./config/config.toml')
    file = open('./config/' + config['themes']['directory'], 'r')
    with file:
        qss = file.read()
        app.setStyleSheet(qss)

    window = MainWindow()
    window.show()
    window.read_settings()

    sys.exit(appExec(window))

