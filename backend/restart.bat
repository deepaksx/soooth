@echo off
echo Stopping old backend processes...

REM Kill any process using port 8001
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do (
    taskkill /F /PID %%a 2>nul
)

echo Starting backend with SEO optimization...
cd /d D:\Dev\Soooth\soooth\backend
call .venv\Scripts\activate.bat
uvicorn app.main:app --reload --port 8001
