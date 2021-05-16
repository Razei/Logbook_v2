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


def center_widget(widget):
    # center the window
    window_geometry_dialog = widget.frameGeometry()
    screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
    center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
    window_geometry_dialog.moveCenter(center_point)
    widget.move(window_geometry_dialog.topLeft())


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
    msg.setStyleSheet(SettingsManager.get_theme_from_settings())
    msg = qtmodern_windows.ModernWindow(msg)
    msg.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowModal)
    msg.setGeometry(0, 0, size.width(), size.height())

    center_widget(msg)

    msg.btnMinimize.setVisible(False)
    msg.btnMaximize.setVisible(False)

    msg.show()
    QtWidgets.QApplication.processEvents()


def open_dialog(message):
    dialog = Dialog()
    dialog.buttonBox.clear()
    ok_button = QtWidgets.QPushButton(dialog.tr("&Ok"))
    ok_button.setDefault(True)
    ok_button.setAccessibleDescription('neutralButton')
    ok_button.setMinimumSize(100, 25)
    ok_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    dialog.buttonBox.addButton(ok_button, QtWidgets.QDialogButtonBox.AcceptRole)
    return dialog.show_dialog(message)


def pre_run_check(settings):
    db_name = settings['database_name']
    path = os.path.dirname(os.path.abspath(__file__))
    database_files = os.listdir(f"{path}\\data")
    year = datetime.now().year

    if not any(db_name in s for s in database_files):
        dialog = Dialog()
        if dialog.show_dialog('It seems the database file doesn\'t exist. \nWould you like Logbook to create it?'):
            new_db_name = f"LogBook{year}"

            try:
                open(f"{path}\\data\\{new_db_name}.db", "x")
            except FileExistsError:
                pass

            DatabaseHandler.set_database_name(new_db_name)
            DatabaseHandler.create_tables_from_script()
            open_dialog(f'Successfully created database {db_name}')
        else:
            DatabaseHandler.set_offline(True)

    db_year = db_name.replace('LogBook', '')
    if year > int(db_year):

        if open_dialog('Happy New Year! Time to make a new database.'):
            new_db_name = f"LogBook{year}"

            try:
                open(f"{path}\\data\\{new_db_name}.db", "x")
            except FileExistsError:
                pass

            DatabaseHandler.set_database_name(new_db_name)
            db_name = DatabaseHandler.create_tables_from_script()
            open_dialog(f'Successfully created database {db_name}.db')


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
