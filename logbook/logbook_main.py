import os
import sys
import qtmodern_package.styles as qtmodern_styles
import qtmodern_package.windows as qtmodern_windows
from scripts.logbook_class import LogBook
from PyQt5 import QtGui, QtCore, QtWidgets
from scripts.settings_manager import SettingsManager

# Logbook v2 written in Python 3.8
# by Jarod Lavine and Shaniquo McKenzie

# learning how to program using python for work term
# with knowledge from COMP-229, COMP-214, COMP-125 and COMP-228
# with help from various stackoverflow answers :)

# using libraries from:
# https://github.com/gmarull/qtmodern Version 0.2.0
# https://www.qt.io/qt-for-python Version 5.14.1
# https://pandas.pydata.org/ Version 1.0.1
# https://pypi.org/project/openpyxl/ Version 3.0.3
# https://pypi.org/project/SQLAlchemy/ Version 1.3.13
# https://pypi.org/project/xlrd/ Version 1.2.0


if __name__ == '__main__':

    path = os.path.dirname(os.path.abspath(__file__))
    settings = SettingsManager.import_settings()
    theme_choice = settings['theme_choice']['name']  # get the name of the last saved chosen theme

    # create new application
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("images/icons/appicon.ico"))
    if settings['theme'][theme_choice]['base_theme'] == 'dark':
        qtmodern_styles.dark(app)  # qtmodern

    if settings['theme'][theme_choice]['base_theme'] == 'light':
        qtmodern_styles.light(app)  # qtmodern

    # create new window of type LogBook and pass settings (calls __init__ constructor to do the rest)
    window = LogBook(settings['theme'][theme_choice], settings['time_format'])
    window.setGeometry(QtCore.QRect(0, 0, 1280, 720))  # start size/location

    # center the window
    windowGeometry = window.frameGeometry()
    screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
    centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
    windowGeometry.moveCenter(centerPoint)
    window.move(windowGeometry.topLeft())

    mw = qtmodern_windows.ModernWindow(window)  # qtmodern

    # make the interface visible
    mw.show()

    timer = QtCore.QTimer()
    timer.timeout.connect(window.clock)  # call clock function every second
    timer.start(1000)

    sys.exit(app.exec_())
