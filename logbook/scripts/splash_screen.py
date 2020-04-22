import os
from scripts.local_pather import resource_path
from scripts import logbook_class
from PyQt5 import QtCore, uic

# get type from ui file
SplashUI, SplashBase = uic.loadUiType(resource_path(os.path.join('views', 'splash.ui')))


class SplashScreen(SplashBase, SplashUI):
    def __init__(self):
        super(SplashScreen, self).__init__()
        self.setupUi(self)

        # reads the qss stylesheet and applies it to the application
        self.theme = logbook_class.LogBook.get_theme()
        self.setStyleSheet(self.theme)

        flags = QtCore.Qt.WindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(flags)

    def finished(self, value):
        if value:
            self.close()
