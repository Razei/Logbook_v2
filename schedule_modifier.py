import sys
from PyQt5 import QtCore, QtGui, uic, QtWidgets
import qtmodern_package.styles as qtmodern_styles
import qtmodern_package.windows as qtmodern_windows
from database_handler import DatabaseHandler
from settings_manager import SettingsManager
from ScheduleObj import ScheduleObj


class ScheduleModifier:
    def __init__(self, server_string):
        self.database_handler = DatabaseHandler(server_string)
        self.schedules = self.get_schedules()
        self.open_lab_schedules = self.get_schedules()

    @staticmethod
    def populate_combo_box(combobox, items):
        combobox.clear()
        combobox.setView(QtWidgets.QListView())
        combobox.addItems(items)
        combobox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)

    @staticmethod
    def make_labels(frame):
        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        first_row = ['Time', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']
        start_time = 8
        for i in range(len(first_row)):
            headers = QtWidgets.QLabel(f'{first_row[i]}')
            headers.setAccessibleDescription('titleLabel')

            if i == 0:  # align the first label left
                headers.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            else:
                headers.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

            layout.addWidget(headers, 0, i)

        for i in range(22 - 7):
            time = QtWidgets.QLabel(f'{start_time}:30')
            time.setAccessibleDescription('normalLabel')
            layout.addWidget(time, i+1, 0)
            start_time += 1

        frame.setLayout(layout)

    def make_checkboxes(self, frame, comboBox):
        layout = frame.layout()
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

        self.populate_combo_box(comboBox, room_list)
        cursor.close()

        for i in range(1, column_count):  # loop starting at column 1
            start_time = 8

            for j in range(1, row_count):  # loop starting at row 1
                check_box = QtWidgets.QCheckBox()
                check_box.setObjectName(f'checkBox{days[i-1]}{start_time}')
                check_box.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                check_box.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

                # had to do this to center the checkboxes
                frame2 = QtWidgets.QFrame()
                frame2.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                c_layout = QtWidgets.QHBoxLayout()
                c_layout.addWidget(check_box)
                c_layout.setAlignment(QtCore.Qt.AlignCenter)
                c_layout.setContentsMargins(0, 0, 0, 0)

                frame2.setLayout(c_layout)
                layout.addWidget(frame2, j, i)
                start_time += 1

    def get_schedules(self):
        # local variables
        schedule_objects = []  # for holding a list of schedule objects

        # query stuff
        query = f"SELECT SCHEDULE_ID, ROOM, DAY, START_TIME, END_TIME FROM dbo.Schedule"
        cursor = self.database_handler.execute_query(query)

        # validate the cursor for empty results
        if not self.database_handler.validate_cursor(cursor):
            return

        schedule_data = cursor.fetchall()

        # loop through the cursor and add data to the scheduleObj class
        for sch_time in schedule_data:
            # the schedule object holds the room number, day, start time, and end time
            schedule_objects.append(ScheduleObj(sch_time.ROOM.strip(), sch_time.DAY.strip(),
                                                sch_time.START_TIME.isoformat(timespec='seconds'),
                                                sch_time.END_TIME.isoformat(timespec='seconds'), sch_time.SCHEDULE_ID))
        cursor.close()
        return schedule_objects

    def get_open_lab_schedules(self):
        # local variables
        schedule_objects = []  # for holding a list of schedule objects

        # query stuff
        query = f"SELECT SCHEDULE_ID, ROOM, DAY, START_TIME, END_TIME FROM dbo.OpenLabSchedule"
        cursor = self.database_handler.execute_query(query)

        # validate the cursor for empty results
        if not self.database_handler.validate_cursor(cursor):
            return

        schedule_data = cursor.fetchall()

        # loop through the cursor and add data to the scheduleObj class
        for sch_time in schedule_data:
            # the schedule object holds the room number, day, start time, and end time
            schedule_objects.append(ScheduleObj(sch_time.ROOM.strip(), sch_time.DAY.strip(),
                                                sch_time.START_TIME.isoformat(timespec='seconds'),
                                                sch_time.END_TIME.isoformat(timespec='seconds'), sch_time.SCHEDULE_ID))
        cursor.close()
        return schedule_objects

    def update_checkboxes(self, frame, comboBox):
        import re
        self.un_check_all(frame)

        schedules = self.schedules
        layout = frame.layout()
        column_count = layout.columnCount()
        row_count = layout.rowCount()
        room = comboBox.currentText().strip()
        focused_list = []
        state = False

        # validate the list for empty results
        if schedules is not None and len(schedules) != 0:
            for entry in schedules:
                if entry.get_room().strip() == room:
                    focused_list.append(entry)

        # validate the list for empty results
        if focused_list is None or len(focused_list) == 0:
            return

        # loop vertically (rows of a column)
        for i in range(1, column_count):
            for j in range(1, row_count):  # loop through all rows for each column
                item = layout.itemAtPosition(j, i)  # itemAtPosition(row, column)
                widget = item.widget().children()[1]  # the checkbox is a child of a layout (to center it)

                if type(widget) == QtWidgets.QCheckBox:
                    for entry in focused_list:
                        w_name = widget.objectName().replace('checkBox', '')
                        temp = re.compile("([a-zA-Z]+)([0-9]+)")
                        res = temp.match(w_name).groups()

                        time_search = entry.get_start_time()[:-3]  # remove the last 3 characters from the string (:00)
                        # if matched or if state (state will make sure all checkboxes after start time are checked until it reaches end time)
                        if ((entry.get_day().strip() == res[0]) and (time_search == res[1] + ':30')) or state:
                            widget.setChecked(True)
                            state = True

                        time_search = entry.get_end_time()[:-3]  # remove the last 3 characters from the string (:00)
                        if (entry.get_day().strip() == res[0]) and (time_search == res[1] + ':30'):
                            widget.setChecked(False)
                            state = False

    @staticmethod
    def check_all(frame):
        for widget in frame.findChildren(QtWidgets.QCheckBox):
            widget.setChecked(True)

    @staticmethod
    def un_check_all(frame):
        for widget in frame.findChildren(QtWidgets.QCheckBox):
            widget.setChecked(False)

    # function for making schedule objects based on which checkboxes are checked
    @staticmethod
    def calculate_times(frame, combo_box):
        layout = frame.layout()
        column_count = layout.columnCount()
        row_count = layout.rowCount()
        room = combo_box.currentText()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        schedules = []
        start_time = ''
        end_time = ''
        state = False

        # loop vertically (rows of a column)
        for i in range(1, column_count):
            for j in range(1, row_count):  # loop through all rows for each column
                item = layout.itemAtPosition(j, i)  # itemAtPosition(row, column)
                widget = item.widget().children()[1]  # the checkbox is a child of a layout (to center it)

                if type(widget) == QtWidgets.QCheckBox and widget.isChecked():  # if it's checked
                    if not state:  # self.state helps to keep track of whether there's a start time already
                        start_time = widget.objectName().replace(f'checkBox{days[i-1]}', '') + ':30'
                        state = True  # indicate there is now a start time waiting for an end time to complete the object
                        continue  # skip the rest of the code

                if type(widget) == QtWidgets.QCheckBox and not widget.isChecked() and state:
                    end_time = widget.objectName().replace(f'checkBox{days[i-1]}', '') + ':30'
                    print(start_time, end_time, days[i - 1], room)
                    state = False
                    schedules.append(ScheduleObj(room, days[i - 1], start_time, end_time))

        return schedules

    def save_schedules(self, frame, combo_box):
        schedules = self.calculate_times(frame, combo_box)
        if schedules is not None:
            query = 'SELECT ROOM,DAY,START_TIME,END_TIME from dbo.Schedule'
            cursor = self.database_handler.execute_query(query)

            data = cursor.fetchall()
            cursor.close()

            # delete all existing entries for this room
            for d in data:
                for i in range(len(schedules)):
                    if d.ROOM == schedules[i].room:
                        query = f'DELETE FROM dbo.Schedule WHERE ROOM = ?'

                        cursor = self.database_handler.execute_query(query, schedules[i].room)

                        if self.database_handler.validate_cursor(cursor):
                            cursor.commit()
                            cursor.close()

            # add new data
            for i in range(len(schedules)):
                query = f'''
                INSERT INTO dbo.Schedule
                    (ROOM,DAY,START_TIME,END_TIME) 
                VALUES 
                    (?, ?, ?, ?)'''  # query string
                list_objects = [schedules[i].room, schedules[i].day, schedules[i].start_time, schedules[i].end_time]  # variables to substitute '?' in the query string
                cursor = self.database_handler.execute_query(query, list_objects)  # passing both to the database handler to do the rest
                cursor.commit()
                cursor.close()

        self.schedules = self.get_schedules()

    # clears all the QT Creator styles in favour of the QSS stylesheet
    def clear_style_sheets(self):
        widget_child = self.centralwidget.findChildren(QtWidgets.QWidget)

        for widget in widget_child:
            widget.setStyleSheet('')


# for testing
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    settings = SettingsManager.import_settings()
    theme_choice = settings['theme_choice']['name']  # get the name of the last saved chosen theme

    if settings['theme'][theme_choice]['base_theme'] == 'dark':
        qtmodern_styles.dark(app)  # qtmodern

    if settings['theme'][theme_choice]['base_theme'] == 'light':
        qtmodern_styles.light(app)  # qtmodern

    s = ScheduleModifier(settings['theme'][theme_choice])

    mw = qtmodern_windows.ModernWindow(s)  # qtmodern
    # make the interface visible
    mw.show()
    sys.exit(app.exec_())
