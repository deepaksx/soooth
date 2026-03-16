@echo off
echo ========================================
echo  SOOOTH - AI Soothing Video Generator
echo ========================================
echo.

:: Clean up old processes
echo [1/4] Cleaning up old processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 >nul
echo      Old processes killed

:: Start backend
echo [2/4] Starting backend with SEO optimization...
start "Soooth Backend" cmd /k "cd /d D:\Dev\Soooth\soooth\backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"
timeout /t 3 >nul
echo      Backend starting on port 8001

:: Start frontend
echo [3/4] Starting frontend...
start "Soooth Frontend" cmd /k "cd /d D:\Dev\Soooth\soooth\frontend && npm run dev"
timeout /t 3 >nul
echo      Frontend starting on port 5173

:: Open browser
echo [4/4] Opening browser...
timeout /t 3 >nul
start http://localhost:5173

echo.
echo ========================================
echo  SOOOTH IS READY!
echo ========================================
echo  Backend:  http://localhost:8001
echo  Frontend: http://localhost:5173
echo ========================================
echo.
echo Press any key to exit (services will keep running)...
pause >nul
