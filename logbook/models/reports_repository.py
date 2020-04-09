from database_handler import DatabaseHandler


class ReportsRepository:
    def __init__(self):
        self._data = None

    def get_data(self):
        db_name = DatabaseHandler.get_database_name()
        query = f'''
            USE {db_name};
            SELECT * FROM dbo.Reports;
        '''
        data = DatabaseHandler.execute_query(query).fetchall()
        pass

    def save_data(self, query, list_obj=None):
        if list_obj is not None:
            cursor = DatabaseHandler.execute_query(query, list_obj)


if __name__ == '__main__':
    rep = ReportsRepository()
    rep.get_data()
