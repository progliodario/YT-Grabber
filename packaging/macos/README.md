# macOS app

*Part of [packaging](../README.md). To install and use it, see the [installation guide](../../docs/install.md#macos).*

`YT-Grabber.app`, one app for **Intel and Apple Silicon** Macs (macOS 10.15 or newer), zipped into `dist/macos/YT-Grabber-macOS.zip`.
It brings its own Python, so nothing needs to be installed first.

## Build

```
packaging\macos\build.bat                 # on Windows (or: python3 packaging/macos/build_app.py)
```

It needs Python and Internet; **no Mac is needed**, because the app is just a folder of files. The script downloads the portable
Python 3.12 builds for Apple Silicon and Intel from [python-build-standalone](https://github.com/astral-sh/python-build-standalone)
(checked against the published SHA256SUMS, cached in `generated/macos-cache/`), assembles `YT-Grabber.app` and zips it, keeping
symbolic links and file permissions.

On a Mac, the release workflow also signs the app "ad hoc" (`codesign --sign -`) and zips it again with `ditto`, then starts it
on an Apple Silicon and an Intel runner. The first start downloads yt-dlp, the JavaScript runtime and ffmpeg (static builds from
osxexperts.net) into `~/Library/Application Support/YT-Grabber`; the app itself is never modified.

## What is in this folder

| File | What it is |
|---|---|
| `build.bat`, `build_app.py` | build the app: download Python, write `Info.plist` and the icon, make the zip |
| `launcher` | the app's executable: opens Terminal and runs `run.sh` there |
| `run.sh` | starts YT Grabber with the bundled Python (first-start setup, then the server; exit code 75 = restart after a yt-dlp update) |
