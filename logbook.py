import json
import os
from lab_checker import labChecker
import time
import datetime
import pyodbc
import pandas as pd
import urllib
import qtmodern.windows
import qtmodern.styles
from PyQt5 import QtCore, QtWidgets, uic


# get path of this python file
path = os.path.dirname(os.path.abspath(__file__))

# get type from ui file
MainWindowUI, MainWindowBase = uic.loadUiType(
    os.path.join(path, 'logbook_design.ui'))


class LogBook(MainWindowBase, MainWindowUI):
    def __init__(self, theme, time_format):
        super(LogBook, self).__init__()
        # self.server_string = 'DESKTOP-B2TFENN' + '\\' + 'SQLEXPRESS'  # change this to your server name
        self.server_string = 'LAPTOP-L714M249\\SQLEXPRESS'

        # using the default setupUi function of the super class
        self.setupUi(self)

        self.staticDate = datetime.datetime.now()
        # get the directory of this script
        self.path = os.path.dirname(os.path.abspath(__file__))

        # build a window object from the .ui file
        self.window = uic.loadUi(os.path.join(self.path, 'logbook_design.ui'))

        # self.setWindowIcon(QtGui.QIcon(os.path.join(self.path,"appicon.ico")))
        # add all click events
        self.addClickEvents()

        # you're going to have to change the server name for it to work on your comp
        self.getAllData()
        self.set_settings(theme['theme_name'], time_format)

        # new lab checker object
        self.lab_checker = labChecker(self.server_string)
        self.schedules = self.lab_checker.getTodaySchedule()
        self.countdowns = ['']

        # set initial activated button
        self.pushButtonDashboard.setAccessibleDescription('menuButtonActive')

        # fetches the qss stylesheet path
        theme_path = os.path.join(os.path.split(__file__)[0], theme['theme_path'])

        # reads the qss stylesheet and applies it to the application
        self.theme = str(open(theme_path, "r").read())

        # clears all the QT Creator styles in favour of the QSS stylesheet
        self.clearStyleSheets()
        self.setStyleSheet(self.theme)

        # show initial frame linked to dashboard button
        self.showLinkedFrame(self.pushButtonDashboard)

    @staticmethod
    def showDialog():
        # create new window of type LogBook (calls __init__ constructor to do the rest)
        windowDialog = QtWidgets.QDialog()

        flags = QtCore.Qt.WindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        windowDialog.setWindowFlags(flags)
        windowDialog.setGeometry(QtCore.QRect(0, 0, 300, 200))  # arbitrary size/location

        # center the window
        windowGeometryDialog = windowDialog.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        windowGeometryDialog.moveCenter(centerPoint)
        windowDialog.move(windowGeometryDialog.topLeft())

        yesBtn = QtWidgets.QPushButton("Yes", windowDialog)
        noBtn = QtWidgets.QPushButton("No", windowDialog)

        yesBtn.clicked.connect(lambda: windowDialog.close())
        noBtn.clicked.connect(lambda: windowDialog.close())

        yesBtn.move(50, 50)
        noBtn.move(150, 50)
        QtWidgets.QLabel("Are you sure?", windowDialog)
        windowDialog.setWindowTitle("Confirm Delete")
        windowDialog.setWindowModality(QtCore.Qt.ApplicationModal)

        mwDialog = qtmodern.windows.ModernWindow(windowDialog)  # qtmodern

        minimizeBtn = mwDialog.findChild(QtWidgets.QToolButton, "btnMinimize")
        minimizeBtn.deleteLater()
        minimizeBtn.setVisible(False)

        maximizeBtn = mwDialog.findChild(QtWidgets.QToolButton, "btnMaximize")
        maximizeBtn.deleteLater()
        maximizeBtn.setVisible(False)

        '''closeBtn = mwDialog.findChild(QtWidgets.QToolButton, "btnbtnClose")
        closeBtn.deleteLater()
        closeBtn.setVisible(False)'''

        mwDialog.show()

        windowDialog.exec_()

    def validateCursor(self, cursor):
        if cursor is None:
            return False

        if cursor.rowcount == 0:
            return False

        return True
    # reusable query function
    def executeQuery(self, query):

        # conn_str ='Trusted_Connection=yes;DRIVER={ODBC Driver 17 for SQL Server};SERVER='+self.server_string+';DATABASE=ReportLog;UID=Helpdesk;PWD=b1pa55'
        # conn_str = 'Driver={SQL Server};Server='+ self.server_string + ';Database=ReportLog;Trusted_Connection=yes;'
        # connect with 5 second timeout
        try:
            conn_str = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}', host=self.server_string,
                                      database='ReportLog', timeout=2,
                                      trusted_connection='Yes')  # user='Helpdesk', password='b1pa55'
            conn = conn_str
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor
        except pyodbc.Error as err:
            print("Couldn't connect (Connection timed out)")
            print(err)
            return

    def getAllData(self):
        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        status = ['Fixed', 'Not Fixed']
        themes = ['Classic Light', 'Classic Dark', 'Centennial Light', 'Centennial Dark']
        formats = ['24 HR', '12 HR']
        room_list = []
        rooms_query = 'SELECT ROOM FROM ReportLog.dbo.Rooms'

        self.populateComboBox(self.comboBoxMonth, months)
        self.populateComboBox(self.comboBoxStatus, status)
        self.populateComboBox(self.comboBoxSettingsTheme, themes)
        self.populateComboBox(self.comboBoxSettingsTimeFormat, formats)

        cursor = self.executeQuery(rooms_query)

        # validate the cursor for empty results
        if not self.validateCursor(cursor):
            return

        rooms = cursor.fetchall()

        for room in rooms:
            room_list.append(room[0])

        self.populateComboBox(self.comboBoxRoom, room_list)

        # hide the row numbers in the tables
        self.tableWidgetReports.verticalHeader().setVisible(False)
        self.tableWidgetProblems.verticalHeader().setVisible(False)
        self.tableWidgetLostAndFound.verticalHeader().setVisible(False)

        self.refreshTables()

    # if you want to test something else and get a database error comment out this function and the function call(I'll do exception handling later lol)
    def populateTable(self, table, query):
        table.clear()

        table.setSortingEnabled(False)  # this is necessary to avoid confusing the table widget (blank rows)

        # new array variables for holding data and column names
        data = []
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

        # QTableWidget requires you to set the amount of rows/columns needed before you populate it
        table.horizontalHeader().setMaximumSectionSize(200)
        table.setRowCount(len(data))
        table.setColumnCount(len(data[0]))
        table.setWordWrap(True)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)

        # set table header labels with column names from database
        table.setHorizontalHeaderLabels(header_names)

        # populate the table
        for i, row in enumerate(data):
            for j, col in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(col).strip())
                table.setItem(i, j, item)

        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
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
                self.changePage(widget)

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
        self.pushButtonFormCancel.clicked.connect(self.cancelNewLog)

        # problems
        self.pushButtonRefreshProblems.clicked.connect(self.refreshTables)
        self.pushButtonDelete.clicked.connect(lambda: self.deleteSelection(self.tableWidgetReports, 'Reports'))
        self.pushButtonReportsView.clicked.connect(lambda: self.viewSelection(self.tableWidgetReports))
        self.pushButtonProblemsView.clicked.connect(lambda: self.viewSelection(self.tableWidgetProblems))
        self.pushButtonViewDataBack.clicked.connect(lambda: self.changePage(self.pageReports))

        # new log
        self.pushButtonFormSave.clicked.connect(self.saveNewLog)
        self.pushButtonFormClear.clicked.connect(self.clearForm)

        # lost and found
        self.pushButtonLostAndFound.clicked.connect(self.showLostAndFoundFrame)
        self.pushButtonNewLAF.clicked.connect(self.newLostAndFound)
        self.pushButtonFormClearLAF.clicked.connect(self.clearLostAndFoundForm)
        self.pushButtonFormCancelLAF.clicked.connect(self.showLostAndFoundFrame)
        self.pushButtonFormSaveLAF.clicked.connect(self.saveLostAndFoundForm)
        self.pushButtonRefreshLAF.clicked.connect(self.refreshTables)
        self.pushButtonDeleteLAF.clicked.connect(lambda: self.deleteSelection(self.tableWidgetLostAndFound, 'LostAndFound'))
        self.checkBoxNewLostAndFoundReturned.clicked.connect(self.showFrameReturnedLAF)

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
        self.clearLostAndFoundForm()

        self.dateEditNewLostAndFound.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLostAndFound.setCurrentSectionIndex(2)

        room_list = []
        query = 'SELECT ROOM FROM ReportLog.dbo.Rooms'
        cursor = self.executeQuery(query)
        rooms = cursor.fetchall()
        for room in rooms:
            room_list.append(room[0])
        self.populateComboBox(self.comboBoxNewLostAndFoundRoom, room_list)

        self.frameReturnedLAF.hide()
        self.refreshTables()
        self.changePage(self.pageNewLostAndFound)

    def clearLostAndFoundForm(self):
        self.dateEditNewLostAndFound.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLostAndFound.setCurrentSectionIndex(2)
        self.comboBoxNewLostAndFoundRoom.setCurrentIndex(0)
        self.comboBoxNewLostAndFoundBy.clear()
        self.textBoxNewLostAndFoundItemDescription.clear()
        self.textBoxNewLostAndFoundNote.clear()
        self.checkBoxNewLostAndFoundReturned.setCheckState(False)
        self.textBoxNewLostAndFoundStudentName.clear()
        self.textBoxNewLostAndFoundStudentNumber.clear()

    def saveLostAndFoundForm(self):
        date = self.dateEditNewLostAndFound.date().toString('yyyy-MM-dd')
        room = self.comboBoxNewLostAndFoundRoom.currentText()
        found_by = self.comboBoxNewLostAndFoundBy.text()
        item_description = self.textBoxNewLostAndFoundItemDescription.text()
        note = self.textBoxNewLostAndFoundNote.text()
        if self.checkBoxNewLostAndFoundReturned.isChecked():
            returned = 'YES'
            returned_date = self.dateEditReturnedNewLostAndFound.date().toString('yyyy-MM-dd')
            student_name = self.textBoxNewLostAndFoundStudentName.text()
            student_number = self.textBoxNewLostAndFoundStudentNumber.text()
            query = f'INSERT INTO dbo.LostAndFound(DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,STUDENT_NAME,STUDENT_NUMBER,RETURNED_DATE,RETURNED) VALUES (\'{date}\',\'{room}\',\'{found_by}\',\'{item_description}\',\'{note}\',\'{student_name}\',\'{student_number}\',\'{returned_date}\',\'{returned}\');'

        else:
            returned = 'NO'
            query = f'INSERT INTO dbo.LostAndFound(DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,RETURNED) VALUES (\'{date}\',\'{room}\',\'{found_by}\',\'{item_description}\',\'{note}\',\'{returned}\');'

        cursor = self.executeQuery(query)
        cursor.commit()
        self.exportData()
        self.showLostAndFoundFrame()

    def showLostAndFoundFrame(self):
        # dQuery = 'SELECT * FROM ReportLog.dbo.LostAndFound'
        # self.populateTable(self.tableWidgetLostAndFound,lostAndFoundQuery)
        self.changePage(self.pageLostAndFound)

    def showFrameReturnedLAF(self):
        if self.checkBoxNewLostAndFoundReturned.isChecked():
            self.dateEditReturnedNewLostAndFound.setDate(QtCore.QDate.currentDate())
            self.dateEditReturnedNewLostAndFound.setCurrentSectionIndex(2)
            self.frameReturnedLAF.show()
        else:
            self.frameReturnedLAF.hide()

    def viewSelection(self, table):
        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1 and table.item(0, 0) is not None:
            row_index = table.currentRow()  # get index of current row
            data = []  # data list

            for i in range(table.columnCount()):  # loop through all columns
                data.append(table.item(row_index, i).text())  # add each field to the list

            # output to widgets
            self.labelViewDataReportNum.setText(data[0])
            self.labelViewDataDate.setText(data[1])
            self.labelViewDataName.setText(data[2])
            self.labelViewDataRoom.setText(data[3])
            self.labelViewDataIssue.setText(data[4])
            self.textEditViewDataNote.setText(data[5])
            self.textEditViewDataResolution.setText(data[6])
            self.labelViewDataFixed.setText(data[7])

            # change to view page
            self.changePage(self.pageViewData)

    def deleteSelection(self, table, table_name):
        self.showDialog()
        # if a row is selected (having no rows selected returns -1)
        if table.currentRow() != -1:
            row_index = table.currentRow()  # get index of current row
            column_index = table.item(row_index, 0).text()
            first_column = self.executeQuery(f"SELECT column_name from information_schema.columns where table_name = '{table_name}' and ordinal_position = 1").fetchone()
            delete_query = f'DELETE FROM dbo.{table_name} WHERE {str(first_column[0])} = {column_index};'

            self.executeQuery(delete_query).commit()
            self.refreshTables()

    def changePage(self, name):
        widget = name

        if self.stackedWidget.indexOf(widget) != -1:
            self.stackedWidget.setCurrentIndex(self.stackedWidget.indexOf(widget))

    @staticmethod
    def validateEmptyForm(text_edit):
        if text_edit.text() == '':
            text_edit.setPlaceholderText('Cannot be blank')
            return False

        return True

    def refreshTables(self):
        reports_query = 'SELECT * FROM ReportLog.dbo.Reports'
        problems_query = 'SELECT DATE,NAME,ROOM,ISSUE,NOTE FROM ReportLog.dbo.Reports WHERE FIXED =\'NO\''
        lost_and_found_query = 'SELECT * FROM ReportLog.dbo.LostAndFound'
        reports_count_query = 'SELECT COUNT(REPORT_ID) FROM ReportLog.dbo.Reports'
        problems_count_query = 'SELECT COUNT(REPORT_ID) FROM ReportLog.dbo.Reports WHERE FIXED =\'NO\''

        cursor = self.executeQuery(problems_count_query)

        # validate the cursor for empty results
        if not self.validateCursor(cursor):
            return

        self.labelNumberProblems.setText(str(cursor.fetchone()[0]))

        cursor = self.executeQuery(reports_count_query)

        # validate the cursor for empty results
        if not self.validateCursor(cursor):
            return

        self.labelNumberReports.setText(str(cursor.fetchone()[0]))

        self.populateTable(self.tableWidgetReports, reports_query)
        self.populateTable(self.tableWidgetProblems, problems_query)
        self.populateTable(self.tableWidgetLostAndFound, lost_and_found_query)

    def saveNewLog(self):

        state = True

        # empty field validation
        if not (self.validateEmptyForm(self.textBoxNewLogIssue)):
            state = False

        if not (self.validateEmptyForm(self.textBoxNewLogName)):
            state = False

        if not state:
            return

        date = self.dateEditNewLog.date().toString('yyyy-MM-dd')
        issue = self.textBoxNewLogIssue.text()
        note = self.textBoxNewLogNote.toPlainText()
        name = self.textBoxNewLogName.text()
        room = self.comboBoxRoom.currentText()
        fixed = ' '

        if self.checkBoxFixed.isChecked():
            fixed = 'YES'
        else:
            fixed = 'NO'

        resolution = self.textBoxNewLogResolution.text()

        query = f'INSERT INTO dbo.Reports(DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) VALUES (\'{date}\',\'{name}\',\'{room}\',\'{issue}\',\'{note}\',\'{resolution}\',\'{fixed}\');'

        cursor = self.executeQuery(query)

        # validate the cursor for empty results
        if not self.validateCursor(cursor):
            self.changePage(self.pageReports)
            return

        cursor.commit()

        self.exportData()
        self.refreshTables()
        self.changePage(self.pageReports)
        self.clearForm()

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
            self.comboBoxSettingsTheme.setCurrentIndex(3)

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

    def exportData(self):

        server = self.server_string

        conn_str = 'Driver={SQL Server};Server=' + server + ';Database=ReportLog;Trusted_Connection=yes;'  # connection string
        conn_str = urllib.parse.quote_plus(conn_str)  # to stop sqlalchemy from complaining
        conn_str = "mssql+pyodbc:///?odbc_connect=%s" % conn_str  # to stop sqlalchemy from complaining
        data = pd.read_sql_query('SELECT * FROM dbo.Reports', conn_str)

        data.to_excel('Reports.xlsx')

    def newLog(self):
        self.clearForm()
        self.dateEditNewLog.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLog.setCurrentSectionIndex(2)
        self.changePage(self.pageNewLog)

    def cancelNewLog(self):
        self.changePage(self.pageReports)

    def countdownHandler(self):
        if self.schedules is not None and range(len(self.schedules) != 0):
            for i in range(len(self.schedules)):  # loop through all of today's schedules
                countdown = self.lab_checker.roomCountdown(self.schedules[i])  # calculate the countdown using the current schedule object
                room_name = self.schedules[i].getRoom().strip()  # get the room name for label
                search = self.schedules[i].getRoom().strip() + str(i)  # room name + i (for multiple open times in the same room)

                # countdown = (datetime.timedelta(seconds=5) + self.staticDate) - datetime.datetime.now()  # for testing
                if countdown is not None and countdown < datetime.timedelta(hours=4): # only show countdown if it's not empty and 2 hours away
                    label = room_name + '         ' + 'In: ' + str(countdown)
                    if self.frameUpcomingRooms.findChild(QtWidgets.QCheckBox, search) is None:  # check to see if the widget exists already
                        checkBox = QtWidgets.QCheckBox(label, self)  # create a new checkbox and append the room name + countdown
                        checkBox.setAccessibleDescription('checkBoxRoom')  # add tag for qss styling
                        checkBox.setObjectName(search)
                        checkBox.stateChanged.connect(self.removeCountdown)
                        self.frameUpcomingRooms.layout().addWidget(checkBox)  # add the checkbox to the frame
                    else:  # if the widget exists already, update it
                        self.frameUpcomingRooms.findChild(QtWidgets.QCheckBox, search).setText(label)
                    if countdown <= datetime.timedelta(seconds=1):  # countdown expired, so remove the widget
                        self.frameUpcomingRooms.findChild(QtWidgets.QCheckBox, search).setVisible(False)
                        self.frameUpcomingRooms.findChild(QtWidgets.QCheckBox, search).deleteLater()

    def durationHandler(self):
        if self.schedules is not None and range(len(self.schedules) != 0):
            for i in range(len(self.schedules)):  # loop through all of today's schedules
                countdown = self.lab_checker.calculateDuration(self.schedules[i])  # calculate the countdown using the current schedule object
                room_name = self.schedules[i].getRoom().strip()  # get the room name for label
                search = self.schedules[i].getRoom().strip() + 'duration'  # room name + i (for multiple open times in the same room)

                # countdown = (datetime.timedelta(seconds=5) + self.staticDate) - datetime.datetime.now()  # for testing
                if countdown is not None:
                    label = room_name + '         ' + 'Vacant for: ' + str(countdown)
                    if self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search) is None:  # check to see if the widget exists already
                        checkBox = QtWidgets.QCheckBox(label, self)  # create a new checkbox and append the room name + countdown
                        checkBox.setAccessibleDescription('checkBoxRoom')  # add tag for qss styling
                        checkBox.setObjectName(search)
                        checkBox.stateChanged.connect(self.removeCountdown)
                        self.frameEmptyRooms.layout().addWidget(checkBox)  # add the checkbox to the frame
                    else:  # if the widget exists already, update it
                        self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setText(label)

                    if countdown <= datetime.timedelta(seconds=1):  # countdown expired, so remove the widget
                        self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).setVisible(False)
                        self.frameEmptyRooms.findChild(QtWidgets.QCheckBox, search).deleteLater()

    def removeCountdown(self):
        self.frameUpcomingRooms.findChild(QtWidgets.QCheckBox, self.sender().objectName()).setVisible(False)
        self.frameUpcomingRooms.findChild(QtWidgets.QCheckBox, self.sender().objectName()).deleteLater()

    def Clock(self):
        t = time.localtime()  # local system time
        d = datetime.date.today()  # local system date
        tFormat24hr = "%H:%M:%S"
        tFormat12hr = "%I:%M:%S %p"

        # assign labels with current time and date
        # current date
        self.labelCurrentDate.setText(d.strftime("%B %d, %Y"))
        self.labelCurrentDate3.setText(d.strftime("%B %d, %Y"))

        self.countdownHandler()
        self.durationHandler()

        # convert time to string format
        timeConvert = time.strftime(tFormat24hr, t)

        if self.comboBoxSettingsTimeFormat.currentText() == '12 HR':
            timeConvert = time.strftime(tFormat12hr, t)

        # current time
        self.labelCurrentTime.setText(timeConvert)