import os
import sys
import qtmodern_package.styles as qtmodern_styles
import qtmodern_package.windows as qtmodern_windows
from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from scripts.database_handler import DatabaseHandler
from scripts.dialog_box import Dialog
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


def message(message, info, title=None):
    msg = QtWidgets.QMessageBox()
    msg.setText(message)
    msg.setInformativeText(info)
    size = msg.sizeHint()

    if title is not None:
        msg.setWindowTitle(title)
    else:
        msg.setWindowTitle('Error')

    flags = QtCore.Qt.WindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    msg.setWindowFlags(flags)
    msg.setStyleSheet(logbook_class.LogBook.get_theme())
    msg = qtmodern_windows.ModernWindow(msg)
    msg.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowModal)
    msg.setGeometry(0, 0, size.width(), size.height())

    logbook_class.center_widget(msg)

    msg.btnMinimize.setVisible(False)
    msg.btnMaximize.setVisible(False)

    msg.show()
    QtWidgets.QApplication.processEvents()


def pre_run_check(settings):
    db_name = settings['database_name']
    path = os.path.dirname(os.path.abspath(__file__))
    test = os.listdir(f"{path}\\data")
    year = str(datetime.now().year)

    if not any(db_name in s for s in test):
        dialog = Dialog()
        if dialog.show_dialog('It seems a database doesn\'t exist. \nWould you like to create a new one?'):
            DatabaseHandler.create_new_database_sqlite()

    db_year = db_name.replace('LogBook', '')
    if int(year) > int(db_year):
        dialog = Dialog()
        dialog.buttonBox.clear()
        ok_button = QtWidgets.QPushButton(dialog.tr("&Ok"))
        ok_button.setDefault(True)
        ok_button.setAccessibleDescription('neutralButton')
        ok_button.setMinimumSize(100, 25)
        ok_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        dialog.buttonBox.addButton(ok_button, QtWidgets.QDialogButtonBox.AcceptRole)

        if dialog.show_dialog('Happy New Year! Time to make a new database'):
            db_name = DatabaseHandler.create_new_database_sqlite()
            message(f'Successfully created database {db_name}', 'Success!')


if __name__ == '__main__':
    # create new application
    app = QApplication(sys.argv)
    pre_run_check(SettingsManager.get_settings())

    from scripts import logbook_class

    settings = logbook_class.LogBook.get_settings()
    path = os.path.dirname(os.path.abspath(__file__))
    theme_choice = settings['theme_choice']['name']  # get the name of the last saved chosen theme

    app.setWindowIcon(QtGui.QIcon("images/icons/appicon.ico"))
    if settings['theme'][theme_choice]['base_theme'] == 'dark':
        qtmodern_styles.dark(app)  # qtmodern

    if settings['theme'][theme_choice]['base_theme'] == 'light':
        qtmodern_styles.light(app)  # qtmodern

    # create new window of type LogBook and pass settings (calls __init__ constructor to do the rest)
    window = logbook_class.LogBook()
    window.setGeometry(QtCore.QRect(0, 0, 1280, 720))  # start size/location

    # center the window
    logbook_class.center_widget(window)

    mw = qtmodern_windows.ModernWindow(window)  # qtmodern

    # make the interface visible
    mw.show()

    timer = QtCore.QTimer()
    timer.timeout.connect(window.clock)  # call clock function every second
    timer.start(1000)

    sys.exit(app.exec_())
