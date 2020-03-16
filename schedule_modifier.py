import sys
import pyodbc
from PyQt5 import QtCore, uic, QtWidgets
import qtmodern_package.styles as qtmodern_styles
import qtmodern_package.windows as qtmodern_windows

# get type from ui file
ScheduleUI, ScheduleBase = uic.loadUiType('schedule_modifier.ui')


class ScheduleModifier(ScheduleUI, ScheduleBase):
    def __init__(self):
        super(ScheduleModifier, self).__init__()
        self.setupUi(self)
        self.server_string = 'DESKTOP-B2TFENN' + '\\' + 'SQLEXPRESS'  # change this to your server name
        self.pushButtonCheckAll.clicked.connect(self.checkAll)
        self.pushButtonUnCheckAll.clicked.connect(self.UnCheckAll)
        self.show()

    def populateComboBox(self, comboBox, items):
        comboBox.clear()
        comboBox.setView(QtWidgets.QListView())
        comboBox.addItems(items)
        comboBox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)

    def make_checkboxes(self):
        layout = self.frameSchedule.layout()
        column_count = layout.columnCount()
        row_count = layout.rowCount()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        rooms_query = "SELECT ROOM FROM ReportLog.dbo.Rooms WHERE NOT ROOM = 'Other'"
        room_list = []
        start_time = 8

        cursor = self.executeQuery(rooms_query)
        # validate the cursor for empty results

        if not self.validateCursor(cursor):
            return

        rooms = cursor.fetchall()

        for room in rooms:
            room_list.append(room[0])

        self.populateComboBox(self.comboBoxRooms, room_list)

        for i in range(1, column_count):  # loop through all columns
            start_time = 8

            for j in range(1, row_count):
                checkBox = QtWidgets.QCheckBox()
                checkBox.setObjectName(f'checkBox{days[i-1]}{start_time}')
                print(checkBox.objectName())
                layout.addWidget(checkBox, j, i)
                start_time += 1
                QtWidgets.QApplication.processEvents()

    def checkAll(self):
        for widget in self.frameSchedule.children():
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(True)

    def UnCheckAll(self):
        for widget in self.frameSchedule.children():
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(False)

    def calculate_times(self):
        layout = self.frameSchedule.layout()
        column_count = layout.columnCount()
        row_count = layout.rowCount()
        room = self.comboBoxRooms.currentText()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for i in range(1, column_count):  # loop through all columns
            for j in range(1, row_count):
                item = self.layout.itemAtPosition(i)
                widget = item.widget()
                if type(widget) == QtWidgets.QCheckBox and widget.checkState():
                    start_time = widget.objectName().replace(f'checkBox{days[i]}', '') + ':30'

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


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    s = ScheduleModifier()
    s.make_checkboxes()

    mw = qtmodern_windows.ModernWindow(s)  # qtmodern

    # make the interface visible
    mw.show()

    sys.exit(app.exec_())