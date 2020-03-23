import time
import datetime
import pandas as pd
import urllib
import qtmodern_package.windows as qtmodern_windows
import schedule_modifier
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5 import QtCore, QtWidgets, uic, QtGui
from PyQt5.QtCore import Qt
from lab_checker import LabChecker
from splash_screen import SplashScreen
from settings_manager import SettingsManager
from database_handler import DatabaseHandler

# get type from ui file
MainWindowUI, MainWindowBase = uic.loadUiType('logbook_design.ui')
DialogUI, DialogBase = uic.loadUiType('logbook_dialog.ui')


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


class Dialog(DialogBase, DialogUI):
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        self.setupUi(self)


class LogBook(MainWindowBase, MainWindowUI):
    def __init__(self, theme, time_format):
        super(LogBook, self).__init__()
        # local variables
        # self.server_string = 'DESKTOP-B2TFENN' + '\\' + 'SQLEXPRESS'  # change this to your server name

        '''Shaniquo's Laptop, DO NOT DELETE'''
        # self.server_string = 'DESKTOP-U3EO5IK\\SQLEXPRESS'
        self.server_string ='DESKTOP-SIF9RD3\\SQLEXPRESS'
        self.db_handler = DatabaseHandler('DESKTOP-SIF9RD3\\SQLEXPRESS')

        #self.server_string = 'LAPTOP-L714M249\\SQLEXPRESS'
        #self.db_handler = DatabaseHandler('LAPTOP-L714M249\\SQLEXPRESS')

        self.lastPage = ''
        self.stored_id = 0
        self.stored_theme = theme

        self.splash = SplashScreen(self.stored_theme)
        self.splash.show()
        self.splash_screen_thread = SplashScreenThread()
        self.splash_screen_thread.countChanged.connect(self.onCountChanged)  # connect this function to the custom countChanged signal from the SplashScreenThread
        self.splash_screen_thread.finished.connect(self.finished)  # connect this function to the custom finished signal from the SplashScreenThread
        self.splash_screen_thread.start()  # start the thread so it will run simultaneously with the logbook
        QtWidgets.QApplication.processEvents()  # force Qt to refresh the interface

        # using the setupUi function of the MainWindow
        self.setupUi(self)

        self.staticDate = datetime.datetime.now()

        # default date to set returned to
        self.default_returned_date = datetime.date(2020, 1, 1)

        # build a window object from the .ui file
        self.window = uic.loadUi('logbook_design.ui')

        # initialise variables that will hold object instances later
        self.lab_checker = None
        self.schedules = None
        self.open_lab_schedules = None
        self.schedule_mod = None
        self.all_rooms = None

        # add all click events
        self.addClickEvents()
        self.getAllData()
        self.apply_settings(theme['theme_name'], time_format)

        # set initial activated button
        self.pushButtonDashboard.setAccessibleDescription('menuButtonActive')
        self.labelSettingsWarning.setVisible(False)

        # fetches the qss stylesheet path
        theme_path = theme['theme_path']

        # reads the qss stylesheet and applies it to the application
        self.theme = str(open(theme_path, "r").read())

        # clears all the QT Creator styles in favour of the QSS stylesheet
        self.clearStyleSheets()
        self.setStyleSheet(self.theme)

        self.setProgressBar(100)  # set the progress bar to 100 to indicate loading is finished

        # show initial frame linked to dashboard button
        self.showLinkedFrame(self.pushButtonDashboard)

    # this function receives the data from the countChanged signal
    def onCountChanged(self, value):
        time.sleep(0.05)
        self.splash.progressBar.setValue(value)
        QtWidgets.QApplication.processEvents()  # force Qt to refresh the interface

    # this function receives the data from the finished signal
    def finished(self, value):
        time.sleep(0.1)
        self.splash.finished(value)

    def show_schedule_modifier(self):
        self.schedule_mod = schedule_modifier.ScheduleModifier(self.stored_theme)  # make a new schedule modifier instance
        self.schedule_mod = qtmodern_windows.ModernWindow(self.schedule_mod)
        self.schedule_mod.setWindowTitle('Schedule Modifier')
        self.schedule_mod.setWindowModality(QtCore.Qt.ApplicationModal)

        self.schedule_mod.btnMaximize.setParent(None)
        self.schedule_mod.btnMinimize.setParent(None)
        self.schedule_mod.btnMaximize.deleteLater()
        self.schedule_mod.btnMinimize.deleteLater()

        # center the window
        window_geometry = self.schedule_mod.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        window_geometry.moveCenter(center_point)

        self.schedule_mod.move(window_geometry.topLeft())
        self.schedule_mod.show()

    def show_dialog(self):

        dialog = Dialog()
        flags = QtCore.Qt.WindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        state = True

        yes_button = dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Yes)
        no_button = dialog.buttonBox.button(QtWidgets.QDialogButtonBox.No)

        dialog.setWindowFlags(flags)

        yes_button.setAccessibleDescription('successButton')
        no_button.setAccessibleDescription('dangerButton')

        yes_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        no_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        yes_button.setMinimumSize(100, 25)
        no_button.setMinimumSize(100, 25)

        dialog.setStyleSheet(self.theme)

        # center the window
        window_geometry_dialog = dialog.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        window_geometry_dialog.moveCenter(center_point)
        dialog.move(window_geometry_dialog.topLeft())

        if not dialog.exec_() == 1:
            state = False
        return state

    def getAllData(self):
        self.setProgressBar(20)

        months = ['All', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        # themes = ['Classic Light', 'Classic Dark', 'Centennial Light', 'Centennial Dark']
        themes = ['Classic Light', 'Centennial Dark']
        formats = ['24 HR', '12 HR']
        rooms_query = 'SELECT ROOM FROM ReportLog.dbo.Rooms'
        room_list = []

        self.populateComboBox(self.comboBoxReportsMonth, months)
        self.populateComboBox(self.comboBoxSettingsTheme, themes)
        self.populateComboBox(self.comboBoxSettingsTimeFormat, formats)

        self.lab_checker = LabChecker(self.server_string)
        self.schedules = self.lab_checker.get_today_schedule()

        self.setProgressBar(43)

        self.open_lab_schedules = self.lab_checker.get_today_open_lab_schedule()

        self.setProgressBar(70)

        cursor = self.db_handler.execute_query(rooms_query)

        # validate the cursor for empty results
        if not self.db_handler.validate_cursor(cursor):
            return

        rooms = cursor.fetchall()

        for room in rooms:
            room_list.append(room[0])

        self.all_rooms = room_list

        self.populateComboBox(self.comboBoxRoom, room_list)
        self.populateComboBox(self.comboBoxNewLostAndFoundRoom, room_list)

        self.setProgressBar(90)

        # hide the row numbers in the tables
        self.tableWidgetReports.verticalHeader().setVisible(False)
        self.tableWidgetProblems.verticalHeader().setVisible(False)
        self.tableWidgetLostAndFound.verticalHeader().setVisible(False)

        self.get_all_labs()
        self.refresh_tables()

    def get_all_labs(self):
        layout = self.scrollAreaAllLabs.widget().layout()

        if self.all_rooms is not None and range(len(self.all_rooms) != 0):

            for room in self.all_rooms:  # loop through all rooms
                current_row = layout.rowCount()  # next row (since the count starts at 0)
                label_times = None

                # label creation
                label_room = QtWidgets.QLabel(room.strip())
                label_room.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                label_room.setAccessibleDescription('formLabel')
                label_room.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                label_room.setMinimumSize(0, 30)
                label_room.setMaximumSize(100, 100)

                # adding to layout
                layout.addWidget(label_room, current_row, 0)

                if self.schedules is not None and range(len(self.schedules) != 0):  # not empty validation
                    for schedule in self.schedules:  # loop through all schedules
                        if schedule.get_room().strip() == room.strip():

                            if label_times is not None:
                                label_times.setText(label_times.text() + '\n' + schedule.get_start_time())
                            else:
                                # label creation
                                label_times = QtWidgets.QLabel(schedule.get_start_time())
                                label_times.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                                label_times.setAccessibleDescription('formLabel')
                                label_times.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                                label_times.setMinimumSize(200, 0)
                                label_times.setMaximumSize(100, 100)

                    if label_times is not None:
                        layout.addWidget(label_times, current_row, 1)
                    else:
                        label_times = QtWidgets.QLabel('No open times')
                        label_times.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                        label_times.setAccessibleDescription('formLabel')
                        label_times.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                        label_times.setMinimumSize(200, 0)
                        label_times.setMaximumSize(100, 100)
                        layout.addWidget(label_times, current_row, 1)

    def setProgressBar(self, value):
        self.splash_screen_thread.count = value
        QtWidgets.QApplication.processEvents()  # force Qt to refresh the interface

    # if you want to test something else and get a database error comment out this function and the function call(I'll do exception handling later lol)
    def populateTable(self, table, query, tProblems=None):

        table.clear()
        table.setSortingEnabled(False)  # this is necessary to avoid confusing the table widget (blank rows)

        # new array variables for holding column names
        header_names = []

        cursor = self.db_handler.execute_query(query)

        # validate the cursor for empty results
        if not self.db_handler.validate_cursor(cursor):
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

        if tProblems and tProblems is not None:
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

    def populateComboBox(self, comboBox, items):
        comboBox.clear()
        comboBox.setView(QtWidgets.QListView())
        comboBox.addItems(items)
        comboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)

    # clears all the QT Creator styles in favour of the QSS stylesheet
    def clearStyleSheets(self):
        widget_child = self.centralwidget.findChildren(QtWidgets.QWidget)

        for widget in widget_child:
            widget.setStyleSheet('')

    # use the button's name to find the linked frame (deliberately named this way)
    def showLinkedFrame(self, member):
        search = str(member.objectName()).replace('pushButton', '')

        for widget in self.stackedWidget.children():
            if search in widget.objectName():
                self.change_page(widget)

    # this function loops through the buttons in the menu to find the active QPushButton and set it to the active colour (green)
    def button_pressed(self):
        # look through the children of the children until we find a QPushButton
        for widget in self.frameMenu.children():
            self.isPushButton(widget)  # check for push buttons and update them
            for frame in widget.children():
                self.isPushButton(frame)  # check for push buttons and update them
                for member in frame.children():
                    self.isPushButton(member)  # check for push buttons and update them

    def isPushButton(self, member):
        # if object is a QPushButton
        if isinstance(member, QtWidgets.QPushButton):

            # if the button that called this function is the same as the member encountered:
            if member.objectName() == self.sender().objectName():

                # change button's colour to active green
                member.setAccessibleDescription('menuButtonActive')

                # use the button's name to find the linked frame (deliberately named this way)
                self.showLinkedFrame(member)
                member.setStyleSheet('')  # force a stylesheet refresh (faster than reapplying the style sheet)

            else:
                # set all other buttons' colour to white
                member.setAccessibleDescription('menuButton')
                member.setStyleSheet('')  # force a stylesheet refresh (faster than reapplying the style sheet)

    # add all click events
    def addClickEvents(self):
        self.pushButtonSchedule.clicked.connect(self.show_schedule_modifier)

        # reports
        self.pushButtonNew.clicked.connect(self.new_log)
        self.pushButtonFormCancel.clicked.connect(self.change_to_last_page)
        self.pushButtonExportData.clicked.connect(self.export_data_sheet)
        self.pushButtonEditReports.clicked.connect(lambda: self.edit_log(self.tableWidgetReports))
        self.comboBoxReportsMonth.currentIndexChanged.connect(lambda: self.sort_by_month(None))

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
        self.pushButtonFormCancelLAF.clicked.connect(lambda: self.change_page(self.pageLostAndFound))
        self.pushButtonFormSaveLAF.clicked.connect(self.save_lost_and_found_form)

        # self.pushButtonRefreshLAF.clicked.connect(self.refreshTables)
        self.pushButtonDeleteLAF.clicked.connect(lambda: self.delete_selection(self.tableWidgetLostAndFound, 'LostAndFound'))
        self.checkBoxNewLostAndFoundReturned.clicked.connect(self.returned_checkbox_changed)

        # save settings signal
        self.pushButtonSaveSettings.clicked.connect(self.save_settings)

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
                data_widget = None

                if replaced == 'NOTE' or replaced == 'RESOLUTION':
                    data_widget = QtWidgets.QTextEdit(f"{data[j]}")
                    data_widget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                    data_widget.setAccessibleDescription('textEdit')
                    data_widget.setReadOnly(True)
                    data_widget.setTextInteractionFlags(Qt.NoTextInteraction)
                    data_widget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
                    data_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                    data_widget.setAcceptRichText(False)
                    data_widget.document().setDocumentMargin(0)
                else:
                    data_widget = QtWidgets.QLabel(f"{data[j]}")
                    data_widget.setScaledContents(True)
                    data_widget.setWordWrap(True)
                    data_widget.setAccessibleDescription('formLabelNormal')
                    data_widget.setAlignment(Qt.AlignLeft | Qt.AlignTop)

                data_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                data_widget.setMaximumSize(500, 150)

                label_widget = QtWidgets.QLabel(f"{replaced}:")
                label_widget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                label_widget.setAccessibleDescription('formLabel')
                label_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                label_widget.setMinimumSize(200, 0)
                label_widget.setMaximumSize(500, 100)

                self.frameViewDataForm.layout().addRow(label_widget, data_widget)

            # change to view page
            self.change_page(self.pageViewData)

    def delete_selection(self, table, table_name):

        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1 and table.item(0, 0) is not None:
            if self.show_dialog():
                row_index = table.currentRow()  # get index of current row
                column_index = table.item(row_index, 0).text()
                first_column = self.db_handler.execute_query(f"SELECT column_name from information_schema.columns where table_name = '{table_name}' and ordinal_position = 1").fetchone()
                delete_query = f'DELETE FROM dbo.{table_name} WHERE {str(first_column[0])} = {column_index};'
                self.db_handler.execute_query(delete_query).commit()
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

    def new_lost_and_found(self):
        self.stored_id = 0
        self.clear_lost_and_found_form()
        self.dateEditNewLostAndFound.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLostAndFound.setCurrentSectionIndex(2)
        self.dateEditReturnedNewLostAndFound.setDate(self.default_returned_date)

        self.frameReturnedLAF.hide()
        self.refresh_tables()
        self.change_page(self.pageNewLAF)

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
            returned_date = self.dateEditReturnedNewLostAndFound.date().toString('yyyy-MM-dd')
            student_name = self.textBoxNewLostAndFoundStudentName.text()
            student_number = self.textBoxNewLostAndFoundStudentNumber.text()

            if self.checkBoxNewLostAndFoundReturned.isChecked():
                returned = 'YES'
                query = f'''
                            INSERT INTO dbo.LostAndFound
                                (DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,STUDENT_NAME,STUDENT_NUMBER,RETURNED_DATE,RETURNED) 
                            VALUES 
                                (?, ?, ?, ?, ?, ?, ?, ?, ?)'''

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

        cursor = self.db_handler.execute_query(query, list_objects)

        # validate the cursor for empty results
        if not self.db_handler.validate_cursor(cursor):
            self.change_to_last_page()
            return

        cursor.commit()
        self.refresh_tables()
        self.change_page(self.pageLostAndFound)

    def edit_laf_form(self):
        table = self.tableWidgetLostAndFound

        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1 and table.item(0, 0) is not None:
            row_index = table.currentRow()  # get index of current row
            entry_id = table.item(row_index, 0).text()
            self.stored_id = entry_id

            query = f'SELECT DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,STUDENT_NAME,STUDENT_NUMBER,RETURNED_DATE,RETURNED FROM dbo.LostAndFound WHERE ENTRY_ID = {entry_id};'
            cursor = self.db_handler.execute_query(query)

            # validate the cursor for empty results
            if not self.db_handler.validate_cursor(cursor):
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

            self.change_page(self.pageNewLAF)

    def show_frame_returned_laf(self):
        if self.checkBoxNewLostAndFoundReturned.isChecked():
            self.frameReturnedLAF.show()
        else:
            self.frameReturnedLAF.hide()

    def returned_checkbox_changed(self):  # this way it only happens if the state was changed
        if self.checkBoxNewLostAndFoundReturned.isChecked():
            self.dateEditReturnedNewLostAndFound.setDate(QtCore.QDate.currentDate())
            self.dateEditReturnedNewLostAndFound.setCurrentSectionIndex(2)

        self.show_frame_returned_laf()

    # limit the amount of characters allowed in a QTextEdit
    @staticmethod
    def max_txt_input(txt_edit):
        text_content = txt_edit.toPlainText()
        length = len(text_content)

        max_length = 1000

        if length > max_length:
            position = txt_edit.textCursor().position()
            text_cursor = txt_edit.textCursor()
            text_content = text_content[:max_length]
            txt_edit.setText(text_content)
            text_cursor.setPosition(position - (length - max_length))
            txt_edit.setTextCursor(text_cursor)

    def change_to_last_page(self):
        # remove the 'tableWidget' from the string (this is why everything is named this way lol)
        name = self.lastPage.replace('tableWidget', '')
        page_name = 'page' + name  # add page to the modified string
        self.change_page(self.findChild(QtWidgets.QWidget, page_name))  # change to last page

    def change_page(self, name):
        widget = name

        # if the widget is in the stackedWidget
        if self.stackedWidget.indexOf(widget) != -1:
            self.stackedWidget.setCurrentIndex(self.stackedWidget.indexOf(widget))  # change the page to the widget

    @staticmethod
    def validate_field(text_edit):
        if text_edit.text() == '':
            text_edit.setPlaceholderText('Cannot be blank')
            return False
        return True

    def refresh_tables(self):
        import calendar
        month = calendar.month_name[datetime.datetime.now().month]  # converting the month number to a string
        index = self.comboBoxReportsMonth.findText(month)
        if index >= 0:
            self.comboBoxReportsMonth.setCurrentIndex(index)

        reports_query = f"SELECT * FROM dbo.Reports WHERE MONTH(DATE) = (SELECT MONTH('{month}' + '2020'))"
        problems_query = 'SELECT REPORT_ID, DATE, NAME, ROOM,ISSUE,NOTE FROM ReportLog.dbo.Reports WHERE FIXED =\'NO\''
        lost_and_found_query = 'SELECT * FROM ReportLog.dbo.LostAndFound'
        problems_count_query = 'SELECT COUNT(REPORT_ID) FROM ReportLog.dbo.Reports WHERE FIXED =\'NO\''
        problems_room_query = 'SELECT DISTINCT(ROOM) FROM ReportLog.dbo.Reports WHERE FIXED =\'NO\''

        self.populateTable(self.tableWidgetReports, reports_query)
        self.populateTable(self.tableWidgetProblems, problems_query, True)
        self.populateTable(self.tableWidgetLostAndFound, lost_and_found_query)

        self.cleanup_empty_cells(self.tableWidgetReports)
        self.cleanup_empty_cells(self.tableWidgetProblems)
        self.cleanup_empty_cells(self.tableWidgetLostAndFound)

        cursor = self.db_handler.execute_query(problems_count_query)
        room_cursor = self.db_handler.execute_query(problems_room_query)

        # validate the cursor for empty results
        if not (self.db_handler.validate_cursor(cursor) and self.db_handler.validate_cursor(room_cursor)):
            return

        self.labelNumberProblems.setText(str(cursor.fetchone()[0]))

        # show the rooms with all the problems
        room_problems = room_cursor.fetchall()
        room_list_problems = []
        for room in room_problems:
            room_list_problems.append(room[0])

        #self.labelRoomProblems.setText('\n'.join(room_list_problems))

    @staticmethod
    def cleanup_empty_cells(table):
        if table.item(0, 0) is None:
            table.clear()
            table.setRowCount(0)

    def sort_by_month(self, input_month=None):  # setting an optional argument to null since python has no overloading
        if input_month is not None:
            query = f"SELECT * FROM dbo.Reports WHERE MONTH(DATE) = (SELECT MONTH('{input_month}' + '2020'))"
        else:
            month = self.sender().currentText()  # receive the combobox's current text
            if month == 'All':
                query = f"SELECT * FROM dbo.Reports"
            else:
                query = f"SELECT * FROM dbo.Reports WHERE MONTH(DATE) = (SELECT MONTH('{month}' + '2020'))"
        self.populateTable(self.tableWidgetReports, query)
        self.cleanup_empty_cells(self.tableWidgetReports)

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

        cursor = self.db_handler.execute_query(query, list_objects)

        # validate the cursor for empty results
        if not self.db_handler.validate_cursor(cursor):
            self.change_page(self.pageReports)
            return

        cursor.commit()

        self.refresh_tables()
        self.change_to_last_page()
        self.clear_form()

    def edit_log(self, table):
        self.lastPage = table.objectName()

        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1 and table.item(0, 0) is not None:
            row_index = table.currentRow()  # get index of current row
            report_id = table.item(row_index, 0).text()
            self.stored_id = report_id

            query = f'SELECT DATE, NAME, ROOM, ISSUE, NOTE, RESOLUTION, FIXED from dbo.Reports WHERE REPORT_ID = {report_id};'
            cursor = self.db_handler.execute_query(query)

            # validate the cursor for empty results
            if not self.db_handler.validate_cursor(cursor):
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

            self.change_page(self.pageNewLog)

    def apply_settings(self, theme, time_format):
        if theme == "Classic Light":
            self.comboBoxSettingsTheme.setCurrentIndex(0)

        if theme == "Classic Dark":
            self.comboBoxSettingsTheme.setCurrentIndex(1)

        if theme == "Centennial Light":
            self.comboBoxSettingsTheme.setCurrentIndex(2)

        if theme == "Centennial Dark":
            self.comboBoxSettingsTheme.setCurrentIndex(1)
            # self.comboBoxSettingsTheme.setCurrentIndex(3)

        if time_format == "12 HR":
            self.comboBoxSettingsTimeFormat.setCurrentIndex(1)
        else:
            self.comboBoxSettingsTimeFormat.setCurrentIndex(0)

    def save_settings(self):
        theme = self.comboBoxSettingsTheme.currentText()
        time_format = self.comboBoxSettingsTimeFormat.currentText()

        output = SettingsManager.settings_theme_switch(theme)
        data = SettingsManager.import_settings()

        data['theme_choice']['name'] = output
        data['time_format'] = time_format

        SettingsManager.export_settings(data)
        '''with open("settings.json", "w") as jsonFile:
            json.dump(data, jsonFile, indent=2)'''

        self.labelSettingsWarning.setVisible(True)

    def export_data_sheet(self):

        server = self.server_string

        conn_str = 'Driver={SQL Server};Server=' + server + ';Database=ReportLog;Trusted_Connection=yes;'  # connection string
        conn_str = urllib.parse.quote_plus(conn_str)  # to stop sqlalchemy from complaining
        conn_str = "mssql+pyodbc:///?odbc_connect=%s" % conn_str  # to stop sqlalchemy from complaining
        data = pd.read_sql_query('SELECT * FROM dbo.Reports', conn_str)

        data_obj = data.select_dtypes(['object'])
        data[data_obj.columns] = data_obj.apply(lambda x: x.str.strip())

        # data.columns.apply(lambda x: x.str.strip())

        test = str(datetime.datetime.now().year)
        data.to_excel(f'Reports{test}.xlsx')

    def new_log(self):
        self.lastPage = 'tableWidgetReports'
        self.clear_form()
        self.stored_id = 0
        self.labelNewLog.setText('NEW LOG')
        self.dateEditNewLog.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLog.setCurrentSectionIndex(2)
        self.change_page(self.pageNewLog)

    # for handling creation and deletion of labels for labs that are soon going to be vacant
    def countdown_handler(self):
        if self.schedules is not None and range(len(self.schedules) != 0):
            for i in range(len(self.schedules)):  # loop through all of today's schedules
                countdown = self.lab_checker.room_countdown(self.schedules[i])  # calculate the countdown using the current schedule object
                room_name = self.schedules[i].get_room().strip()  # get the room name for label
                search = room_name + str(i)  # room name + i (for multiple open times in the same room)

                # countdown = (datetime.timedelta(seconds=5) + self.staticDate) - datetime.datetime.now()  # for testing
                if countdown is not None and countdown < datetime.timedelta(hours=3):  # only show countdown if it's not empty and 2 hours away
                    label = room_name + '         ' + 'In: ' + str(countdown)  # text for the label
                    if self.frameUpcomingRooms.findChild(QtWidgets.QLabel, search) is None:  # check to see if the widget exists already
                        label_upcoming = QtWidgets.QLabel(label, self)  # create a new checkbox and append the room name + countdown
                        label_upcoming.setAccessibleDescription('checkBoxRoom')  # add tag for qss styling
                        label_upcoming.setObjectName(search)  # set the object name so it's searchable later
                        label_upcoming.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                        self.frameUpcomingRooms.layout().addWidget(label_upcoming)  # add the checkbox to the frame
                    else:  # the widget exists already so just update it
                        self.frameUpcomingRooms.findChild(QtWidgets.QLabel, search).setText(label)

                    if countdown <= datetime.timedelta(seconds=1):  # countdown expired, so hide and remove the widget
                        self.frameUpcomingRooms.findChild(QtWidgets.QLabel, search).setVisible(False)
                        self.frameUpcomingRooms.findChild(QtWidgets.QLabel, search).deleteLater()

        if self.open_lab_schedules is not None and range(len(self.open_lab_schedules) != 0):
            for i in range(len(self.open_lab_schedules)):  # loop through all of today's schedules
                countdown = self.lab_checker.room_countdown(self.open_lab_schedules[i])  # calculate the countdown using the current schedule object
                room_name = self.open_lab_schedules[i].get_room().strip()  # get the room name for label
                search = room_name + str(i)  # room name + i (for multiple open times in the same room)

                # countdown = (datetime.timedelta(seconds=5) + self.staticDate) - datetime.datetime.now()  # for testing
                if countdown is not None:  # only show countdown if it's not empty
                    label = room_name + '         ' + 'In: ' + str(countdown)  # text for the label
                    if self.frameUpcomingOpenLabs.findChild(QtWidgets.QLabel, search) is None:  # check to see if the widget exists already
                        label_upcoming = QtWidgets.QLabel(label, self)  # create a new checkbox and append the room name + countdown
                        label_upcoming.setAccessibleDescription('checkBoxRoom')  # add tag for qss styling
                        label_upcoming.setObjectName(search)  # set the object name so it's searchable later
                        label_upcoming.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                        self.frameUpcomingOpenLabs.layout().addWidget(label_upcoming)  # add the checkbox to the frame
                    else:  # the widget exists already so just update it
                        self.frameUpcomingOpenLabs.findChild(QtWidgets.QLabel, search).setText(label)
                        if countdown < datetime.timedelta(minutes=30):
                            if countdown.seconds % 2 == 0:
                                self.frameUpcomingOpenLabs.findChild(QtWidgets.QLabel, search).setAccessibleDescription('timerDanger')
                            else:
                                self.frameUpcomingOpenLabs.findChild(QtWidgets.QLabel, search).setAccessibleDescription('checkBoxRoom')
                            self.frameUpcomingOpenLabs.findChild(QtWidgets.QLabel, search).setStyleSheet('')  # force a stylesheet refresh (faster than reapplying the style sheet)

                    if countdown <= datetime.timedelta(seconds=1):  # countdown expired, so hide and remove the widget
                        self.frameUpcomingOpenLabs.findChild(QtWidgets.QLabel, search).setVisible(False)
                        self.frameUpcomingOpenLabs.findChild(QtWidgets.QLabel, search).deleteLater()

    # for handling creation and deletion of checkboxes for labs that are vacant
    def duration_handler(self):

        if self.schedules is not None and range(len(self.schedules) != 0):  # ensuring we're not looping an empty list
            for i in range(len(self.schedules)):  # loop through all of today's schedules
                countdown = self.lab_checker.calculate_duration(self.schedules[i])  # calculate the countdown using the current schedule object
                room_name = self.schedules[i].get_room().strip()  # get the room name for label
                search = room_name + 'duration' + str(i)  # room name + i (for multiple open times in the same room)

                # countdown = (datetime.timedelta(seconds=2230) + self.staticDate) - datetime.datetime.now()  # for testing (will countdown from 30 seconds)
                if countdown is not None:
                    label = room_name + '         ' + 'Vacant for: ' + str(countdown)

                    if self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search) is None:  # check to see if the widget exists already
                        checkBox = QtWidgets.QCheckBox(label, self)  # create a new checkbox and append the room name + countdown
                        checkBox.setAccessibleDescription('checkBoxRoom')  # add tag for qss styling
                        checkBox.setObjectName(search)
                        checkBox.stateChanged.connect(self.remove_countdown)
                        checkBox.setAccessibleName(str(self.schedules[i].get_schedule_id()))  # to link the schedule ID
                        self.frameEmptyRooms.layout().addWidget(checkBox)  # add the checkbox to the frame

                    else:  # if the widget exists already, update it

                        self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setText(label)
                        if countdown < datetime.timedelta(minutes=30):
                            if countdown.seconds % 2 == 0:
                                self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setAccessibleDescription('timerDanger')
                            else:
                                self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setAccessibleDescription('checkBoxRoom')
                            self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setStyleSheet('')  # force a stylesheet refresh (faster than reapplying the style sheet)

                    if countdown <= datetime.timedelta(seconds=1):  # countdown expired, so remove the widget
                        self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setVisible(False)
                        self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).deleteLater()

        # open labs
        if self.open_lab_schedules is not None and range(len(self.open_lab_schedules) != 0):
            for i in range(len(self.open_lab_schedules)):  # loop through all of today's schedules
                countdown = self.lab_checker.calculate_duration(self.open_lab_schedules[i])  # calculate the countdown using the current schedule object
                room_name = self.open_lab_schedules[i].get_room().strip()  # get the room name for label
                search = room_name + str(i)  # room name + i (for multiple open times in the same room)

                # countdown = (datetime.timedelta(seconds=5) + self.staticDate) - datetime.datetime.now()  # for testing
                if countdown is not None:  # only show countdown if it's not empty
                    label = room_name + '         ' + str(countdown)  # text for the label
                    if self.frameOpenLabs.findChild(QtWidgets.QLabel, search) is None:  # check to see if the widget exists already
                        label_duration = QtWidgets.QLabel(label, self)  # create a new label and append the room name + countdown
                        label_duration.setAccessibleDescription('checkBoxRoom')  # add tag for qss styling
                        label_duration.setObjectName(search)  # set the object name so it's searchable later
                        label_duration.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                        self.frameOpenLabs.layout().addWidget(label_duration)  # add the checkbox to the frame
                    else:  # the widget exists already so just update it
                        self.frameOpenLabs.findChild(QtWidgets.QLabel, search).setText(label)

                    if countdown <= datetime.timedelta(seconds=1):  # countdown expired, so hide and remove the widget
                        self.frameOpenLabs.findChild(QtWidgets.QLabel, search).setVisible(False)
                        self.frameOpenLabs.findChild(QtWidgets.QLabel, search).deleteLater()

    def remove_countdown(self):
        for schedule in self.schedules:
            if schedule.get_schedule_id() == int(self.sender().accessibleName()):  # if the schedule ID is the same as the sender's accessibleName field
                schedule.set_end_time(datetime.datetime.now().time().isoformat(timespec='seconds'))  # expire the time

        self.sender().setVisible(False)  # hide the widget
        self.sender().deleteLater()  # schedule the widget for deletion

    def Clock(self):  # this function is called every second during runtime
        t = time.localtime()  # local system time
        d = datetime.date.today()  # local system date
        t_format_24hr = "%H:%M:%S"
        t_format_12hr = "%I:%M:%S %p"

        # convert time to string format
        time_convert = time.strftime(t_format_24hr, t)

        if self.comboBoxSettingsTimeFormat.currentText() == '12 HR':
            time_convert = time.strftime(t_format_12hr, t)

        # current time
        self.labelCurrentTime.setText(time_convert)

        # assign labels with current time and date
        self.labelCurrentDate.setText(d.strftime("%B %d, %Y"))
        self.labelCurrentDate2.setText(d.strftime("%B %d, %Y"))
        self.labelCurrentDate3.setText(d.strftime("%B %d, %Y"))

        # call the handlers for the countdowns
        self.countdown_handler()
        self.duration_handler()
