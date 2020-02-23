import time
import datetime

class labChecker():
    def __init__(self):
        self.tFormat = "%H:%M:%S" #24hr by default
    
    def setTimeFormat(self, tFormat):
        tFormat24hr = "%H:%M:%S"
        tFormat12hr = "%I:%M:%S %p"
        if (tFormat == '12HR'):
            self.tFormat = tFormat12hr
        else:
            self.tFormat = tFormat24hr


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
    
        #taken from https://www.geeksforgeeks.org/
        # get() method of dictionary data type returns  
        # value of passed argument if it is present  
        # in dictionary otherwise second argument will 
        # be assigned as default value of passed argument 
        return switcher.get(argument, "n/a") 
    
    def Clock (self):
        date = datetime.datetime.today() #local system date
        today = date.weekday() #current weekday (Monday is 0 and Sunday is 6)
        current_time = date.time().isoformat(timespec='seconds') #return the 'time' part of the date as a string with seconds precision level

        print (current_time)

        first_time = datetime.datetime.strptime("22:30:00", "%H:%M:%S") #testing
        current_time = datetime.datetime.strptime(current_time, "%H:%M:%S")
        tdelta = first_time - current_time
        
        print(f'Weekday: {self.weekday_switch(today)}') #testing weekday switch
        print(f'Time left: {tdelta}')
        
        if tdelta.days < 0: #if the time has passed
            print(abs(tdelta)) # amount of seconds since it passed

        timeConvert = time.strftime(self.tFormat,time.gmtime(tdelta.seconds))# for converting time if necessary
        print (timeConvert)
        #timeConvert = datetime.datetime.strptime(self.tFormat, tdelta)


#temporary main for testing
if __name__ == '__main__':
    labChk = labChecker()
    labChk.setTimeFormat('12HR')
    labChk.Clock()

