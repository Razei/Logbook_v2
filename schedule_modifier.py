import sys
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
import qtmodern_package.styles as qtmodern_styles
import qtmodern_package.windows as qtmodern_windows
from database_handler import DatabaseHandler
from settings_manager import SettingsManager
from ScheduleObj import ScheduleObj


def get_database_schedules():
    # local variables
    schedule_objects = []  # for holding a list of schedule objects

    # query stuff
    query = f"SELECT SCHEDULE_ID, ROOM, DAY, START_TIME, END_TIME FROM dbo.Schedule"
    cursor = DatabaseHandler.execute_query(query)

    # validate the cursor for empty results
    if not DatabaseHandler.validate_cursor(cursor):
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


def get_database_open_lab_schedules():
    # local variables
    schedule_objects = []  # for holding a list of schedule objects

    # query stuff
    query = f"SELECT SCHEDULE_ID, ROOM, DAY, START_TIME, END_TIME FROM dbo.OpenLabSchedule"
    cursor = DatabaseHandler.execute_query(query)

    # validate the cursor for empty results
    if not DatabaseHandler.validate_cursor(cursor):
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


class ScheduleModifier:
    schedules = get_database_schedules()
    open_lab_schedules = get_database_open_lab_schedules()

    @classmethod
    def get_schedules(cls):
        return cls.schedules

    @classmethod
    def get_open_lab_schedules(cls):
        return cls.open_lab_schedules

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

    @classmethod
    def make_checkboxes(cls, frame, comboBox, room_list):
        layout = frame.layout()
        column_count = layout.columnCount()
        row_count = layout.rowCount()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # validate the cursor for empty results
        if room_list is None:
            return

        for room in room_list:
            if room.strip() == 'Other':
                room_list.remove(room)

        cls.populate_combo_box(comboBox, room_list)

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

    @classmethod
    def update_checkboxes(cls, frame, comboBox, mode):
        import re
        cls.un_check_all(frame)

        if mode is None or mode == '':
            return

        if mode == 'Open':
            schedules = cls.open_lab_schedules
        else:
            schedules = cls.schedules

        layout = frame.layout()
        column_count = layout.columnCount()
        row_count = layout.rowCount()
        room = comboBox.currentText().strip()
        focused_list = []  # holding schedules focused on a specific room
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
                        temp = re.compile("([a-zA-Z]+)([0-9]+)")  # separate the string and the digit
                        res = temp.match(w_name).groups()  # execute

                        # convert the digit to a formatted time string
                        t_compare = datetime.strptime(res[1] + ':30', '%H:%M').strftime('%H:%M')  # I couldn't find a more elegant way to do this so....

                        time_search = entry.get_start_time()[:-3]  # remove the last 3 characters from the string (:00)
                        # if matched or if state (state will make sure all checkboxes after start time are checked until it reaches end time)
                        if ((entry.get_day() == res[0]) and (time_search == t_compare)) or state:
                            widget.setChecked(True)
                            state = True

                        time_search = entry.get_end_time()[:-3]  # remove the last 3 characters from the string (:00)
                        if (entry.get_day().strip() == res[0]) and (time_search == t_compare):
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

                widget_time = widget.objectName().replace(f'checkBox{days[i - 1]}', '') + ':30'

                # if it's checked and it's not 22:30
                if (type(widget) == QtWidgets.QCheckBox and widget.isChecked()) and not (widget_time == '22:30'):  # 22:30 cannot be a start time
                    if not state:  # self.state helps to keep track of whether there's a start time already
                        start_time = widget.objectName().replace(f'checkBox{days[i-1]}', '') + ':30:00'
                        state = True  # indicate there is now a start time waiting for an end time to complete the object below
                        continue  # skip the rest of the code

                if (type(widget) == QtWidgets.QCheckBox and not widget.isChecked() and state) or (widget_time == '22:30' and state):
                    end_time = widget.objectName().replace(f'checkBox{days[i-1]}', '') + ':30:00'
                    print(start_time, end_time, days[i - 1], room)
                    state = False
                    schedules.append(ScheduleObj(room, days[i - 1], start_time, end_time))

        return schedules

    @classmethod
    def save_schedules(cls, frame, combo_box, mode):
        schedules = cls.calculate_times(frame, combo_box)

        if schedules is not None:
            if mode == 'Open':
                table_name = 'dbo.OpenLabSchedule'
            else:
                table_name = 'dbo.Schedule'

            query = f'SELECT ROOM,DAY,START_TIME,END_TIME from {table_name}'
            cursor = DatabaseHandler.execute_query(query)

            # validate the cursor for empty results
            if DatabaseHandler.validate_cursor(cursor):
                data = cursor.fetchall()
                cursor.close()

                current_room = combo_box.currentText()

                # delete all existing entries for this room
                for d in data:
                    if d.ROOM.strip() == current_room:
                        query = f'DELETE FROM {table_name} WHERE ROOM = ?'

                        cursor = DatabaseHandler.execute_query(query, current_room)

                        if DatabaseHandler.validate_cursor(cursor):
                            cursor.commit()
                            cursor.close()

            # add new data
            if schedules is not None and len(schedules) != 0:
                for i in range(len(schedules)):
                    query = f'''
                    INSERT INTO {table_name}
                        (ROOM,DAY,START_TIME,END_TIME) 
                    VALUES 
                        (?, ?, ?, ?)'''  # query string
                    list_objects = [schedules[i].room, schedules[i].day, schedules[i].start_time, schedules[i].end_time]  # variables to substitute '?' in the query string
                    cursor = DatabaseHandler.execute_query(query, list_objects)  # passing both to the database handler to do the rest
                    cursor.commit()
                    cursor.close()

        if mode == 'Open':
            cls.open_lab_schedules = get_database_open_lab_schedules()
        else:
            cls.schedules = get_database_schedules()


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
