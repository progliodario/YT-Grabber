# YT Grabber

Download **videos, playlists (even with thousands of items), albums and channels** from YouTube and YouTube Music,
from a local web page that works in any browser (Chrome, Edge, Firefox, Safari, Brave, Opera, phone included).

- **Always 10 downloads at the same time**, even with several playlists in the queue.
- Files are **numbered in playlist order** (`001 - Title.mp3`, `002 - ...`).
- Every failed video is **listed with its number and the exact reason**, with a one-click retry.
- Stop and resume at any time: finished files are recognized and skipped.

## Start here: which one do I use?

| You have | Use | Details |
|---|---|---|
| **Windows PC**, nothing installed | double-click **`YT-Grabber.exe`** | [build-exe/README.md](build-exe/README.md) |
| Windows with **Python** installed | double-click **`Start.bat`** | below |
| **Linux / macOS** | run **`./Start.sh`** | below |
| **Android phone**, no computer needed | install an app from the **`APK\`** folder | [build-apk/README.md](build-apk/README.md) |
| Android phone, via **Termux** (alternative to the APK) | follow the guide in `termux\` | [termux/README.md](termux/README.md) |

Then paste one or more links (one per line) and press **Download**. The page opens by itself at
`http://localhost:8765/`. Files go to `Downloads\YT-Grabber\` (change it in *Settings*).

On first start everything needed (yt-dlp, JavaScript runtime, ffmpeg) is installed by itself: you need Internet and
about 200 MB, only once.

`Start.bat` options: `--port 9000`, `--dir D:\Music`, `--host 0.0.0.0` (to use it from another device on the same
network: open `http://PC-IP-ADDRESS:8765/`; files are still saved on the computer running the program).

## What is in each folder

```
YT-Grabber\
├─ README.md            this guide: read it first
├─ YT-Grabber.exe       Windows: double-click and go (nothing to install)
├─ Start.bat            Windows, if you already have Python (alternative to the exe)
├─ Start.sh             Linux / macOS / Termux
├─ LICENSE              MIT license
│
├─ program\             the program itself: server.py, ytworker.py, ytcommon.py, setup_tools.py
│                         and web\ (the user interface)
├─ APK\                 the Android apps, ready to install on the phone
│
├─ build-exe\           to rebuild YT-Grabber.exe (build-exe.bat) + guide
├─ build-apk\           to rebuild the APKs (build-apk.bat), with the signing key + guide
├─ termux\              alternative to the APK: install on the phone with Termux + guide
│
└─ generated\           created by the program (ffmpeg, yt-dlp, settings, logs, build files): safe to delete
```

`YT-Grabber.exe`, `APK\` and `generated\` are not source files (they are not in git): they are rebuilt with the
scripts in `build-exe\` and `build-apk\`. The exe keeps its own data in `%LOCALAPPDATA%\YT-Grabber\`.

## How it works

- **Always 10 simultaneous downloads**, in total, even with several playlists in the queue.
- The playlist is read in blocks and **downloads start immediately**, without waiting for the end of the list.
- Each worker is a separate, persistent process: no repeated program starts, no limit caused by Python's GIL.
- When a file finishes downloading and moves on to **conversion** (ffmpeg), its download slot is freed right away:
  the network already downloads the next song while the CPU converts the previous ones.
- It uses the fastest YouTube client (`visionos`, no ad wait); if a video fails, the next attempt automatically uses
  yt-dlp's default clients.
- **M4A and Opus are not re-encoded**: they are the fastest choice for huge playlists. MP3 uses a fast lame setting.

## The interface

- **Link preview**: as soon as you paste, the box below shows what was recognized (playlist, video, invalid links).
- **Download cards** with cover art, progress ring, counters (completed, downloading, converting, queued, errors) and
  estimated time.
- **List** with thumbnails, numbers, the state of every item, search by title or number, and filter tabs (all,
  downloading, queued, completed, errors).
- **Theme**: light, dark or automatic (button at the top right); adapts to phones and tablets.
- The same link cannot be added twice while it is already in progress. *Clear completed* empties the list without
  touching the files.

## Numbered files, in order

Each playlist has its own folder and the files are named `001 - Title.mp3`, `002 - ...` (the number of digits grows
with the playlist: 4 digits above 999 items, and so on), so the order is always the playlist's order. The folder also
contains `_playlist.m3u8` (the playlist in order, openable with VLC and similar players) and, if there are errors,
`_ERRORS.txt`. Single videos go to `Singles\` without a number.

## Errors: see right away which ones and why

- On the download card the **exact numbers** of the failed videos are shown (`Numbers: #012 #044 ...`).
- *Open list* → **Errors** tab: for each one you see number, title, **reason** (private video, deleted, blocked in your
  country, sign-in required, Music Premium only, network, ...), the technical message and a **Retry** or **Open**
  (on YouTube) button.
- The red panel groups errors by reason (click to filter) and offers **Retry all errors**, **Copy list** and
  **Download list (.txt)**.
- Private or deleted videos are reported immediately, already while the playlist is being read.
- Temporary errors (network, rate limit) are retried automatically; if YouTube limits requests, an **automatic pause**
  starts and then downloading resumes.

## Resume after a stop

If you close the program or the PC shuts down, downloads stop but their state stays saved: open `Start.bat` (or the
exe, or the app) again and press **Resume** on the download. Files already downloaded are recognized and skipped without
connecting to the Internet; if the playlist changed in the meantime, the numbers in the file names are updated.

## Cookies (age-restricted videos, your own private videos, anti-bot check)

*Settings → Cookies*: choose a browser where you are already signed in to YouTube (Firefox is the most reliable) or
upload a `cookies.txt` file exported from the browser. They are not needed for normal public videos.

## If something stops working

YouTube changes often. Go to *Settings → Update yt-dlp and restart*: in most cases that fixes everything.
Logs of the download processes: folder `generated\data\logs\` (with the exe: `%LOCALAPPDATA%\YT-Grabber\data\logs\`).

## Building from source

Nothing needs to be built to run the program from the sources: `Start.bat` / `Start.sh` only need Python 3 (tested with 3.13).
The ready-to-use files are built with a script each:

| Result | Script | Needs |
|---|---|---|
| `YT-Grabber.exe` | `build-exe\build-exe.bat` | Python (PyInstaller is fetched automatically) |
| `APK\*.apk` | `build-apk\build-apk.bat` | JDK 21, Android SDK, Gradle 8.7 (see [build-apk/README.md](build-apk/README.md)) |

## License and third-party components

YT Grabber is released under the [MIT License](LICENSE). It builds on other projects, each with its own license:
[yt-dlp](https://github.com/yt-dlp/yt-dlp) (downloading), [FFmpeg](https://ffmpeg.org/) (conversion, downloaded on
first start from [yt-dlp/FFmpeg-Builds](https://github.com/yt-dlp/FFmpeg-Builds)), [Deno](https://deno.com/)
(JavaScript runtime), [PyInstaller](https://pyinstaller.org/) (the exe) and
[youtubedl-android](https://github.com/yausername/youtubedl-android) (Python and FFmpeg for the Android app).
Programs and APKs that bundle them are also subject to their licenses.

## Responsible use

Only download content you have the right to save (yours, freely licensed, or for personal use where the law allows
it). Downloading may violate YouTube's Terms of Service. This project is not affiliated with YouTube or Google.
