import os


class CustomThemeMaker:
    def __init__(self):
        # path of qss stylesheet
        theme_path = os.path.join(os.path.split(__file__)[0], "themes//logbook_main_styles_custom.qss")

        self.theme_input = str(open(theme_path, "r").read()).splitlines()
        self.output_file_name = ''

        self.background_colour = ''
        self.background_colour2 = ''
        self.background_colour3 = ''

        self.main_colour = ''
        self.main_colour2 = ''

        self.text_colour = ''
        self.active_text_colour = ''

        self.accent = ''
        self.accent2 = ''

        self.danger_colour = ''
        self.danger_gradient = ''

    def dark_theme(self):
        # path of qss stylesheet
        self.output_file_name = "logbook_main_styles_centennial_dark.qss"

        self.background_colour = '#454547'
        self.background_colour2 = '#585858'
        self.background_colour3 = '#5E5E5E'

        self.main_colour = '#454547'
        self.main_colour2 = '#454547'

        self.text_colour = '#FFFFFF'
        self.active_text_colour = '#454547'

        self.accent = '#86DA50'
        self.accent2 = '#D2DA50'

        self.danger_colour = '#FF5959'
        self.danger_gradient = 'qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0.5,stop: 0 #FF0505, stop: 1 #FF5959)'

        self.replace_strings()

    def light_theme(self):
        # path of qss stylesheet
        self.output_file_name = "logbook_main_styles_light.qss"

        self.background_colour = '#EBEBEB'
        self.background_colour2 = '#E3E3E3'
        self.background_colour3 = '#F9F9F9'

        self.main_colour = '#FFFFFF'
        self.main_colour2 = '#454547'

        self.text_colour = '#454547'
        self.active_text_colour = '#FFFFFF'

        self.accent = '#0055FF'
        self.accent2 = '#0083FF'

        self.danger_colour = '#FF5959'
        self.danger_gradient = 'qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0.5,stop: 0 #FF0505, stop: 1 #FF5959)'

        self.replace_strings()

    def replace_strings(self):
        output_path = os.path.join(os.path.split(__file__)[0], 'themes//' + self.output_file_name)
        theme_output = open(output_path, "w")
        # replace custom words with colour codes
        for line in self.theme_input:
            line = line.replace('active_text_colour', self.active_text_colour)
            line = line.replace('text_colour', self.text_colour)
            line = line.replace('background_colour2', self.background_colour2)
            line = line.replace('background_colour3', self.background_colour3)
            line = line.replace('background_colour', self.background_colour)
            line = line.replace('main_colour2', self.main_colour2)
            line = line.replace('main_colour', self.main_colour)

            line = line.replace('accent2', self.accent2)
            line = line.replace('accent', self.accent)

            line = line.replace('danger_colour', self.danger_colour)
            line = line.replace('danger_gradient', self.danger_gradient)

            theme_output.write(line + '\n')


if __name__ == '__main__':
    custom_theme = CustomThemeMaker()
    custom_theme.light_theme()
    custom_theme.dark_theme()
