class ScheduleObj:

    def __init__(self,  room, day, start_time, end_time, schedule_id=None):
        self.room = room
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.schedule_id = None
        if schedule_id is not None:
            self.schedule_id = schedule_id

    def get_schedule_id(self):
        if self.schedule_id is not None:
            return self.schedule_id

    def get_room(self):
        return self.room

    def get_day(self):
        return self.day

    def get_start_time(self):
        return self.start_time
    
    def get_end_time(self):
        return self.end_time

    def set_start_time(self, start_time):
        if start_time is not None:
            self.start_time = start_time

    def set_end_time(self, end_time):
        if end_time is not None:
            self.end_time = end_time
