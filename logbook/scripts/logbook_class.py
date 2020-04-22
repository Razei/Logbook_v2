import os
import time
import datetime
from pathlib import Path
from openpyxl import Workbook
from pandas import read_sql_query, ExcelWriter
from urllib import parse
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5 import QtCore, QtWidgets, uic, QtGui
from PyQt5.QtCore import Qt
from scripts.local_pather import resource_path
from scripts.lab_checker import LabChecker
from scripts.splash_screen import SplashScreen
from scripts.settings_manager import SettingsManager
from scripts.database_handler import DatabaseHandler
from scripts.schedule_modifier import ScheduleModifier
from scripts.dialog_box import Dialog

os.chdir(Path(__file__).parent.parent)


def center_widget(widget):
    # center the window
    window_geometry_dialog = widget.frameGeometry()
    screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
    center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
    window_geometry_dialog.moveCenter(center_point)
    widget.move(window_geometry_dialog.topLeft())


# get type from ui file
MainWindowUI, MainWindowBase = uic.loadUiType(resource_path('views\\logbook_design.ui'))
DialogUI, DialogBase = uic.loadUiType(resource_path('views\\logbook_dialog.ui'))


class SplashScreenThread(QThread):
    """
    Runs a counter thread.
    """
    countChanged = pyqtSignal(int)
    finished = pyqtSignal(bool)
    count = 0
    last_count = 0
    max_progress = 100

    def run(self):
        while self.count < self.max_progress:
            QtWidgets.QApplication.processEvents()  # force Qt to refresh the interface
            for i in range(self.last_count, self.count):
                self.count += 1
                self.countChanged.emit(self.count)  # emit the countChanged signal and pass the count variable to whatever catches the event
            self.last_count = self.count

        self.countChanged.emit(100)  # emit the countChanged signal and pass the count variable to whatever catches the event
        QtWidgets.QApplication.processEvents()  # force Qt to refresh the interface
        time.sleep(0.5)
        self.finished.emit(True)   # emit the finished signal to close the splash screen


class Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)


