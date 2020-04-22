from PyQt5 import uic, QtCore, QtWidgets, QtGui
from scripts.local_pather import resource_path
from scripts.settings_manager import SettingsManager

DialogUI, DialogBase = uic.loadUiType(resource_path('views\\logbook_dialog.ui'))


def center_widget(widget):
    # center the window
    window_geometry_dialog = widget.frameGeometry()
    screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
    center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
    window_geometry_dialog.moveCenter(center_point)
    widget.move(window_geometry_dialog.topLeft())


class Dialog(QtWidgets.QDialog, DialogUI):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.theme = SettingsManager.get_theme_from_settings()
        flags = QtCore.Qt.WindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        yes_button = self.buttonBox.button(QtWidgets.QDialogButtonBox.Yes)
        no_button = self.buttonBox.button(QtWidgets.QDialogButtonBox.No)

        self.setWindowFlags(flags)

        yes_button.setAccessibleDescription('successButton')
        no_button.setAccessibleDescription('dangerButton')

        yes_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        no_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        yes_button.setMinimumSize(100, 25)
        no_button.setMinimumSize(100, 25)

    def show_dialog(self, text):
        state = True
        center_widget(self)

        self.label.setText(text)
        self.setStyleSheet(self.theme)
        if not self.exec_() == 1:
            state = False
        return state
