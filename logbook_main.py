import os
import sys
from lab_checker import labChecker
import time
import datetime
import pyodbc
import pandas as pd
import urllib    
import qtmodern.windows
import qtmodern.styles
from datetime import date
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from pathlib import Path

# Logbook v2 written in Python 3.8
# by Jarod Lavine and Shaniquo McKenzie

#this is for exe making (don't touch lmao)
root = Path()
if getattr(sys, 'frozen', False):
    root = Path(sys._MEIPASS)
    qtmodern.styles._STYLESHEET = root / 'qtmodern/style.qss'
    qtmodern.windows._FL_STYLESHEET = root / 'qtmodern/frameless.qss'

#get ppath of this python file
path = os.path.dirname(os.path.abspath(__file__))

#get type from ui file
MainWindowUI, MainWindowBase = uic.loadUiType(
    os.path.join(path, 'logbook_design.ui'))

class LogBook(MainWindowBase, MainWindowUI):
    def __init__(self):
        super(LogBook, self).__init__()

        #self.server_string = 'DESKTOP-B2TFENN\\SQLEXPRESS' #change this to your server name
        self.server_string = 'LAPTOP-L714M249\\SQLEXPRESS;'

        # using the default setupUi function of the super class
        self.setupUi(self)

        # get the directory of this script
        self.path = os.path.dirname(os.path.abspath(__file__))

        # build a window object from the .ui file
        self.window = uic.loadUi(os.path.join(self.path, 'logbook_design.ui'))

        #self.setWindowIcon(QtGui.QIcon(os.path.join(self.path,"appicon.ico")))
        #add all click events
        self.addClickEvents()

        #you're going to have to change the server name for it to work on your comp
        self.getAllData()

        #new lab checker object
        self.labchecker = labChecker()

        #set initial activated button
        self.pushButtonDashboard.setAccessibleDescription('menuButtonActive') 

        #fetches the qss stylesheet path
        themePath = os.path.join(os.path.split(__file__)[0],"logbook_main_styles_light.qss")

        #reads the qss stylesheet and applies it to the application
        self.theme = str(open(themePath,"r").read())
        
        #clears all the QT Creator styles in favour of the QSS stylesheet
        self.clearStyleSheets()
        self.setStyleSheet(self.theme)

        #show initial frame linked to dashboard button
        self.showLinkedFrame(self.pushButtonDashboard)



    #reusable query function
    def executeQuery(self, query):
        
        server = self.server_string 
        conn_str = 'Driver={SQL Server};Server=' + server + ';Database=ReportLog;Trusted_Connection=yes;'

        #connect with 5 second timeout
        try:
            conn=pyodbc.connect(conn_str, timeout=2)
        except pyodbc.Error as err:
            print("Couldn't connect (Connection timed out)")
            print(err)

        cursor = conn.cursor()
        cursor.execute(query)

        return cursor

    def getAllData(self):
        months = ['January','February','March','April','May','June','July','August','September','October','November','December']
        status = ['Fixed','Not Fixed']
        themes = ['Classic Light','Classic Dark', 'Centennial Light', 'Centennial Dark']
        formats = ['24 HR', '12 HR']
        roomList = []
        reportsQuery = 'SELECT * FROM ReportLog.dbo.Reports'
        roomsQuery = 'SELECT ROOM FROM ReportLog.dbo.Rooms'
        problemsQuery = 'SELECT * FROM ReportLog.dbo.Reports WHERE FIXED =\'NO\''
        lostAndFoundQuery = 'SELECT * FROM ReportLog.dbo.LostAndFound'

        cursor = self.executeQuery(roomsQuery)
        rooms = cursor.fetchall()

        for room in rooms:
            roomList.append(room[0])

        self.populateComboBox(self.comboBoxRoom, roomList)

        #hide the row numbers in the tables
        self.tableWidgetReports.verticalHeader().setVisible(False)
        self.tableWidgetProblems.verticalHeader().setVisible(False)
        self.tableWidgetLostAndFound.verticalHeader().setVisible(False)

        self.populateTable(self.tableWidgetProblems,problemsQuery)
        self.populateTable(self.tableWidgetReports,reportsQuery)
        self.populateTable(self.tableWidgetLostAndFound,lostAndFoundQuery)

        self.populateComboBox(self.comboBoxMonth,months)
        self.populateComboBox(self.comboBoxStatus,status)
        self.populateComboBox(self.comboBoxSettingsTheme, themes)
        self.populateComboBox(self.comboBoxSettingsTimeFormat, formats)

    #if you want to test something else and get a database error comment out this function and the function call(I'll do exception handling later lol)
    def populateTable(self, table, query):

        #new array variables for holding data and column names
        data = []
        headerNames = []

        cursor = self.executeQuery(query)
        
        data = cursor.fetchall()
        cursorDesc = cursor.description


        #get all column names from the database
        for column in cursorDesc:
           headerNames.append(column[0])

        #QTableWidget requires you to set the amount of rows/columns needed before you populate it
        table.horizontalHeader().setMaximumSectionSize(200)
        table.setRowCount(len(data))
        table.setColumnCount(len(data[0]))
        table.setWordWrap(True)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)

        #set table header labels with column names from database
        table.setHorizontalHeaderLabels(headerNames)

        #populate the table
        for i, row in enumerate(data):
            for j, col in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(col).strip())
                table.setItem(i, j, item)

        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        table.resizeColumnsToContents()
    
    def populateComboBox(self, comboBox, items):
        comboBox.clear()
        comboBox.setView(QtWidgets.QListView())
        comboBox.addItems(items)
        comboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)

    #clears all the QT Creator styles in favour of the QSS stylesheet
    def clearStyleSheets(self):
        widgetChild = self.centralwidget.findChildren(QtWidgets.QWidget)

        for widget in widgetChild:
            widget.setStyleSheet('')

    def addClickEvents(self):
        problemsQuery = 'SELECT * FROM ReportLog.dbo.Reports WHERE FIXED =\'NO\''
        lostAndFoundQuery = 'SELECT * FROM ReportLog.dbo.LostAndFound'

        self.pushButtonNew.clicked.connect(self.newLog)
        self.pushButtonFormCancel.clicked.connect(self.cancelNewLog)
        self.pushButtonRefreshProblems.clicked.connect(lambda: self.populateTable(self.tableWidgetProblems,problemsQuery))
        self.pushButtonDelete.clicked.connect(lambda: self.deleteSelection(self.tableWidgetProblems, 'Reports'))
        self.pushButtonReportsView.clicked.connect(lambda: self.viewSelection(self.tableWidgetReports))
        self.pushButtonViewDataBack.clicked.connect(lambda: self.changePage(self.pageReports))
        self.pushButtonFormSave.clicked.connect(self.saveNewLog)
        self.pushButtonFormClear.clicked.connect(self.clearForm)
        self.pushButtonLostAndFound.clicked.connect(self.showLostAndFoundFrame)
        self.pushButtonNewLAF.clicked.connect(self.newLostAndFound)
        self.pushButtonFormClearLAF.clicked.connect(self.clearLostAndFoundForm)
        self.pushButtonFormCancelLAF.clicked.connect(self.showLostAndFoundFrame)
        self.pushButtonFormSaveLAF.clicked.connect(self.saveLostAndFoundForm)
        self.pushButtonRefreshLAF.clicked.connect(lambda: self.populateTable(self.tableWidgetLostAndFound,lostAndFoundQuery))
        self.pushButtonDeleteLAF.clicked.connect(lambda: self.deleteSelection(self.tableWidgetLostAndFound, 'LostAndFound'))
        self.checkBoxNewLostAndFoundReturned.clicked.connect(self.showFrameReturnedLAF)


        #look through the children of the children until we find a QPushButton
        for widget in self.frameMenu.children():
            if isinstance(widget, QtWidgets.QPushButton):
                widget.clicked.connect(self.button_pressed) #connect click event function
                
            for frame in widget.children():
                if isinstance(frame, QtWidgets.QPushButton):
                    frame.clicked.connect(self.button_pressed) #connect click event function

                for member in frame.children():                    
                    if isinstance(member, QtWidgets.QPushButton):
                        member.clicked.connect(self.button_pressed) #connect click event function
    
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

        roomList = []
        query = 'SELECT ROOM FROM ReportLog.dbo.Rooms'
        cursor = self.executeQuery(query)
        rooms = cursor.fetchall()
        for room in rooms:
            roomList.append(room[0])
        self.populateComboBox(self.comboBoxNewLostAndFoundRoom, roomList)

        self.frameReturnedLAF.hide()
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
            foundBy = self.comboBoxNewLostAndFoundBy.text()
            itemDescription = self.textBoxNewLostAndFoundItemDescription.text()
            note = self.textBoxNewLostAndFoundNote.text()
            if self.checkBoxNewLostAndFoundReturned.isChecked():
                returned = 'YES'
                returnedDate = self.dateEditReturnedNewLostAndFound.date().toString('yyyy-MM-dd')
                studentName = self.textBoxNewLostAndFoundStudentName.text()
                studentNumber = self.textBoxNewLostAndFoundStudentNumber.text()
                query = f'INSERT INTO dbo.LostAndFound(DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,STUDENT_NAME,STUDENT_NUMBER,RETURNED_DATE,RETURNED) VALUES (\'{date}\',\'{room}\',\'{foundBy}\',\'{itemDescription}\',\'{note}\',\'{studentName}\',\'{studentNumber}\',\'{returnedDate}\',\'{returned}\');'

            else:
                returned = 'NO'
                query = f'INSERT INTO dbo.LostAndFound(DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,RETURNED) VALUES (\'{date}\',\'{room}\',\'{foundBy}\',\'{itemDescription}\',\'{note}\',\'{returned}\');'

            cursor = self.executeQuery(query)
            cursor.commit()
            self.exportData()
            self.showLostAndFoundFrame()

    def showLostAndFoundFrame(self):
        lostAndFoundQuery = 'SELECT * FROM ReportLog.dbo.LostAndFound'
        self.populateTable(self.tableWidgetLostAndFound,lostAndFoundQuery)
        self.changePage(self.pageLostAndFound)

    def showFrameReturnedLAF(self):
        if self.checkBoxNewLostAndFoundReturned.isChecked():
            self.dateEditReturnedNewLostAndFound.setDate(QtCore.QDate.currentDate())
            self.dateEditReturnedNewLostAndFound.setCurrentSectionIndex(2)
            self.frameReturnedLAF.show()
        else:
            self.frameReturnedLAF.hide()

    
    def viewSelection(self, table):
        
        #if a row is selected (having no rows selected returns -1)
        if (table.currentRow() != -1):
            rowIndex = table.currentRow() #get index of current row
            data = [] #data list

            for i in range(table.columnCount()): #loop through all columns     
                data.append(table.item(rowIndex,i).text()) #add each field to the list

            #output to widgets
            self.labelViewDataReportNum.setText(data[0])
            self.labelViewDataDate.setText(data[1])
            self.labelViewDataName.setText(data[2])
            self.labelViewDataRoom.setText(data[3])
            self.labelViewDataIssue.setText(data[4])
            self.textEditViewDataNote.setText(data[5])
            self.textEditViewDataResolution.setText(data[6])
            self.labelViewDataFixed.setText(data[7])

            #change to view page
            self.changePage(self.pageViewData)

    def deleteSelection(self, table, tableName):
        #dbo.Reports
        #test = table.currentRow()
        #if a row is selected (having no rows selected returns -1)
        if (table.currentRow() != -1):
            rowIndex = table.currentRow() #get index of current row
            #data = [] #data list

            columnIndex = table.item(rowIndex,0).text()
            deleteQuery = f"DELETE FROM dbo.{tableName} WHERE ='{columnIndex}';"
            self.executeQuery(deleteQuery).commit()

            selectQuery =f"SELECT * FROM dbo.{tableName}"
            
            if tableName == 'Reports':
                self.populateTable(self.tableWidgetProblems, f"{selectQuery} WHERE FIXED =\'NO\'")
                self.populateTable(self.tableWidgetReports, selectQuery)
            elif tableName == 'LostAndFound':
                self.populateTable(self.tableWidgetLostAndFound,selectQuery)
                #self.showLostAndFoundFrame()

    def changePage(self, name):
        widget = name

        if (self.stackedWidget.indexOf(widget) != -1):
            self.stackedWidget.setCurrentIndex(self.stackedWidget.indexOf(widget))

    def validateEmptyForm(self, textEdit):
        if(textEdit.text() == ''):
            textEdit.setPlaceholderText('Cannot be blank')
            return False

        return True
        
    def saveNewLog(self):

        state = True
        
        if not(self.validateEmptyForm(self.textBoxNewLogIssue)):
            state = False

        if not(self.validateEmptyForm(self.textBoxNewLogName)):
            state = False
            
        if (state == False):
            return

        date = self.dateEditNewLog.date().toString('yyyy-MM-dd')
        issue = self.textBoxNewLogIssue.text()
        note = self.textBoxNewLogNote.text()
        name = self.textBoxNewLogName.text()
        room = self.comboBoxRoom.currentText()

        fixed = ''
        if (self.checkBoxFixed.isChecked()):
            fixed = 'YES'
        else:
            fixed = 'NO'

        resolution = self.textBoxNewLogResolution.text()

        query = f'INSERT INTO dbo.Reports(DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) VALUES (\'{date}\',\'{name}\',\'{room}\',\'{issue}\',\'{note}\',\'{resolution}\',\'{fixed}\');'

        cursor = self.executeQuery(query)
        cursor.commit()

        self.exportData()
        self.changePage(self.pageProblems)

    def exportData(self):

        server = self.server_string

        conn_str = 'Driver={SQL Server};Server=' + server + ';Database=ReportLog;Trusted_Connection=yes;' #connection string
        conn_str = urllib.parse.quote_plus(conn_str) #to stop sqlalchemy from complaining
        conn_str = "mssql+pyodbc:///?odbc_connect=%s" % conn_str #to stop sqlalchemy from complaining
        data = pd.read_sql_query('SELECT * FROM dbo.Reports',conn_str)

        data.to_excel('Reports.xlsx')

    def newLog(self):
        self.dateEditNewLog.setDate(QtCore.QDate.currentDate())
        self.dateEditNewLog.setCurrentSectionIndex(2)
        self.changePage(self.pageNewLog)

    def cancelNewLog(self):
        self.changePage(self.pageProblems)

    def Clock (self):
        t = time.localtime() #local system time
        d = datetime.date.today() #local system date
        tFormat24hr = "%H:%M:%S"
        tFormat12hr = "%I:%M:%S %p"

        #print(time.strftime("%H:%M:%S", t)) #testing time output

        schedules = self.labchecker.roomCountdown(self.labchecker.getTodaySchedule()[0])
        print(schedules[0])

        #assign labels with current time and date
        #current date
        self.labelCurrentDate.setText(d.strftime("%B %d, %Y"))
        self.labelCurrentDate2.setText(d.strftime("%B %d, %Y"))
        self.labelCurrentDate3.setText(d.strftime("%B %d, %Y"))

        #convert time to string format
        timeConvert = time.strftime(tFormat24hr, t)

        first_time = datetime.datetime.now()
        later_time = datetime.datetime.strptime("17:30:00",tFormat24hr)
        difference = later_time - first_time

        #convert seconds to string format
        #difference = time.strftime(tFormat24hr, time.gmtime(difference.seconds))
        difference = str(schedules[0])

        if (self.comboBoxSettingsTimeFormat.currentText() == '12 HR'):
            timeConvert = time.strftime(tFormat12hr, t)

        
        #current time
        self.labelCurrentTime.setText(timeConvert)
        self.labelCountdownTest.setText(difference)

    #use the button's name to find the linked frame (deliberately named this way)
    def showLinkedFrame(self, member):
        search = str(member.objectName()).replace('pushButton','')
        
        for widget in self.stackedWidget.children():   
            if (search in widget.objectName()):
                self.changePage(widget)

    #this function loops through the buttons in the menu to find the active QPushButton and set it to the active colour (green)
    def button_pressed(self):
        #look through the children of the children until we find a QPushButton
        for widget in self.frameMenu.children():
            self.isPushButton(widget) #check for push buttons and update them
            for frame in widget.children():
                self.isPushButton(frame) #check for push buttons and update them
                for member in frame.children():
                    self.isPushButton(member) #check for push buttons and update them

                    
        
    def isPushButton(self, member):
        #if object is a QPushButton           
        if isinstance(member, QtWidgets.QPushButton):

            #if the button that called this function is the same as the member encountered:
            if (member.objectName() == self.sender().objectName()):

                #change button's colour to active green
                member.setAccessibleDescription('menuButtonActive')

                #use the button's name to find the linked frame (deliberately named this way)
                self.showLinkedFrame(member) 
                member.setStyleSheet('') #force a stylesheet recalculation (faster than reapplying the style sheet)
                
            else:
                #set all other buttons' colour to white 
                member.setAccessibleDescription('menuButton')
                member.setStyleSheet('') #force a stylesheet recalculation (faster than reapplying the style sheet)

if __name__ == '__main__':

    path = os.path.dirname(os.path.abspath(__file__))

    #create new application   
    app = QtWidgets.QApplication(sys.argv)

    app.setWindowIcon(QtGui.QIcon(os.path.join(path,"appicon.ico")))
    #qtmodern.styles.dark(app)  # qtmodern

    #create new window of type LogBook (calls __init__ constructor to do the rest)
    window = LogBook()

    # flags = QtCore.Qt.WindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
    # window.setWindowFlags(flags)
    window.setGeometry(QtCore.QRect(0, 0, 1280, 720))  # arbitrary size/location

    #center the window
    windowGeometry = window.frameGeometry()
    centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
    windowGeometry.moveCenter(centerPoint)
    window.move(windowGeometry.topLeft())

    mw = qtmodern.windows.ModernWindow(window)  # qtmodern

    #make the interface visible
    mw.show()

    
    #window.show()
            
    timer = QtCore.QTimer()
    timer.timeout.connect(window.Clock) #call clock function every second
    timer.start(1000)

    sys.exit(app.exec_())