class LogBook(MainWindowBase, MainWindowUI):
    # class variables
    settings = SettingsManager.get_settings()
    theme = SettingsManager.get_theme_from_settings()

    def __init__(self):
        super(LogBook, self).__init__()
        self.setupUi(self)
        # local variables
        self.lastPage = ''
        self.stored_id = 0

        self.theme = self.__class__.theme
        self.chosen_theme = self.__class__.settings['theme_choice']['name']
        self.time_format = self.__class__.settings['time_format']
        self.theme_choice = self.__class__.settings['theme'][self.chosen_theme]

        self.staticDate = datetime.datetime.now()
        self.default_returned_date = datetime.date(2020, 1, 1)  # default date to set returned to

        # initialise variables that will hold object instances later
        self.lab_checker = None
        self.schedules = None
        self.open_lab_schedules = None
        self.all_rooms = None
        self.all_labs_page_obj = None
        self.floating = None
        self.floating_state = False

        # self.server_string = 'DESKTOP-B2TFENN\\SQLEXPRESS'  # change this to your server name
        '''Shaniquo's Laptop, DO NOT DELETE'''
        # self.server_string = 'DESKTOP-U3EO5IK\\SQLEXPRESS'
        # self.server_string ='DESKTOP-SIF9RD3\\SQLEXPRESS'

        self.server_string = 'LAPTOP-L714M249\\SQLEXPRESS'
        DatabaseHandler.set_server_string(self.server_string)

        self.server_string = DatabaseHandler.get_server_string()

        self.splash = SplashScreen()
        self.splash.show()
        self.splash_screen_thread = SplashScreenThread()
        self.splash_screen_thread.countChanged.connect(self.on_count_changed)  # connect this function to the custom countChanged signal from the SplashScreenThread
        self.splash_screen_thread.finished.connect(self.finished)  # connect this function to the custom finished signal from the SplashScreenThread
        self.splash_screen_thread.start()  # start the thread so it will run simultaneously with the logbook
        QtWidgets.QApplication.processEvents()  # force Qt to refresh the interface immediately

        # using the setupUi function of the MainWindow
        self.get_all_data()
        self.add_all_events()
        self.apply_settings(self.theme_choice['theme_name'], self.time_format)

        # clears all the QT Creator styles in favour of the QSS stylesheet
        self.clear_style_sheets()
        self.setStyleSheet(self.theme)

        self.set_progress_bar(100)  # set the progress bar to 100 to indicate loading is finished

        # set initial activated button
        self.pushButtonDashboard.clicked.emit()
        self.labelSettingsWarning.setVisible(False)

        # show initial frame linked to dashboard button
        self.show_linked_frame(self.pushButtonDashboard)

    ############# CLASS METHODS #############
    @classmethod
    def get_theme(cls):
        return cls.theme

    @classmethod
    def get_settings(cls):
        return cls.settings

    ############# CORE FUNCTIONS #############
    def clock(self):  # this function is called every second during runtime
        t = time.localtime()  # local system time
        d = datetime.date.today()  # local system date
        t_format_24hr = '%H:%M:%S'
        t_format_12hr = '%I:%M:%S %p'
        date_format = '%A %B %d, %Y'

        # convert time to string format
        time_convert = time.strftime(t_format_24hr, t)

        if self.comboBoxSettingsTimeFormat.currentText() == '12 HR':
            time_convert = time.strftime(t_format_12hr, t)

        # current time
        self.labelCurrentTime.setText(time_convert)

        # assign labels with current time and date
        self.labelCurrentDate.setText(d.strftime(date_format))
        self.labelCurrentDate2.setText(d.strftime(date_format))
        self.labelCurrentDate3.setText(d.strftime(date_format))

        # call the handlers for the countdowns
        self.countdown_handler()
        self.duration_handler()

    # import all necessary data
    def get_all_data(self):
        self.set_progress_bar(20)
        months = ['All', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        themes = ['Classic Light', 'Centennial Dark']
        formats = ['24 HR', '12 HR']
        rooms_query = f'SELECT ROOM FROM dbo.Rooms'
        room_list = []

        self.populate_combo_box(self.comboBoxReportsMonth, months)
        self.populate_combo_box(self.comboBoxLostAndFoundMonth, months)
        self.populate_combo_box(self.comboBoxSettingsTheme, themes)
        self.populate_combo_box(self.comboBoxSettingsTimeFormat, formats)

        self.lab_checker = LabChecker()
        self.schedules = self.lab_checker.get_today_schedule()
        self.open_lab_schedules = self.lab_checker.get_today_open_lab_schedule()

        self.set_progress_bar(43)

        cursor = DatabaseHandler.execute_query(rooms_query)

        # validate the cursor for empty results
        if not DatabaseHandler.validate_cursor(cursor):
            return

        rooms = cursor.fetchall()

        for room in rooms:
            room_list.append(room[0].strip())

        self.all_rooms = room_list

        cursor.close()

        self.set_progress_bar(70)

        ScheduleModifier.make_labels(self.frameScheduleMod)
        ScheduleModifier.make_checkboxes(self.frameScheduleMod, self.comboBoxScheduleRooms, room_list)
        ScheduleModifier.update_checkboxes(self.frameScheduleMod, self.comboBoxScheduleRooms, self.pushButtonScheduleSave.accessibleName())
        self.populate_combo_box(self.comboBoxRoom, room_list)
        self.populate_combo_box(self.comboBoxNewLostAndFoundRoom, room_list)

        self.set_progress_bar(90)

        # hide the row numbers in the tables
        self.tableWidgetReports.verticalHeader().setVisible(False)
        self.tableWidgetProblems.verticalHeader().setVisible(False)
        self.tableWidgetLostAndFound.verticalHeader().setVisible(False)

        self.get_all_labs()
        self.refresh_tables()

    # add all events
    def add_all_events(self):
        self.pushButtonRefreshDashboard.clicked.connect(self.refresh_dashboard)

        # click event for the big number on the dashboard
        self.labelNumberProblems.mousePressEvent = self.problems_link

        # reports
        self.pushButtonNew.clicked.connect(self.new_log)
        self.pushButtonFormCancel.clicked.connect(self.change_to_last_page)
        self.pushButtonExportData.clicked.connect(self.export_data_sheet)
        self.pushButtonEditReports.clicked.connect(lambda: self.edit_log(self.tableWidgetReports))
        self.comboBoxReportsMonth.currentIndexChanged.connect(lambda: self.sort_by_month('Reports'))
        self.comboBoxLostAndFoundMonth.currentIndexChanged.connect(lambda: self.sort_by_month('LostAndFound'))

        # problems
        # self.pushButtonRefreshProblems.clicked.connect(self.refreshTables)
        self.pushButtonDelete.clicked.connect(lambda: self.delete_selection(self.tableWidgetReports, 'Reports'))
        self.pushButtonProblemsFixed.clicked.connect(lambda: self.edit_log(self.tableWidgetProblems))
        self.pushButtonReportsView.clicked.connect(lambda: self.view_selection(self.tableWidgetReports))
        self.pushButtonProblemsView.clicked.connect(lambda: self.view_selection(self.tableWidgetProblems))
        self.pushButtonViewDataBack.clicked.connect(self.change_to_last_page)

        # new log
        self.pushButtonFormSave.clicked.connect(self.save_new_log)
        self.pushButtonFormClear.clicked.connect(self.clear_form)
        self.textBoxNewLogNote.textChanged.connect(lambda: self.max_txt_input(self.textBoxNewLogNote))
        self.textBoxNewLogResolution.textChanged.connect(lambda: self.max_txt_input(self.textBoxNewLogResolution))
        self.textBoxNewLostAndFoundNote.textChanged.connect(lambda: self.max_txt_input(self.textBoxNewLostAndFoundNote))

        # lost and found
        self.pushButtonViewLAF.clicked.connect(lambda: self.view_selection(self.tableWidgetLostAndFound))
        self.pushButtonNewLAF.clicked.connect(self.new_lost_and_found)
        self.pushButtonEditLAF.clicked.connect(self.edit_laf_form)
        self.pushButtonFormClearLAF.clicked.connect(self.clear_lost_and_found_form)
        self.pushButtonFormCancelLAF.clicked.connect(lambda: self.change_page(self.stackedWidget, self.pageLostAndFound))
        self.pushButtonFormSaveLAF.clicked.connect(self.save_lost_and_found_form)

        # search lost and found & Reports
        self.pushButtonSearchLAF.clicked.connect(lambda: self.search_buttons(self.tableWidgetLostAndFound, self.txtBoxSearchLAF))
        self.pushButtonSearchReports.clicked.connect(lambda: self.search_buttons(self.tableWidgetReports, self.txtBoxSearchReports))

        # all labs
        self.pushButtonFloatingAllLabs.clicked.connect(self.move_to_floating_window)

        # schedule modifier
        self.comboBoxScheduleRooms.currentIndexChanged.connect(self.schedule_modifier_index_changed)
        self.pushButtonScheduleBack.clicked.connect(lambda: self.change_page(self.stackedWidgetSchedule, self.pageOptions))
        self.pushButtonScheduleMod.clicked.connect(self.show_schedule_modifier)
        self.pushButtonOpenLabScheduleMod.clicked.connect(self.show_open_lab_schedule_modifier)
        self.pushButtonScheduleSave.clicked.connect(lambda: self.save_schedules(self.frameScheduleMod, self.comboBoxScheduleRooms))
        self.pushButtonScheduleCheckAll.clicked.connect(lambda: ScheduleModifier.check_all(self.frameScheduleMod))
        self.pushButtonScheduleUnCheckAll.clicked.connect(lambda: ScheduleModifier.un_check_all(self.frameScheduleMod))

        # self.pushButtonRefreshLAF.clicked.connect(self.refreshTables)
        self.pushButtonDeleteLAF.clicked.connect(lambda: self.delete_selection(self.tableWidgetLostAndFound, 'LostAndFound'))
        self.checkBoxNewLostAndFoundReturned.clicked.connect(self.returned_checkbox_changed)

        # Settings
        self.pushButtonTimetables.clicked.connect(lambda: self.open_folder('images\\timetables'))
        self.pushButtonSaveSettings.clicked.connect(self.save_settings)
        self.pushButtonBackupDatabase.clicked.connect(lambda: self.try_backup())

        # User guide
        self.pushButtonUserGuideDoc.clicked.connect(lambda: self.open_user_guide('logbook_user_guide.pdf'))

        # look through the children of the children until we find a QPushButton
        for widget in self.frameMenu.children():
            if isinstance(widget, QtWidgets.QPushButton):
                widget.clicked.connect(self.button_pressed)  # connect click event function

            for frame in widget.children():
                if isinstance(frame, QtWidgets.QPushButton):
                    frame.clicked.connect(self.button_pressed)  # connect click event function

                for member in frame.children():
                    if isinstance(member, QtWidgets.QPushButton):
                        member.clicked.connect(self.button_pressed)  # connect click event function

    ############# SPLASH SCREEN #############
    def set_progress_bar(self, value):
        self.splash_screen_thread.count = value
        QtWidgets.QApplication.processEvents()  # force Qt to refresh the interface

    # this function receives the data from the countChanged signal in the SplashScreenThread
    def on_count_changed(self, value):
        time.sleep(0.05)
        self.splash.progressBar.setValue(value)
        QtWidgets.QApplication.processEvents()  # force Qt to refresh the interface

    # this function receives the data from the finished signal
    def finished(self, value):
        time.sleep(0.1)
        self.splash.finished(value)

    ############# ONE SHOT FUNCTIONS #############
    # clears all the QT Creator styles in favour of the QSS stylesheet
    def clear_style_sheets(self):
        widget_child = self.centralwidget.findChildren(QtWidgets.QWidget)

        for widget in widget_child:
            widget.setStyleSheet('')

    ############# STATIC METHODS #############
    # limit the amount of characters allowed in a QTextEdit
    @staticmethod
    def open_folder(relative_path):
        path = resource_path(relative_path)
        os.startfile(path)

    @staticmethod
    def open_user_guide(relative_path):
        path = resource_path(relative_path)
        os.startfile(path)

    @staticmethod
    def max_txt_input(txt_edit):
        text_content = txt_edit.toPlainText()
        length = len(text_content)

        max_length = 999

        if length > max_length:
            position = txt_edit.textCursor().position()
            text_cursor = txt_edit.textCursor()
            text_content = text_content[:max_length]
            txt_edit.setText(text_content)
            text_cursor.setPosition(position - (length - max_length))
            txt_edit.setTextCursor(text_cursor)

    @staticmethod
    def validate_field(text_edit):
        if text_edit.text() == '':
            text_edit.setPlaceholderText('Cannot be blank')
            return False
        return True

    def try_backup(self):
        import pyodbc
        try:
            DatabaseHandler.auto_backup()
        except pyodbc.ProgrammingError as err:
            self.show_message_box('Access denied, try a different location', str(err.args), 'Error')

    @staticmethod
    def cleanup_empty_cells(table):
        if table.item(0, 0) is None:
            table.clear()
            table.setRowCount(0)

    @staticmethod
    def true_row_count(frame):
        layout = frame.layout()
        count = 1
        if layout is not None:
            row_count = layout.rowCount()
            for j in range(row_count):  # loop through all rows
                if layout.itemAtPosition(j, 0) is not None:
                    count += 1
        return count

    @staticmethod
    def change_page(stacked_widget, name):
        widget = name

        # if the widget is in the stackedWidget
        if stacked_widget.indexOf(widget) != -1:
            stacked_widget.setCurrentIndex(stacked_widget.indexOf(widget))  # change the page to the widget

    @staticmethod
    def clear_layout(widget):
        layout = widget.layout()

        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                    widget.setParent(None)

    @staticmethod
    def populate_table(table, query, t_problems=None):

        table.clear()
        table.setSortingEnabled(False)  # this is necessary to avoid confusing the table widget (blank rows)

        # new array variables for holding column names
        header_names = []

        cursor = DatabaseHandler.execute_query(query)

        # validate the cursor for empty results
        if not DatabaseHandler.validate_cursor(cursor):
            return

        data = cursor.fetchall()
        cursor_desc = cursor.description

        # get all column names from the database
        for column in cursor_desc:
            header_names.append(column[0])

        table.horizontalHeader().setMaximumSectionSize(200)  # max size per column
        table.verticalHeader().setMaximumSectionSize(40)  # min size per row

        # QTableWidget requires you to set the amount of rows/columns needed before you populate it
        table.setRowCount(len(data))
        table.setColumnCount(len(data[0]))

        if t_problems and t_problems is not None:
            table.setColumnHidden(0, True)

        table.setWordWrap(True)
        table.setTextElideMode(Qt.ElideRight)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

        # set table header labels with column names from database
        table.setHorizontalHeaderLabels(header_names)

        # populate the table
        for i, row in enumerate(data):
            for j, col in enumerate(row):
                item = QtWidgets.QTableWidgetItem()

                if type(col) is int:  # if the column is a number
                    item.setData(Qt.EditRole, col)  # set correct role so sorting works properly
                else:
                    item = QtWidgets.QTableWidgetItem(str(col).strip())
                table.setItem(i, j, item)

        table.resizeColumnsToContents()
        table.setSortingEnabled(True)
        table.sortItems(0, QtCore.Qt.DescendingOrder)

    @staticmethod
    def populate_combo_box(comboBox, items):
        comboBox.clear()
        comboBox.setView(QtWidgets.QListView())
        comboBox.addItems(items)
        comboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)

    @staticmethod
    def time_convert(string, mode):
        if mode == '12 HR':
            time_string = datetime.datetime.strptime(string, '%H:%M:%S').strftime('%I:%M %p')
        else:
            time_string = datetime.datetime.strptime(string, '%H:%M:%S').strftime('%H:%M')
        return time_string

    ############# MENU #############
    # this function loops through the buttons in the menu to find the active QPushButton and set it to the active colour (green)
    def button_pressed(self):
        self.change_page(self.stackedWidgetSchedule, self.pageOptions)

        # look through the children of the children until we find a QPushButton
        for widget in self.frameMenu.children():
            self.is_push_button(widget)  # check for push buttons and update them
            for frame in widget.children():
                self.is_push_button(frame)  # check for push buttons and update them
                for member in frame.children():
                    self.is_push_button(member)  # check for push buttons and update them

    def is_push_button(self, member):
        # if object is a QPushButton
        if isinstance(member, QtWidgets.QPushButton):
            icon_name = member.accessibleName()

            if self.theme_choice['base_theme'] == 'dark':
                icon_normal = QtGui.QIcon()
                icon_active = QtGui.QIcon()

                icon_normal.addPixmap(QtGui.QPixmap(resource_path(f'images\\icons\\light_theme\\{icon_name}_light.png')))
                icon_active.addPixmap(QtGui.QPixmap(resource_path(f'images\\icons\\dark_theme\\{icon_name}_dark.png')))
            else:
                icon_normal = QtGui.QIcon()
                icon_active = QtGui.QIcon()
                icon_normal.addPixmap(QtGui.QPixmap(resource_path(f'images\\icons\\dark_theme\\{icon_name}_dark.png')))
                icon_active.addPixmap(QtGui.QPixmap(resource_path(f'images\\icons\\light_theme\\{icon_name}_light.png')))

            # if the button that called this function is the same as the member encountered:
            if member.objectName() == self.sender().objectName():

                # change button's colour to active green
                member.setAccessibleDescription('menuButtonActive')

                member.setIcon(icon_active)

                # use the button's name to find the linked frame
                self.show_linked_frame(member)

                member.setStyleSheet('')  # force a stylesheet refresh (faster than reapplying the style sheet)

            else:
                # set all other buttons' colour to white
                member.setAccessibleDescription('menuButton')
                member.setIcon(icon_normal)
                member.setStyleSheet('')  # force a stylesheet refresh (faster than reapplying the style sheet)

    # use the button's name to find the linked frame (deliberately named this way)
    def show_linked_frame(self, member):
        search = str(member.objectName()).replace('pushButton', '')

        for widget in self.stackedWidget.children():
            if search in widget.objectName():
                self.change_page(self.stackedWidget,widget)

    ############# DASHBOARD #############
    def problems_link(self, *args):
        self.pushButtonProblems.clicked.emit()

    # for handling creation and deletion of labels for labs that are soon going to be vacant
    def countdown_handler(self):
        # nicknames
        all_labs = self.all_labs_page_obj
        schedules = self.schedules
        open_lab_schedules = self.open_lab_schedules

        # local variables
        got_room = False
        last_room = ''
        focused_list = []  # this list holds one schedule per room

        if schedules is not None and len(schedules) != 0:  # not empty test

            # The purpose of this loop is to only retrieve the NEXT countdown for a room.
            # This is to ensure that the dashboard is only showing the one countdown for each room
            # if there are multiple open times throughout the day

            for schedule in schedules:  # loop through all of today's schedules
                room_name = schedule.get_room()  # get the room name of the current schedule

                if last_room != room_name:  # current room isn't the same as the last room
                    got_room = False

                if not got_room:  # if we don't already have an active countdown for this room
                    if not schedule.get_countdown().get_countdown_expired():  # check to see if the countdown is still valid
                        focused_list.append(schedule)
                        got_room = True  # indicate we have a room already for the next iteration

                last_room = room_name

            if focused_list is not None and len(focused_list) != 0:  # not empty test

                # Now we can go ahead and only loop through the focused list
                for schedule in focused_list:
                    for row in all_labs:
                        if schedule.get_room() == row[0]:
                            countdown = str(schedule.get_countdown().get_countdown())  # calculate the countdown using the current schedule object
                            room_name = schedule.get_room()  # get the room name for label
                            search = room_name + str(schedule.get_schedule_id())  # room name + scheduleID (for multiple open times in the same room)

                            # countdown = (datetime.timedelta(seconds=5) + self.staticDate) - datetime.datetime.now()  # for testing
                            if countdown is not None:  # only show countdown if it's not empty
                                countdown = datetime.datetime.strptime(str(countdown), '%H:%M:%S').strftime('%H:%M:%S')
                                label = room_name + '\t' + 'In: ' + str(countdown)  # text for the label
                                find_child = self.frameUpcomingRooms.findChild(QtWidgets.QPushButton, search)

                                if find_child is None:  # check to see if the widget exists already

                                    btn_label_countdown = QtWidgets.QPushButton(label, self)
                                    btn_label_countdown.setObjectName(search)
                                    btn_label_countdown.setAccessibleDescription('checkBoxRoom')
                                    btn_label_countdown.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                                    btn_label_countdown.setFlat(True)
                                    btn_label_countdown.setWhatsThis(room_name)
                                    btn_label_countdown.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
                                    btn_label_countdown.clicked.connect(self.open_image)

                                    self.add_to_empty_row(self.frameUpcomingRooms, btn_label_countdown)
                                else:  # the widget exists already so just update it
                                    find_child.setText(label)

                                if schedule.get_countdown().get_countdown_expired() and find_child is not None:  # countdown expired, so hide and remove the widget
                                    find_child.setVisible(False)
                                    find_child.deleteLater()

        # below for "all labs" page
        layout = self.scrollAreaAllLabs.widget().layout()
        current_row = 1

        if all_labs is not None and len(all_labs) != 0:  # not empty test
            for row in all_labs:
                room = row[0]
                row_num = row[1]

                item = layout.itemAtPosition(row_num, 3)

                if item is not None:  # remove existing widget
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                        widget.setParent(None)

                label_all_labs_countdown = None

                if schedules is not None and len(schedules) != 0:
                    for schedule in schedules:  # loop through all of today's schedules
                        if room == schedule.get_room():
                            all_countdown = schedule.get_countdown().get_countdown()

                            if label_all_labs_countdown is None:  # if the object hasn't been created already
                                if schedule.get_countdown().get_countdown_expired():  # if the first countdown for this room expired
                                    label_all_labs_countdown = QtWidgets.QLabel('expired', self)
                                    label_all_labs_countdown.setAccessibleDescription('formLabel')
                                    label_all_labs_countdown.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                                    label_all_labs_countdown.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

                                elif all_countdown is not None:
                                    all_countdown = datetime.datetime.strptime(str(all_countdown), '%H:%M:%S').strftime('%H:%M:%S')
                                    label_all_labs_countdown = QtWidgets.QLabel(all_countdown, self)
                                    label_all_labs_countdown.setAccessibleDescription('formLabel')
                                    label_all_labs_countdown.setWhatsThis(room)
                                    label_all_labs_countdown.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
                            else:
                                if schedule.get_countdown().get_countdown_expired():  # if the first countdown for this room expired
                                    label_all_labs_countdown.setText(label_all_labs_countdown.text() + '\n' + 'expired')
                                elif all_countdown is not None:
                                    all_countdown = datetime.datetime.strptime(str(all_countdown), '%H:%M:%S').strftime('%H:%M:%S')
                                    label_all_labs_countdown.setText(label_all_labs_countdown.text() + '\n' + all_countdown)

                if label_all_labs_countdown is not None:
                    layout.addWidget(label_all_labs_countdown, current_row, 3)

                current_row += 1

        if open_lab_schedules is not None and len(open_lab_schedules) != 0:
            for schedule in open_lab_schedules:  # loop through all of today's schedules
                dash_open_countdown = schedule.get_countdown().get_countdown()  # calculate the dash_open_countdown using the current schedule object
                room_name = schedule.get_room()  # get the room name for label
                search = room_name + str(schedule.get_schedule_id())  # room name + i (for multiple open times in the same room)
                find_child = self.frameUpcomingOpenLabs.findChild(QtWidgets.QPushButton, search)

                # dash_open_countdown = (datetime.timedelta(seconds=5) + self.staticDate) - datetime.datetime.now()  # for testing
                if dash_open_countdown is not None:  # only show dash_open_countdown if it's not empty
                    label = room_name + '         ' + 'In: ' + str(dash_open_countdown)  # text for the label
                    if find_child is None:  # check to see if the widget exists already
                        btn_label_upcoming = QtWidgets.QPushButton(label, self)
                        btn_label_upcoming.setObjectName(search)
                        btn_label_upcoming.setAccessibleDescription('checkBoxRoom')
                        btn_label_upcoming.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                        btn_label_upcoming.setFlat(True)
                        btn_label_upcoming.setWhatsThis(room_name)
                        btn_label_upcoming.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
                        btn_label_upcoming.clicked.connect(self.open_image)

                        self.frameUpcomingOpenLabs.layout().addWidget(btn_label_upcoming)  # add the checkbox to the frame
                    else:  # the widget exists already so just update it
                        find_child.setText(label)
                        if dash_open_countdown < datetime.timedelta(minutes=30):
                            if dash_open_countdown.seconds % 2 == 0:
                                find_child.setAccessibleDescription('timerDanger')
                            else:
                                find_child.setAccessibleDescription('checkBoxRoom')
                            find_child.setStyleSheet('')  # force a stylesheet refresh (faster than reapplying the style sheet)

                    if schedule.get_countdown().get_countdown_expired() and find_child is not None:  # countdown expired, so hide and remove the widget
                        find_child.setVisible(False)
                        find_child.deleteLater()

    # for handling creation and deletion of checkboxes for labs that are vacant
    def duration_handler(self):
        schedules = self.schedules
        open_lab_schedules = self.open_lab_schedules

        if schedules is not None and len(schedules) != 0:
            for schedule in schedules:  # loop through all of today's schedules
                dash_duration = schedule.get_countdown().get_duration()
                room_name = schedule.get_room()  # get the room name for label
                search = room_name + 'duration' + str(schedule.get_schedule_id())  # room name + i (for multiple open times in the same room)
                find_child = self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search)
                find_child2 = self.frameEmptyRooms.findChild(QtWidgets.QPushButton, 'label' + search)

                # dash_duration = (datetime.timedelta(seconds=2230) + self.staticDate) - datetime.datetime.now()  # for testing (will countdown from 30 seconds)
                if dash_duration is not None:
                    label = room_name + '       ' + str(dash_duration)

                    if find_child is None:  # check to see if the widget exists already
                        checkBox = QtWidgets.QCheckBox(self)  # create a new checkbox and append the room name + dash_duration
                        checkBox.setAccessibleDescription('checkBoxRoom')  # add tag for qss styling
                        checkBox.setObjectName(search)
                        checkBox.stateChanged.connect(self.remove_countdown)
                        checkBox.setWhatsThis(room_name)
                        checkBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                        checkBox.setAccessibleName(str(schedule.get_schedule_id()))  # to link the schedule ID

                        checkbox_label = QtWidgets.QPushButton(label, self)
                        checkbox_label.setObjectName('label' + search)
                        checkbox_label.setAccessibleDescription('checkBoxRoom')
                        checkbox_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                        checkbox_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
                        checkbox_label.setFlat(True)
                        checkbox_label.setWhatsThis(room_name)
                        checkbox_label.clicked.connect(self.open_image)

                        self.add_to_empty_row(self.frameEmptyRooms, checkBox, checkbox_label)

                        # self.frameEmptyRooms.layout().addWidget(checkBox, current_row, 0)  # add the checkbox to the frame
                        # self.frameEmptyRooms.layout().addWidget(checkbox_label, current_row, 1)  # add the checkbox to the frame
                    else:  # if the widget exists already, update it
                        if find_child2 is not None:
                            find_child2.setText(label)
                            if dash_duration < datetime.timedelta(minutes=30):
                                if dash_duration.seconds % 2 == 0:  # change the style to red every other second
                                    find_child2.setAccessibleDescription('timerDanger')
                                else:
                                    find_child2.setAccessibleDescription('checkBoxRoom')
                                find_child2.setStyleSheet('')  # force a stylesheet refresh (faster than reapplying the style sheet)

                    if schedule.get_countdown().get_duration_expired() and find_child is not None:  # duration expired, so remove the widget
                        find_child.setVisible(False)
                        find_child2.setVisible(False)
                        find_child.deleteLater()
                        find_child2.deleteLater()

        if open_lab_schedules is not None and len(open_lab_schedules) != 0:
            for schedule in open_lab_schedules:  # loop through all of today's schedules
                dash_open_countdown = schedule.get_countdown().get_duration()  # calculate the dash_open_countdown using the current schedule object
                room_name = schedule.get_room()  # get the room name for label
                search = 'ol' + room_name + str(schedule.get_schedule_id())  # room name + i (for multiple open times in the same room)
                find_child = self.frameOpenLabs.findChild(QtWidgets.QPushButton, search)

                # dash_open_countdown = (datetime.timedelta(seconds=5) + self.staticDate) - datetime.datetime.now()  # for testing
                if dash_open_countdown is not None:  # only show dash_open_countdown if it's not empty
                    label = room_name + '         ' + str(dash_open_countdown)  # text for the label
                    if find_child is None:  # check to see if the widget exists already
                        label_duration = QtWidgets.QPushButton(label, self)
                        label_duration.setObjectName(search)
                        label_duration.setAccessibleDescription('checkBoxRoom')
                        label_duration.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                        label_duration.setFlat(True)
                        label_duration.setWhatsThis(room_name)
                        label_duration.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
                        label_duration.clicked.connect(self.open_image)

                        self.frameOpenLabs.layout().addWidget(label_duration)  # add the checkbox to the frame
                    else:  # the widget exists already so just update it
                        find_child.setText(label)

                    if schedule.get_countdown().get_duration_expired() and find_child is not None:  # dash_open_countdown expired, so hide and remove the widget
                        find_child.setVisible(False)
                        find_child.deleteLater()

    def open_image(self):
        room = self.sender().whatsThis()
        room = room.replace('-', '_')
        path = resource_path(f'images\\timetables\\{room}' + '.jpg')

        try:
            os.startfile(path)
        except FileNotFoundError:
            message = f'Oh no! Windows could not find the timetable image for {room}'
            info = f'Path searched: \'{path}\''
            self.show_message_box(message, info)

    def show_message_box(self, message, info, title=None):

        msg = QtWidgets.QMessageBox()
        import qtmodern_package.windows as qtmodern_windows
        msg.setObjectName('Lab_Error')
        msg.setText(message)
        msg.setInformativeText(info)
        size = msg.sizeHint()

        if title is not None:
            msg.setWindowTitle(title)
        else:
            msg.setWindowTitle('Error')

        flags = QtCore.Qt.WindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        msg.setWindowFlags(flags)
        msg.setStyleSheet(self.theme)
        msg = qtmodern_windows.ModernWindow(msg)
        msg.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowModal)
        msg.setGeometry(0, 0, size.width(), size.height())

        center_widget(msg)

        msg.btnMinimize.setVisible(False)
        msg.btnMaximize.setVisible(False)

        msg.show()

    def remove_countdown(self):
        if self.sender().isChecked():
            for schedule in self.schedules:
                if schedule.get_schedule_id() == int(self.sender().accessibleName()):  # if the schedule ID is the same as the sender's accessibleName field
                    schedule.get_countdown().set_end_time(datetime.datetime.now().time().isoformat(timespec='seconds'))  # expire the time

            search = 'label' + self.sender().objectName()
            widget_child = self.frameDashboardBrief.findChildren(QtWidgets.QPushButton)

            for widget in widget_child:
                if widget.objectName() == search:
                    widget.setVisible(False)  # hide the widget
                    widget.deleteLater()  # schedule the widget for deletion

            self.sender().setVisible(False)  # hide the widget
            self.sender().deleteLater()  # schedule the widget for deletion
        self.clear_layout(self.frameEmptyRooms)

    def show_schedule_modifier(self):
        self.labelSchedule.setText('SCHEDULE MODIFIER')
        self.pushButtonScheduleSave.setAccessibleName('Schedule')
        self.comboBoxScheduleRooms.currentIndexChanged.emit(0)  # emit something to trigger the update_checkboxes function
        self.change_page(self.stackedWidgetSchedule, self.pageScheduleModifier)

    def show_open_lab_schedule_modifier(self):
        self.labelSchedule.setText('OPEN LAB SCHEDULE MODIFIER')
        self.pushButtonScheduleSave.setAccessibleName('Open')
        self.comboBoxScheduleRooms.currentIndexChanged.emit(0)  # emit something to trigger the update_checkboxes function
        self.change_page(self.stackedWidgetSchedule, self.pageScheduleModifier)

    def restore(self, frame, parent):
        parent.layout().addWidget(frame)
        frame.setVisible(True)
        self.floating_state = False  # floating window inactive

    def make_floating_window(self):
        import qtmodern_package.windows as qtmodern_windows

        window = Window(self)
        window.setCentralWidget(QtWidgets.QWidget())
        window.setGeometry(QtCore.QRect(0, 0, 480, 720))  # start size/location
        window.setStyleSheet(self.theme)
        window.setWindowTitle('All Labs')

        central_widget = window.centralWidget()
        central_widget.setLayout(QtWidgets.QGridLayout())
        central_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        container_frame = QtWidgets.QFrame()
        container_frame.setObjectName('container')
        container_frame.setLayout(QtWidgets.QGridLayout())
        container_frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        container_frame.setAccessibleDescription('backgroundFrame')
        central_widget.layout().addWidget(container_frame)

        center_widget(window)

        sizegrip = QtWidgets.QSizeGrip(window)

        central_widget.layout().addWidget(sizegrip, 1, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)

        mw = qtmodern_windows.ModernWindow(window, self)
        mw.btnMaximize.setVisible(False)
        mw.btnMinimize.setVisible(False)

        return mw

    def move_to_floating_window(self):
        state = self.floating_state  # for determining whether a floating window is active already

        if not state:  # make new floating window
            self.floating = self.make_floating_window()

        window = self.floating

        frame = self.scrollAreaAllLabs
        frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        find_child = window.w.centralWidget().findChild(QtWidgets.QFrame, 'container')
        find_child.layout().addWidget(frame)

        frame.setVisible(True)

        window.btnClose.clicked.connect(lambda: self.restore(frame, self.frameScrollContainer))
        self.floating_state = True  # floating window is active
        window.show()

    def add_to_empty_row(self, frame, widget, label=None):
        layout = frame.layout()

        if layout is not None:
            row_count = self.true_row_count(frame)
            max = 11

            for j in range(row_count):  # loop through all rows
                if row_count >= max:
                    if label is not None:
                        item = layout.itemAtPosition(j, 2)
                        if item is None:
                            if label is not None:
                                layout.addWidget(widget, j, 2)  # add to new column in same row
                                layout.addWidget(label, j, 3)  # add to new column in same row
                                return
                    else:
                        item = layout.itemAtPosition(j, 1)
                        if item is None:
                            layout.addWidget(widget, j, 1)  # add to new column in same row
                            return
                else:
                    item = layout.itemAtPosition(j, 0)
                    if item is None:
                        if label is not None:
                            layout.addWidget(widget, j, 0)
                            layout.addWidget(label, j, 1)  # add to new column in same row
                            return
                        else:
                            layout.addWidget(widget, j, 0)
                            return

            if row_count == 0:  # if the layout has nothing in it
                layout.addWidget(widget, 0, 0)
                if label is not None:
                    layout.addWidget(label, 0, 1)  # add to new column in same row

                return

    ############# PROBLEMS, REPORTS, LOST AND FOUND #############

    def view_selection(self, table):
        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1 and table.item(0, 0) is not None:
            self.lastPage = table.objectName()
            row_index = table.currentRow()  # get index of current row
            data = []  # data list
            labels = []
            layout = self.frameViewDataForm.layout()

            for i in range(table.columnCount()):  # loop through all columns
                data.append(table.item(row_index, i).text())  # add each field to the list
                labels.append(table.horizontalHeaderItem(i).text())

            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                        widget.setParent(None)

            for j in range(len(data)):

                replaced = labels[j].replace('_', ' ')

                if replaced == 'NOTE' or replaced == 'RESOLUTION':
                    data_widget = QtWidgets.QTextEdit(f'{data[j]}')
                    data_widget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                    data_widget.setAccessibleDescription('textEdit')
                    data_widget.setReadOnly(True)
                    data_widget.setTextInteractionFlags(Qt.NoTextInteraction)
                    data_widget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
                    data_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                    data_widget.setAcceptRichText(False)
                    data_widget.document().setDocumentMargin(0)
                else:
                    data_widget = QtWidgets.QLabel(f'{data[j]}')
                    data_widget.setScaledContents(True)
                    data_widget.setWordWrap(True)
                    data_widget.setAccessibleDescription('formLabelNormal')
                    data_widget.setAlignment(Qt.AlignLeft | Qt.AlignTop)

                data_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

                label_widget = QtWidgets.QLabel(f'{replaced}:')
                label_widget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                label_widget.setAccessibleDescription('formLabel')
                label_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                label_widget.setMinimumSize(200, 0)
                label_widget.setMaximumSize(500, 100)

                self.frameViewDataForm.layout().addRow(label_widget, data_widget)

            # change to view page
            self.change_page(self.stackedWidget, self.pageViewData)

    def delete_selection(self, table, table_name):

        dialog = Dialog()
        center_widget(dialog)

        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1 and table.item(0, 0) is not None:
            if dialog.show_dialog('Are you sure?'):
                row_index = table.currentRow()  # get index of current row
                column_index = table.item(row_index, 0).text()
                first_column = DatabaseHandler.execute_query(f"SELECT column_name from information_schema.columns where table_name = '{table_name}' and ordinal_position = 1").fetchone()
                delete_query = f'DELETE FROM dbo.{table_name} WHERE {str(first_column[0])} = {column_index};'
                DatabaseHandler.execute_query(delete_query).commit()
                self.refresh_tables()

    def clear_form(self):
        self.dateEditNewLog.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLog.setCurrentSectionIndex(2)
        self.textBoxNewLogIssue.setText('')
        self.textBoxNewLogNote.setText('')
        self.textBoxNewLogName.setText('')
        self.checkBoxFixed.setCheckState(False)
        self.textBoxNewLogResolution.setText('')
        self.comboBoxRoom.setCurrentIndex(0)

    def save_new_log(self):

        state = True
        list_objects = None

        # empty field validation
        if not (self.validate_field(self.textBoxNewLogIssue)):
            state = False

        if not (self.validate_field(self.textBoxNewLogName)):
            state = False

        if not state:
            return

        date = self.dateEditNewLog.date().toString('yyyy-MM-dd')
        issue = self.textBoxNewLogIssue.text().strip()
        note = self.textBoxNewLogNote.toPlainText()
        name = self.textBoxNewLogName.text().strip()
        room = self.comboBoxRoom.currentText().strip()
        fixed = ' '

        if self.checkBoxFixed.isChecked():
            fixed = 'YES'
        else:
            fixed = 'NO'

        resolution = self.textBoxNewLogResolution.toPlainText().strip()

        if self.stored_id == 0:
            query = f'''
            INSERT INTO dbo.Reports
                (DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) 
            VALUES 
                (?, ?, ?, ?, ?, ?, ?)'''
            list_objects = [date, name, room, issue, note, resolution, fixed]
        else:
            query = f'''
            UPDATE dbo.Reports 
            SET 
                DATE = ?, 
                NAME = ?, 
                ROOM = ?, 
                ISSUE = ?, 
                NOTE = ?, 
                RESOLUTION = ?, 
                FIXED = ? 
            WHERE 
                REPORT_ID = {self.stored_id};'''

            list_objects = [date, name, room, issue, note, resolution, fixed]

        cursor = DatabaseHandler.execute_query(query, list_objects)

        # validate the cursor for empty results
        if not DatabaseHandler.validate_cursor(cursor):
            self.change_page(self.stackedWidget, self.pageReports)
            return

        cursor.commit()

        self.refresh_tables()
        self.change_to_last_page()
        self.clear_form()

    def search_buttons(self, table, button):
        keyword = button.text()

        if table.objectName().find('Lost') != -1:
            if self.comboBoxLostAndFoundMonth.currentText() != 'All':
                month = self.comboBoxLostAndFoundMonth.currentText()
                query = f'''
                    SELECT * FROM dbo.LostAndFound 
                    where 
                    MONTH(DATE_FOUND) = (SELECT MONTH('{month}' + '2020')) AND
                    (
                        ITEM_DESC like '%{keyword}%'or 
                        NAME like '%{keyword}%' or 
                        ROOM like '%{keyword}%' or 
                        NOTE like '%{keyword}%' or 
                        STUDENT_NAME like '%{keyword}%' or 
                        STUDENT_NUMBER like '%{keyword}%' or 
                        RETURNED_DATE like '%{keyword}%' or 
                        RETURNED like '%{keyword}%'
                    );
                '''
            else:
                query = f'''
                    SELECT * FROM dbo.LostAndFound 
                    where 
                        ITEM_DESC like '%{keyword}%'or 
                        NAME like '%{keyword}%' or 
                        ROOM like '%{keyword}%' or 
                        NOTE like '%{keyword}%' or
                        STUDENT_NAME like '%{keyword}%' or 
                        STUDENT_NUMBER like '%{keyword}%' or 
                        RETURNED_DATE like '%{keyword}%' or 
                        RETURNED like '%{keyword}%';
                '''
            self.populate_table(table, query)
            self.cleanup_empty_cells(table)

        elif table.objectName().find('Reports') != -1:
            if self.comboBoxReportsMonth.currentText() != 'All':
                month = self.comboBoxReportsMonth.currentText()
                query = f'''
                            SELECT * FROM dbo.Reports 
                            where 
                            MONTH(DATE) = (SELECT MONTH('{month}' + '2020')) AND
                            (
                                ISSUE like '%{keyword}%'or 
                                NAME like '%{keyword}%' or 
                                ROOM like '%{keyword}%' or 
                                RESOLUTION like '%{keyword}%' or
                                FIXED like '%{keyword}%' or 
                                NOTE like '%{keyword}%'
                            );
                        '''
            else:
                query = f'''
                    SELECT * FROM dbo.Reports 
                    where ISSUE like '%{keyword}%'or 
                    NAME like '%{keyword}%' or 
                    ROOM like '%{keyword}%' or 
                    RESOLUTION like '%{keyword}%' or
                    FIXED like '%{keyword}%' or 
                    NOTE like '%{keyword}%';
                '''
            self.populate_table(table, query)
            self.cleanup_empty_cells(table)

    def edit_log(self, table):
        self.lastPage = table.objectName()

        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1 and table.item(0, 0) is not None:
            row_index = table.currentRow()  # get index of current row
            report_id = table.item(row_index, 0).text()
            self.stored_id = report_id

            query = f'SELECT DATE, NAME, ROOM, ISSUE, NOTE, RESOLUTION, FIXED from dbo.Reports WHERE REPORT_ID = {report_id};'
            cursor = DatabaseHandler.execute_query(query)

            # validate the cursor for empty results
            if not DatabaseHandler.validate_cursor(cursor):
                self.change_to_last_page()
                return

            log = cursor.fetchall()
            self.clear_form()
            self.labelNewLog.setText('EDIT LOG')
            self.dateEditNewLog.setDate(log[0].DATE)
            self.dateEditNewLog.setCurrentSectionIndex(2)
            self.textBoxNewLogName.setText(str(log[0].NAME).strip())
            self.textBoxNewLogIssue.setText(str(log[0].ISSUE).strip())
            self.textBoxNewLogNote.setText(str(log[0].NOTE.strip()))
            self.textBoxNewLogResolution.setText(str(log[0].RESOLUTION).strip())

            index = self.comboBoxRoom.findText(log[0].ROOM, QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.comboBoxRoom.setCurrentIndex(index)

            if str(log[0].FIXED).strip() == 'YES':
                self.checkBoxFixed.setChecked(True)
            else:
                self.checkBoxFixed.setChecked(False)

            self.change_page(self.stackedWidget,self.pageNewLog)

    def returned_checkbox_changed(self):  # this way it only happens if the state was changed
        if self.checkBoxNewLostAndFoundReturned.isChecked():
            self.dateEditReturnedNewLostAndFound.setDate(QtCore.QDate.currentDate())
            self.dateEditReturnedNewLostAndFound.setCurrentSectionIndex(2)

        self.show_frame_returned_laf()

    def change_to_last_page(self):
        # remove the 'tableWidget' from the string (this is why everything is named this way lol)
        name = self.lastPage.replace('tableWidget', '')
        page_name = 'page' + name  # add page to the modified string
        self.change_page(self.stackedWidget,self.findChild(QtWidgets.QWidget, page_name))  # change to last page

    def refresh_tables(self):
        import calendar
        month = calendar.month_name[datetime.datetime.now().month]  # converting the month number to a string
        index = self.comboBoxReportsMonth.findText(month)
        if index >= 0:
            self.comboBoxReportsMonth.setCurrentIndex(index)

        reports_query = f"SELECT * FROM dbo.Reports WHERE MONTH(DATE) = (SELECT MONTH('{month}' + '2020'))"
        problems_query = 'SELECT REPORT_ID, DATE, NAME, ROOM,ISSUE,NOTE FROM dbo.Reports WHERE FIXED =\'NO\''
        lost_and_found_query = 'SELECT * FROM dbo.LostAndFound'
        problems_count_query = 'SELECT COUNT(REPORT_ID) FROM dbo.Reports WHERE FIXED =\'NO\''

        self.populate_table(self.tableWidgetReports, reports_query)
        self.populate_table(self.tableWidgetProblems, problems_query, True)
        self.populate_table(self.tableWidgetLostAndFound, lost_and_found_query)

        self.cleanup_empty_cells(self.tableWidgetReports)
        self.cleanup_empty_cells(self.tableWidgetProblems)
        self.cleanup_empty_cells(self.tableWidgetLostAndFound)

        cursor = DatabaseHandler.execute_query(problems_count_query)

        # validate the cursor for empty results
        if not DatabaseHandler.validate_cursor(cursor):
            return

        self.labelNumberProblems.setText(str(cursor.fetchone()[0]))

    def sort_by_month(self, mode, input_month=None):  # setting an optional argument to null since python has no overloading
        if mode == 'Reports':
            if input_month is not None:
                query = f"SELECT * FROM dbo.Reports WHERE MONTH(DATE) = (SELECT MONTH('{input_month}' + '2020'))"
            else:
                month = self.sender().currentText()  # receive the combobox's current text
                if month == 'All':
                    query = f"SELECT * FROM dbo.Reports"
                else:
                    query = f"SELECT * FROM dbo.Reports WHERE MONTH(DATE) = (SELECT MONTH('{month}' + '2020'))"
            self.populate_table(self.tableWidgetReports, query)
            self.cleanup_empty_cells(self.tableWidgetReports)

        if mode == 'LostAndFound':
            if input_month is not None:
                query = f"SELECT * FROM dbo.LostAndFound WHERE MONTH(DATE_FOUND) = (SELECT MONTH('{input_month}' + '2020'))"
            else:
                month = self.sender().currentText()  # receive the combobox's current text
                if month == 'All':
                    query = f"SELECT * FROM dbo.LostAndFound"
                else:
                    query = f"SELECT * FROM dbo.LostAndFound WHERE MONTH(DATE_FOUND) = (SELECT MONTH('{month}' + '2020'))"
            self.populate_table(self.tableWidgetLostAndFound, query)
            self.cleanup_empty_cells(self.tableWidgetLostAndFound)

    def new_lost_and_found(self):
        self.stored_id = 0
        self.clear_lost_and_found_form()
        self.dateEditNewLostAndFound.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLostAndFound.setCurrentSectionIndex(2)
        self.dateEditReturnedNewLostAndFound.setDate(self.default_returned_date)

        self.frameReturnedLAF.hide()
        self.refresh_tables()
        self.change_page(self.stackedWidget,self.pageNewLAF)

    def clear_lost_and_found_form(self):
        self.dateEditNewLostAndFound.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLostAndFound.setCurrentSectionIndex(2)
        self.comboBoxNewLostAndFoundRoom.setCurrentIndex(0)
        self.textBoxNewLostAndFoundBy.clear()
        self.textBoxNewLostAndFoundItemDescription.clear()
        self.textBoxNewLostAndFoundNote.clear()
        self.dateEditReturnedNewLostAndFound.setDate(self.default_returned_date)
        self.checkBoxNewLostAndFoundReturned.setCheckState(False)
        self.textBoxNewLostAndFoundStudentName.clear()
        self.textBoxNewLostAndFoundStudentNumber.clear()
        self.show_frame_returned_laf()

    def save_lost_and_found_form(self):
        date = self.dateEditNewLostAndFound.date().toString('yyyy-MM-dd')
        room = self.comboBoxNewLostAndFoundRoom.currentText()
        found_by = self.textBoxNewLostAndFoundBy.text()
        item_description = self.textBoxNewLostAndFoundItemDescription.text()
        note = self.textBoxNewLostAndFoundNote.toPlainText()
        list_objects = None
        state = True

        # empty field validation
        if not (self.validate_field(self.textBoxNewLostAndFoundBy)):
            state = False

        if not state:
            return

        if self.stored_id == 0:  # id of 0 means it's a new entry
            student_name = self.textBoxNewLostAndFoundStudentName.text()
            student_number = self.textBoxNewLostAndFoundStudentNumber.text()

            if self.checkBoxNewLostAndFoundReturned.isChecked():
                returned_date = self.dateEditReturnedNewLostAndFound.date().toString('yyyy-MM-dd')
                returned = 'YES'
                query = f'''
                            INSERT INTO dbo.LostAndFound
                                (DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,STUDENT_NAME,STUDENT_NUMBER,RETURNED_DATE,RETURNED) 
                            VALUES 
                                (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
                list_objects = [date, room, found_by, item_description, note, student_name, student_number, returned_date, returned]
            else:
                returned = 'NO'
                query = f'''
                            INSERT INTO dbo.LostAndFound
                                (DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,STUDENT_NAME,STUDENT_NUMBER,RETURNED) 
                            VALUES 
                                (?, ?, ?, ?, ?, ?, ?, ?)'''
                list_objects = [date, room, found_by, item_description, note, student_name, student_number, returned]

        else:  # already has an id, meaning it's an update
            if self.checkBoxNewLostAndFoundReturned.isChecked():
                returned = 'YES'
                returned_date = self.dateEditReturnedNewLostAndFound.date().toString('yyyy-MM-dd')
                student_name = self.textBoxNewLostAndFoundStudentName.text()
                student_number = self.textBoxNewLostAndFoundStudentNumber.text()

                query = f'''
                UPDATE dbo.LostAndFound 
                SET 
                    DATE_FOUND = ?, 
                    ROOM = ?, 
                    NAME = ?, 
                    ITEM_DESC = ?, 
                    NOTE = ?, 
                    STUDENT_NAME = ?, 
                    STUDENT_NUMBER = ?, 
                    RETURNED_DATE = ?, 
                    RETURNED = ?
                WHERE 
                    ENTRY_ID = {self.stored_id};'''

                list_objects = [date, room, found_by, item_description, note, student_name, student_number, returned_date, returned]
            else:
                returned = 'NO'
                student_name = ''
                student_number = ''
                query = f'''
                UPDATE dbo.LostAndFound 
                SET 
                    DATE_FOUND = ?, 
                    ROOM = ?, 
                    NAME = ?, 
                    ITEM_DESC = ?, 
                    NOTE = ?, 
                    STUDENT_NAME = ?, 
                    STUDENT_NUMBER = ?, 
                    RETURNED_DATE = null, 
                    RETURNED = ?
                WHERE 
                    ENTRY_ID = {self.stored_id};'''
                list_objects = [date, room, found_by, item_description, note, student_name, student_number, returned]

        cursor = DatabaseHandler.execute_query(query, list_objects)

        # validate the cursor for empty results
        if not DatabaseHandler.validate_cursor(cursor):
            self.change_to_last_page()
            return

        cursor.commit()
        self.refresh_tables()
        self.change_page(self.stackedWidget,self.pageLostAndFound)

    def edit_laf_form(self):
        table = self.tableWidgetLostAndFound

        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1 and table.item(0, 0) is not None:
            row_index = table.currentRow()  # get index of current row
            entry_id = table.item(row_index, 0).text()
            self.stored_id = entry_id

            query = f'SELECT DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,STUDENT_NAME,STUDENT_NUMBER,RETURNED_DATE,RETURNED FROM dbo.LostAndFound WHERE ENTRY_ID = {entry_id};'
            cursor = DatabaseHandler.execute_query(query)

            # validate the cursor for empty results
            if not DatabaseHandler.validate_cursor(cursor):
                self.change_to_last_page()
                return

            laf = cursor.fetchall()
            self.clear_form()
            self.labelNewLostAndFound.setText('EDIT LOST AND FOUND')
            self.dateEditNewLostAndFound.setDate(laf[0].DATE_FOUND)
            self.dateEditNewLostAndFound.setCurrentSectionIndex(2)

            self.dateEditReturnedNewLostAndFound.setDate(laf[0].RETURNED_DATE or self.default_returned_date)
            self.dateEditReturnedNewLostAndFound.setCurrentSectionIndex(2)

            self.textBoxNewLostAndFoundBy.setText(str(laf[0].NAME).strip())
            self.textBoxNewLostAndFoundItemDescription.setText(str(laf[0].ITEM_DESC).strip())
            self.textBoxNewLostAndFoundNote.setText(str(laf[0].NOTE.strip()))

            self.textBoxNewLostAndFoundStudentName.setText(str(laf[0].STUDENT_NAME).strip())
            self.textBoxNewLostAndFoundStudentNumber.setText(str(laf[0].STUDENT_NUMBER).strip())

            index = self.comboBoxNewLostAndFoundRoom.findText(laf[0].ROOM, QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.comboBoxNewLostAndFoundRoom.setCurrentIndex(index)

            if str(laf[0].RETURNED).strip() == 'YES':
                self.checkBoxNewLostAndFoundReturned.setChecked(True)
                self.show_frame_returned_laf()
            else:
                self.checkBoxNewLostAndFoundReturned.setChecked(False)
                self.show_frame_returned_laf()

            self.change_page(self.stackedWidget,self.pageNewLAF)

    def show_frame_returned_laf(self):
        if self.checkBoxNewLostAndFoundReturned.isChecked():
            self.frameReturnedLAF.show()
        else:
            self.frameReturnedLAF.hide()

    ############# ALL LABS #############

    def get_all_labs(self):
        layout = self.scrollAreaAllLabs.widget().layout()
        column_count = layout.columnCount()
        row_count = layout.rowCount()
        schedules = self.schedules

        if layout is not None:
            for i in range(column_count):  # loop through all columns
                for j in range(1, row_count):  # loop starting at row 1
                    item = layout.itemAtPosition(j, i)
                    if item is not None:
                        widget = item.widget()
                        if widget is not None:
                            widget.deleteLater()
                            widget.setParent(None)
                            del widget

        current_row = 1  # start with the row after the headers

        if self.all_rooms is not None and range(len(self.all_rooms) != 0):
            for room in self.all_rooms:  # loop through all rooms
                label_times = None
                label_end_times = None

                # label creation
                label_room = QtWidgets.QPushButton(room)
                label_room.setAccessibleDescription('allRooms')
                label_room.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                label_room.setFlat(True)
                label_room.setWhatsThis(room)
                label_room.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                label_room.clicked.connect(self.open_image)
                label_room.setMinimumSize(0, 30)
                label_room.setMaximumSize(100, 100)

                # adding to layout
                layout.addWidget(label_room, current_row, 0)

                if schedules is not None and range(len(schedules) != 0):  # not empty validation
                    for schedule in schedules:  # loop through all schedules
                        if schedule.get_room() == room:
                            mode = self.time_format

                            start_time = self.time_convert(str(schedule.get_start_time()), mode)
                            end_time = self.time_convert(str(schedule.get_end_time()), mode)

                            if label_times is not None:
                                label_times.setText(label_times.text() + '\n' + start_time)
                            else:
                                # label creation
                                label_times = QtWidgets.QLabel(start_time)
                                label_times.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                                label_times.setAccessibleDescription('formLabel')
                                label_times.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                                label_times.setMinimumSize(50, 0)
                                label_times.setMaximumSize(100, 100)

                            if label_end_times is not None:
                                label_end_times.setText(label_end_times.text() + '\n' + end_time)
                            else:
                                # label creation
                                label_end_times = QtWidgets.QLabel(end_time)
                                label_end_times.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                                label_end_times.setAccessibleDescription('formLabel')
                                label_end_times.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                                label_end_times.setMinimumSize(50, 0)
                                label_end_times.setMaximumSize(100, 100)

                if label_times is not None:
                    layout.addWidget(label_times, current_row, 1)
                else:
                    label_times = QtWidgets.QLabel('None')
                    label_times.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    label_times.setAccessibleDescription('formLabel')
                    label_times.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    label_times.setMinimumSize(50, 0)
                    label_times.setMaximumSize(100, 100)
                    layout.addWidget(label_times, current_row, 1)

                if label_end_times is not None:
                    layout.addWidget(label_end_times, current_row, 2)

                current_row += 1

        self.all_labs_page_obj = self.get_all_labs_obj()

    # for getting the row number of a room label in the layout
    def get_all_labs_obj(self):
        layout = self.scrollAreaAllLabs.widget().layout()
        row_count = layout.rowCount()
        data = []
        if layout is not None or row_count != 0:
            for j in range(1, row_count):
                widget = layout.itemAtPosition(j, 0).widget()
                data.append([widget.text(), j])
        return data
    ############# SCHEDULE MODIFIER #############

    def schedule_modifier_index_changed(self):
        mode = self.pushButtonScheduleSave.accessibleName()
        self.label_schedule_room.setText(self.comboBoxScheduleRooms.currentText())
        ScheduleModifier.update_checkboxes(self.frameScheduleMod, self.comboBoxScheduleRooms, mode)
        self.show_room_schedule(self.comboBoxScheduleRooms.currentText(), mode)

    def show_room_schedule(self, room, mode):
        layout = self.frameCurrentSchedule.layout()

        if mode == 'Open':
            schedules = ScheduleModifier.get_open_lab_schedules()
        else:
            schedules = ScheduleModifier.get_schedules()

        if layout is not None:
            column_count = layout.columnCount()
            row_count = layout.rowCount()
            for i in range(column_count):  # loop through all columns
                for j in range(row_count):  # loop starting at row 1
                    item = layout.itemAtPosition(j, i)
                    if item is not None:
                        widget = item.widget()
                        if widget is not None:
                            widget.deleteLater()
                            widget.setParent(None)

        current_row = layout.rowCount()  # this will always be an empty row index

        # label creation
        header_day = QtWidgets.QLabel('DAY')
        header_start_time = QtWidgets.QLabel('START TIME')
        header_end_time = QtWidgets.QLabel('END TIME')

        header_day.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        header_start_time.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        header_end_time.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # accessible description for qss styling
        header_day.setAccessibleDescription('titleLabel')
        header_start_time.setAccessibleDescription('titleLabel')
        header_end_time.setAccessibleDescription('titleLabel')

        header_day.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        header_start_time.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        header_end_time.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        header_day.setMinimumSize(0, 30)
        header_start_time.setMinimumSize(0, 30)
        header_end_time.setMinimumSize(0, 30)

        layout.addWidget(header_day, current_row, 0)
        layout.addWidget(header_start_time, current_row, 1)
        layout.addWidget(header_end_time, current_row, 2)

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for schedule_day in days:  # loop through all schedule days
            current_row = layout.rowCount()  # this will always be an empty row index
            label_start_time = None
            label_end_time = None

            # label creation
            label_day = QtWidgets.QLabel(schedule_day)
            label_day.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label_day.setAccessibleDescription('formLabel')
            label_day.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            label_day.setMinimumSize(0, 30)

            layout.addWidget(label_day, current_row, 0)

            if schedules is not None and range(len(schedules) != 0):  # not empty validation
                for schedule in schedules:  # loop through all schedules
                    if schedule.get_room() == room and schedule.get_day() == schedule_day:
                        mode = self.time_format

                        start_time = self.time_convert(str(schedule.get_start_time()), mode)
                        end_time = self.time_convert(str(schedule.get_end_time()), mode)

                        # label creation
                        if label_start_time is not None:
                            label_start_time.setText(label_start_time.text() + '\n' + start_time)
                        else:
                            label_start_time = QtWidgets.QLabel(start_time)
                            label_start_time.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                            label_start_time.setAccessibleDescription('formLabel')
                            label_start_time.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

                        # label creation
                        if label_end_time is not None:
                            label_end_time.setText(label_end_time.text() + '\n' + end_time)
                        else:
                            label_end_time = QtWidgets.QLabel(end_time)
                            label_end_time.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                            label_end_time.setAccessibleDescription('formLabel')
                            label_end_time.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

            if label_start_time is not None:
                layout.addWidget(label_start_time, current_row, 1)
            else:
                label_start_time = QtWidgets.QLabel('None')
                label_start_time.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                label_start_time.setAccessibleDescription('formLabel')
                label_start_time.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                label_start_time.setMinimumSize(200, 0)
                layout.addWidget(label_start_time, current_row, 1)

            if label_end_time is not None:
                layout.addWidget(label_end_time, current_row, 2)

    def save_schedules(self, frame, combo_box):
        mode = self.pushButtonScheduleSave.accessibleName()
        ScheduleModifier.save_schedules(frame, combo_box, mode)
        self.schedules = self.lab_checker.get_today_schedule()
        self.open_lab_schedules = self.lab_checker.get_today_open_lab_schedule()
        self.get_all_labs()
        self.show_room_schedule(combo_box.currentText(), mode)

        self.refresh_dashboard()

    def refresh_dashboard(self):
        self.clear_layout(self.frameEmptyRooms)
        self.clear_layout(self.frameUpcomingRooms)
        self.clear_layout(self.frameOpenLabs)
        self.clear_layout(self.frameUpcomingOpenLabs)

    ############# SETTINGS #############
    def apply_settings(self, theme, time_format):
        if theme == 'Classic Light':
            self.comboBoxSettingsTheme.setCurrentIndex(0)

            # use dark versions of icons for contrast
            self.pushButtonDashboard.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\dashboard_dark.png')))
            self.pushButtonProblems.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\problems_dark.png')))
            self.pushButtonReports.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\reports_dark.png')))
            self.pushButtonLostAndFound.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\lost_and_found_dark.png')))
            self.pushButtonAllLabs.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\all_labs_dark.png')))
            self.pushButtonSchedule.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\schedule_mod_dark.png')))
            self.pushButtonSettings.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\settings_dark.png')))
            self.pushButtonUserGuide.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\guide_dark.png')))
            self.pushButtonScheduleMod.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\schedule_mod_edit_dark.png')))
            self.pushButtonOpenLabScheduleMod.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\schedule_mod_edit_open_dark.png')))
            self.pushButtonBackupDatabase.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\database_backup_dark.png')))

            self.pushButtonFloatingAllLabs.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\new_window_light.png')))
            self.pushButtonRefreshDashboard.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\dashboard_refresh_light.png')))

        if theme == 'Centennial Dark':
            self.comboBoxSettingsTheme.setCurrentIndex(1)

            # use light versions of icons for contrast
            self.pushButtonDashboard.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\dashboard_light.png')))
            self.pushButtonProblems.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\problems_light.png')))
            self.pushButtonReports.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\reports_light.png')))
            self.pushButtonLostAndFound.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\lost_and_found_light.png')))
            self.pushButtonAllLabs.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\all_labs_light.png')))
            self.pushButtonSchedule.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\schedule_mod_light.png')))
            self.pushButtonSettings.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\settings_light.png')))
            self.pushButtonUserGuide.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\guide_light.png')))
            self.pushButtonScheduleMod.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\schedule_mod_edit_light.png')))
            self.pushButtonOpenLabScheduleMod.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\schedule_mod_edit_open_light.png')))
            self.pushButtonBackupDatabase.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\database_backup_light.png')))

            self.pushButtonFloatingAllLabs.setIcon(QtGui.QIcon(resource_path('images\\icons\\dark_theme\\new_window_dark.png')))
            self.pushButtonRefreshDashboard.setIcon(QtGui.QIcon(resource_path('images\\icons\\light_theme\\dashboard_refresh_light.png')))

        if time_format == '12 HR':
            self.comboBoxSettingsTimeFormat.setCurrentIndex(1)
        else:
            self.comboBoxSettingsTimeFormat.setCurrentIndex(0)

    def export_data_sheet(self):

        server = DatabaseHandler.get_server_string()
        db_name = DatabaseHandler.get_database_name()

        conn_str = 'Driver={SQL Server};Server=' + server + ';Database=' + db_name + ';Trusted_Connection=yes;'  # connection string
        conn_str = parse.quote_plus(conn_str)  # to stop sqlalchemy from complaining
        conn_str = 'mssql+pyodbc:///?odbc_connect=%s' % conn_str  # to stop sqlalchemy from complaining
        reports_data = read_sql_query('SELECT * FROM dbo.Reports', conn_str)
        year = str(datetime.datetime.now().year)
        path = QtWidgets.QFileDialog.getSaveFileName(QtWidgets.QFileDialog(), 'Save File', f'Reports{year}.xlsx',filter='.xlsx')[0]

        book = Workbook()  # create new workbook
        book.remove(book.active)  # remove the default sheet

        writer = ExcelWriter(path, engine='openpyxl')
        writer.book = book

        if reports_data is not None:
            reports_obj = reports_data.select_dtypes(['object'])  # get the datatypes from the result
            reports_data[reports_obj.columns] = reports_obj.apply(lambda x: x.str.strip())  # removing spaces for all columns

        lost_and_found_data = read_sql_query('SELECT * FROM dbo.LostAndFound', conn_str)

        if lost_and_found_data is not None:
            lost_and_found_obj = lost_and_found_data.select_dtypes(['object'])  # get the datatypes from the result
            lost_and_found_data[lost_and_found_obj.columns] = lost_and_found_obj.apply(lambda x: x.str.strip())  # removing spaces for all columns

        if path != '':
            try:
                reports_data.to_excel(writer, sheet_name='Reports', index=False)  # convert data frame to excel
                lost_and_found_data.to_excel(writer, sheet_name='Lost and Found', index=False)  # convert data frame to excel
                writer.save()
                writer.close()
                os.startfile(os.path.dirname(os.path.abspath(path)))  # open the folder
            except PermissionError:
                message = f'Exporting failed: Permission denied'
                info = f'If the file is open in Excel, please close it'
                self.show_message_box(message, info)

    def save_settings(self):
        theme = self.comboBoxSettingsTheme.currentText()
        time_format = self.comboBoxSettingsTimeFormat.currentText()

        output = SettingsManager.settings_theme_switch(theme)
        data = SettingsManager.get_settings()

        data['theme_choice']['name'] = output
        data['time_format'] = time_format

        SettingsManager.export_settings(data)

        self.labelSettingsWarning.setVisible(True)

    def new_log(self):
        self.lastPage = 'tableWidgetReports'
        self.clear_form()
        self.stored_id = 0
        self.labelNewLog.setText('NEW LOG')
        self.dateEditNewLog.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLog.setCurrentSectionIndex(2)
        self.change_page(self.stackedWidget, self.pageNewLog)
