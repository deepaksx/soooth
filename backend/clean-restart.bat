@echo off
echo Cleaning up old backend processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
timeout /t 2 >nul

echo Starting fresh backend with SEO optimization...
cd /d D:\Dev\Soooth\soooth\backend
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --port 8001

pause
