@echo off
echo Starting Soooth...
echo.

:: Start backend
start "Soooth Backend" cmd /k "cd /d C:\Dev\Soooth\backend && .venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000"

:: Start frontend
start "Soooth Frontend" cmd /k "cd /d C:\Dev\Soooth\frontend && npx vite --host 0.0.0.0 --port 5173"

timeout /t 3 >nul
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
start http://localhost:5173
