@echo off
call .venv\Scripts\activate.bat
if not exist .git git init
if not exist .dvc dvc init
dvc cache dir --local C:\dvc_cache
dvc repro
echo.
echo Pipeline finished. Metrics: reports\metrics.json
