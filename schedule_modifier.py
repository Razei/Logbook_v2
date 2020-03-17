import json
import sys
import pyodbc
from PyQt5 import QtCore, QtGui, uic, QtWidgets
import qtmodern_package.styles as qtmodern_styles
import qtmodern_package.windows as qtmodern_windows
from database_handler import DatabaseHandler
from ScheduleObj import ScheduleObj

# get type from ui file
ScheduleUI, ScheduleBase = uic.loadUiType('schedule_modifier.ui')


class ScheduleModifier(ScheduleUI, ScheduleBase):
    def __init__(self, theme):
        super(ScheduleModifier, self).__init__()
        self.setupUi(self)

        # fetches the qss stylesheet path
        theme_path = theme['theme_path']

        # reads the qss stylesheet and applies it to the application
        self.theme = str(open(theme_path, "r").read())
        self.setStyleSheet(self.theme)

        # self.database_handler = DatabaseHandler('LAPTOP-L714M249\\SQLEXPRESS')
        self.database_handler = DatabaseHandler('DESKTOP-B2TFENN' + '\\' + 'SQLEXPRESS')

        self.pushButtonCheckAll.clicked.connect(self.check_all)
        self.pushButtonUnCheckAll.clicked.connect(self.un_check_all)
        self.pushButtonSave.clicked.connect(self.save_schedules)
        self.state = False

    @staticmethod
    def populate_combo_box(combobox, items):
        combobox.clear()
        combobox.setView(QtWidgets.QListView())
        combobox.addItems(items)
        combobox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)

    def make_checkboxes(self):
        layout = self.frameSchedule.layout()
        column_count = layout.columnCount()
        row_count = layout.rowCount()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        rooms_query = "SELECT ROOM FROM ReportLog.dbo.Rooms WHERE NOT ROOM = 'Other'"
        room_list = []

        cursor = self.database_handler.execute_query(rooms_query)
        # validate the cursor for empty results

        if not self.database_handler.validate_cursor(cursor):
            return

        rooms = cursor.fetchall()

        for room in rooms:
            room_list.append(room[0])

        self.populate_combo_box(self.comboBoxRooms, room_list)

        cursor.close()

        for i in range(1, column_count):  # loop through all columns
            start_time = 8

            for j in range(1, row_count):
                check_box = QtWidgets.QCheckBox()
                check_box.setObjectName(f'checkBox{days[i-1]}{start_time}')
                check_box.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                check_box.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

                # had to do this to center the checkboxes
                frame = QtWidgets.QFrame()
                c_layout = QtWidgets.QHBoxLayout()
                c_layout.addWidget(check_box)
                c_layout.setAlignment(QtCore.Qt.AlignCenter)
                c_layout.setContentsMargins(0, 0, 0, 0)

                frame.setLayout(c_layout)
                print(check_box.objectName())
                layout.addWidget(frame, j, i)
                start_time += 1
                QtWidgets.QApplication.processEvents()

    def check_all(self):
        for widget in self.frameSchedule.findChildren(QtWidgets.QCheckBox):
            widget.setChecked(True)

    def un_check_all(self):
        for widget in self.frameSchedule.findChildren(QtWidgets.QCheckBox):
            widget.setChecked(False)

    def calculate_times(self):
        layout = self.frameSchedule.layout()
        column_count = layout.columnCount()
        row_count = layout.rowCount()
        room = self.comboBoxRooms.currentText()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        schedules = []
        start_time = ''
        end_time = ''

        for i in range(1, column_count):  # loop through all columns
            for j in range(1, row_count):
                item = layout.itemAtPosition(j, i)
                widget = item.widget().children()[1]

                if type(widget) == QtWidgets.QCheckBox and widget.isChecked():
                    if not self.state:
                        start_time = widget.objectName().replace(f'checkBox{days[i-1]}', '') + ':30'
                        self.state = True
                        continue

                if type(widget) == QtWidgets.QCheckBox and not widget.isChecked() and self.state:
                    end_time = widget.objectName().replace(f'checkBox{days[i-1]}', '') + ':30'
                    print(start_time, end_time, days[i - 1], room)
                    self.state = False
                    schedules.append(ScheduleObj(room, days[i - 1], start_time, end_time))

        return schedules

    def save_schedules(self):
        schedules = self.calculate_times()
        if schedules is not None:
            query = 'SELECT ROOM,DAY,START_TIME,END_TIME from dbo.Schedule'
            cursor = self.database_handler.execute_query(query)

            data = cursor.fetchall()
            cursor.close()
            for d in data:
                for i in range(len(schedules)):
                    if d.ROOM == schedules[i].room:
                        query = f'DELETE FROM dbo.Schedule WHERE ROOM = ?'

                        cursor = self.database_handler.execute_query(query, schedules[i].room)

                        if self.database_handler.validate_cursor(cursor):
                            cursor.commit()
                            cursor.close()

            for i in range(len(schedules)):
                query = f'''
                INSERT INTO dbo.Schedule
                    (ROOM,DAY,START_TIME,END_TIME) 
                VALUES 
                    (?, ?, ?, ?)'''
                list_objects = [schedules[i].room, schedules[i].day, schedules[i].start_time, schedules[i].end_time]
                cursor = self.database_handler.execute_query(query, list_objects)
                cursor.commit()
                cursor.close()

    # clears all the QT Creator styles in favour of the QSS stylesheet
    def clearStyleSheets(self):
        widget_child = self.centralwidget.findChildren(QtWidgets.QWidget)

        for widget in widget_child:
            widget.setStyleSheet('')


def import_settings():
    with open('settings.json', 'r') as json_file:
        data = json.load(json_file)
        return data


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    settings = import_settings()
    theme_choice = settings['theme_choice']['name']  # get the name of the last saved chosen theme

    if settings['theme'][theme_choice]['base_theme'] == 'dark':
        qtmodern_styles.dark(app)  # qtmodern

    if settings['theme'][theme_choice]['base_theme'] == 'light':
        qtmodern_styles.light(app)  # qtmodern

    s = ScheduleModifier(settings['theme'][theme_choice])
    s.make_checkboxes()

    mw = qtmodern_windows.ModernWindow(s)  # qtmodern
    # make the interface visible
    mw.show()
    sys.exit(app.exec_())
