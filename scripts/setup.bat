@echo off
REM One-time setup on Windows (run from project root in cmd or PowerShell)
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
echo.
echo Setup complete. Activate later with:  .venv\Scripts\activate
