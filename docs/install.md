# Installing YT Grabber

Ready-made files are on the [releases page](https://github.com/progliodario/YT-Grabber/releases/latest). Pick your system:

[Windows](#windows) · [macOS](#macos) · [Linux](#linux) · [Android](#android) · [iPhone and iPad](#iphone-and-ipad) ·
[From the source code](#from-the-source-code)

On the first start YT Grabber installs what it needs (yt-dlp, a JavaScript runtime, ffmpeg). You need Internet and about
200 MB, once. After that, how to use it is in the [usage guide](usage.md).

Before you install: if you want to be sure that a file is the genuine one, see [SECURITY.md](../SECURITY.md).

---

## Windows

Windows 10 or 11. Nothing else needs to be installed: Python is included.

### The installer (recommended)

1. Download `YT-Grabber-Setup-<version>.exe` and run it. It installs for your user account, so **no administrator
   password is needed** (the wizard also offers "for all users").
2. The setup has no paid code-signing certificate, so SmartScreen may show "Windows protected your PC": click
   **More info → Run anyway**. Why, and how to check the file, is in [SECURITY.md](../SECURITY.md).
3. Choose whether to add a desktop shortcut and whether YT Grabber starts when you sign in, and finish.

YT Grabber is now in the **Start menu** and in *Settings → Apps → Installed apps*.

Or from a terminal, with **winget**: `winget install progliodario.YTGrabber`; with **Scoop**:

```
scoop bucket add progliodario https://github.com/progliodario/scoop-bucket
scoop install yt-grabber
```

(Scoop unpacks the installer instead of running it: there is no entry in *Settings → Apps*, and you remove it with
`scoop uninstall yt-grabber`. Do not install both the installer and the Scoop version on the same PC.)

### Using it

- Open **YT Grabber** from the Start menu. It opens **in its own window** and puts an icon in the notification area
  (near the clock). The window is Microsoft Edge in "app mode" (Chrome, or the default browser, if Edge is missing).
- **Closing the window does not stop the downloads.** The program keeps running in the notification area: click its icon
  to bring the window back; right-click it for *Open YT Grabber*, *Open downloads folder* and *Quit*. Quit from there
  when you are done (it asks first if downloads are in progress; they can be resumed later).
- When a download finishes you get a bubble from the tray icon, even with the window closed.
- **First start only:** a small window shows the download of ffmpeg (about 200 MB). Later starts take a few seconds.
- The installer, this menu and the start-up window follow the language of Windows (16 languages).
- If the Windows firewall asks for network permission, allow **private networks**.

Settings, the download list, cookies, logs and the downloaded tools live in `%LOCALAPPDATA%\YT-Grabber`. Downloaded files go
to `Downloads\YT-Grabber`. The program log is `%LOCALAPPDATA%\YT-Grabber\data\logs\app.log`.

### Update and uninstall

- **Update:** run a newer installer (it keeps your settings and list). If YT Grabber is running, Setup asks you to quit it
  first (tray icon → Quit). winget: `winget upgrade progliodario.YTGrabber`; Scoop: `scoop update yt-grabber`.
- **Uninstall:** *Settings → Apps → Installed apps → YT Grabber → Uninstall*. It asks whether you also want to delete your
  settings and the downloaded tools; the music and videos you downloaded are never deleted.

---

## macOS

macOS 10.15 or newer, Intel and Apple Silicon. The app brings its own Python.

### With Homebrew

```
brew install --cask progliodario/tap/yt-grabber
```

It also removes the quarantine flag, so the first-start prompt below does not appear.

### By hand

1. Download `YT-Grabber-macOS.zip`, unzip it (a double click) and drag **YT-Grabber.app** to *Applications*.
2. The app is signed "ad hoc" but **not notarized by Apple** (that needs a paid developer account), so the first time macOS
   blocks it:
   - **macOS 14 or older:** right-click (or Control-click) the app → **Open** → **Open**.
   - **macOS 15 or newer:** double-click the app, then *System Settings → Privacy & Security*, scroll down to the message
     about YT-Grabber and click **Open Anyway**.
   - Or, in Terminal: `xattr -dr com.apple.quarantine /Applications/YT-Grabber.app`
3. A **Terminal window** opens and the browser goes to `http://localhost:8765/`. Keep the Terminal window open while
   downloading; close it (or press Ctrl+C) to quit.

The first start installs yt-dlp and downloads ffmpeg (about 45 MB, static builds from osxexperts.net).

Settings, the list, cookies, logs and the downloaded tools are in `~/Library/Application Support/YT-Grabber`; downloads go to
`~/Downloads/YT-Grabber` (the first time, macOS may ask permission to use the Downloads folder: allow it).

**Remove:** `brew uninstall --cask yt-grabber`, or drag the app to the Trash, and delete
`~/Library/Application Support/YT-Grabber`.

> Tested by GitHub Actions on a real Apple Silicon and a real Intel Mac (the app starts and serves the page). The
> double-click experience (Gatekeeper prompt, the Terminal window) has not been tried on a Mac by the maintainer.

---

## Linux

### The apt repository (Debian, Ubuntu, Linux Mint, Pop!_OS, Raspberry Pi OS)

Signed, and updated with the normal system updates:

```
sudo install -d /etc/apt/keyrings
curl -fsSL https://progliodario.github.io/YT-Grabber/yt-grabber.gpg | sudo tee /etc/apt/keyrings/yt-grabber.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/yt-grabber.gpg] https://progliodario.github.io/YT-Grabber/apt stable main" | sudo tee /etc/apt/sources.list.d/yt-grabber.list
sudo apt update && sudo apt install yt-grabber
```

### The dnf repository (Fedora, RHEL, Rocky, Alma, openSUSE)

```
sudo curl -fsSL -o /etc/yum.repos.d/yt-grabber.repo https://progliodario.github.io/YT-Grabber/yt-grabber.repo
sudo dnf install yt-grabber
```

### A downloaded package

```
sudo apt install ./yt-grabber_<version>_all.deb          # Debian / Ubuntu family
sudo dnf install ./yt-grabber-<version>-1.noarch.rpm     # Fedora / RHEL family
```

The `.deb` and `.rpm` work on every processor (PC, ARM, Raspberry Pi). They need **Python 3 and pip** (the package manager
installs them if missing); `ffmpeg` and `python3-tk` (for the *Browse...* button) are recommended. On Fedora ffmpeg is not in
the default repositories: if the system has none, YT Grabber downloads a static copy on the first start.

Open **YT Grabber** from the applications menu, or run `yt-grabber` in a terminal. A terminal window stays open while it
runs; close it (or press Ctrl+C) to quit. The program is installed in `/opt/yt-grabber` and is never modified.

### AppImage (any distribution)

One file with its own Python, nothing to install:

```
chmod +x YT-Grabber-x86_64.AppImage      # or YT-Grabber-aarch64.AppImage on ARM
./YT-Grabber-x86_64.AppImage
```

### Flatpak

```
flatpak install --user YT-Grabber-x86_64.flatpak
flatpak run io.github.progliodario.YTGrabber
```

The AppImage and the Flatpak have no window to close: they quit by themselves after 10 minutes without use (never while a
download or a subscription is active).

### Subscriptions in the background

Subscriptions need the program to be running. The `.deb` and `.rpm` include a systemd user service that keeps it running
without a window; then you just open `http://localhost:8765/` whenever you want to look:

```
systemctl --user enable --now yt-grabber
```

### Where things are

| | |
|---|---|
| Settings, list, cookies, yt-dlp, logs | `~/.local/share/yt-grabber` (Flatpak: `~/.var/app/io.github.progliodario.YTGrabber`) |
| Downloaded files | the *Downloads* folder of your user, in `YT-Grabber` (change it in *Settings*) |

**Remove:** `sudo apt remove yt-grabber` (or `sudo dnf remove yt-grabber`); optionally `rm -rf ~/.local/share/yt-grabber`.

> Tested by GitHub Actions before every release: the `.deb` is installed and started on Ubuntu, the `.rpm` on Fedora, the
> AppImage on Ubuntu, the Flatpak is built and run, and the apt and dnf repositories are installed from. Other
> distributions and desktops have not been tried: please report problems.

---

## Android

### The app (no computer needed)

A standalone app that contains everything (Python, yt-dlp, ffmpeg and the interface). It downloads, numbers and saves by
itself into the phone's *Download* folder, always with 10 downloads in parallel.

| File | For which phones |
|---|---|
| `YT-Grabber-arm64-v8a.apk` | **almost all phones from 2017 onwards: choose this one** |
| `YT-Grabber-armeabi-v7a.apk` | 32-bit phones, very old |
| `YT-Grabber-x86_64.apk` | Android emulators on a PC |

1. Copy the APK to the phone (USB cable, Drive, Telegram, email...) or download it there from the releases page.
2. Open it from the file manager. Android asks you to allow *"Install unknown apps"* for the app you are using (Files,
   Chrome...): allow it. This is normal for apps that do not come from the Play Store. If Android warns that the app "was not
   verified by Play Protect", choose *Install anyway*.
3. Open **YT Grabber**. The first start takes a few tens of seconds to prepare the engine, then allow:
   - **Notifications** (to see the progress and the *Close* button);
   - **All files access** (to save into *Download/YT-Grabber*; if you refuse, files go to a private app folder);
   - the **battery optimization** exclusion, so it also downloads with the screen off.

Use it:

- Paste links and press **Download**. From YouTube, YouTube Music or Chrome you can tap *Share → YT Grabber*.
- While it downloads there is a notification with the progress. You can close the app: downloads continue. To stop
  everything, tap **Close** in the notification.
- To resume after a stop or a restart: reopen the app and press **Resume**.
- On the phone the default format is **M4A**: no re-encoding, fastest, least battery. Use Wi-Fi for big playlists.
- Android 12 or newer may limit background processes: if downloads stop by themselves, turn on **Disable child process
  restrictions** in *Developer options*.

To **update**, install the new APK over the old one (it has the same signing key). The page shows a notice when a new
version is out. When a download finishes the app posts a notification of its own (switch it off in the settings of the page).

> Tested in an Android 14 emulator (x86_64): first start with all the permission requests, engine extraction, server start,
> sharing a link from another app, a download of an 11-video playlist saved and numbered in `Download/YT-Grabber`, and the
> automatic restart of the service after the system killed the process. The `arm64-v8a` APK has the same code and libraries
> but was **not run on a physical phone** by the maintainer.

### Termux (alternative to the app)

The program runs on the phone inside the free **Termux** app. The computer is only needed to hand over the files once.
Prefer the APK if you can: it is easier.

1. **Install Termux from F-Droid** (<https://f-droid.org/packages/com.termux/>), **not** the Play Store one (it is old and
   does not work). Optional: **Termux:Widget**, also from F-Droid, for a start icon on the Home screen.
2. **On the PC** (same Wi-Fi as the phone), from a copy of this repository, double-click
   `packaging\termux\Share-to-phone.bat`. It prints a command like `curl -s http://192.168.1.20:8800/i | sh`. If Windows
   asks for firewall permission, allow *private networks*. Leave the window open.
3. **On the phone**, paste that command into Termux. It downloads Python, ffmpeg and yt-dlp (a few minutes). Then you can
   close the window on the PC.

Without a shared Wi-Fi: run `python packaging/termux/share_to_phone.py --zip-only` on the PC (it creates
`generated/YT-Grabber-android.zip`), copy the zip to the phone's *Download* folder and, in Termux:

```
termux-setup-storage
pkg install -y unzip && mkdir -p ~/yt-grabber && unzip -o ~/storage/downloads/YT-Grabber-android.zip -d ~/yt-grabber && sh ~/yt-grabber/termux/install-termux.sh
```

Every day: open Termux and type `cd yt-grabber && sh Start.sh` (or tap the *YT-Grabber* icon of Termux:Widget). The browser
opens at `http://localhost:8765/`. **Keep Termux open** while it downloads; Ctrl+C stops it. Files are in
**Download/YT-Grabber**. To get an app-like icon, in Chrome use ⋮ → **Add to Home screen**.

Recommended: *Settings → Apps → Termux → Battery → Unrestricted*; on Android 12 or newer, *Disable child process
restrictions* in *Developer options*. To update the program, repeat steps 2 and 3 (your downloads and settings stay). Logs are
in `~/yt-grabber/generated/data/logs/`.

---

## iPhone and iPad

There is **no iOS app**, and one cannot be built for this program: iOS does not allow an app to run a Python server or
yt-dlp, an app needs Apple's signing (a paid developer account), and Apple does not accept YouTube downloaders in the App
Store. What works is to use the web page from the phone, with the program running on a computer (or any always-on Linux
box, such as a Raspberry Pi) on the same Wi-Fi:

1. On the computer start the program so it accepts other devices: `Start.bat --host 0.0.0.0` (Windows),
   `./Start.sh --host 0.0.0.0` (Linux, macOS) or `yt-grabber --host 0.0.0.0` (Linux package). With the Windows installer
   run `YT-Grabber.exe --host 0.0.0.0` from `%LOCALAPPDATA%\Programs\YT Grabber`. It prints the address to use, for example
   `http://192.168.1.6:8765/`.
2. On the iPhone or iPad open that address in **Safari**. For an app-like icon: Share → **Add to Home Screen**.
3. Paste the links and press **Download**: the files are saved on the computer. To get a file on the phone, open the list
   and use the save button next to a finished item.

Only do this on a network you trust: anyone on the same Wi-Fi can open the page. The iPhone and iPad use has **not been
tried** by the maintainer (no device was available): it is the same page that works in Chrome and Firefox.

---

## From the source code

You need Python 3 (3.10 or newer; developed with 3.12 and 3.13). Get the code with `git clone https://github.com/progliodario/YT-Grabber`
or the *Download ZIP* button, then:

- **Windows:** double-click **`Start.bat`** (if Python is missing it offers to install it with winget).
- **Linux, macOS, Termux:** run **`./Start.sh`**.

The first start installs yt-dlp, the JavaScript runtime and ffmpeg into the `generated/` folder (not in git). Options: `--port 9000`,
`--dir D:\Music`, `--host 0.0.0.0` (to use it from another device on the network: open `http://COMPUTER-IP:8765/`; the files
are still saved on the computer running the program), `--no-browser`. The full list is in the [usage guide](usage.md#command-line-options).
