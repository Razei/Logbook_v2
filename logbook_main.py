import os
import sys
import json
import time
from PyQt5.QtCore import QThread
from logbook import LogBook
from PyQt5 import QtGui, QtCore, QtWidgets
from splash_screen import SplashScreen
import qtmodern_package.styles as qtmodern_styles
import qtmodern_package.windows as qtmodern_windows

# Logbook v2 written in Python 3.8
# by Jarod Lavine and Shaniquo McKenzie

# get path of this python file
path = os.path.dirname(__file__)


def import_settings():
    with open('settings.json', 'r') as json_file:
        data = json.load(json_file)
        return data


if __name__ == '__main__':

    path = os.path.dirname(os.path.abspath(__file__))
    settings = import_settings()
    theme_choice = settings['theme_choice']['name']  # get the name of the last saved chosen theme

    # create new application
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("images/appicon.ico"))

    if settings['theme'][theme_choice]['base_theme'] == 'dark':
        qtmodern_styles.dark(app)  # qtmodern

    if settings['theme'][theme_choice]['base_theme'] == 'light':
        qtmodern_styles.light(app)  # qtmodern

    # create new window of type LogBook and pass settings (calls __init__ constructor to do the rest)
    window = LogBook(settings['theme'][theme_choice], settings['time_format'])
    window.setGeometry(QtCore.QRect(0, 0, 1280, 720))  # arbitrary size/location

    # center the window
    windowGeometry = window.frameGeometry()
    centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
    windowGeometry.moveCenter(centerPoint)
    window.move(windowGeometry.topLeft())

    mw = qtmodern_windows.ModernWindow(window)  # qtmodern

    # make the interface visible
    mw.show()

    timer = QtCore.QTimer()
    timer.timeout.connect(window.Clock)  # call clock function every second
    timer.start(1000)

    sys.exit(app.exec_())
