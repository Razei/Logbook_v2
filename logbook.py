import json
import time
import datetime
import pyodbc
import pandas as pd
import urllib
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import Qt
from lab_checker import labChecker

# get type from ui file
MainWindowUI, MainWindowBase = uic.loadUiType('logbook_design.ui')
DialogUI, DialogBase = uic.loadUiType('logbook_dialog.ui')


class Dialog(DialogBase, DialogUI):
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        self.setupUi(self)


class LogBook(MainWindowBase, MainWindowUI):
    def __init__(self, theme, time_format):
        super(LogBook, self).__init__()
        # local variables
        self.server_string = 'DESKTOP-B2TFENN' + '\\' + 'SQLEXPRESS'  # change this to your server name

        '''Shaniquo's Laptop, DO NOT DELETE'''
        # self.server_string = 'DESKTOP-U3EO5IK\\SQLEXPRESS'
        # self.server_string = 'LAPTOP-L714M249\\SQLEXPRESS'
        self.lastPage = ''
        self.stored_id = 0

        # using the default setupUi function of the super class
        self.setupUi(self)

        self.staticDate = datetime.datetime.now()
        self.default_returned_date = datetime.date(2020, 1, 1)

        # build a window object from the .ui file
        self.window = uic.loadUi('logbook_design.ui')

        # new lab checker object
        self.lab_checker = None
        self.schedules = None
        self.open_lab_schedules = None

        # add all click events
        self.addClickEvents()
        self.getAllData()

        # self.getAllData()
        self.set_settings(theme['theme_name'], time_format)

        # set initial activated button
        self.pushButtonDashboard.setAccessibleDescription('menuButtonActive')
        self.labelSettingsWarning.setVisible(False)

        # temporarily disabled
        self.pushButtonAllLabs.setVisible(False)
        self.pushButtonSchedule.setVisible(False)
        self.pushButtonUserGuide.setVisible(False)

        # fetches the qss stylesheet path
        theme_path = theme['theme_path']

        # reads the qss stylesheet and applies it to the application
        self.theme = str(open(theme_path, "r").read())

        # clears all the QT Creator styles in favour of the QSS stylesheet
        self.clearStyleSheets()
        self.setStyleSheet(self.theme)

        # show initial frame linked to dashboard button
        self.showLinkedFrame(self.pushButtonDashboard)

    def showDialog(self):

        dialog = Dialog()
        flags = QtCore.Qt.WindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        state = True

        dialog.setWindowFlags(flags)
        dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Yes).setAccessibleDescription('successButton')
        dialog.buttonBox.button(QtWidgets.QDialogButtonBox.No).setAccessibleDescription('dangerButton')

        dialog.buttonBox.button(QtWidgets.QDialogButtonBox.Yes).setMinimumSize(100, 25)
        dialog.buttonBox.button(QtWidgets.QDialogButtonBox.No).setMinimumSize(100, 25)

        dialog.setStyleSheet(self.theme)

        # center the window
        windowGeometryDialog = dialog.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        windowGeometryDialog.moveCenter(centerPoint)
        dialog.move(windowGeometryDialog.topLeft())

        if not dialog.exec_() == 1:
            state = False
        return state

    @staticmethod
    def validateCursor(cursor):
        if cursor is None or cursor.rowcount == 0:
            return False

        return True

    # reusable query function
    def executeQuery(self, query, list_objects=None):

        # conn_str ='Trusted_Connection=yes;DRIVER={ODBC Driver 17 for SQL Server};SERVER='+self.server_string+';DATABASE=ReportLog;UID=Helpdesk;PWD=b1pa55'
        # conn_str = 'Driver={SQL Server};Server='+ self.server_string + ';Database=ReportLog;Trusted_Connection=yes;'
        # connect with 5 second timeout
        try:
            conn_str = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}', host=self.server_string,
                                      database='ReportLog', timeout=2,
                                      trusted_connection='Yes')  # user='Helpdesk', password='b1pa55'
            conn = conn_str
            cursor = conn.cursor()

            if list_objects is not None:
                cursor.execute(query, list_objects)
            else:
                cursor.execute(query)

            return cursor
        except pyodbc.Error as err:
            print("Couldn't connect (Connection timed out)")
            print(err)
            return

    def getAllData(self):
        months = ['All', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        # themes = ['Classic Light', 'Classic Dark', 'Centennial Light', 'Centennial Dark']
        themes = ['Classic Light', 'Centennial Dark']
        formats = ['24 HR', '12 HR']
        rooms_query = 'SELECT ROOM FROM ReportLog.dbo.Rooms'
        room_list = []

        self.populateComboBox(self.comboBoxReportsMonth, months)
        self.populateComboBox(self.comboBoxSettingsTheme, themes)
        self.populateComboBox(self.comboBoxSettingsTimeFormat, formats)

        self.lab_checker = labChecker(self.server_string)
        self.schedules = self.lab_checker.getTodaySchedule()
        self.open_lab_schedules = self.lab_checker.getTodayOpenLabSchedule()

        cursor = self.executeQuery(rooms_query)

        # validate the cursor for empty results
        if not self.validateCursor(cursor):
            return

        rooms = cursor.fetchall()

        for room in rooms:
            room_list.append(room[0])

        self.populateComboBox(self.comboBoxRoom, room_list)
        self.populateComboBox(self.comboBoxNewLostAndFoundRoom, room_list)

        # hide the row numbers in the tables
        self.tableWidgetReports.verticalHeader().setVisible(False)
        self.tableWidgetProblems.verticalHeader().setVisible(False)
        self.tableWidgetLostAndFound.verticalHeader().setVisible(False)

        self.refreshTables()

    # if you want to test something else and get a database error comment out this function and the function call(I'll do exception handling later lol)
    def populateTable(self, table, query, tProblems=None):

        table.clear()
        table.setSortingEnabled(False)  # this is necessary to avoid confusing the table widget (blank rows)

        # new array variables for holding column names
        header_names = []

        cursor = self.executeQuery(query)

        # validate the cursor for empty results
        if not self.validateCursor(cursor):
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
                member.setStyleSheet('')  # force a stylesheet recalculation (faster than reapplying the style sheet)

            else:
                # set all other buttons' colour to white
                member.setAccessibleDescription('menuButton')
                member.setStyleSheet('')  # force a stylesheet recalculation (faster than reapplying the style sheet)

    # add all click events
    def addClickEvents(self):

        # reports
        self.pushButtonNew.clicked.connect(self.newLog)
        self.pushButtonFormCancel.clicked.connect(lambda: self.change_to_last_page())
        self.pushButtonExportData.clicked.connect(self.exportData)
        self.pushButtonEditReports.clicked.connect(lambda: self.edit_log(self.tableWidgetReports))
        self.comboBoxReportsMonth.currentIndexChanged.connect(lambda: self.sort_by_month(None))

        # problems
        # self.pushButtonRefreshProblems.clicked.connect(self.refreshTables)
        self.pushButtonDelete.clicked.connect(lambda: self.deleteSelection(self.tableWidgetReports, 'Reports'))
        self.pushButtonProblemsFixed.clicked.connect(lambda: self.edit_log(self.tableWidgetProblems))
        self.pushButtonReportsView.clicked.connect(lambda: self.viewSelection(self.tableWidgetReports))
        self.pushButtonProblemsView.clicked.connect(lambda: self.viewSelection(self.tableWidgetProblems))
        self.pushButtonViewDataBack.clicked.connect(self.change_to_last_page)

        # new log
        self.pushButtonFormSave.clicked.connect(self.saveNewLog)
        self.pushButtonFormClear.clicked.connect(self.clearForm)
        self.textBoxNewLogNote.textChanged.connect(lambda: self.txtInputChanged(self.textBoxNewLogNote))
        self.textBoxNewLogResolution.textChanged.connect(lambda: self.txtInputChanged(self.textBoxNewLogResolution))
        self.textBoxNewLostAndFoundNote.textChanged.connect(lambda: self.txtInputChanged(self.textBoxNewLostAndFoundNote))

        # lost and found
        self.pushButtonViewLAF.clicked.connect(lambda: self.viewSelection(self.tableWidgetLostAndFound))
        self.pushButtonNewLAF.clicked.connect(self.newLostAndFound)
        self.pushButtonEditLAF.clicked.connect(self.edit_laf_form)
        self.pushButtonFormClearLAF.clicked.connect(self.clearLostAndFoundForm)
        self.pushButtonFormCancelLAF.clicked.connect(lambda: self.change_page(self.pageLostAndFound))
        self.pushButtonFormSaveLAF.clicked.connect(self.saveLostAndFoundForm)

        # self.pushButtonRefreshLAF.clicked.connect(self.refreshTables)
        self.pushButtonDeleteLAF.clicked.connect(lambda: self.deleteSelection(self.tableWidgetLostAndFound, 'LostAndFound'))
        self.checkBoxNewLostAndFoundReturned.clicked.connect(self.returned_checkbox_changed)

        # save settings signal
        self.pushButtonSaveSettings.clicked.connect(lambda: self.save_settings())

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

    def clearForm(self):
        self.dateEditNewLog.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLog.setCurrentSectionIndex(2)
        self.textBoxNewLogIssue.setText('')
        self.textBoxNewLogNote.setText('')
        self.textBoxNewLogName.setText('')
        self.checkBoxFixed.setCheckState(False)
        self.textBoxNewLogResolution.setText('')
        self.comboBoxRoom.setCurrentIndex(0)

    def newLostAndFound(self):
        self.stored_id = 0
        self.clearLostAndFoundForm()
        self.dateEditNewLostAndFound.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLostAndFound.setCurrentSectionIndex(2)
        self.dateEditReturnedNewLostAndFound.setDate(self.default_returned_date)

        self.frameReturnedLAF.hide()
        self.refreshTables()
        self.change_page(self.pageNewLAF)

    def clearLostAndFoundForm(self):
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
        self.showFrameReturnedLAF()

    def saveLostAndFoundForm(self):
        date = self.dateEditNewLostAndFound.date().toString('yyyy-MM-dd')
        room = self.comboBoxNewLostAndFoundRoom.currentText()
        found_by = self.textBoxNewLostAndFoundBy.text()
        item_description = self.textBoxNewLostAndFoundItemDescription.text()
        note = self.textBoxNewLostAndFoundNote.toPlainText()
        list_objects = None
        state = True

        # empty field validation
        if not (self.validateField(self.textBoxNewLostAndFoundBy)):
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

        cursor = self.executeQuery(query, list_objects)

        # validate the cursor for empty results
        if not self.validateCursor(cursor):
            self.change_to_last_page()
            return

        cursor.commit()
        self.refreshTables()
        self.change_page(self.pageLostAndFound)

    def edit_laf_form(self):
        table = self.tableWidgetLostAndFound

        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1 and table.item(0, 0) is not None:
            row_index = table.currentRow()  # get index of current row
            entry_id = table.item(row_index, 0).text()
            self.stored_id = entry_id

            query = f'SELECT DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,STUDENT_NAME,STUDENT_NUMBER,RETURNED_DATE,RETURNED FROM dbo.LostAndFound WHERE ENTRY_ID = {entry_id};'
            cursor = self.executeQuery(query)

            # validate the cursor for empty results
            if not self.validateCursor(cursor):
                self.change_to_last_page()
                return

            laf = cursor.fetchall()
            self.clearForm()
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
                self.showFrameReturnedLAF()
            else:
                self.checkBoxNewLostAndFoundReturned.setChecked(False)
                self.showFrameReturnedLAF()

            self.change_page(self.pageNewLAF)

    def showFrameReturnedLAF(self):
        if self.checkBoxNewLostAndFoundReturned.isChecked():
            self.frameReturnedLAF.show()
        else:
            self.frameReturnedLAF.hide()

    def returned_checkbox_changed(self):  # this way it only happens if the state was changed
        if self.checkBoxNewLostAndFoundReturned.isChecked():
            self.dateEditReturnedNewLostAndFound.setDate(QtCore.QDate.currentDate())
            self.dateEditReturnedNewLostAndFound.setCurrentSectionIndex(2)

        self.showFrameReturnedLAF()

    def viewSelection(self, table):

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

    # limit the amount of characters allowed in a QTextEdit
    def txtInputChanged(self, txtEdit):
        text_content = txtEdit.toPlainText()
        length = len(text_content)

        max_length = 1000

        if length > max_length:
            position = txtEdit.textCursor().position()
            text_cursor = txtEdit.textCursor()
            text_content = text_content[:max_length]
            txtEdit.setText(text_content)
            text_cursor.setPosition(position - (length - max_length))
            txtEdit.setTextCursor(text_cursor)


    def deleteSelection(self, table, table_name):

        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1 and table.item(0, 0) is not None:
            if self.showDialog():
                row_index = table.currentRow()  # get index of current row
                column_index = table.item(row_index, 0).text()
                first_column = self.executeQuery(f"SELECT column_name from information_schema.columns where table_name = '{table_name}' and ordinal_position = 1").fetchone()
                delete_query = f'DELETE FROM dbo.{table_name} WHERE {str(first_column[0])} = {column_index};'
                self.executeQuery(delete_query).commit()
                self.refreshTables()

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
    def validateField(text_edit):
        if text_edit.text() == '':
            text_edit.setPlaceholderText('Cannot be blank')
            return False

        return True

    def refreshTables(self):
        import calendar
        month = datetime.datetime.now().month
        month = calendar.month_name[month]
        index = self.comboBoxReportsMonth.findText(month)
        if index >= 0:
            self.comboBoxReportsMonth.setCurrentIndex(index)

        reports_query = f"SELECT * FROM dbo.Reports WHERE MONTH(DATE) = (SELECT MONTH('{month}' + '2020'))"
        problems_query = 'SELECT REPORT_ID, DATE, NAME, ROOM,ISSUE,NOTE FROM ReportLog.dbo.Reports WHERE FIXED =\'NO\''
        lost_and_found_query = 'SELECT * FROM ReportLog.dbo.LostAndFound'
        problems_count_query = 'SELECT COUNT(REPORT_ID) FROM ReportLog.dbo.Reports WHERE FIXED =\'NO\''

        self.populateTable(self.tableWidgetReports, reports_query)
        self.populateTable(self.tableWidgetProblems, problems_query, True)
        self.populateTable(self.tableWidgetLostAndFound, lost_and_found_query)

        self.cleanup_empty_cells(self.tableWidgetReports)
        self.cleanup_empty_cells(self.tableWidgetProblems)
        self.cleanup_empty_cells(self.tableWidgetLostAndFound)

        cursor = self.executeQuery(problems_count_query)

        # validate the cursor for empty results
        if not self.validateCursor(cursor):
            return

        self.labelNumberProblems.setText(str(cursor.fetchone()[0]))

    @staticmethod
    def cleanup_empty_cells(table):
        if table.item(0, 0) is None:
            table.clear()
            table.setRowCount(0)

    def sort_by_month(self, input_month=None):  # setting an optional argument to null since python has no overloading
        if input_month is not None:
            query = f"SELECT * FROM dbo.Reports WHERE MONTH(DATE) = (SELECT MONTH('{input_month}' + '2020'))"
        else:
            month = self.sender().currentText()
            if month == 'All':
                query = f"SELECT * FROM dbo.Reports"
            else:
                query = f"SELECT * FROM dbo.Reports WHERE MONTH(DATE) = (SELECT MONTH('{month}' + '2020'))"
        self.populateTable(self.tableWidgetReports, query)
        self.cleanup_empty_cells(self.tableWidgetReports)

    def saveNewLog(self):

        state = True
        list_objects = None

        # empty field validation
        if not (self.validateField(self.textBoxNewLogIssue)):
            state = False

        if not (self.validateField(self.textBoxNewLogName)):
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

        cursor = self.executeQuery(query, list_objects)

        # validate the cursor for empty results
        if not self.validateCursor(cursor):
            self.change_page(self.pageReports)
            return

        cursor.commit()

        self.refreshTables()
        self.change_to_last_page()
        self.clearForm()

    def edit_log(self, table):
        self.lastPage = table.objectName()

        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1 and table.item(0, 0) is not None:
            row_index = table.currentRow()  # get index of current row
            report_id = table.item(row_index, 0).text()
            self.stored_id = report_id

            query = f'SELECT DATE, NAME, ROOM, ISSUE, NOTE, RESOLUTION, FIXED from dbo.Reports WHERE REPORT_ID = {report_id};'
            cursor = self.executeQuery(query)

            # validate the cursor for empty results
            if not self.validateCursor(cursor):
                self.change_to_last_page()
                return

            log = cursor.fetchall()
            self.clearForm()
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

    @staticmethod
    def import_settings():
        with open('settings.json', 'r') as json_file:
            data = json.load(json_file)
            return data

    @staticmethod
    def settings_switch(argument):  # python doesn't have switch case so this is an alternative
        switcher = {
            "Classic Light": 'classic_light',
            "Classic Dark": 'classic_dark',
            "Centennial Light": 'centennial_light',
            "Centennial Dark": 'centennial_dark',
        }

        # taken from https://www.geeksforgeeks.org/
        # get() method of dictionary data type returns
        # value of passed argument if it is present
        # in dictionary otherwise second argument will
        # be assigned as default value of passed argument
        return switcher.get(argument, 'classic_light')

    def set_settings(self, theme, time_format):
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

        output = self.settings_switch(theme)
        data = self.import_settings()

        data['theme_choice']['name'] = output
        data['time_format'] = time_format

        with open("settings.json", "w") as jsonFile:
            json.dump(data, jsonFile, indent=2)

        self.labelSettingsWarning.setVisible(True)

    def exportData(self):

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

    def newLog(self):
        self.clearForm()
        self.stored_id = 0
        self.labelNewLog.setText('NEW LOG')
        self.dateEditNewLog.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLog.setCurrentSectionIndex(2)
        self.change_page(self.pageNewLog)

    # for handling creation and deletion of labels for labs that are soon going to be vacant
    def countdown_handler(self):
        '''if self.schedules is not None and range(len(self.schedules) != 0):
            for i in range(len(self.schedules)):  # loop through all of today's schedules
                countdown = self.lab_checker.roomCountdown(self.schedules[i])  # calculate the countdown using the current schedule object
                room_name = self.schedules[i].getRoom().strip()  # get the room name for label
                search = room_name + str(i)  # room name + i (for multiple open times in the same room)

                # countdown = (datetime.timedelta(seconds=5) + self.staticDate) - datetime.datetime.now()  # for testing
                if countdown is not None and countdown < datetime.timedelta(hours=3):  # only show countdown if it's not empty and 2 hours away
                    label = room_name + '         ' + 'In: ' + str(countdown)  # text for the label
                    if self.frameUpcomingRooms.findChild(QtWidgets.QLabel, search) is None:  # check to see if the widget exists already
                        label_upcoming = QtWidgets.QLabel(label, self)  # create a new checkbox and append the room name + countdown
                        label_upcoming.setAccessibleDescription('checkBoxRoom')  # add tag for qss styling
                        label_upcoming.setObjectName(search)  # set the object name so it's searchable later
                        self.frameUpcomingRooms.layout().addWidget(label_upcoming)  # add the checkbox to the frame
                    else:  # the widget exists already so just update it
                        self.frameUpcomingRooms.findChild(QtWidgets.QLabel, search).setText(label)

                    if countdown <= datetime.timedelta(seconds=1):  # countdown expired, so hide and remove the widget
                        self.frameUpcomingRooms.findChild(QtWidgets.QLabel, search).setVisible(False)
                        self.frameUpcomingRooms.findChild(QtWidgets.QLabel, search).deleteLater()'''

        if self.open_lab_schedules is not None and range(len(self.open_lab_schedules) != 0):
            for i in range(len(self.open_lab_schedules)):  # loop through all of today's schedules
                countdown = self.lab_checker.roomCountdown(self.open_lab_schedules[i])  # calculate the countdown using the current schedule object
                room_name = self.open_lab_schedules[i].getRoom().strip()  # get the room name for label
                search = room_name + str(i)  # room name + i (for multiple open times in the same room)

                # countdown = (datetime.timedelta(seconds=5) + self.staticDate) - datetime.datetime.now()  # for testing
                if countdown is not None:  # only show countdown if it's not empty
                    label = room_name + '         ' + 'In: ' + str(countdown)  # text for the label
                    if self.frameOpenLabs.findChild(QtWidgets.QLabel, search) is None:  # check to see if the widget exists already
                        label_upcoming = QtWidgets.QLabel(label, self)  # create a new checkbox and append the room name + countdown
                        label_upcoming.setAccessibleDescription('checkBoxRoom')  # add tag for qss styling
                        label_upcoming.setObjectName(search)  # set the object name so it's searchable later
                        self.frameOpenLabs.layout().addWidget(label_upcoming)  # add the checkbox to the frame
                    else:  # the widget exists already so just update it
                        self.frameOpenLabs.findChild(QtWidgets.QLabel, search).setText(label)
                        if countdown < datetime.timedelta(minutes=30):
                            if countdown.seconds % 2 == 0:
                                self.frameOpenLabs.findChild(QtWidgets.QLabel, search).setAccessibleDescription('timerDanger')
                            else:
                                self.frameOpenLabs.findChild(QtWidgets.QLabel, search).setAccessibleDescription('checkBoxRoom')
                            self.frameOpenLabs.findChild(QtWidgets.QLabel, search).setStyleSheet('')  # force a stylesheet recalculation (faster than reapplying the style sheet)

                    if countdown <= datetime.timedelta(seconds=1):  # countdown expired, so hide and remove the widget
                        self.frameOpenLabs.findChild(QtWidgets.QLabel, search).setVisible(False)
                        self.frameOpenLabs.findChild(QtWidgets.QLabel, search).deleteLater()

    # for handling creation and deletion of checkboxes for labs that are vacant
    def duration_handler(self):
        if self.schedules is not None and range(len(self.schedules) != 0):  # ensuring we're not looping an empty list
            for i in range(len(self.schedules)):  # loop through all of today's schedules
                countdown = self.lab_checker.calculateDuration(self.schedules[i])  # calculate the countdown using the current schedule object
                room_name = self.schedules[i].getRoom().strip()  # get the room name for label
                search = room_name + 'duration' + str(i)  # room name + i (for multiple open times in the same room)

                # countdown = (datetime.timedelta(seconds=2230) + self.staticDate) - datetime.datetime.now()  # for testing (will countdown from 30 seconds)
                if countdown is not None:
                    label = room_name + '         ' + 'Vacant for: ' + str(countdown)

                    if self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search) is None:  # check to see if the widget exists already
                        checkBox = QtWidgets.QCheckBox(label, self)  # create a new checkbox and append the room name + countdown
                        checkBox.setAccessibleDescription('checkBoxRoom')  # add tag for qss styling
                        checkBox.setObjectName(search)
                        checkBox.stateChanged.connect(self.remove_countdown)
                        checkBox.setAccessibleName(str(self.schedules[i].getScheduleID())) # to link the schedule ID
                        self.frameEmptyRooms.layout().addWidget(checkBox)  # add the checkbox to the frame

                    else:  # if the widget exists already, update it

                        self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setText(label)
                        if countdown < datetime.timedelta(minutes=30):
                            if countdown.seconds % 2 == 0:
                                self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setAccessibleDescription('timerDanger')
                            else:
                                self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setAccessibleDescription('checkBoxRoom')
                            self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setStyleSheet('')  # force a stylesheet recalculation (faster than reapplying the style sheet)

                    if countdown <= datetime.timedelta(seconds=1):  # countdown expired, so remove the widget
                        self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setVisible(False)
                        self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).deleteLater()

    def remove_countdown(self):
        for schedule in self.schedules:
            if schedule.getScheduleID() == int(self.sender().accessibleName()):  # if the schedule ID is the same as the sender's accessibleName field
                schedule.setEndTime(datetime.datetime.now().time().isoformat(timespec='seconds'))  # expire the time

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
        # self.duration_handler()
