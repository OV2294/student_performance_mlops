@echo off
call .venv\Scripts\activate
uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
