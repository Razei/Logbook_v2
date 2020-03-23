import datetime
from ScheduleObj import ScheduleObj
from database_handler import DatabaseHandler


# lab checker class
# the schedule object holds the room number, day, start time, and end time
# the schedule list holds all the schedules for all the rooms for the current day
class LabChecker:
    def __init__(self, server_string):
        self.server_string = server_string
        self.db_handler = DatabaseHandler(self.server_string)
        self.tFormat = "%H:%M:%S"  # 24hr by default
        self.weekday_string = self.weekday_switch(self.get_local_date().weekday())

    @staticmethod
    def get_local_date():
        return datetime.datetime.today()  # local system date

    def set_time_format(self, t_format):
        # local variables
        t_format24hr = "%H:%M:%S"
        t_format12hr = "%I:%M:%S %p"

        if t_format == '12HR':
            self.tFormat = t_format12hr
        else:
            self.tFormat = t_format24hr

    def get_today_schedule(self):
        # local variables
        schedule_objects = []  # for holding a list of schedule objects
        self.weekday_string = self.weekday_switch(self.get_local_date().weekday())  # get weekday string of today

        # query stuff
        query = f"SELECT SCHEDULE_ID, ROOM, DAY, START_TIME, END_TIME FROM dbo.Schedule WHERE DAY = '{self.weekday_string}'"
        cursor = self.db_handler.execute_query(query)

        # validate the cursor for empty results
        if not self.db_handler.validate_cursor(cursor):
            return

        schedule_data = cursor.fetchall()

        # loop through the cursor and add data to the scheduleObj class
        for sch_time in schedule_data:
            # the schedule object holds the room number, day, start time, and end time
            schedule_objects.append(ScheduleObj(sch_time.ROOM, sch_time.DAY, sch_time.START_TIME.isoformat(timespec='seconds'), sch_time.END_TIME.isoformat(timespec='seconds'), sch_time.SCHEDULE_ID))
        cursor.close()
        return schedule_objects

    def get_today_open_lab_schedule(self):
        # local variables
        schedule_objects = []  # for holding a list of schedule objects
        self.weekday_string = self.weekday_switch(self.get_local_date().weekday())  # get weekday string of today
        # query stuff
        query = f"SELECT SCHEDULE_ID, ROOM, DAY, START_TIME, END_TIME FROM dbo.OpenLabSchedule WHERE DAY = '{self.weekday_string}'"
        cursor = self.db_handler.execute_query(query)

        # validate the cursor for empty results
        if not self.db_handler.validate_cursor(cursor):
            return

        schedule_data = cursor.fetchall()

        # loop through the cursor and add data to the scheduleObj class
        for sch_time in schedule_data:
            schedule_objects.append(ScheduleObj(sch_time.ROOM, sch_time.DAY, sch_time.START_TIME.isoformat(timespec='seconds'), sch_time.END_TIME.isoformat(timespec='seconds'), sch_time.SCHEDULE_ID))
        cursor.close()
        return schedule_objects

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

    def calculate_countdown(self, time_stamp):
        current_time = self.get_local_date().time().isoformat(timespec='seconds')  # return the 'time' part of the date as a string with seconds precision level

        first_time = datetime.datetime.strptime(time_stamp, "%H:%M:%S")  # convert time stamp string to datetime object
        second_time = datetime.datetime.strptime(current_time, "%H:%M:%S")  # make sure the current time is formatted correctly and make it into a datetime object
        t_delta = first_time - second_time  # subtract current time from timestamp to get time difference

        return t_delta

    def compare_times(self, time_stamp):
        if datetime.datetime.strptime(time_stamp, "%H:%M:%S").time() > self.get_local_date().time():  # if the time stamp is in the future (larger than current time)
            return True
        return False

    def room_countdown(self, schedule_input):
        time_left = None

        # if the start time is still in the future
        if self.compare_times(schedule_input.get_start_time()):
            t_delta = self.calculate_countdown(schedule_input.get_start_time())
            # print(f'Time left: {t_delta}')
            time_left = t_delta

        return time_left

    def calculate_duration(self, schedule_input):
        time_left = None

        # if the start time passed and the end time is still in the future
        if not self.compare_times(schedule_input.get_start_time()) and self.compare_times(schedule_input.get_end_time()):
            t_delta = self.calculate_countdown(schedule_input.get_end_time())
            time_left = t_delta

        return time_left


# temporary main for testing
if __name__ == '__main__':
    server_string = 'DESKTOP-SIF9RD3\\SQLEXPRESS;'
    labChk = LabChecker(server_string)
    labChk.set_time_format('12HR')
    schedules = labChk.get_today_schedule()

    for schedule in schedules:
        print(labChk.room_countdown(schedule))
