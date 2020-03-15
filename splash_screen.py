from PyQt5 import QtCore, uic, QtWidgets

# get type from ui file
SplashUI, SplashBase = uic.loadUiType('splash.ui')


class SplashScreen(SplashBase, SplashUI):
    def __init__(self):
        super(SplashScreen, self).__init__()
        self.setupUi(self)

        flags = QtCore.Qt.WindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowFlags(flags)
        self.show()

    def finished(self, value):
        if value:
            QtWidgets.QApplication.processEvents()
            self.close()