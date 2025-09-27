@echo off
echo Setting up Stalker 2 Mod Manager Development Environment...
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment. Make sure Python is installed.
    pause
    exit /b 1
)

REM Activate and install dependencies
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Running tests...
python test_ui.py
if %errorlevel% neq 0 (
    echo Tests failed. Check the output above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To run the application:
echo   run.bat
echo.
echo To activate the virtual environment manually:
echo   venv\Scripts\activate
echo.
echo To run tests:
echo   python test_ui.py
echo.
pause