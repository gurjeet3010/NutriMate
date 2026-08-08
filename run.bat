@echo off
cd /d "%~dp0"
echo ===================================================
echo Starting NutriMate Nutrition Planner Application...
echo ===================================================

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" app.py
) else if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" app.py
) else (
    echo [INFO] Python virtual environment not found. Setting up...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt flask-cors
    python app.py
)
pause
