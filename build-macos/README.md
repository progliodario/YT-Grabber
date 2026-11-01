# YT Grabber for macOS

*Part of [YT Grabber](../README.md). The ready-to-use app is in the **`macOS\`** folder in the main folder; this folder
contains what is needed to **rebuild** it.*

**`YT-Grabber-macOS.zip`** contains **`YT-Grabber.app`**, one app for both **Intel** and **Apple Silicon** Macs
(macOS 10.15 or newer). It brings its own Python, so nothing needs to be installed first.

## Install and open

**With Homebrew:** `brew install --cask progliodario/tap/yt-grabber` (it removes the quarantine flag for you, so step 2 below is not needed).

**By hand:**

1. Download `YT-Grabber-macOS.zip` and unzip it (a double click does it). Drag **YT-Grabber.app** to *Applications*
   (or anywhere you like).
2. The app is only signed "ad hoc" and **not notarized by Apple** (that needs a paid developer account), so the first time macOS blocks
   it. To open it:
   - **macOS 14 or older:** right-click (or Control-click) the app → **Open** → **Open**.
   - **macOS 15 or newer:** double-click the app, then open **System Settings → Privacy & Security**, scroll down to the
     message about YT-Grabber and click **Open Anyway**.
   - Or, in Terminal: `xattr -dr com.apple.quarantine /Applications/YT-Grabber.app`
3. A **Terminal window** opens and the browser goes to `http://localhost:8765/`. Keep the Terminal window open while
   downloading; close it (or press Ctrl+C) to quit.

The first start needs Internet: it installs yt-dlp and downloads ffmpeg (about 45 MB, static builds from
osxexperts.net). Later starts are immediate.

## Where things are

- The app is never modified. Settings, the download list, cookies, logs and the downloaded tools live in
  `~/Library/Application Support/YT-Grabber`.
- Downloads go to `~/Downloads/YT-Grabber` (change it in *Settings*). The first time, macOS may ask permission to
  access the Downloads folder: allow it.
- To remove everything: drag the app to the Trash and delete `~/Library/Application Support/YT-Grabber`.

## Rebuild the app

```
build-macos\build-macos.bat
```

It needs Python and Internet; **no Mac is needed** to build it (the app is just a folder of files). The script downloads
the portable Python 3.12 builds for Apple Silicon and Intel from
[python-build-standalone](https://github.com/astral-sh/python-build-standalone) (checked against the SHA256SUMS
published with the release, and cached in `generated\macos-cache\`), assembles `YT-Grabber.app` and zips it into
`macOS\YT-Grabber-macOS.zip`, keeping symbolic links and file permissions. The same script works on Linux and macOS
(`python3 build-macos/build_app.py`).

### What is in this folder

| File | What it is |
|---|---|
| `build-macos.bat` | the build script for Windows |
| `build_app.py` | does the work (downloads Python, writes `Info.plist` and the icon, builds the zip) |
| `launcher` | the app's executable: opens Terminal and runs `run.sh` there |
| `run.sh` | starts YT Grabber with the bundled Python (first-start setup, then the server) |

## Status

Before every release, GitHub Actions builds the app, signs it ad hoc, and starts it on a real **Apple Silicon** Mac and
a real **Intel** Mac: the server must answer and serve the page. What the maintainer could **not** try is the
double-click experience on a Mac (Gatekeeper prompt, the Terminal window, opening the browser), because no Mac was
available to them. If something does not work, please open an issue on GitHub.
