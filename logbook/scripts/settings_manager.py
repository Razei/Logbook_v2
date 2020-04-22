import json
from scripts.local_pather import resource_path


def import_settings():
    path = resource_path('settings.json')
    with open(path, 'r') as json_file:
        data = json.load(json_file)
        return data


class SettingsManager:
    path = resource_path('settings.json')
    settings = import_settings()

    @classmethod
    def get_settings(cls):
        return cls.settings

    @classmethod
    def export_settings(cls, data):
        with open(cls.path, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=2)

        cls.settings = data

    @classmethod
    def get_theme_from_settings(cls):
        theme_choice = cls.settings['theme_choice']['name']
        theme_path = cls.settings['theme'][theme_choice]['theme_path']
        path = resource_path(theme_path)
        theme = str(open(path, 'r').read())
        return theme

    @staticmethod
    def settings_theme_switch(argument):  # python doesn't have switch case so this is an alternative
        switcher = {
            "Classic Light": 'classic_light',
            "Classic Dark": 'classic_dark',
            "Centennial Light": 'centennial_light',
            "Centennial Dark": 'centennial_dark',
        }

        # taken from https://www.geeksforgeeks.org/
        # get() method of dictionary data type returns
        # value of passed argument if it is present
        # in dictionary otherwise second argument will
        # be assigned as default value of passed argument
        return switcher.get(argument, 'classic_light')