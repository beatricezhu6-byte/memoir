@echo off
setlocal
cd /d "%~dp0"

if "%DASHSCOPE_KEY%"=="" (
  echo.
  echo   DASHSCOPE_KEY is not set.
  echo   In PowerShell, run:
  echo     $env:DASHSCOPE_KEY="your-key"
  echo   Then double-click this file again.
  echo.
  pause
  exit /b 1
)

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Python 3.11 was not found at the expected location.
  pause
  exit /b 1
)

if "%MEMOIR_PORT%"=="" set "MEMOIR_PORT=8000"

echo Starting Memoir Assistant on port %MEMOIR_PORT% ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList 'app.py' -WorkingDirectory '%CD%' -WindowStyle Hidden"
ping 127.0.0.1 -n 3 >nul
start "Memoir Assistant" http://localhost:%MEMOIR_PORT%/

endlocal
