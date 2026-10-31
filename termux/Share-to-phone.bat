@echo off
rem Prepares YT Grabber for the Android phone and makes it downloadable from the phone (Wi-Fi), only once.
chcp 65001 >nul
cd /d "%~dp0\.."
title YT Grabber - share with the phone
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py -3" )
if not defined PY (
  echo Python not found. Run Start.bat once first.
  pause
  exit /b 1
)
%PY% termux\share_to_phone.py %*
pause
