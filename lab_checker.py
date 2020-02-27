import time
import datetime
import pyodbc
import pandas as pd
from scheduleObj import scheduleObj

#lab checker class
#the schedule object holds the room number, day, start time, and end time
#the schedule list holds all the schedules for all the rooms for the current day
class labChecker():
    def __init__(self, serverString):
        self.server_string = serverString #change this to your server name
        #self.server_string = 'LAPTOP-L714M249\\SQLEXPRESS;'
        self.tFormat = "%H:%M:%S" #24hr by default
        self.weekday_string = self.weekday_switch(self.getLocalDate().weekday())
        #self.todaySchedule = self.getTodaySchedule()
    
    def getLocalDate(self):
        return datetime.datetime.today() #local system date

    def setTimeFormat(self, tFormat):
        #local variables
        tFormat24hr = "%H:%M:%S"
        tFormat12hr = "%I:%M:%S %p"

        if (tFormat == '12HR'):
            self.tFormat = tFormat12hr
        else:
            self.tFormat = tFormat24hr

    def getTodaySchedule(self):
        #local variables
        schedule = [] #for holding a list of schedule objects
        self.weekday_string = 'Monday' #get weekday string of today

        #query stuff
        query = f"SELECT ROOM, DAY, START_TIME, END_TIME FROM dbo.Schedule WHERE DAY = '{self.weekday_string}'"
        cursor = self.executeQuery(query)
        schedules = cursor.fetchall()

        #loop through the cursor and add data to the scheduleObj class
        for time in schedules:
            schedule.append(scheduleObj(time.ROOM, time.DAY,time.START_TIME,time.END_TIME))
            #print (time)

        return schedule

    #reusable query function
    def executeQuery(self, query):
        #local variables
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
        
    
    def weekday_switch(self, argument): #python doesn't have switch case so this is an alternative
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
        current_time = self.getLocalDate().time().isoformat(timespec='seconds') #return the 'time' part of the date as a string with seconds precision level
        
        first_time = datetime.datetime.strptime(time_stamp, "%H:%M:%S") #testing
        second_time = datetime.datetime.strptime(current_time, "%H:%M:%S")
        tdelta = first_time - second_time

        return tdelta


    def compareTimes(self,time_stamp):
        if datetime.datetime.strptime(time_stamp, "%H:%M:%S").time() > self.getLocalDate().time():
            return True
        return False

    def roomCountdown(self, schedule):
        current_time = self.getLocalDate().time().isoformat(timespec='seconds') #return the 'time' part of the date as a string with seconds precision level
        times = []
        time_left = None
        #print (f'Current time: {current_time}')
        #print(f'Weekday: {self.weekday_string}')

        #if the start time is still in the future
        if self.compareTimes(schedule.getStartTime()):
            tdelta = self.calculateCountdown(schedule.getStartTime())    
            #print(f'Time left: {tdelta}')
            time_left = tdelta
            times.append(tdelta)

        #if the end time is still in the future
        elif self.compareTimes(schedule.getEndTime()):
            tdelta = self.calculateCountdown(schedule.getEndTime())
            #print(f'Time left (end): {tdelta}')
            time_left = tdelta
            times.append(tdelta)
            
        '''        
        #start time has passed
        else:
            tdelta = self.calculateCountdown(schedule.getStartTime())
            print(f'Start Time passed {abs(tdelta)} ago')
            times.append(abs(tdelta))'''

        '''
        #end time has passed
        else:
            tdelta = self.calculateCountdown(schedule.getEndTime())
            print(f'End Time passed {abs(tdelta)} ago') # amount of time since it passed
            times.append(abs(tdelta))'''

        return time_left

        '''del tdelta 
        del schedule
        del first_time
        # in python, variables created in 
        # loops are still accessible outside of the loop
        # if you want to re-create a variable 
        # name outside this scope, you have 
        # to manually delete it first'''
        
        

        '''timeConvert = time.strftime(self.tFormat,time.gmtime(tdelta.seconds))# for converting time if necessary
        print (timeConvert)
        
        #timeConvert = datetime.datetime.strptime(self.tFormat, tdelta)'''


#temporary main for testing
if __name__ == '__main__':
    labChk = labChecker()
    labChk.setTimeFormat('12HR')
    schedules = labChk.getTodaySchedule()

    for schedule in schedules:
        print (labChk.roomCountdown(schedule))

    

