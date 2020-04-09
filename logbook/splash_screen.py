from PyQt5 import QtCore, uic

# get type from ui file
SplashUI, SplashBase = uic.loadUiType('views\\splash.ui')


class SplashScreen(SplashBase, SplashUI):
    def __init__(self, theme):
        super(SplashScreen, self).__init__()
        self.setupUi(self)

        # fetches the qss stylesheet path
        theme_path = theme['theme_path']

        # reads the qss stylesheet and applies it to the application
        self.theme = str(open(theme_path, "r").read())
        self.setStyleSheet(self.theme)

        flags = QtCore.Qt.WindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(flags)

    def finished(self, value):
        if value:
            self.close()
