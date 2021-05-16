cd /D "%~dp0"

call venv\Scripts\activate

ECHO y | pyinstaller logbook_main.spec

ECHO Python app built

call test_build.bat

PAUSE