# Packaging

This folder contains everything that is needed to build each package of YT Grabber. The packages themselves are built and tested by
GitHub Actions for every release (see the [development guide](../docs/development.md#automatic-builds-github-actions)); the folders
are intended for building a package locally. To **install** YT Grabber, see the [installation guide](../docs/install.md).

| Folder | Builds | Command | Result |
|---|---|---|---|
| [`windows/`](windows/README.md) | the installer with the windowed application (PyInstaller + Inno Setup) | `packaging\windows\build.bat` | `dist\windows\YT-Grabber-Setup-<version>.exe` |
| [`android/`](android/README.md) | the Android application (Gradle, Kotlin) | `packaging\android\build.bat` | `dist\android\*.apk` |
| [`linux/`](linux/README.md) | `.deb`, `.rpm`, AppImage, Flatpak | `packaging\linux\build.bat` and the scripts in `appimage/` and `flatpak/` | `dist/linux/` |
| [`macos/`](macos/README.md) | the Mac application (`YT-Grabber.app`, zipped) | `packaging\macos\build.bat` | `dist/macos/YT-Grabber-macOS.zip` |
| [`termux/`](termux/README.md) | the helper that installs the program on a phone with Termux | `packaging\termux\Share-to-phone.bat` | (serves the files on the Wi-Fi network) |

The version number is set in several places and must always be changed with `python tools/bump_version.py <version>`.
The results are placed in `dist/` (not tracked by git).
