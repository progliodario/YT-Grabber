# Installing YT Grabber

Ready-made files are available on the [releases page](https://github.com/progliodario/YT-Grabber/releases/latest). Select the
system in use:

[Windows](#windows) · [macOS](#macos) · [Linux](#linux) · [Android](#android) · [iPhone and iPad](#iphone-and-ipad) ·
[From the source code](#from-the-source-code)

At the first start, YT Grabber installs the components it requires (yt-dlp, a JavaScript runtime and ffmpeg). This needs an
Internet connection and approximately 200 MB, once only. Instructions for using the program are given in the
[usage guide](usage.md).

To verify that a file is genuine before installing it, see [SECURITY.md](../SECURITY.md).

---

## Windows

Windows 10 or 11. Nothing else needs to be installed, because Python is included.

### The installer (recommended)

1. Download `YT-Grabber-Setup-<version>.exe` and run it. The installation is made for the current user account, so **no
   administrator password is required** (the wizard also offers an installation for all users).
2. The installer is not signed with a paid code-signing certificate, so SmartScreen may display "Windows protected your PC".
   Select **More info → Run anyway**. The reason, and the way to verify the file, are explained in [SECURITY.md](../SECURITY.md).
3. Choose whether to add a desktop shortcut and whether YT Grabber should start at sign-in, then finish the wizard.

YT Grabber then appears in the **Start menu** and in *Settings → Apps → Installed apps*.

It can also be installed from a terminal with **winget** (`winget install progliodario.YTGrabber`) or with **Scoop**:

```
scoop bucket add progliodario https://github.com/progliodario/scoop-bucket
scoop install yt-grabber
```

Scoop unpacks the installer instead of running it. As a consequence, there is no entry in *Settings → Apps*, and the program is
removed with `scoop uninstall yt-grabber`. The installer and the Scoop version should not be installed on the same computer.

### Using it

- Open **YT Grabber** from the Start menu. It opens **in its own window** and places an icon in the notification area (near the
  clock). The window is Microsoft Edge in "app mode" (Chrome, or the default browser, if Edge is not present).
- **Closing the window does not stop the downloads.** The program continues to run in the notification area. Clicking its icon
  brings the window back, and right-clicking it offers *Open YT Grabber*, *Open downloads folder* and *Quit*. *Quit* should be used
  when the program is no longer needed; it asks for confirmation if downloads are in progress, and they can be resumed later.
- When a download finishes, a bubble is shown by the tray icon, even if the window is closed.
- **First start only:** a small window shows the download of ffmpeg (about 200 MB). Later starts take a few seconds.
- The installer, the tray menu and the start-up window follow the language of Windows (16 languages).
- If the Windows firewall requests network permission, **private networks** should be allowed.

Settings, the download list, cookies, logs and the downloaded tools are stored in `%LOCALAPPDATA%\YT-Grabber`. Downloaded files are
saved in `Downloads\YT-Grabber`. The program log is `%LOCALAPPDATA%\YT-Grabber\data\logs\app.log`.

### Updating and uninstalling

- **Update:** when a new version is available, the notice at the top of the page offers **Update now**. The button downloads the
  installer, verifies it, closes the application, installs the new version and reopens it; settings and the list are kept.
  Alternatively, a newer installer can be run manually. If YT Grabber is running, the installer asks to quit it first (tray icon →
  Quit). With winget, use `winget upgrade progliodario.YTGrabber`; with Scoop, `scoop update yt-grabber`.
- **Uninstall:** *Settings → Apps → Installed apps → YT Grabber → Uninstall*. The uninstaller asks whether the settings and the
  downloaded tools should also be deleted. The music and videos that were downloaded are never deleted.

---

## macOS

macOS 10.15 or later, on Intel and Apple Silicon. The application includes its own Python.

### With Homebrew

```
brew install --cask progliodario/tap/yt-grabber
```

This also removes the quarantine flag, so the first-start prompt described below does not appear.

### Manual installation

1. Download `YT-Grabber-macOS.zip`, unzip it (double-click) and drag **YT-Grabber.app** to *Applications*.
2. The application is signed "ad hoc" but **not notarised by Apple** (notarisation requires a paid developer account), so macOS
   blocks it the first time:
   - **macOS 14 or earlier:** right-click (or Control-click) the application → **Open** → **Open**.
   - **macOS 15 or later:** double-click the application, then open *System Settings → Privacy & Security*, scroll down to the
     message about YT-Grabber and select **Open Anyway**.
   - Alternatively, in Terminal: `xattr -dr com.apple.quarantine /Applications/YT-Grabber.app`
3. A **Terminal window** opens and the browser goes to `http://localhost:8765/`. The Terminal window must remain open while
   downloading; closing it (or pressing Ctrl+C) quits the program.

At the first start, yt-dlp is installed and ffmpeg is downloaded (about 45 MB, static builds from osxexperts.net).

Settings, the list, cookies, logs and the downloaded tools are stored in `~/Library/Application Support/YT-Grabber`. Downloads are
saved in `~/Downloads/YT-Grabber` (the first time, macOS may ask for permission to use the Downloads folder, which should be
allowed).

**Removal:** `brew uninstall --cask yt-grabber`, or move the application to the Trash, and delete
`~/Library/Application Support/YT-Grabber`.

> GitHub Actions tests the application on a real Apple Silicon Mac and a real Intel Mac (the application starts and serves the
> page). The double-click experience (the Gatekeeper prompt and the Terminal window) has not been tried on a Mac by the maintainer.

---

## Linux

### The apt repository (Debian, Ubuntu, Linux Mint, Pop!_OS, Raspberry Pi OS)

The repository is signed and is updated together with the normal system updates:

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

The `.deb` and `.rpm` packages work on every processor (PC, ARM, Raspberry Pi). They require **Python 3 and pip**, which the package
manager installs if they are missing; `ffmpeg` and `python3-tk` (for the *Browse...* button) are recommended. On Fedora, ffmpeg is
not in the default repositories: if the system does not have it, YT Grabber downloads a static copy at the first start.

**YT Grabber** can be opened from the applications menu, or by running `yt-grabber` in a terminal. A terminal window remains open
while the program runs; closing it (or pressing Ctrl+C) quits the program. The program is installed in `/opt/yt-grabber` and is
never modified.

### AppImage (any distribution)

A single file with its own Python; nothing needs to be installed:

```
chmod +x YT-Grabber-x86_64.AppImage      # or YT-Grabber-aarch64.AppImage on ARM
./YT-Grabber-x86_64.AppImage
```

### Flatpak

```
flatpak install --user YT-Grabber-x86_64.flatpak
flatpak run io.github.progliodario.YTGrabber
```

The AppImage and the Flatpak have no window to close: they quit automatically after 10 minutes without use (never while a download
or a subscription is active).

### Subscriptions in the background

Subscriptions require the program to be running. The `.deb` and `.rpm` packages include a systemd user service that keeps it
running without a window; `http://localhost:8765/` is then opened whenever needed:

```
systemctl --user enable --now yt-grabber
```

### File locations

| Data | Location |
|---|---|
| Settings, list, cookies, yt-dlp, logs | `~/.local/share/yt-grabber` (Flatpak: `~/.var/app/io.github.progliodario.YTGrabber`) |
| Downloaded files | the *Downloads* folder of the user, in `YT-Grabber` (can be changed in *Settings*) |

**Removal:** `sudo apt remove yt-grabber` (or `sudo dnf remove yt-grabber`); optionally `rm -rf ~/.local/share/yt-grabber`.

> GitHub Actions tests the packages before every release: the `.deb` is installed and started on Ubuntu, the `.rpm` on Fedora, the
> AppImage on Ubuntu, the Flatpak is built and run, and the apt and dnf repositories are installed from. Other distributions and
> desktop environments have not been tried; problems should be reported.

---

## Android

### The application (no computer required)

A standalone application that contains everything it needs (Python, yt-dlp, ffmpeg and the interface). It downloads, numbers and
saves the files by itself in the *Download* folder of the phone, always with 10 downloads in parallel.

| File | Suitable phones |
|---|---|
| `YT-Grabber-arm64-v8a.apk` | **almost all phones from 2017 onwards: this is the file to choose** |
| `YT-Grabber-armeabi-v7a.apk` | 32-bit phones (very old) |
| `YT-Grabber-x86_64.apk` | Android emulators on a PC |

1. Copy the APK to the phone (USB cable, a cloud drive, Telegram, email, and so on) or download it directly from the releases page.
2. Open it from the file manager. Android asks for permission to *"Install unknown apps"* for the application in use (Files,
   Chrome, and so on), which must be allowed. This is normal for applications that do not come from the Play Store. If Android warns
   that the application "was not verified by Play Protect", choose *Install anyway*.
3. Open **YT Grabber**. The first start takes a few tens of seconds to prepare the engine. The following permissions are then
   requested:
   - **Notifications** (for the progress, the *Close* button and the notification of a finished download);
   - **All files access** (to save in *Download/YT-Grabber*; if it is refused, the files are saved in a private application folder);
   - the **battery optimisation** exclusion, so that downloads also continue with the screen off.

Use:

- Paste the links and press **Download**. From YouTube, YouTube Music or Chrome, *Share → YT Grabber* can be used.
- While downloading, a notification shows the progress. The application can be closed and the downloads continue. To stop
  everything, tap **Close** in the notification.
- To resume after a stop or a restart, reopen the application and press **Resume**.
- On the phone the default format is **M4A**: it requires no re-encoding, so it is the fastest and uses the least battery. Wi-Fi is
  recommended for large playlists.
- Android 12 or later may limit background processes. If downloads stop by themselves, enable **Disable child process
  restrictions** in *Developer options*.

To **update**, install the new APK over the old one (it has the same signing key). The page shows a notice when a new version is
available. When a download finishes, the application posts a notification of its own (it can be disabled in the settings of the
page).

> Tested in an Android 14 emulator (x86_64): first start with all the permission requests, engine extraction, server start, sharing a
> link from another application, a download of an 11-video playlist saved and numbered in `Download/YT-Grabber`, and the automatic
> restart of the service after the system terminated the process. The `arm64-v8a` APK contains the same code and libraries but was
> **not run on a physical phone** by the maintainer.

### Termux (alternative to the application)

The program runs on the phone inside the free **Termux** application. A computer is needed only to hand over the files once. The
APK is preferable whenever possible, because it is simpler.

1. **Install Termux from F-Droid** (<https://f-droid.org/packages/com.termux/>), **not** from the Play Store (that version is
   outdated and does not work). Optionally, install **Termux:Widget**, also from F-Droid, to obtain a start icon on the Home screen.
2. **On the PC** (on the same Wi-Fi network as the phone), from a copy of this repository, double-click
   `packaging\termux\Share-to-phone.bat`. It prints a command such as `curl -s http://192.168.1.20:8800/i | sh`. If Windows requests
   firewall permission, allow *private networks*. The window must remain open.
3. **On the phone**, paste that command into Termux. It downloads Python, ffmpeg and yt-dlp (a few minutes). The window on the PC
   can then be closed.

Without a shared Wi-Fi network, run `python packaging/termux/share_to_phone.py --zip-only` on the PC (it creates
`generated/YT-Grabber-android.zip`), copy the zip to the *Download* folder of the phone and, in Termux, run:

```
termux-setup-storage
pkg install -y unzip && mkdir -p ~/yt-grabber && unzip -o ~/storage/downloads/YT-Grabber-android.zip -d ~/yt-grabber && sh ~/yt-grabber/termux/install-termux.sh
```

For daily use, open Termux and type `cd yt-grabber && sh Start.sh` (or tap the *YT-Grabber* icon of Termux:Widget). The browser
opens at `http://localhost:8765/`. **Termux must remain open** while downloading; Ctrl+C stops the program. The files are saved in
**Download/YT-Grabber**. To obtain an icon that behaves like an application, use ⋮ → **Add to Home screen** in Chrome.

Recommended settings: *Settings → Apps → Termux → Battery → Unrestricted* and, on Android 12 or later, *Disable child process
restrictions* in *Developer options*. To update the program, repeat steps 2 and 3 (downloads and settings are kept). The logs are in
`~/yt-grabber/generated/data/logs/`.

---

## iPhone and iPad

There is **no iOS application**, and one cannot be built for this program: iOS does not allow an application to run a Python server
or yt-dlp, an application requires Apple's signing (a paid developer account), and Apple does not accept YouTube downloaders in the
App Store. The alternative is to use the web page from the phone, with the program running on a computer (or on any always-on
Linux machine, such as a Raspberry Pi) on the same Wi-Fi network:

1. On the computer, start the program so that it accepts other devices: `Start.bat --host 0.0.0.0` (Windows),
   `./Start.sh --host 0.0.0.0` (Linux, macOS) or `yt-grabber --host 0.0.0.0` (Linux package). With the Windows installer, run
   `YT-Grabber.exe --host 0.0.0.0` from `%LOCALAPPDATA%\Programs\YT Grabber`. The program prints the address to use, for example
   `http://192.168.1.6:8765/`.
2. On the iPhone or iPad, open that address in **Safari**. To obtain an icon that behaves like an application, use Share →
   **Add to Home Screen**.
3. Paste the links and press **Download**: the files are saved on the computer. To transfer a file to the phone, open the list and use
   the save button next to a finished item.

This should be done only on a trusted network, because anyone on the same Wi-Fi network can open the page. Use on an iPhone and an
iPad has **not been tried** by the maintainer (no device was available); it is the same page that works in Chrome and Firefox.

---

## From the source code

Python 3 is required (3.10 or later; development uses 3.12 and 3.13). The code is obtained with
`git clone https://github.com/progliodario/YT-Grabber` or with the *Download ZIP* button. Then:

- **Windows:** double-click **`Start.bat`** (if Python is missing, it offers to install it with winget).
- **Linux, macOS, Termux:** run **`./Start.sh`**.

The first start installs yt-dlp, the JavaScript runtime and ffmpeg in the `generated/` folder (not tracked by git). Available options
include `--port 9000`, `--dir D:\Music`, `--host 0.0.0.0` (to use the program from another device on the network by opening
`http://COMPUTER-IP:8765/`; the files are still saved on the computer that runs the program) and `--no-browser`. The complete list
is in the [usage guide](usage.md#command-line-options).
