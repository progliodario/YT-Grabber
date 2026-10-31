@echo off
rem Builds YT-Grabber.exe (a single file containing Python and the program) and puts it in the main folder.
rem Needs Python. The rest (PyInstaller, yt-dlp) is downloaded by itself the first time.
rem Intermediate files and build tools: generated\exe-build\ (created automatically, not in git).
setlocal
chcp 65001 >nul
cd /d "%~dp0.."
set "ROOT=%cd%"
set "SRC=%ROOT%\program"
set "RT=%ROOT%\generated"
set "OUT=%RT%\exe-build"

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py -3" )
if not defined PY ( echo Python not found. Install it or run Start.bat first. & exit /b 1 )

rem yt-dlp and its libraries (generated\vendor): prepared with the setup script if missing
if not exist "%RT%\vendor\yt_dlp" (
  %PY% "%SRC%\setup_tools.py" || ( echo Preparing yt-dlp failed & exit /b 1 )
)

rem PyInstaller, in a local folder (does not dirty the system Python)
if not exist "%OUT%\pyinstaller\PyInstaller" (
  %PY% -m pip install --disable-pip-version-check --target "%OUT%\pyinstaller" pyinstaller || ( echo Installing PyInstaller failed & exit /b 1 )
)

if not exist "%ROOT%\build-exe\icon.ico" ( %PY% "%ROOT%\build-exe\make_icon.py" )

set "PYTHONPATH=%OUT%\pyinstaller;%RT%\vendor"
%PY% -m PyInstaller --noconfirm --clean --onefile --name YT-Grabber --icon "%ROOT%\build-exe\icon.ico" --version-file "%ROOT%\build-exe\version.txt" ^
  --distpath "%OUT%\dist" --workpath "%OUT%\work" --specpath "%OUT%" ^
  --paths "%SRC%" --paths "%RT%\vendor" ^
  --add-data "%SRC%\web;web" ^
  --hidden-import server --hidden-import ytworker --hidden-import ytcommon --hidden-import setup_tools ^
  --collect-all yt_dlp --collect-all yt_dlp_ejs --collect-all certifi ^
  --hidden-import mutagen --hidden-import websockets --hidden-import requests --hidden-import brotli --hidden-import Cryptodome ^
  --exclude-module pytest --exclude-module unittest --exclude-module pydoc ^
  "%ROOT%\build-exe\exe_main.py" || ( echo Build failed & exit /b 1 )

copy /y "%OUT%\dist\YT-Grabber.exe" "%ROOT%\YT-Grabber.exe" >nul
echo.
echo DONE: %ROOT%\YT-Grabber.exe
for %%F in ("%ROOT%\YT-Grabber.exe") do echo Size: %%~zF bytes
