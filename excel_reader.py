import pandas as pd
import pyodbc

df = pd.read_excel(r'Report Log 2020.xlsx', sheet_name='January')
df = df.fillna(value='')


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


if __name__ == '__main__':
    cursor = get_connection().cursor()
    sql_cols = ['DATE', 'NAME', 'ROOM', 'ISSUE', 'NOTE', 'RESOLUTION', 'FIXED']

    cursor.executemany('INSERT INTO dbo.Reports (DATE,NAME,ROOM,ISSUE,NOTE,RESOLUTION,FIXED) VALUES (?, ?, ?, ?, ?, ?, ?)', df[sql_cols].values.tolist())
    cursor.commit()






