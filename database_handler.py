import pyodbc


class DatabaseHandler:
    server_string = 'LAPTOP-L714M249\\SQLEXPRESS'
    __user = 'Helpdesk'
    __password = 'b1pa55'

    @classmethod
    def get_server_string(cls):
        return cls.server_string

    @classmethod
    def set_server_string(cls, s_string):
        if s_string is not None:
            cls.server_string = s_string

    @classmethod
    def __make_connection(cls):
        try:
            connection = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}', host=cls.server_string,
                                        database='ReportLog', timeout=5,
                                        trusted_connection='Yes')
            return connection
        except pyodbc.Error:
            raise pyodbc.Error

    # reusable query function
    @classmethod
    def execute_query(cls, query, list_objects=None):
        try:
            connection = cls.__make_connection()

            cursor = connection.cursor()

            if list_objects is not None:
                cursor.execute(query, list_objects)
            else:
                cursor.execute(query)

            return cursor
        except pyodbc.Error as err:
            print("Couldn't connect (Connection timed out)")
            print(err)
            return

    @staticmethod
    def validate_cursor(cursor):
        if cursor is None or cursor.rowcount == 0:
            return False
        return True

    @classmethod
    def create_new_database(cls, year_str=None):
        import datetime
        year = datetime.datetime.now().year

        # I tried to do this in SQL Server with a SQL file, but I couldn't figure out how to make a dynamic database name
        # so I'll just use python instead lol
        database_name = 'ReportLog' + str(year)

        query = f'''
        USE master;

        DROP DATABASE {database_name};
        CREATE DATABASE {database_name};

        USE {database_name};

        DROP TABLE dbo.Reports;
        DROP TABLE dbo.LostAndFound;
        DROP TABLE dbo.Schedule;
        DROP TABLE dbo.Courses;
        DROP TABLE dbo.OpenLabSchedule;
        DROP TABLE dbo.Rooms;
        
        CREATE TABLE dbo.Rooms (
            ROOM NCHAR(6) PRIMARY KEY,
            NAME NCHAR(70),
        );
        
        INSERT INTO 
            dbo.Rooms(ROOM, NAME) 
        VALUES 
            ('Other','Not a room'),
            ('A1-61', 'Software Gaming Lab'),
            ('A3-11','Software Engineering'),
            ('A3-13','Software Engineering'),
            ('A3-15','Software Engineering'),
            ('A3-17','Software/Mobile Dev. Lab'),
            ('A3-21','Operating Systems'),
            ('A3-22','WAN Networking'),
            ('A3-23','Operating Systems'),
            ('A3-24','LAN Networking'),
            ('A3-26','Enterprise Networking'),
            ('A3-32','Data Center'),
            ('A3-52','Biomedical'),
            ('A3-55','Telecommunications'),
            ('A3-55B','Storage Room'),
            ('A3-56','Electronics(Embedded)'),
            ('A3-61','Hardware Lab'),
            ('A3-61A','Hardware Lab Storage'),
            ('A3-63','Wireless Communication'),
            ('A3-65','Digital Communication'),
            ('B3-17','Security Lab'),
            ('D1-21','Electronics Lab'),
            ('D1-22','Digital Electronics Lab'),
            ('E2-16','Flex Lab');
        
        CREATE TABLE dbo.Reports (
            REPORT_ID INT IDENTITY(1,1) PRIMARY KEY,
            DATE DATE NOT NULL,
            NAME NCHAR(70) NOT NULL,
            ROOM NCHAR(6) FOREIGN KEY REFERENCES ROOMS(ROOM) ON DELETE CASCADE,
            ISSUE NCHAR(255),
            NOTE NCHAR(1000),
            RESOLUTION NCHAR(1000),
            FIXED NCHAR(5) NOT NULL,
        );
        
        CREATE TABLE dbo.Courses (
            COURSE_ID NCHAR(70) PRIMARY KEY,
            COURSE_NAME NCHAR(255),
        );
        
        INSERT INTO 
            dbo.Courses(COURSE_ID, COURSE_NAME) 
        VALUES 
            ('CNET101','PC Hardware'),
            ('CNET102', 'PC Operating Systems'),
            ('CNET104','Technical Writing with MS Office and Visio'),
            ('CNET124','Fundamentals of Computer Networks'),
            ('CNET126','Electricity for Computer Systems'),
            ('CNET128','Basic Electrical Safety'),
            ('CNET201','Fundamentals of Routing and Switching'),
            ('CNET202','Windows Server Operating System'),
            ('CNET204','Introduction to Web Design'),
            ('CNET205','Customer Skills'),
            ('CNET206','Introduction to Unix/Linux'),
            ('CNET217','Switching and Routing Essentials'),
            ('CNET219','The Physical Layer'),
            ('CNET221','Network Security'),
            ('CNET222','Network Services'),
            ('CNET224','Data Communications'),
            ('CNET225','Introduction to Telephony'),
            ('CNET227','Technician Project'),
            ('CNET229','Introduction to Business and ICT'),
            ('CNET231','WAN Technologies'),
            ('CNET232','Introduction to Programming'),
            ('CNET239','Computer Forensics');
        
        CREATE TABLE dbo.LostAndFound (
            ENTRY_ID INT IDENTITY(1,1) PRIMARY KEY,
            ROOM NCHAR(6) FOREIGN KEY REFERENCES ROOMS(ROOM) ON DELETE CASCADE,
            NAME NCHAR(70) NOT NULL,
            DATE_FOUND DATE NOT NULL,
            ITEM_DESC NCHAR(1000),  
            NOTE NCHAR(1000),
            RETURNED NCHAR(5),
            STUDENT_NAME NCHAR(70),
            STUDENT_NUMBER NCHAR(9),
            RETURNED_DATE DATE
        );
        
        CREATE TABLE dbo.Schedule(
            SCHEDULE_ID INT IDENTITY(1,1) PRIMARY KEY,
            ROOM NCHAR(6) FOREIGN KEY REFERENCES ROOMS(ROOM) ON DELETE CASCADE,
            DAY NCHAR(10),
            START_TIME TIME(0),
            END_TIME TIME(0)
        );
        
        CREATE TABLE dbo.OpenLabSchedule(
            SCHEDULE_ID INT IDENTITY(1,1) PRIMARY KEY,
            ROOM NCHAR(6) FOREIGN KEY REFERENCES ROOMS(ROOM) ON DELETE CASCADE,
            DAY NCHAR(10),
            START_TIME TIME(0),
            END_TIME TIME(0)
        );   
        '''

        cursor = cls.execute_query(query)

        if not cls.validate_cursor(cursor):
            return

        cursor.commit()
        cursor.close()

        return database_name


if __name__ == '__main__':
    DatabaseHandler.create_new_database()
