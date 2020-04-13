import datetime
from scripts.schedule_modifier import ScheduleModifier


# lab checker class
# the schedule object holds the room number, day, start time, and end time
# the schedule list holds all the schedules for all the rooms for the current day
class LabChecker:
    def __init__(self):
        self.tFormat = "%H:%M:%S"  # 24hr by default
        self.weekday_string = self.weekday_switch(self.get_local_date().weekday())
        self.schedules = ScheduleModifier.get_schedules()
        self.open_lab_schedules = ScheduleModifier.get_open_lab_schedules()

    @staticmethod
    def get_local_date():
        return datetime.datetime.today()  # local system date

    def get_today_schedule(self):
        self.schedules = ScheduleModifier.get_schedules()

        # local variables
        schedule_objects = []  # for holding a list of schedule objects

        self.weekday_string = self.weekday_switch(self.get_local_date().weekday())  # get weekday string of today

        if self.schedules is not None and len(self.schedules) != 0:  # not empty check
            for sch in self.schedules:  # loop through all schedules
                if sch.get_day() == self.weekday_string:
                    schedule_objects.append(sch)  # append schedules that match today
        return schedule_objects

    def get_today_open_lab_schedule(self):
        self.open_lab_schedules = ScheduleModifier.get_open_lab_schedules()

        # local variables
        ol_schedules = self.open_lab_schedules
        schedule_objects = []  # for holding a list of schedule objects
        self.weekday_string = self.weekday_switch(self.get_local_date().weekday())  # get weekday string of today

        if ol_schedules is not None and len(ol_schedules) != 0:
            for sch in ol_schedules:
                if sch.get_day() == self.weekday_string:
                    schedule_objects.append(sch)
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
