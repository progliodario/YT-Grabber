# Termux (YT Grabber on an Android phone, without the app)

*Part of [packaging](../README.md). The instructions for users are in the [installation guide](../../docs/install.md#termux-alternative-to-the-app).*

The program runs on the phone inside the free **Termux** app (a simple web page cannot download from YouTube: the browser prevents
it). The computer only hands over the files once. The Android app is easier; this is the alternative.

| File | What it is |
|---|---|
| `Share-to-phone.bat` | double-click on the PC: runs `share_to_phone.py` |
| `share_to_phone.py` | builds `generated/YT-Grabber-android.zip` (`Start.sh`, `README.md`, `program/` and these scripts as `termux/`) and serves it, with the installer, on the Wi-Fi (port 8800), so that the phone can run `curl -s http://PC-IP:8800/i \| sh`; `--zip-only` only builds the zip |
| `install-termux.sh` | the installer that runs inside Termux: installs Python, ffmpeg and node, unpacks the zip, installs yt-dlp and adds a Termux:Widget shortcut |

Line endings are converted to Unix style in the zip (Android needs them).
