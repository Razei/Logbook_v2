import pyodbc


class DatabaseHandler:
    def __init__(self, server_string):
        self.server_string = server_string

# reusable query function
    def execute_query(self, query, list_objects=None):

        # conn_str ='Trusted_Connection=yes;DRIVER={ODBC Driver 17 for SQL Server};SERVER='+self.server_string+';DATABASE=ReportLog;UID=Helpdesk;PWD=b1pa55'
        # conn_str = 'Driver={SQL Server};Server='+ self.server_string + ';Database=ReportLog;Trusted_Connection=yes;'
        # connect with 5 second timeout
        try:
            conn_str = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}', host=self.server_string,
                                      database='ReportLog', timeout=2,
                                      trusted_connection='Yes')  # user='Helpdesk', password='b1pa55'
            conn = conn_str
            cursor = conn.cursor()

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
