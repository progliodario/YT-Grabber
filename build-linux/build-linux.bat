@echo off
rem Builds the Linux packages (.deb and .rpm) and puts them in Linux\ (in the main folder).
rem Needs Python. nfpm (the packaging tool) is downloaded and checked automatically the first time.
setlocal
chcp 65001 >nul
cd /d "%~dp0.."

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py -3" )
if not defined PY ( echo Python not found. Install it first. & exit /b 1 )

%PY% build-linux\build_packages.py || ( echo Build failed & exit /b 1 )
