# YT Grabber for Windows (installer)

*Part of [YT Grabber](../README.md). The ready-to-use installer is in the **`Windows\`** folder in the main folder (or
on the GitHub Releases page); this folder contains what is needed to **rebuild** it.*

**`YT-Grabber-Setup-<version>.exe`** (or `winget install progliodario.YTGrabber`) installs YT Grabber like any other
Windows program: nothing else needs to be installed first (Python is included).

## Install

1. Run `YT-Grabber-Setup-<version>.exe` and follow the wizard. It installs for your user account, so **no administrator
   password is needed** (the wizard also offers "for all users").
2. The setup has no paid code-signing certificate, so Windows SmartScreen may show "Windows protected your PC": click
   **More info → Run anyway**.
3. Choose whether to add a desktop shortcut and whether YT Grabber should start when you sign in to Windows, and
   finish. YT Grabber is now in the **Start menu** and in **Settings → Apps → Installed apps**.

## Use

- Open **YT Grabber** from the Start menu (or the desktop shortcut). It opens **in its own window**, like a normal
  program, and puts an icon in the notification area (near the clock).
- **Closing the window does not stop the downloads.** The program keeps running in the notification area:
  click its icon to bring the window back; right-click it for *Open YT Grabber*, *Open downloads folder* and *Quit*.
  Quit it from there when you are done (it asks first if downloads are in progress; they can be resumed later).
- Opening YT Grabber while it is already running just shows the window again.
- **First start only:** a small window shows the download of ffmpeg (about 200 MB, needed for conversions). Later starts
  take a few seconds.
- The window is Microsoft Edge (already part of Windows 10 and 11) in "app mode"; if Edge is missing, Chrome or the
  default browser is used.
- Settings, the download list, cookies, logs and the downloaded tools live in `%LOCALAPPDATA%\YT-Grabber`
  (paste that path into File Explorer). Downloaded files go to `Downloads\YT-Grabber`.
- **Update yt-dlp** (if YouTube stops responding): *Settings → Update yt-dlp and restart*. If the downloaded one is
  damaged it is set aside and the bundled version is used again, so the app always starts.
- The program log is `%LOCALAPPDATA%\YT-Grabber\data\logs\app.log`.

## Update

Run a newer installer: it replaces the old version and keeps your settings and downloads list. If YT Grabber is
running, Setup asks you to quit it first (icon in the notification area → Quit).

## Uninstall

*Settings → Apps → Installed apps → YT Grabber → Uninstall*. The uninstaller asks whether you also want to delete your
settings and the downloaded tools (ffmpeg); the music and videos you downloaded are never deleted.

## Languages

The installer, the notification-area menu, the start-up window and the web interface follow the language of Windows
(16 languages, listed in the main README). The language of the page can be changed with the selector at the top of the
page. Where the installer wizard itself has no translation (Hindi, Indonesian, Chinese) it is shown in English; the app
is fully translated.

## Windows warnings and antivirus

The setup and the program have no paid code-signing certificate, so SmartScreen may warn at first run. The release is
built on GitHub's machines with PyInstaller's launcher compiled from source (fewer false alarms), and it is covered by
`SHA256SUMS` and a build attestation (see [SECURITY.md](../SECURITY.md)). Some antivirus programs wrongly flag programs created with PyInstaller: if that happens, add the installation
folder to the exceptions. If you want to be sure of what it contains, you can rebuild it yourself from the sources
(see below). At first run the Windows firewall may ask for network permission: allow **private networks**.

## Rebuild the installer

```
build-windows\build-windows.bat
```

It needs **Python** and **Inno Setup 6** (`winget install JRSoftware.InnoSetup`, or download it from
https://jrsoftware.org/isdl.php); PyInstaller and yt-dlp are fetched automatically. It takes a few minutes and creates:

- the app, as a folder, in `generated\exe-build\dist\YT-Grabber\`;
- the installer in `Windows\YT-Grabber-Setup-<version>.exe`.

### What is in this folder

| File | What it is |
|---|---|
| `build-windows.bat` | the build script |
| `build_windows.py` | does the work: PyInstaller for the app, then Inno Setup for the installer |
| `installer.iss` | the installer description (Start menu, shortcuts, uninstaller, start with Windows) |
| `exe_main.py` | entry point of the app: starts the server, the window and the tray icon |
| `winapp.py` | the Windows shell: single instance, own window, tray icon, startup splash |
| `winlang.py` | the texts of that shell in 16 languages |
| `make_icon.py`, `icon.ico` | the app icon (the script regenerates it if missing) |
| `version.txt` | version information shown by Windows in the file properties |

## How it works (in short)

It is the same Python program as `Start.bat`, packaged with PyInstaller as a windowed program (no console). The 10
parallel downloads are separate processes: each "worker" is the same program started with `--worker`. Command-line
options for advanced use: `--port 9000`, `--dir D:\Music`, `--host 0.0.0.0` (to use it from a phone on the same
network), `--background` (start in the notification area without opening the window) and `--diag` (print where
yt-dlp and the data are loaded from; run it from a terminal).
