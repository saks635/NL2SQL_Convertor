@echo off
echo Starting NL2SQL Full Stack Application...
echo.

REM Start Backend in new PowerShell window
echo Starting Backend (Flask)...
start "NL2SQL Backend" powershell -Command "cd 'C:\Users\SAKSHAM NILAJKAR\Desktop\SMARTDESK-AI\backend\nl2sql\backend'; .\venv\Scripts\Activate.ps1; python enhanced_app.py"

REM Wait a few seconds for backend to start
timeout /t 3 /nobreak

REM Start Frontend in new PowerShell window
echo Starting Frontend (React)...
start "NL2SQL Frontend" powershell -Command "cd 'C:\Users\SAKSHAM NILAJKAR\Desktop\SMARTDESK-AI\backend\nl2sql\frontend'; npm start"

echo.
echo =====================================================
echo Both applications are starting in separate windows:
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Press any key to continue...
pause > nul
