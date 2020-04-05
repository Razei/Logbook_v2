import datetime


class ScheduleObj:

    def __init__(self,  room, day, start_time, end_time, schedule_id=None):
        self.room = room
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.schedule_id = None
        self.countdown = Countdown(self.start_time, self.end_time)
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

    def get_countdown(self):
        return self.countdown

    def set_start_time(self, start_time):
        if start_time is not None:
            self.start_time = start_time

    def set_end_time(self, end_time):
        if end_time is not None:
            self.end_time = end_time


class Countdown:

    def __init__(self, start_time, end_time):
        self.duration_expired = False
        self.countdown_expired = False
        self.start_time = start_time
        self.end_time = end_time
        self.countdown = self.room_countdown()
        self.duration = self.calculate_duration()

    def get_countdown(self):
        self.countdown = self.room_countdown()
        return self.countdown

    def get_duration(self):
        self.duration = self.calculate_duration()
        return self.duration

    def get_duration_expired(self):
        return self.duration_expired

    def set_end_time(self, value):
        self.end_time = value

    def get_countdown_expired(self):
        return self.countdown_expired

    def check(self, countdown):
        if countdown is None:
            return True

        if countdown <= datetime.timedelta(seconds=1):  # dash_countdown expired, so hide and remove the widget
            return True

    @staticmethod
    def get_local_date():
        return datetime.datetime.today()  # local system date

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

    def room_countdown(self):
        time_left = None

        # if the start time is still in the future
        if self.compare_times(self.start_time):
            t_delta = self.calculate_countdown(self.start_time)
            # print(f'Time left: {t_delta}')
            time_left = t_delta
            self.countdown = t_delta

        self.countdown_expired = self.check(time_left)
        return time_left

    def calculate_duration(self):
        time_left = None

        # if the start time passed and the end time is still in the future
        if not self.compare_times(self.start_time) and self.compare_times(self.end_time):
            t_delta = self.calculate_countdown(self.end_time)
            time_left = t_delta
            self.duration = t_delta

        self.duration_expired = self.check(time_left)
        return time_left
