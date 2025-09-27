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

REM Activate virtual environment for all commands
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check for command line arguments
if "%1"=="db-info" (
    echo Showing database information...
    python show_db_info.py
    goto :end
)

if "%1"=="db-reset" (
    echo Resetting database...
    python reset_database.py
    goto :end
)

if "%1"=="test" (
    echo Running tests...
    python test_ui.py
    echo.
    python test_database.py
    goto :end
)

REM Default: Run the application
echo Running application...
python main.py

:end
REM Deactivate when done
deactivate
echo.
echo Additional commands:
echo   run.bat db-info    - Show database information
echo   run.bat db-reset   - Reset database
echo   run.bat test       - Run test suite
echo.
pause