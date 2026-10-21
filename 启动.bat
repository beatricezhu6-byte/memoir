@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Python 3.11 was not found at the expected location.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList 'app.py' -WorkingDirectory '%CD%' -WindowStyle Hidden"
ping 127.0.0.1 -n 3 >nul
start "Memoir Assistant" http://localhost:7860/

endlocal
