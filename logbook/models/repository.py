from database_handler import DatabaseHandler


class Repository:
    def __init__(self):
        self._data_set = None

    @property
    def data_set(self):
        try:
            return self._data_set
        except AttributeError:
            raise NotImplementedError('subclasses must have requirements')

    def save_data(self, query, list_obj=None):
        if list_obj is not None:
            cursor = DatabaseHandler.execute_query(query, list_obj)
