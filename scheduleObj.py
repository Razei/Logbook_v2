class scheduleObj():

    def __init__(self, schedule_id, room, day, start_time, end_time):
        self.room = room
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.schedule_id = schedule_id

    def getScheduleID(self):
        return self.schedule_id

    def getRoom(self):
        return self.room

    def getDay(self):
        return self.day

    def getStartTime(self):
        return self.start_time
    
    def getEndTime(self):
        return self.end_time

    def setStartTime(self, start_time):
        if start_time is not None:
            self.start_time = start_time

    def setEndTime(self, end_time):
        if end_time is not None:
            self.end_time = end_time

