import pandas as pd
import pyodbc


def get_connection():
    server_string = 'DESKTOP-B2TFENN' + '\\' + 'SQLEXPRESS'
    try:
        conn_str = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}', host=server_string,
                                  database='ReportLog', timeout=2,
                                  trusted_connection='Yes')  # user='Helpdesk', password='b1pa55'
        conn = conn_str
        return conn
    except pyodbc.Error as err:
        print("Couldn't connect (Connection timed out)")
        print(err)
        return


def read_reports():
    df = pd.read_excel(r'Report Log 2020.xlsx', sheet_name='January')
    df = df.fillna(value='')

    cursor = get_connection().cursor()
    sql_cols = ['DATE', 'NAME', 'ROOM', 'ISSUE', 'NOTE', 'RESOLUTION', 'FIXED']

    columns = df[sql_cols].values.tolist()
    columns.reverse()

    cursor.executemany('INSERT INTO dbo.Reports (DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) VALUES (?, ?, ?, ?, ?, ?, ?)', columns)
    cursor.commit()


def read_lost_and_found():
    df = pd.read_excel(r'Report Log 2020.xlsx', sheet_name='Lost & Found')
    df = df.fillna(value='')

    cursor = get_connection().cursor()
    sql_cols = ['DATE', 'ROOM', 'FOUND_BY', 'DESCRIPTION', 'NOTE', 'STUDENT_NAME', 'STUDENT_NUMBER', 'RETURNED_DATE', 'RETURNED']

    columns = df[sql_cols].values.tolist()
    columns.reverse()

    cursor.executemany('INSERT INTO dbo.LostAndFound (DATE_FOUND,ROOM,NAME,ITEM_DESC,NOTE,STUDENT_NAME,STUDENT_NUMBER,RETURNED_DATE,RETURNED) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', columns)
    cursor.commit()


if __name__ == '__main__':
    # read_reports()
    read_lost_and_found()







