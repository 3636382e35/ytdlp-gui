#!/usr/bin/env python3

import sys, toml, os, urllib
from YoutubeDownload import YoutubeDownload
from Logger import Logger
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDir, QSettings 
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QApplication,QGridLayout, QVBoxLayout, \
                            QMainWindow, QFileDialog, QLabel, QWidget  \
                            

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

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Youtube Downloader")

        self.youtube_info_frame.setHidden(True)
        self.audio_format_frame.setHidden(True)
        self.video_format_frame.setHidden(True)

        self.yt_search_chkbx.setHidden(True)
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
                'postprocessors': [{  
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'm4a',
                }]
        }))

        self.format_video_Rbtn.toggled.connect(
            lambda: self.ydl_opts.update({
                'format': 'bestvideo/best'})
        )

        self.format_audio_btn_1.toggled.connect(
            lambda: self.ydl_opts.update({
                'format': 'mp3/bestaudio/best'})
        )

        self.format_audio_btn_2.toggled.connect(
            lambda: self.ydl_opts.update({
                'format': 'm4a/bestaudio/best'})
        )

        self.format_video_btn_1.toggled.connect(
            lambda: self.ydl_opts.update({
                'format': 'mp4/bestvideo/best'})
        )

        self.format_video_btn_2.toggled.connect(
            lambda: self.ydl_opts.update({
                'format': 'webm/bestvideo/best'})
        )

        self.actionThemes.triggered.connect(self.select_colorscheme) 

        self.format_audio_Rbtn.toggled.connect(self.check_formats)
        self.format_video_Rbtn.toggled.connect(self.check_formats)


        self.clear_edit_txt_btn.clicked.connect(self.textEdit.clear)
        self.ydl_opts_btn.clicked.connect(self.check_ydl_opts)
        self.start_download_button.clicked.connect(self.onEditingFinished)
        self.toolButton.clicked.connect(self.show_file_dialog)


        self.yt_search_chkbx.stateChanged.connect(
            lambda: self.ydl_opts.update({
                'yt_search': self.yt_search_chkbx.isChecked()
            })
        )

    def check_formats(self):
        if self.format_audio_Rbtn.isChecked():
            self.audio_format_frame.setHidden(False)
            self.video_format_frame.setHidden(True)

        elif self.format_video_Rbtn.isChecked():
            self.audio_format_frame.setHidden(True)
            self.video_format_frame.setHidden(False)
        else:
            self.audio_format_frame.setHidden(True)
            self.video_format_frame.setHidden(True)

            # self.audio_format_btn_1.setChecked(False)
            # self.audio_format_btn_2.setChecked(False)

            # self.video_format_btn_1.setChecked(False)
            # self.video_format_btn_2.setChecked(False)


    def display_thumbnail(self, pixmap, title, duration):
        self.thumbnail_label.setPixmap(pixmap)
        self.title_label.setText(f"Title: {title}")
        self.duration_label.setText(f"Duration: {duration}")

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

    # TODO: 
    def select_colorscheme(self):
        self.file_dialog = QFileDialog(self)
        file_path = self.file_dialog.getOpenFileName(self, "Select QSS", "./config/themes/", "QSS Files (*.qss)")[0]
        if file_path:  # Check if a file path was selected
            with open(file_path, 'r') as file:
                qss = file.read()
                app.setStyleSheet(qss)

        with open('./config/config.toml', 'r') as f:
            config = toml.load(f)
        config['themes']['directory'] = file_path.split('/')[-1]
        with open('./config/config.toml', 'w') as f:
            toml.dump(config, f)

    def check_button_flags(self):
        return self.format_audio_Rbtn.isChecked() or self.format_video_Rbtn.isChecked()


    def onEditingFinished(self):
        self.textEdit.append(self.normalFormat.format("Downloading..."))
        if self.check_button_flags():

            url = self.url_line_edit.text()
            logger = Logger()

            logger.messageSignal.connect(self.textEdit.append)
            self.ydl_opts.update({'logger': logger})

            self.thread = YoutubeDownload(url, self.ydl_opts, self)
            self.thread.progress.connect(self.update_progress)
            self.thread.message.connect(self.display_message)
            self.thread.thumbnailFetched.connect(self.display_thumbnail)
            # self.thread.clear_console_log.connect(self.clear_console_log)
            self.thread.clear_thumbnail.connect(self.clear_thumbnail_label)
            self.thread.start()

        else:
            self.textEdit.append(self.warningFormat.format("Please select format."))


    def clear_thumbnail_label(self):
        self.thumbnail_label.clear()
        self.title_label.clear()
        self.duration_label.clear()
        self.youtube_info_frame.setHidden(True)

    def check_ydl_opts(self):
        self.textEdit.append("\n".join("{}\t{}".format(k, v) \
            for k, v in self.ydl_opts.items()))

    def update_progress(self, value):
        self.progressBar.setValue(value)
        if self.progressBar.value == 100:
            self.progressBar.setValue(0)

    # def clear_console_log(self):
    #     self.textEdit.clear()
        
    def display_message(self, format_str, message):
        self.textEdit.append(format_str.format(message))
        self.textEdit.verticalScrollBar().setValue(self.textEdit.verticalScrollBar().maximum())


    def read_settings(self):
        settings = QSettings("./config/config.ini", QSettings.IniFormat)
        audio_btn_state = settings.value("audio_btn_state", False, type=bool)
        video_btn_state = settings.value("video_btn_state", False, type=bool)
        yt_search_chkbx_state = settings.value("yt_search_chkbx_state", False, type=bool)
        format_audio_btn_1_state = settings.value("format_audio_btn_1_state", False, type=bool)
        format_audio_btn_2_state = settings.value("format_audio_btn_2_state", False, type=bool)
        format_video_btn_1_state = settings.value("format_video_btn_1_state", False, type=bool)
        format_video_btn_2_state = settings.value("format_video_btn_2_state", False, type=bool)
        video_format_frame_state = settings.value("video_format_frame_state", False, type=bool)
        audio_format_frame_state = settings.value("audio_format_frame_state", False, type=bool)

        self.video_format_frame.setHidden(video_format_frame_state)
        self.audio_format_frame.setHidden(audio_format_frame_state)
        self.format_audio_Rbtn.setChecked(audio_btn_state)
        self.format_video_Rbtn.setChecked(video_btn_state)
        self.yt_search_chkbx.setChecked(yt_search_chkbx_state)
        self.format_audio_btn_1.setChecked(format_audio_btn_1_state)
        self.format_audio_btn_2.setChecked(format_audio_btn_2_state)
        self.format_video_btn_1.setChecked(format_video_btn_1_state)
        self.format_video_btn_2.setChecked(format_video_btn_2_state)
        pos = settings.value("pos", self.pos())
        size = settings.value("size", self.size())
        self.move(pos)
        self.resize(size)


    def write_settings(self):
        settings = QSettings("./config/config.ini", QSettings.IniFormat)
        settings.setValue("audio_btn_state", self.format_audio_Rbtn.isChecked())
        settings.setValue("video_btn_state", self.format_video_Rbtn.isChecked())
        settings.setValue("yt_search_chkbx_state", self.yt_search_chkbx.isChecked())
        settings.setValue("format_audio_btn_1_state", self.format_audio_btn_1.isChecked())
        settings.setValue("format_audio_btn_2_state", self.format_audio_btn_2.isChecked())
        settings.setValue("format_video_btn_1_state", self.format_video_btn_1.isChecked())
        settings.setValue("format_video_btn_2_state", self.format_video_btn_2.isChecked())
        settings.setValue("video_format_frame_state", self.video_format_frame.isChecked())
        settings.setValue("audio_format_frame_state", self.audio_format_frame_state.isChecked())
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    config = toml.load('./config/config.toml')
    file = open('./config/themes/' + config['themes']['directory'], 'r')
    with file:
        qss = file.read()
        app.setStyleSheet(qss)

    window = MainWindow()
    window.show()
    window.read_settings()

    sys.exit(appExec(window))

