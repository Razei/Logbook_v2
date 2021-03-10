call venv\Scripts\activate
pip freeze > requirements.txt
ECHO.
ECHO All dependencies stored in requirements.txt
TIMEOUT /T 10