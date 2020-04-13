import json
from scripts.local_pather import resource_path


class SettingsManager:
    path = resource_path('settings.json')

    @classmethod
    def import_settings(cls):
        with open(cls.path, 'r') as json_file:
            data = json.load(json_file)
            return data

    @classmethod
    def export_settings(cls, data):
        with open(cls.path, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=2)

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