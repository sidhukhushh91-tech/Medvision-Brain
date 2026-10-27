@echo off
title MedVision AI Setup and Run
cd /d "%~dp0"

echo ==========================================
echo       MedVision AI - Setup and Run
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3.11 from https://www.python.org/downloads/
    echo During installation, select "Add Python to PATH".
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Could not create virtual environment.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat
echo.
echo Installing required packages. This may take several minutes...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Package installation failed. Check the error above and your internet connection.
    pause
    exit /b 1
)

echo.
echo Starting MedVision AI in your browser...
python -m streamlit run app.py
pause
