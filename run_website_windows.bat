@echo off
setlocal
title MedVision AI Website Launcher
cd /d "%~dp0"

set "PROJECT_DIR=%~dp0"
set "PYTHON=%PROJECT_DIR%..\.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"

where node >nul 2>nul
if errorlevel 1 (
    echo Node.js was not found. Install Node.js 20 or newer, then try again.
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo npm was not found. Reinstall Node.js with npm, then try again.
    pause
    exit /b 1
)

if not exist "%PYTHON%" (
    echo Creating Python virtual environment...
    python -m venv "%PROJECT_DIR%.venv"
    if errorlevel 1 (
        echo Could not create the Python environment. Install Python 3.11 or newer.
        pause
        exit /b 1
    )
    set "PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
)

"%PYTHON%" -c "import fastapi, uvicorn" >nul 2>nul
if errorlevel 1 (
    echo Installing Python packages. This can take several minutes...
    "%PYTHON%" -m pip install -r "%PROJECT_DIR%requirements.txt"
    if errorlevel 1 (
        echo Python package installation failed. Review the error above.
        pause
        exit /b 1
    )
)

if not exist "%PROJECT_DIR%frontend\node_modules\vite\bin\vite.js" (
    echo Installing frontend packages...
    call npm install --prefix "%PROJECT_DIR%frontend"
    if errorlevel 1 (
        echo Frontend package installation failed. Review the error above.
        pause
        exit /b 1
    )
)

curl.exe --fail --silent http://127.0.0.1:8000/api/health >nul 2>nul
if errorlevel 1 (
    echo Starting the classifier API...
    start "MedVision AI API" /D "%PROJECT_DIR%" "%PYTHON%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
)

curl.exe --fail --silent http://127.0.0.1:5173 >nul 2>nul
if errorlevel 1 (
    echo Starting the React website...
    start "MedVision AI Frontend" /D "%PROJECT_DIR%frontend" "%ComSpec%" /k npm run dev -- --host 127.0.0.1
)

echo Waiting for the website to become available...
for /L %%i in (1,1,30) do (
    curl.exe --fail --silent http://127.0.0.1:5173 >nul 2>nul
    if not errorlevel 1 goto open_website
    timeout /t 1 /nobreak >nul
)

echo The website did not start. Check the MedVision AI API and Frontend windows for errors.
pause
exit /b 1

:open_website
echo Opening MedVision AI at http://localhost:5173
start "" "http://localhost:5173"
exit /b 0
