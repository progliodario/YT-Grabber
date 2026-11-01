# Using YT Grabber

How to install it is in the [installation guide](install.md). This guide is about using it.

- [Downloading](#downloading) · [Numbered files](#numbered-files-in-order) · [Errors](#errors-which-ones-and-why) ·
  [Resuming](#resuming-after-a-stop) · [Cookies](#cookies)
- [Subscriptions](#subscriptions) · [Notifications and new versions](#notifications-and-new-versions) · [Languages](#languages)
- [Settings](#settings) · [Command-line options](#command-line-options) · [Where things are stored](#where-things-are-stored) ·
  [If something stops working](#if-something-stops-working)

![The main page: paste links, choose the format, press Download](screenshots/main-light.png)

Everything can be done with the keyboard and works with screen readers, high contrast and zoom: keys and details are in the
[accessibility statement](accessibility.md).

## Downloading

1. Paste one or more links in the box, **one per line**. Videos, playlists, albums, whole channels and YouTube Music links
   all work, and you can mix them. As you paste, a line below the box shows what was recognized (playlist, video, invalid link).
2. Choose **what to download**:
   - **Audio**: **MP3** (re-encoded: the slowest), **M4A** or **Opus** (not re-encoded: 2–3 times faster, no quality loss;
     the best choice for huge playlists). For MP3 you also choose the quality (128, 192, 256 or 320 kbps).
   - **Video**: the best quality up to the height you choose (360p to 4K), saved as MP4.
   - *Cover art and metadata* adds the thumbnail and the tags to the files.
   - *Video+playlist links: only the video*: a link to a video that is inside a playlist downloads only that video.
   - *Download again even if already present*: ignores the files that are already in the folder.
3. Press **Download**. Several links make several cards in the list; the same link cannot be added twice while it is in progress.

**Always 10 downloads at the same time**, in total, even with several playlists in the queue. The list is read in blocks and
the downloads start immediately, without waiting for the end of the list. When a file finishes downloading and moves on to
conversion (ffmpeg), its slot is freed at once, so the network already downloads the next song while the CPU converts the
previous ones.

![A playlist being downloaded: 10 at a time, with speed and time left](screenshots/downloads-light.png)

Each card shows the cover art, a progress ring, the counters (completed, downloading, converting, queued, errors), the
speed and the estimated time. Buttons: **Pause** / **Resume**, **Open list**, **Cancel**, **Folder** (opens the folder),
**Playlist M3U** (the playlist in order, to open with VLC and similar players), **Download all again**, **Remove**.
*Clear completed* empties the list without touching the files.

**Open list** shows every item with its thumbnail, number and state, a search box (by title or number) and filter tabs (all,
downloading, converting, queued, completed, errors). The theme is light, dark or automatic (button at the top right).

![The numbered list of a playlist, in the dark theme](screenshots/list-dark.png)

## Numbered files, in order

Each playlist has its own folder and the files are named `001 - Title.mp3`, `002 - ...`: the number is the position in the
playlist, so the order is always the playlist's order. The number of digits grows with the playlist (4 digits above 999
items, and so on). The folder also contains `_playlist.m3u8` and, if there were errors, `_ERRORS.txt`. Single videos go to
the `Singles` folder, without a number. If the playlist changes later, the numbers in the file names are updated.

## Errors: which ones, and why

- On the card you see the **exact numbers** of the videos that failed (`Numbers: #012 #044 ...`).
- *Open list* → **Errors** tab: for each one, the number, the title, the **reason** (private video, deleted, blocked in your
  country, sign-in required, YouTube Music Premium only, network, ...), the technical message and a **Retry** or **Open**
  (on YouTube) button.
- The red panel groups the errors by reason (click one to filter) and offers **Retry all errors**, **Copy list** and
  **Download list (.txt)**.
- Private and deleted videos are reported at once, while the playlist is still being read.
- Temporary errors (network, rate limit) are retried automatically. If YouTube limits the requests, an **automatic pause**
  starts and downloading resumes by itself.

## Resuming after a stop

If you close the program or the computer shuts down, the downloads stop but their state is saved: open YT Grabber again and press
**Resume** on the download. The files that are already there are recognized and skipped without connecting to the Internet.

## Cookies

Needed only for age-restricted videos, your own private videos, or when YouTube asks to "confirm you're not a bot".
*Settings → Cookies*: choose a browser where you are already signed in to YouTube (Firefox is the most reliable; Chrome and
Edge sometimes block reading their cookies while they are open) or upload a `cookies.txt` file exported from the browser. Normal
public videos do not need them.

## Subscriptions

Tick **Keep playlists and channels up to date** under the link box, choose how often to check (every hour up to once a
week) and press **Download**. The link is downloaded now and then checked at that interval: only the videos that are not
already in the folder are downloaded, so a check never repeats work.

![The two options for subscriptions: how often to check, and only new videos](screenshots/only-new.png)

If you only want what is published **from now on**, also tick **Only new videos: skip the ones already there**. YT Grabber
then makes a note of everything that is in the playlist, album or channel at that moment, downloads none of it, and from the
next check on downloads only the videos that were not on that list. The files keep the number of their position in the
playlist, and the skipped videos are listed as *Skipped*. To change the mode of an existing subscription, subscribe to the
same link again with the option ticked or not: what is there at that moment becomes the starting point.

The **Subscriptions** section lists everything you follow: when it was last checked, how many videos were found, the
*only new videos* tag, and buttons to change the interval, check now, pause or remove.

![Subscriptions: channels and playlists that are checked automatically](screenshots/subscriptions.png)

The program must be running for the checks to happen (on Windows it stays in the notification area; on Linux the packages
include a systemd service, see the [installation guide](install.md#subscriptions-in-the-background)). A check that finds nothing
new leaves no card in the list.

## Notifications and new versions

- When a download finishes you get a **system notification**: a bubble from the tray icon in the Windows app, a browser
  notification elsewhere (the browser asks for permission the first time; if it is blocked, allow it in the site settings).
  Subscription checks that find nothing new stay silent. Not available in the Android app.
- When a newer version of YT Grabber exists, a **notice** appears at the top of the page. For that, the program asks GitHub
  twice a day which is the latest release, sending only its name and version.

![The notice shown when a new version is available](screenshots/update-banner.png)

Both can be switched off in *Settings → Notifications and updates*, where *Check now* also looks for a new version at once.

## Languages

16 languages: English, Italiano, Español, Français, Deutsch, Português, Nederlands, Polski, Русский, Türkçe, العربية, हिन्दी,
Bahasa Indonesia, 中文, 日本語, 한국어. The page uses the language of your browser, and you can change it with the selector at
the top; the choice is remembered. The Windows app (menu, start-up window, installer) and the Android app follow the language
of the device. Arabic is shown right to left. The translations were written with an AI model and may need corrections: see
[CONTRIBUTING.md](../CONTRIBUTING.md#translations).

| Italiano | 日本語 | العربية |
|---|---|---|
| ![Italian](screenshots/lang-it.png) | ![Japanese](screenshots/lang-ja.png) | ![Arabic, right to left](screenshots/lang-ar.png) |

## Settings

![Settings: folder, cookies, notifications and updates](screenshots/settings.png)

- **Destination folder**: where the playlists' folders go.
- **Cookies**: see above.
- **Download engine**: the versions of yt-dlp, ffmpeg and the JavaScript runtime, and *Update yt-dlp and restart*.
- **Notifications and updates**: see above.

## Command-line options

Pass them to `Start.bat`, `./Start.sh`, `yt-grabber`, the AppImage or `YT-Grabber.exe`.

| Option | Meaning |
|---|---|
| `--port 9000` | the port of the page (default 8765; if it is busy, the next free one is used) |
| `--dir D:\Music` | the destination folder |
| `--host 0.0.0.0` | accept other devices on the network (a phone, a tablet): they open `http://COMPUTER-IP:8765/` and the files are still saved on the computer. Only on a network you trust |
| `--no-browser` | do not open the page |
| `--idle-exit 10` | quit after this many minutes without use (used by the AppImage and the Flatpak; never while something is downloading or a subscription is active) |
| `--background` | Windows app only: start in the notification area without opening the window |
| `--diag` | Windows app only: print where yt-dlp and the data are loaded from (run it from a terminal) |

## Where things are stored

| | Settings, list, cookies, tools, logs | Downloads |
|---|---|---|
| Windows (installed) | `%LOCALAPPDATA%\YT-Grabber` | `Downloads\YT-Grabber` |
| Linux packages, AppImage | `~/.local/share/yt-grabber` | `~/Downloads/YT-Grabber` |
| Flatpak | `~/.var/app/io.github.progliodario.YTGrabber` | `~/Downloads/YT-Grabber` |
| macOS | `~/Library/Application Support/YT-Grabber` | `~/Downloads/YT-Grabber` |
| Android app | private to the app | `Download/YT-Grabber` |
| From the sources, Termux | `generated/` next to `Start.bat` / `Start.sh` | `Downloads/YT-Grabber` |

Logs of the download processes are in the `data/logs` folder of the first column.

## If something stops working

- **Many errors at once, or nothing downloads**: YouTube changes often. *Settings → Update yt-dlp and restart* fixes it in
  most cases.
- **The same error on every video**: update yt-dlp first, then look at the cookies.
- **"ffmpeg not found" warning**: conversions need ffmpeg. Check the Internet connection and restart: it is downloaded on
  the start. On Linux you can also install it with the package manager.
- **The page does not open**: look at the address printed in the terminal (the port may be different if 8765 was busy).
  On Windows, check that YT Grabber is running in the notification area.
- **A phone cannot reach the page**: start the program with `--host 0.0.0.0`, use the computer's address, and allow the program
  through the firewall on private networks.
- **Slow MP3**: MP3 is re-encoded. M4A and Opus are not, and are much faster for big playlists.

Still stuck? [Open an issue](https://github.com/progliodario/YT-Grabber/issues/new/choose) and attach the log.
