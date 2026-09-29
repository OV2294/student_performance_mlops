@echo off
REM Usage: scripts\push_to_github.bat https://github.com/<user>/student-performance-mlops.git
if "%1"=="" (echo Provide the GitHub repo URL & exit /b 1)
git init
git add .
git commit -m "Initial commit: Student Performance MLOps pipeline"
git branch -M main
git remote add origin %1
git push -u origin main
