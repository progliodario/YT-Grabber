# Termux (YT Grabber on an Android phone, without the application)

*Part of [packaging](../README.md). The instructions for users are in the [installation guide](../../docs/install.md#termux-alternative-to-the-application).*

The program runs on the phone inside the free **Termux** application (a plain web page cannot download from YouTube, because the
browser prevents it). The computer is needed only to hand over the files once. The Android application is simpler; this is the
alternative.

| File | Description |
|---|---|
| `Share-to-phone.bat` | double-clicked on the PC; it runs `share_to_phone.py` |
| `share_to_phone.py` | builds `generated/YT-Grabber-android.zip` (`Start.sh`, `README.md`, `program/` and these scripts as `termux/`) and serves it, together with the installer, on the Wi-Fi network (port 8800), so that the phone can run `curl -s http://PC-IP:8800/i \| sh`; `--zip-only` builds only the zip |
| `install-termux.sh` | the installer that runs inside Termux: it installs Python, ffmpeg and node, unpacks the zip, installs yt-dlp and adds a Termux:Widget shortcut |

Line endings are converted to Unix style in the zip, because Android requires them.
