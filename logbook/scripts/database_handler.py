import pyodbc
import sqlite3
from sqlite3 import Error

from scripts.local_pather import resource_path
from scripts.settings_manager import SettingsManager


def get_database_name():
    settings = SettingsManager.get_settings()
    return settings['database_name']


def get_server_string_setting():
    settings = SettingsManager.get_settings()
    return settings['server_string']


def export_database_name(db_name):
    settings = SettingsManager.get_settings()
    settings['database_name'] = db_name
    SettingsManager.export_settings(settings)


class DatabaseHandler:
    __server_string = get_server_string_setting()
    __database_name = get_database_name()
    __mode = 'SQLite'
    __user = ''
    __password = ''

    @classmethod
    def auto_backup(cls, default=None):
        from PyQt5 import QtWidgets
        if default is not None:
            query = f"BACKUP DATABASE [{get_database_name()}] TO DISK = N'C:\\{get_database_name()}Backup.bak'"
        else:
            path = QtWidgets.QFileDialog.getSaveFileName(QtWidgets.QFileDialog(), 'Save Backup', f'{get_database_name()}Backup.bak', filter='.bak')[0]
            if path == '' or path is None:
                return
            query = f"BACKUP DATABASE [{get_database_name()}] TO DISK = N'{path}'"

        connection = cls.__make_connection(True)
        cursor = connection.cursor()
        try:
            cursor.execute(query)
        except WindowsError:
            raise WindowsError

        if not cls.validate_cursor(cursor):
            return

        while cursor.nextset():
            pass

        connection.close()

    @classmethod
    def set_user_name(cls, user):
        if user is not None:
            cls.__user = user

    @classmethod
    def set_password(cls, password):
        if password is not None:
            cls.__password = password

    @classmethod
    def get_server_string(cls):
        return cls.__server_string

    @classmethod
    def set_server_string(cls, s_string):
        if s_string is not None:
            cls.__server_string = s_string

    @classmethod
    def get_database_name(cls):
        return cls.__database_name

    @classmethod
    def set_database_name(cls, db_name):
        if db_name is not None:
            cls.__database_name = db_name

    @classmethod
    def __make_connection(cls):
        db_file = resource_path(cls.__server_string)
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print(e)

    # reusable query function
    @classmethod
    def execute_query(cls, query, list_objects=None, commit=None):
        try:
            connection = cls.__make_connection()
            cursor = connection.cursor()

            if list_objects is not None:
                cursor.execute(query, list_objects)
            else:
                cursor.execute(query)

            if commit is not None:
                connection.commit()

            return cursor
        except pyodbc.Error as err:
            # print("Couldn't connect (Connection timed out)")
            print(err)
            return

    @classmethod
    def commit(cls):
        connection = cls.__make_connection()
        connection.commit()

    @staticmethod
    def validate_cursor(cursor):
        if cursor is None or cursor.rowcount == 0:
            return False
        return True

    @classmethod
    def create_new_database_sqlite(cls):
        import datetime
        year = datetime.datetime.now().year
        database_name = 'LogBook' + str(year)
        sql_script_path = resource_path('LogbookDB.sql')
        query_create_db = open(sql_script_path, 'r').read()

        connection = cls.__make_connection()
        cursor = connection.cursor()
        cursor.executescript(query_create_db)
        cursor.close()

        cls.__database_name = database_name
        export_database_name(database_name)

        return database_name

    @classmethod
    def create_new_database(cls):
        import datetime
        year = datetime.datetime.now().year

        # I tried to do this in SQL Server with a SQL file, but I couldn't figure out how to make a dynamic database name
        # so I'll just use python instead lol
        database_name = 'ReportLog' + str(year)

        query_create_tables = f'SELECT NAME from sys.databases WHERE NAME = \'{database_name}\''
        # for some reason when I run the create database
        # query with pyodbc SQL Server lets me overwrite
        # the existing database without throwing the
        # "Database already exists" message. So I'll have to
        # check manually I guess ¯\_(ツ)_/¯

        cursor = DatabaseHandler.execute_query(query_create_tables)
        if not DatabaseHandler.validate_cursor(cursor):  # only do this if the cursor returns no results
            query_create_db = f'CREATE DATABASE {database_name};'

            query_create_tables = f'''
            USE {database_name};
            
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

            connection = cls.__make_connection(True)
            cursor = connection.cursor()

            cursor.execute(query_create_db)
            cursor.execute(query_create_tables)

            cls.__database_name = database_name
            export_database_name(database_name)

            return database_name
