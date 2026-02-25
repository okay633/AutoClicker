@echo off
setlocal

REM Build AutoClicker.exe using current Python interpreter
python "%~dp0build_exe.py"
if %errorlevel% neq 0 (
  echo.
  echo Build failed.
  pause
  exit /b %errorlevel%
)

echo.
echo Build completed successfully.
pause
