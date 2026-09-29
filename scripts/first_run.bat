@echo off
REM One-shot: venv + install + git + dvc + dvc repro.   Run from the project root:   scripts\first_run.bat
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
if not exist .git git init
if not exist .dvc dvc init
REM short DVC cache path => avoids the Windows 260-char path limit no matter where the project lives
dvc cache dir --local C:\dvc_cache
dvc repro
echo.
echo Done. Metrics: reports\metrics.json
