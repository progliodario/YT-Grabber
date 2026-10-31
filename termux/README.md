# YT Grabber on an Android phone with Termux (no computer needed)

*Part of [YT Grabber](../README.md). This is the alternative to the Android app: if you can, install the APK from the
`APK\` folder instead (see [build-apk/README.md](../build-apk/README.md)), it is easier to install and use.*

The program runs **directly on the phone**, inside the free **Termux** app. The computer is only needed to hand over
the program files once; afterwards the phone does everything by itself: it reads playlists, downloads (always 10
downloads in parallel) and saves the files in the phone's *Download* folder, numbered in order.

> A simple web page cannot download from YouTube (the browser prevents it): that is why Termux is needed; it runs the
> same program as the computer. The interface is the same and adapts to the phone screen.

## Installation (only once, about 10 minutes)

### 1. Install Termux
Get it from **F-Droid** (https://f-droid.org/packages/com.termux/). **Not** the Play Store one: it is old and does not work.
Optional but handy: **Termux:Widget** (also from F-Droid) to have a start icon on the Home screen.

### 2. On the PC: share the program
Double-click **`termux\Share-to-phone.bat`**. A command similar to this appears:

```
curl -s http://192.168.1.20:8800/i | sh
```

If Windows asks for firewall permission, allow *private networks*. Leave the window open.

### 3. On the phone: paste the command into Termux
Phone and PC must be on the **same Wi-Fi network**. Open Termux, paste the command and press Enter.
If the file access request appears, tap **Allow**. The installation downloads Python, ffmpeg and yt-dlp
(a few minutes). At the end you can close the window on the PC.

### Without a shared Wi-Fi (copy by hand)
1. On the PC run `python termux\share_to_phone.py --zip-only`: it creates `generated\YT-Grabber-android.zip`.
2. Copy the zip to the phone's *Download* folder (USB cable, Drive, Telegram...).
3. In Termux: `termux-setup-storage` (allow), then
   ```
   pkg install -y unzip && mkdir -p ~/yt-grabber && unzip -o ~/storage/downloads/YT-Grabber-android.zip -d ~/yt-grabber && sh ~/yt-grabber/termux/install-termux.sh
   ```

## Everyday use

1. Open Termux and type: `cd yt-grabber && sh Start.sh` (or tap the *YT-Grabber* icon of Termux:Widget).
2. The browser opens at `http://localhost:8765/`. Paste the links and press **Download**.
3. **Keep Termux open** (even in the background) while it downloads. To stop it: Ctrl+C in Termux.
4. Files are in **Download/YT-Grabber** (visible from Gallery, Music and Files).

To have an icon like an app: in Chrome, menu ⋮ → **Add to Home screen** (the page opens full screen).
The icon opens the page, but the program must already be running in Termux.

## Recommended settings on the phone

- **Battery**: Settings → Apps → Termux → Battery → *Unrestricted* (otherwise Android stops downloads with the screen off).
- **Android 12 or newer**: Android may kill Termux's child processes. If downloads stop by themselves, go to
  *Developer options* and turn on **Disable child process restrictions**.
- **Format**: on the phone the default is **M4A**, which does not re-encode and uses little power. MP3 works but is heavier.
- **Space**: check the free storage before downloading big playlists.
- **Network**: on mobile data a whole playlist uses a lot of traffic: Wi-Fi is better.

## Updates and problems

- **Update yt-dlp** (if YouTube stops responding): *Settings → Update yt-dlp and restart*.
- **Update the program**: repeat steps 2 and 3 of the installation; your downloads and settings stay.
- **The same error on all videos**: try updating yt-dlp, then look at *Settings → Cookies*.
- Logs of the download processes are in `~/yt-grabber/generated/data/logs/`.

### What is in this folder

| File | What it is |
|---|---|
| `Share-to-phone.bat` | double-click on the PC: prepares the files and prints the command for the phone |
| `share_to_phone.py` | what the `.bat` runs (builds the zip and serves it on the Wi-Fi) |
| `install-termux.sh` | the installer that runs inside Termux on the phone |
