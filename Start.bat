@echo off
rem YT Grabber - start with Python (double-click). On first start it installs what it needs by itself.
rem Options: Start.bat --port 9000 | --dir D:\Music | --host 0.0.0.0 (access from other devices on the network)
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title YT Grabber

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py -3" )
if not defined PY (
  echo Python is not installed.
  echo Trying to install it with winget...
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
  echo.
  echo Installation finished. CLOSE this window and double-click Start.bat again.
  pause
  exit /b 1
)

%PY% program\setup_tools.py
if errorlevel 1 (
  echo.
  echo Setup failed. Check your connection and try again.
  pause
  exit /b 1
)

:loop
%PY% program\server.py %*
rem 75 = the server asks to be restarted (yt-dlp update). "if errorlevel 75" would mean "75 or more".
if %errorlevel%==75 goto loop
echo.
echo YT Grabber has stopped.
pause
