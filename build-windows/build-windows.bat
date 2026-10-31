@echo off
rem Builds the Windows installer (YT-Grabber-Setup-<version>.exe) and puts it in Windows\ (in the main folder).
rem Needs Python and Inno Setup 6 (winget install JRSoftware.InnoSetup). PyInstaller and yt-dlp are fetched automatically.
rem Intermediate files and build tools: generated\exe-build\ (created automatically, not in git).
setlocal
chcp 65001 >nul
cd /d "%~dp0.."

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py -3" )
if not defined PY ( echo Python not found. Install it or run Start.bat first. & exit /b 1 )

%PY% build-windows\build_windows.py || ( echo Build failed & exit /b 1 )
