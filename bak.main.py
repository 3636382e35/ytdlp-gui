#!/usr/bin/env python3
# basedpyright: strict, reportUnknownVariableType=false

import yt_dlp, sys, os
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic, QtCore, QtGui

class MyLogger(QtCore.QObject):

    messageSignal = QtCore.pyqtSignal(str)
    def debug(self, msg):
        self.messageSignal.emit(msg)

    def warning(self, msg):
        self.messageSignal.emit(msg)

    def error(self, msg):
        self.messageSignal.emit(msg)

class YoutubeDownload(QtCore.QThread):
    def __init__(self, url, ydl_opts, *args, **kwargs):
        QtCore.QThread.__init__(self, *args, **kwargs)
        self.url = url
        self.ydl_opts = ydl_opts

    def run(self):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            ydl.download([self.url])


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # Load the UI file
        uic.loadUi('./ui/main.ui', self)

        # Connect any signals and slots here, for example:
        # self.myButton.clicked.connect(self.on_button_click)

        # Set the window size to the size of the UI
        self.ydl_opts = {
            'quiet' : False,
            'yt_search' : False,
            'progress_hooks': [],
            'logger' : None
        }

        self.setFixedSize(self.size())

        self.download_btn.clicked.connect(self.onEditingFinished) 
        self.url_check_btn.clicked.connect(self.on_check_url_click)
        self.yt_search_chkbx.stateChanged.connect(self.yt_search_chkbx_click) 


    def yt_search_chkbx_click(self):
        if self.yt_search_chkbx.isChecked():
           self.ydl_opts.update({
               'yt_search' : True,              
           })

        else:
            self.ydl_opts.update({
               'yt_search' : False,              
            })

            # self.lineEdit.setEnabled(False)

    def on_check_url_click(self):

        url = self.lineEdit.text() # type : ignore[ruleName]
        prev_cursor = self.plainTextEdit.textCursor() # ignore[ruleName]
        logger = MyLogger()
        logger.messageSignal.connect(self.plainTextEdit.append)


        if self.is_valid_url(url, logger):
            # self.plainTextEdit.moveCursor(QTextCursor.End)
            # self.plainTextEdit.insertPlaintext(url)
            self.plainTextEdit.append("'"+url+"' is a valid URL.")
            # self.plainTextEdit.append(str(self.ydl_opts))
            # self.plainTextEdit.setTextCursor(prev_cursor)
        else:
            # self.plainTextEdit.moveCursor(QTextCursor.End)
            self.plainTextEdit.append("'"+url+"' is not a valid URL.")
            # self.plainTextEdit.append(str(self.ydl_opts))
            # self.plainTextEdit.setTextCursor(prev_cursor)
            # self.

    def onEditingFinished(self):

        url = self.lineEdit.text() # type : ignore[ruleName]

        if url != "":
            logger = MyLogger()
            logger.messageSignal.connect(self.plainTextEdit.append)
            self.ydl_opts.update({
                'logger': logger
            })
            self.thread = YoutubeDownload(url, self.ydl_opts)
            self.thread.start()

    def is_valid_url(self, url, logger):

        self.ydl_opts.update({
            'quiet' : True, 
            'progress_hooks': [self.my_hook],
            'logger' : logger
        })

        # ydl_opts = {
        #     'quiet' : True,
        #     'progress_hooks': [self.myhook],
        # }

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                result = ydl.extract_info(url, download=False)
                return True
            except (
                    yt_dlp.utils.DownloadError, 
                    yt_dlp.utils.ExtractorError, 
                    yt_dlp.utils.UnsupportedError, 
                    yt_dlp.utils.RegexNotFoundError):

                return False

    def my_hook(self, d):
        if d['status'] == 'finished':
            file_tuple = os.path.split(os.path.abspath(d['filename']))
            print("Done downloading {}".format(file_tuple[1]))
        if d['status'] == 'downloading':
            p = d['_percent_str']
            p = p.replace('%','')
            self.progrressBar.setValue(float(p))
            print(d['filename'], d['_percent_str'], d['_eta_str'])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

