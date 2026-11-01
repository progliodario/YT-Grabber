@echo off
rem Builds YT-Grabber.app for macOS (Intel + Apple Silicon) and puts it, zipped, in dist\macos\.
rem Needs Python and Internet (the portable Python for the Mac is downloaded and checked the first time, about 50 MB).
setlocal
chcp 65001 >nul
cd /d "%~dp0..\.."

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py -3" )
if not defined PY ( echo Python not found. Install it first. & exit /b 1 )

%PY% packaging\macos\build_app.py || ( echo Build failed & exit /b 1 )
