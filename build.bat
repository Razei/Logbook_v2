cd /D "%~dp0"

call install_dependencies.bat

call venv\Scripts\activate

ECHO y | pyinstaller logbook_main.spec --noconfirm

ECHO Python app built

call test_build.bat

TIMEOUT /T 5