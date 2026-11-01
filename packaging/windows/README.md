# Windows package (installer and windowed app)

*Part of [packaging](../README.md). To install and use it, see the [installation guide](../../docs/install.md#windows).*

Builds `dist\windows\YT-Grabber-Setup-<version>.exe`: an Inno Setup installer that contains a PyInstaller build of the program, with
its own window (Microsoft Edge in "app mode"), a tray icon, and Python included.

## Build

```
packaging\windows\build.bat
```

Needs **Python** and **Inno Setup 6** (`winget install JRSoftware.InnoSetup`, or <https://jrsoftware.org/isdl.php>); PyInstaller and
yt-dlp are fetched automatically. It takes a few minutes and creates:

- the app, as a folder, in `generated\exe-build\dist\YT-Grabber\`;
- the installer in `dist\windows\YT-Grabber-Setup-<version>.exe`.

For the official releases, GitHub Actions sets `YTG_PYINSTALLER_FROM_SOURCE=1`: PyInstaller's small launcher is compiled from its
source code on the build machine (it needs Visual Studio's C compiler) instead of using the prebuilt one, which some antivirus
programs flag by mistake. You can do the same locally.

## What is in this folder

| File | What it is |
|---|---|
| `build.bat` | the build script |
| `build_windows.py` | does the work: PyInstaller for the app, then Inno Setup for the installer |
| `installer.iss` | the installer: Start menu, shortcuts, start with Windows, uninstaller, the wizard's languages |
| `exe_main.py` | entry point of the app: starts the server, the window and the tray icon (`--worker` runs a download process) |
| `winapp.py` | the Windows shell: single instance, own window, tray icon and notification bubbles, start-up window |
| `winlang.py` | the texts of that shell in 16 languages (the language chosen in the page, else the one of Windows) |
| `make_icon.py`, `icon.ico` | the app icon (the script regenerates it if it is missing) |
| `version.txt` | the version information Windows shows in the file's properties (set it with `tools/bump_version.py`) |

## How it works

It is the same Python program as `Start.bat`, packaged with PyInstaller as a windowed program (no console), in a folder rather than a
single file so that an installed app does not unpack itself at every start. The 10 parallel downloads are separate processes: each
worker is the same exe started with `--worker`. Data goes to `%LOCALAPPDATA%\YT-Grabber`. A second launch finds the running copy (it
looks for the server on the nearby ports) and just shows its window. The app also accepts `--port`, `--dir`, `--host`,
`--background` and `--diag`.

The installer wizard falls back to English for Hindi, Indonesian and Chinese; the app itself is fully translated.
