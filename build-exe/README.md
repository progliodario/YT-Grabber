# YT-Grabber.exe (Windows)

*Part of [YT Grabber](../README.md). This folder contains everything needed to **rebuild** the exe; to just use it,
double-click `YT-Grabber.exe` in the main folder.*

A single file, **`YT-Grabber.exe`**, containing the whole program: no need to install Python or anything else.
Double-click it and the browser opens at `http://localhost:8765/`.

## First start

The first time, the exe downloads **ffmpeg** (about 190 MB) and the **JavaScript runtime** (about 40 MB) by itself into
`%LOCALAPPDATA%\YT-Grabber\bin`: you need Internet and it takes about a minute. You can follow the progress in the
black window. Later starts take about 7 seconds (the exe is a single file that unpacks into a temporary folder;
folders left by abrupt closures are cleaned up automatically at the next start).

## Usage

- Keep the **black window** open while downloading: closing it stops the program (interrupted downloads can be
  resumed by reopening the exe and pressing *Resume*). The rest of the behavior is described in the main
  [README.md](../README.md).
- You can move the exe anywhere, even to a USB stick: it does not depend on other files.
- Command-line options: `YT-Grabber.exe --port 9000`, `--dir D:\Music`, `--no-browser`,
  `--host 0.0.0.0` (to use it from another device on the network).
- **Settings, download list, cookies, logs and tools** live in `%LOCALAPPDATA%\YT-Grabber`
  (paste that path into File Explorer). Downloaded files go to `Downloads\YT-Grabber`, as usual.
- **Update yt-dlp** (if YouTube stops responding): *Settings → Update yt-dlp and restart*. The exe downloads the
  latest version and restarts by itself. If the downloaded one is damaged it is set aside and the bundled version is
  used again, so the exe always starts.
- To **uninstall**: delete `YT-Grabber.exe` and the folder `%LOCALAPPDATA%\YT-Grabber`.
- Diagnostics: `YT-Grabber.exe --diag` shows versions and paths.

## Windows warnings and antivirus

The exe is not digitally signed: at first start Windows SmartScreen may show "Windows protected your PC".
Click **More info → Run anyway**. Some antivirus programs wrongly flag programs created with PyInstaller: if that
happens, add `YT-Grabber.exe` to the exceptions. If you want to be sure of what it contains, you can rebuild it
yourself from the sources (see below).

At first run the Windows firewall may ask for network permission: just allow **private networks**.

## Rebuild the exe from the sources

```
build-exe\build-exe.bat
```

It only needs Python: the script prepares PyInstaller and yt-dlp by itself. The result is `YT-Grabber.exe` in the
main folder. Intermediate files and PyInstaller live in `generated\exe-build\` (created automatically, safe to
delete). It takes about a minute.

### What is in this folder

| File | What it is |
|---|---|
| `build-exe.bat` | the build script |
| `exe_main.py` | entry point of the exe (starts the server, or the worker / folder picker when asked) |
| `make_icon.py`, `icon.ico` | the exe icon (the script regenerates it if missing) |
| `version.txt` | version information shown by Windows in file properties |

## How it works (in short)

It is the same Python program as `Start.bat`, packaged with PyInstaller. The 10 parallel downloads are separate
processes: each "worker" is the exe itself started with `--worker` (it reuses the already unpacked files, so it starts
immediately).
