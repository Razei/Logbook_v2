class scheduleObj():

    def __init__(self, room, day, start_time, end_time):
        self.room = room
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
    
    def getRoom(self):
        return self.room

    def getDay(self):
        return self.day

    def getStartTime(self):
        return self.start_time
    
    def getEndTime(self):
        return self.end_time