# Windows package (installer and windowed application)

*Part of [packaging](../README.md). For installation and use, see the [installation guide](../../docs/install.md#windows).*

This folder builds `dist\windows\YT-Grabber-Setup-<version>.exe`: an Inno Setup installer that contains a PyInstaller build of the
program, with its own window (Microsoft Edge in "app mode"), a tray icon, and Python included.

## Build

```
packaging\windows\build.bat
```

The build requires **Python** and **Inno Setup 6** (`winget install JRSoftware.InnoSetup`, or <https://jrsoftware.org/isdl.php>);
PyInstaller and yt-dlp are fetched automatically. It takes a few minutes and creates:

- the application, as a folder, in `generated\exe-build\dist\YT-Grabber\`;
- the installer, in `dist\windows\YT-Grabber-Setup-<version>.exe`.

For the official releases, GitHub Actions sets `YTG_PYINSTALLER_FROM_SOURCE=1`: the small PyInstaller launcher is compiled from its
source code on the build machine (this requires the Visual Studio C compiler) instead of using the prebuilt one, which some
antivirus programs flag in error. The same can be done locally.

## Contents of this folder

| File | Description |
|---|---|
| `build.bat` | the build script |
| `build_windows.py` | does the work: PyInstaller for the application, then Inno Setup for the installer |
| `installer.iss` | the installer: Start menu, shortcuts, start with Windows, uninstaller, the languages of the wizard, and the `/RELAUNCH=1` parameter used by *Update now* |
| `exe_main.py` | entry point of the application: starts the server, the window and the tray icon (`--worker` runs a download process) |
| `winapp.py` | the Windows shell: single instance, own window, tray icon and notification bubbles, start-up window |
| `winlang.py` | the texts of that shell in 16 languages (the language chosen in the page, otherwise that of Windows) |
| `make_icon.py`, `icon.ico` | the application icon (the script regenerates it if it is missing) |
| `version.txt` | the version information that Windows shows in the properties of the file (set with `tools/bump_version.py`) |

## How it works

It is the same Python program as `Start.bat`, packaged with PyInstaller as a windowed program (without a console), in a folder rather
than a single file, so that an installed application does not unpack itself at every start. The 10 parallel downloads are separate
processes: each worker is the same exe started with `--worker`. Data is stored in `%LOCALAPPDATA%\YT-Grabber`. A second launch finds
the running copy (it looks for the server on the neighbouring ports) and only shows its window. The application also accepts
`--port`, `--dir`, `--host`, `--background` and `--diag`.

**Update now.** The button in the page asks the server to download the new installer and verify its SHA-256 fingerprint. The server
then starts the installer detached, with `/SILENT /SUPPRESSMSGBOXES /NORESTART /RELAUNCH=1`, closes the window and quits. When the
installation has finished, the installer starts the application again (the `[Run]` entry with the `Relaunch` check in
`installer.iss`).

The installer wizard falls back to English for Hindi, Indonesian and Chinese; the application itself is fully translated.
