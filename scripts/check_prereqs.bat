@echo off
REM Verifies every tool needed by the project + Jenkins is installed and on PATH
echo ---- Python ----   & python --version
echo ---- pip ----      & pip --version
echo ---- Git ----      & git --version
echo ---- Docker ----   & docker --version
echo ---- Compose ----  & docker compose version
echo ---- Java ----     & java -version
echo.
echo If any line above says "not recognized", install that tool and open a NEW terminal.
