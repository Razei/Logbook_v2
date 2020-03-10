
--To make sure SQL Server is using the ReportLog database and not master
USE ReportLog;

--drop if table exists
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

--Test data
/*
INSERT INTO dbo.Reports(DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) VALUES ('2020-01-02','Jarod','A3-26','Lab Check','No issues','reset','YES');
INSERT INTO dbo.Reports(DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) VALUES ('2020-02-04','John','B3-17','Console cables crossed in B3-17','The console cables and outlets are changed around','','NO');
INSERT INTO dbo.Reports(DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) VALUES ('2020-02-05','Peter','Other','Printer low on paper','hallway printer','refilled tray 1','YES');
INSERT INTO dbo.Reports(DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) VALUES ('2020-02-04','Solomon','A3-21','Lab Check','All systems are functional','Checked systems and cleaned keyboards','YES');
INSERT INTO dbo.Reports(DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) VALUES ('2020-02-04','Aastha','D1-22','Lab Check','Computers are working fine','','YES');
INSERT INTO dbo.Reports(DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) VALUES ('2020-01-02','Shaniquo','A3-55','Lab Check','Computers are working ok','','YES');
--INSERT INTO dbo.Reports(DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) VALUES ('2020-01-02','Shaniquo','A3-55','Lab Check','Computers are working ok','','YES');

SELECT * FROM dbo.Reports;
*/

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
/*
INSERT INTO dbo.LostAndFound(DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,STUDENT_NAME,STUDENT_NUMBER,RETURNED_DATE,RETURNED) VALUES ('2020-01-02','A3-26','Jarod','White iPad','Found at the teachers desk','New Student','123456789','2020-01-02','YES');
SELECT * FROM dbo.LostAndFound;
*/

CREATE TABLE dbo.Schedule(
	SCHEDULE_ID INT IDENTITY(1,1) PRIMARY KEY,
	ROOM NCHAR(6) FOREIGN KEY REFERENCES ROOMS(ROOM) ON DELETE CASCADE,
	DAY NCHAR(10),
	START_TIME TIME(0),
	END_TIME TIME(0)
);

/*
INSERT INTO dbo.Schedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('D1-22','Monday','12:00','15:00');
INSERT INTO dbo.Schedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('D1-22','Monday','16:00','17:00');
INSERT INTO dbo.Schedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('A3-15','Friday','11:30','13:30');
INSERT INTO dbo.Schedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('A3-15','Tuesday','8:30','10:30');
INSERT INTO dbo.Schedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('A3-11','Monday','20:00','22:30');
INSERT INTO dbo.Schedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('A3-13','Monday','22:00','00:30');
INSERT INTO dbo.Schedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('A3-21','Wednesday','13:00','13:30');
INSERT INTO dbo.Schedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('A3-22','Monday','0:00','23:59'); --for testing countdowns
--INSERT INTO dbo.Schedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('D1-22','Monday','0:00','23:59'); --for testing countdowns
INSERT INTO dbo.Schedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('D1-22','Monday','19:00','19:23'); --for testing countdowns
INSERT INTO dbo.Schedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('B3-17','Monday','23:00','00:30');

SELECT * FROM dbo.Schedule;
*/

CREATE TABLE dbo.OpenLabSchedule(
	SCHEDULE_ID INT IDENTITY(1,1) PRIMARY KEY,
	ROOM NCHAR(6) FOREIGN KEY REFERENCES ROOMS(ROOM) ON DELETE CASCADE,
	DAY NCHAR(10),
	START_TIME TIME(0),
	END_TIME TIME(0)
);

INSERT INTO dbo.OpenLabSchedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('A3-22','Wednesday','17:30','21:30');
INSERT INTO dbo.OpenLabSchedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('A3-22','Friday','12:30','16:30');
INSERT INTO dbo.OpenLabSchedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('A3-24','Thursday','19:00','22:00');
INSERT INTO dbo.OpenLabSchedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('A3-55','Monday','17:30','21:30');
INSERT INTO dbo.OpenLabSchedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('B3-17','Monday','9:30','12:30');
INSERT INTO dbo.OpenLabSchedule(ROOM,DAY,START_TIME,END_TIME) VALUES ('B3-17','Sunday','12:30','14:30');