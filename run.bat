@echo off
echo Starting Stalker 2 Mod Manager...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo.
    echo Installing dependencies...
    venv\Scripts\pip install -r requirements.txt
    echo.
)

REM Activate virtual environment and run application
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Running application...
python main.py

REM Deactivate when done
deactivate
pause