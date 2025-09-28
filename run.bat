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

REM Set default log level if not specified
if "%LOG_LEVEL%"=="" set LOG_LEVEL=INFO

REM Check for log level parameter
if "%1"=="--log-level" (
    set LOG_LEVEL=%2
    shift
    shift
    echo Log level set to: %LOG_LEVEL%
    echo.
)

REM Export log level as environment variable
set LOG_LEVEL=%LOG_LEVEL%

REM Check for command line arguments
if "%1"=="db-info" (
    echo Showing database information...
    python scripts\show_db_info.py
    goto :end
)

if "%1"=="db-reset" (
    echo Resetting database...
    python scripts\reset_database.py
    goto :end
)

if "%1"=="test" (
    echo Running tests...
    python tests\run_all_tests.py
    goto :end
)

if "%1"=="demo" (
    echo Running API demo...
    python scripts\demo_nexus_api.py
    goto :end
)

if "%1"=="validate" (
    echo Running API compliance validation...
    python scripts\validate_api_compliance.py
    goto :end
)

if "%1"=="detect-game" (
    echo Running game detection utility...
    python scripts\detect_game.py
    goto :end
)

REM Default: Run the application
echo Running application with log level: %LOG_LEVEL%...
python main.py

:end
REM Deactivate when done
deactivate
echo.
echo Additional commands:
echo   run.bat                          - Run application (default log level: INFO)
echo   run.bat --log-level DEBUG        - Run with DEBUG logging
echo   run.bat --log-level WARNING      - Run with WARNING logging
echo   run.bat --log-level ERROR        - Run with ERROR logging
echo   run.bat db-info                  - Show database information
echo   run.bat db-reset                 - Reset database
echo   run.bat test                     - Run test suite
echo   run.bat demo                     - Run API demo
echo   run.bat validate                 - Validate API compliance
echo   run.bat detect-game              - Detect Stalker 2 installations
echo.
echo Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
echo.
pause