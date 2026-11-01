# macOS application

*Part of [packaging](../README.md). For installation and use, see the [installation guide](../../docs/install.md#macos).*

`YT-Grabber.app` is a single application for **Intel and Apple Silicon** Macs (macOS 10.15 or later), zipped into
`dist/macos/YT-Grabber-macOS.zip`. It includes its own Python, so nothing needs to be installed beforehand.

## Build

```
packaging\macos\build.bat                 # on Windows (or: python3 packaging/macos/build_app.py)
```

The build requires Python and an Internet connection; **a Mac is not required**, because the application is only a folder of files.
The script downloads the portable Python 3.12 builds for Apple Silicon and Intel from
[python-build-standalone](https://github.com/astral-sh/python-build-standalone) (verified against the published SHA256SUMS and cached
in `generated/macos-cache/`), assembles `YT-Grabber.app` and zips it, preserving symbolic links and file permissions.

On a Mac, the release workflow also signs the application "ad hoc" (`codesign --sign -`) and zips it again with `ditto`, then starts
it on an Apple Silicon runner and an Intel runner. The first start downloads yt-dlp, the JavaScript runtime and ffmpeg (static builds
from osxexperts.net) into `~/Library/Application Support/YT-Grabber`; the application itself is never modified.

## Contents of this folder

| File | Description |
|---|---|
| `build.bat`, `build_app.py` | build the application: download Python, write `Info.plist` and the icon, and create the zip |
| `launcher` | the executable of the application: opens Terminal and runs `run.sh` there |
| `run.sh` | starts YT Grabber with the bundled Python (first-start setup, then the server; exit code 75 means restart after a yt-dlp update) |
