import time
import datetime
import pyodbc
from scheduleObj import scheduleObj


# lab checker class
# the schedule object holds the room number, day, start time, and end time
# the schedule list holds all the schedules for all the rooms for the current day
class labChecker():
    def __init__(self, server_string):
        self.server_string = server_string  # change this to your server name
        # self.server_string = 'LAPTOP-L714M249\\SQLEXPRESS'
        self.tFormat = "%H:%M:%S"  # 24hr by default
        self.weekday_string = self.weekday_switch(self.getLocalDate().weekday())
        # self.todaySchedule = self.getTodaySchedule()

    def validateCursor(self, cursor):
        if cursor is None:
            return False

        if cursor.rowcount == 0:
            return False

        return True

    def getLocalDate(self):
        return datetime.datetime.today()  # local system date

    def setTimeFormat(self, tFormat):
        # local variables
        tFormat24hr = "%H:%M:%S"
        tFormat12hr = "%I:%M:%S %p"

        if tFormat == '12HR':
            self.tFormat = tFormat12hr
        else:
            self.tFormat = tFormat24hr

    def getTodaySchedule(self):
        # local variables
        schedule_objects = []  # for holding a list of schedule objects
        self.weekday_string = 'Monday'  # get weekday string of today

        # query stuff
        query = f"SELECT SCHEDULE_ID, ROOM, DAY, START_TIME, END_TIME FROM dbo.Schedule WHERE DAY = '{self.weekday_string}'"
        cursor = self.executeQuery(query)

        # validate the cursor for empty results
        if not self.validateCursor(cursor):
            return

        schedule_data = cursor.fetchall()

        # loop through the cursor and add data to the scheduleObj class
        for sch_time in schedule_data:
            schedule_objects.append(scheduleObj(sch_time.SCHEDULE_ID, sch_time.ROOM, sch_time.DAY, sch_time.START_TIME.isoformat(timespec='seconds'), sch_time.END_TIME.isoformat(timespec='seconds')))

        return schedule_objects

    # reusable query function
    def executeQuery(self, query):
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

    @staticmethod
    def weekday_switch(argument):  # python doesn't have switch case so this is an alternative
        switcher = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday",
        }

        # taken from https://www.geeksforgeeks.org/
        # get() method of dictionary data type returns  
        # value of passed argument if it is present  
        # in dictionary otherwise second argument will 
        # be assigned as default value of passed argument 
        return switcher.get(argument, "n/a")

    def calculateCountdown(self, time_stamp):
        current_time = self.getLocalDate().time().isoformat(timespec='seconds')  # return the 'time' part of the date as a string with seconds precision level

        first_time = datetime.datetime.strptime(time_stamp, "%H:%M:%S")  # convert time stamp string to datetime object
        second_time = datetime.datetime.strptime(current_time, "%H:%M:%S")  # make sure the current time is formatted correctly and make it into a datetime object
        t_delta = first_time - second_time  # subtract current time from timestamp to get time difference

        return t_delta

    def compareTimes(self, time_stamp):
        if datetime.datetime.strptime(time_stamp, "%H:%M:%S").time() > self.getLocalDate().time():  # if the time stamp is in the future (larger than current time)
            return True
        return False

    def roomCountdown(self, schedule_input):
        time_left = None

        # if the start time is still in the future
        if self.compareTimes(schedule_input.getStartTime()):
            t_delta = self.calculateCountdown(schedule_input.getStartTime())
            # print(f'Time left: {t_delta}')
            time_left = t_delta

        return time_left

    def calculateDuration(self, schedule_input):
        time_left = None

        # if the start time passed and the end time is still in the future
        if not self.compareTimes(schedule_input.getStartTime()) and self.compareTimes(schedule_input.getEndTime()):
            t_delta = self.calculateCountdown(schedule_input.getEndTime())
            time_left = t_delta

        return time_left


# temporary main for testing
if __name__ == '__main__':
    server_string = 'LAPTOP-L714M249\\SQLEXPRESS;'
    labChk = labChecker(server_string)
    labChk.setTimeFormat('12HR')
    schedules = labChk.getTodaySchedule()

    for schedule in schedules:
        print(labChk.roomCountdown(schedule))