# Using YT Grabber

Installation is described in the [installation guide](install.md). This guide describes how to use the program.

- [Downloading](#downloading) · [Choosing the videos](#choosing-the-videos) · [Numbered files](#numbered-files-in-order) ·
  [Errors](#errors-which-ones-and-why) ·
  [Resuming](#resuming-after-a-stop) · [Cookies](#cookies)
- [Subscriptions](#subscriptions) · [Notifications and new versions](#notifications-and-new-versions) · [Languages](#languages)
- [Settings](#settings) · [Command-line options](#command-line-options) · [Where things are stored](#where-things-are-stored) ·
  [If something stops working](#if-something-stops-working)

![The main page: paste links, choose the format, press Download](screenshots/main-light.png)

Every function can be used with the keyboard, and the program works with screen readers, high contrast and zoom. The keys and
further details are given in the [accessibility statement](accessibility.md).

## Downloading

1. Paste one or more links in the box, **one per line**. Videos, playlists, albums, entire channels and YouTube Music links are
   all accepted and can be mixed. While the links are pasted, a line below the box shows what was recognised (playlist, video,
   invalid link).
2. Choose **what to download**:
   - **Audio**: **MP3** (re-encoded, therefore the slowest), **M4A** or **Opus** (not re-encoded: two to three times faster, with
     no loss of quality, and the best choice for very large playlists). For MP3, the quality is also selected (128, 192, 256 or
     320 kbps). **FLAC**, **WAV** and **OGG** (Vorbis) are also offered; they are always re-encoded. FLAC and WAV are
     lossless, but the audio of YouTube is already compressed, so the files are much bigger without sounding better (WAV also cannot
     carry a cover picture).
   - **Video**: the best available quality up to the chosen height (360p to 4K), saved as MP4. *Subtitles inside the video* (with
     the language codes to look for, for example `en, it`) puts the subtitles in the MP4, from the ones the author wrote or, when
     there are none, the automatic ones.
   - *Cover art and metadata* adds the thumbnail and the tags to the files.
   - *Cut out sponsor segments (SponsorBlock)* removes the parts that the SponsorBlock community has marked as sponsorship,
     self-promotion or a reminder to like and subscribe, in audio and in video. It asks the SponsorBlock service
     (`sponsor.ajay.app`) for the marks of each video, which sends it the video identifier; videos without marks are left as they are.
   - *Video+playlist links: only the video*: a link to a video that belongs to a playlist downloads only that video.
   - *Download again even if already present*: ignores the files that are already in the folder.
   - *Let me choose the videos first*: nothing is downloaded until the unwanted videos have been unticked (see [Choosing the videos](#choosing-the-videos)).
3. Press **Download**. Several links produce several cards in the list. The same link cannot be added twice while it is in progress.

**Exactly 10 downloads run at the same time** in total, even when several playlists are queued. The list is read in blocks, and the
downloads start immediately, without waiting for the end of the list. When a file has been downloaded and passes to conversion
(ffmpeg), its slot is released at once, so the network already downloads the next song while the processor converts the previous
ones.

![A playlist being downloaded: 10 at a time, with speed and time left](screenshots/downloads-light.png)

Each card shows the cover art, a progress ring, the counters (completed, downloading, converting, queued, errors), the speed and the
estimated time. The buttons are **Pause** / **Resume**, **Open list**, **Cancel**, **Folder** (opens the folder), **Playlist M3U**
(the playlist in order, to be opened with VLC and similar players), **Download all again** and **Remove**. *Clear completed* empties
the list without touching the files.

**Open list** shows every item with its thumbnail, number and state, a search box (by title or number) and filter tabs (all,
downloading, converting, queued, completed, errors). The theme is light, dark or automatic (button at the top right). Within the
list, the arrow keys move from one item to the next.

![The numbered list of a playlist, in the dark theme](screenshots/list-dark.png)

## Choosing the videos

By default a whole playlist is downloaded. To leave some videos out, there are two ways:

- **Before the download starts.** Select **Let me choose the videos first** under the link box (the choice is remembered) and press
  **Download**. The program reads the list but downloads nothing: the card says *Choose the videos* and its list opens with a box in
  every row. Untick the videos that are not wanted (*Select all* and *Select none* act on the whole list, *Invert selection* swaps ticked and unticked, and
  *Select a range…* asks for numbers and ranges such as `1-20, 25, 30-35`, ticking those and leaving out all the others; with the
  keyboard, the arrow keys move between the rows and Space ticks or unticks the one that has the focus), then press **Start**, which
  shows how many videos are selected.
- **While the download runs.** Every video that is still waiting has a **Do not download this video** button. A video that was left
  out shows **Download this video after all**, also when the job has already finished.

![A playlist waiting for the choice: a box in every row, Select all and Select none, and the Start button](screenshots/choose-videos.png)

The videos that were left out are listed as *Skipped* ("You chose not to download it"), with their own tab in the list. The files keep
the number of their position in the playlist, so the numbers of the downloaded files have gaps where videos were left out. A
subscription that checks the same playlist later downloads the videos that are missing from the folder again: leaving a video out
applies to that download only.

## Numbered files, in order

Each playlist has its own folder, and the files are named `001 - Title.mp3`, `002 - ...`. The number is the position in the
playlist, so the order is always that of the playlist. The number of digits grows with the playlist (four digits above 999 items,
and so on). The folder also contains `_playlist.m3u8` and, if errors occurred, `_ERRORS.txt`. Single videos are saved in the
`Singles` folder, without a number. If the playlist changes later, the numbers in the file names are updated.

## Errors: which ones, and why

- The card shows the **exact numbers** of the videos that failed (`Numbers: #012 #044 ...`).
- *Open list* → **Errors** tab: for each failure, the number, the title, the **reason** (private video, deleted, blocked in the
  country, sign-in required, YouTube Music Premium only, network, and so on), the technical message and a **Retry** or **Open** (on
  YouTube) button.
- The red panel groups the errors by reason (selecting one filters the list) and offers **Retry all errors**, **Copy list** and
  **Download list (.txt)**.
- Private and deleted videos are reported immediately, while the playlist is still being read.
- Temporary errors (network, rate limit) are retried automatically. If YouTube limits the requests, an **automatic pause** starts
  and downloading resumes by itself.

## Pausing everything

When several downloads are on the list, **Pause all** and **Resume all** (next to *Clear completed*) act on all of them at once. They
appear only when there is something to pause or resume; lists that are waiting for the choice of the videos are left as they are. A
pause does not stop the videos that are already downloading: they finish, and nothing new starts.

The button **Move to top** on a list that is downloading makes the scheduler serve it before the others (the 10 downloads in
progress are not interrupted: the next free slots go to that list). After a restart the lists return to the order in which they were
added.

## Resuming after a stop

If the program is closed or the computer shuts down, the downloads stop but their state is saved. After YT Grabber is opened again,
pressing **Resume** on the download continues it. Files that are already present are recognised and skipped without connecting to
the Internet.

## Cookies

Cookies are needed only for age-restricted videos, for the user's own private videos, or when YouTube asks to "confirm you're not a
bot". In *Settings → Cookies*, select a browser in which the user is already signed in to YouTube (Firefox is the most reliable;
Chrome and Edge sometimes prevent their cookies from being read while they are open) or upload a `cookies.txt` file exported from
the browser. Normal public videos do not need cookies.

## Subscriptions

Select **Keep playlists and channels up to date** under the link box, choose how often to check (from every hour to once a week)
and press **Download**. The link is downloaded immediately and then checked at that interval. Only the videos that are not already in
the folder are downloaded, so a check never repeats work.

![The two options for subscriptions: how often to check, and only new videos](screenshots/only-new.png)

To receive only what is published **from now on**, also select **Only new videos: skip the ones already there**. YT Grabber then
records everything that is in the playlist, album or channel at that moment, downloads none of it, and from the next check onwards
downloads only the videos that were not on that list. The files keep the number of their position in the playlist, and the skipped
videos are listed as *Skipped*. To change the mode of an existing subscription, subscribe to the same link again with the option
selected or cleared: what exists at that moment becomes the starting point.

The **Subscriptions** section lists everything that is followed: when it was last checked, how many videos were found, the *only new
videos* tag, and buttons to change the interval, check immediately, pause or remove.

![Subscriptions: channels and playlists that are checked automatically](screenshots/subscriptions.png)

The program must be running for the checks to take place (on Windows it remains in the notification area; on Linux the packages
include a systemd service, see the [installation guide](install.md#subscriptions-in-the-background)). A check that finds nothing new
leaves no card in the list.

## Notifications and new versions

- When a download finishes, a **system notification** is shown: a bubble from the tray icon in the Windows application, and a browser
  notification elsewhere (the browser asks for permission the first time; if it is blocked, it must be allowed in the site
  settings). Subscription checks that find nothing new remain silent. In the Android application it is a normal notification of the
  application (Android asks for permission the first time; the progress notification is unchanged).
- When a newer version of YT Grabber exists, a **notice** appears at the top of the page. To detect it, the program asks GitHub twice
  a day for the latest release, sending only the program name and version.
- In the **Windows application**, the notice has an **Update now** button. It asks for confirmation, downloads the installer from
  the project's releases, checks its SHA-256 fingerprint against the one published by GitHub, closes the application, installs the
  new version and opens it again. Nothing is installed if the fingerprint does not match. Installations made with Scoop, winget or
  Chocolatey are updated with their own tool, so the button is not shown for them.

![The notice shown when a new version is available](screenshots/update-banner.png)

Both functions can be disabled in *Settings → Notifications and updates*, where *Check now* also looks for a new version
immediately.

## Languages

16 languages are available: English, Italiano, Español, Français, Deutsch, Português, Nederlands, Polski, Русский, Türkçe, العربية,
हिन्दी, Bahasa Indonesia, 中文, 日本語, 한국어. The page uses the language of the browser, which can be changed with the selector at the
top; the choice is remembered. The Windows application (menu, start-up window, installer) and the Android application follow the
language of the device. Arabic is shown right to left. The translations were written with an AI model and may need corrections; see
[CONTRIBUTING.md](../CONTRIBUTING.md#translations).

| Italiano | 日本語 | العربية |
|---|---|---|
| ![Italian](screenshots/lang-it.png) | ![Japanese](screenshots/lang-ja.png) | ![Arabic, right to left](screenshots/lang-ar.png) |

## Settings

![Settings: folder, cookies, notifications and updates](screenshots/settings.png)

- **Destination folder**: where the folders of the playlists are created.
- **Cookies**: see above.
- **Download engine**: the versions of yt-dlp, ffmpeg and the JavaScript runtime, and *Update yt-dlp and restart*. The option
  *Keep yt-dlp up to date automatically* (enabled by default) makes YT Grabber ask GitHub once a day for the latest yt-dlp release.
  When a newer one exists, it is installed as soon as nothing is downloading and nobody has pressed anything in the page for two
  minutes, and the program restarts by itself (queued and paused downloads are saved and can be resumed). The same version is never
  installed more than once a day, so a failed update cannot cause repeated restarts.
- **Speed, schedule and proxy**: *Speed limit* is in KB/s and applies to **each** of the (up to 10) simultaneous downloads, 0 meaning
  no limit. *Download only during these hours* lets nothing new start outside the chosen window (for example 01:00 to 07:00); what is
  already downloading finishes, and a note at the top of the page says that the program is waiting. A window whose end is before its
  start goes through midnight (22:00 to 06:00). *Proxy* is the address of a proxy server used by all the downloads and by the reading
  of the lists: `http://host:port`, `https://host:port`, `socks4://host:port` or `socks5://host:port`, with `user:password@` before
  the host if the proxy asks for one. The address is kept in the settings file of the data folder.
- **Library**: *Do not download a video twice* looks, before downloading, for the same video (same format) in another folder where
  YT Grabber already saved it: if the file is still there it is linked into the new folder (a hard link, so it takes no more space
  on the same drive; a copy otherwise) with the number of its place in the new list. Only videos downloaded since the option exists
  are known (the list is kept in `archive.json` in the data folder).
- **Backup**: *Save subscriptions and links* downloads `yt-grabber-backup.json`, a small file with the subscriptions (link, interval,
  format, *only new videos*) and the links of the lists that are on the page. It holds no cookies, settings, folders or files.
  *Restore from a backup file* adds the subscriptions of such a file (the ones that already exist stay as they are; a restored
  subscription is first checked about a minute later, and the following ones half a minute apart) and puts its links in the box
  of the page, ready to be downloaded: nothing is downloaded until *Download* is pressed. Only YouTube playlists and channels are
  accepted as subscriptions.
- **Text size**: 100%, 125%, 150% or 200%, in addition to the zoom of the browser. The choice is remembered on the device.
- **Notifications and updates**: see above.

## Command-line options

These options are passed to `Start.bat`, `./Start.sh`, `yt-grabber`, the AppImage or `YT-Grabber.exe`.

| Option | Meaning |
|---|---|
| `--port 9000` | the port of the page (default 8765; if it is busy, the next free port is used) |
| `--dir D:\Music` | the destination folder |
| `--host 0.0.0.0` | accept other devices on the network (a phone or a tablet), which open `http://COMPUTER-IP:8765/`; the files are still saved on the computer. To be used only on a trusted network |
| `--token` | require an access token for the page: the address printed at start (and the one of the window) carries it, and a browser that opens it keeps it in a cookie. The token is kept in the data folder (`token.txt`), so the address stays the same between runs |
| `--no-token` | with `--host 0.0.0.0` only: do not ask for the token (anyone on the network can use the page; to be used only on a network that is trusted) |
| `--no-browser` | do not open the page |
| `--idle-exit 10` | quit after this many minutes without use (used by the AppImage and the Flatpak; never while something is downloading or a subscription is active) |
| `--background` | Windows application only: start in the notification area without opening the window |
| `--diag` | Windows application only: print where yt-dlp and the data are loaded from (to be run from a terminal) |

## Where things are stored

| | Settings, list, cookies, tools, logs | Downloads |
|---|---|---|
| Windows (installed) | `%LOCALAPPDATA%\YT-Grabber` | `Downloads\YT-Grabber` |
| Linux packages, AppImage | `~/.local/share/yt-grabber` | `~/Downloads/YT-Grabber` |
| Flatpak | `~/.var/app/io.github.progliodario.YTGrabber` | `~/Downloads/YT-Grabber` |
| macOS | `~/Library/Application Support/YT-Grabber` | `~/Downloads/YT-Grabber` |
| Android application | private to the application | `Download/YT-Grabber` |
| From the sources, Termux | `generated/` next to `Start.bat` / `Start.sh` | `Downloads/YT-Grabber` |

The logs of the download processes are in the `data/logs` folder of the first column.

## If something stops working

- **Many errors at once, or nothing downloads:** YouTube changes frequently. yt-dlp is normally updated automatically (see
  [Settings](#settings)); if the problem appears before that happens, *Settings → Update yt-dlp and restart* resolves it in most
  cases.
- **The same error on every video:** update yt-dlp first, then check the cookies.
- **"ffmpeg not found" warning:** conversions require ffmpeg. The Internet connection should be checked and the program restarted,
  because ffmpeg is downloaded at start. On Linux it can also be installed with the package manager.
- **The page does not open:** read the address printed in the terminal (the port may differ if 8765 was busy). On Windows, check that
  YT Grabber is running in the notification area.
- **A phone cannot reach the page:** start the program with `--host 0.0.0.0`, use the address of the computer **as printed by
  the program** (it ends with `/?t=...`: that part is the access token), and allow the program through the firewall on private networks.
- **"An access link is needed":** the page was opened without its token. Use the address printed when the program starts, or open the
  page from the program (the window, the tray menu, the Android application).
- **Slow MP3:** MP3 is re-encoded, whereas M4A and Opus are not and are much faster for large playlists.

If the problem persists, [open an issue](https://github.com/progliodario/YT-Grabber/issues/new/choose) and attach the log.
