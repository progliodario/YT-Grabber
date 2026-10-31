# YT Grabber for Android (APK)

*Part of [YT Grabber](../README.md). The ready-to-install apps are in the **`APK\`** folder in the main folder; this
folder contains the Android project used to **rebuild** them.*

A standalone Android app: it contains everything (Python, yt-dlp, ffmpeg and the interface). **No computer needed**:
it downloads, numbers and saves by itself into the phone's *Download* folder, always with 10 downloads in parallel.

## Which file to install

The APKs are in `APK\` (they are built with `build-apk\build-apk.bat`):

| File | For which phones |
|---|---|
| `YT-Grabber-arm64-v8a.apk` | **almost all phones from 2017 onwards: choose this one** |
| `YT-Grabber-armeabi-v7a.apk` | 32-bit phones, very old |
| `YT-Grabber-x86_64.apk` | Android emulators on the PC (testing) |

If you are not sure: install the `arm64-v8a` one; if Android says "app not compatible", try `armeabi-v7a`.

## Installation

1. Copy the APK to the phone (USB cable, Google Drive, Telegram, email...).
2. Open it from the file manager. Android asks you to allow *"Install unknown apps"* for the app you are using
   (Files, Chrome...): allow it and continue. This is normal for apps that do not come from the Play Store.
3. Open **YT Grabber**. On first start it takes a few tens of seconds to prepare the engine, then:
   - **Notifications**: allow (needed to see progress and the *Close* button).
   - **All files access**: needed to save into *Download/YT-Grabber*. If you refuse, files go to a private app folder
     (harder to reach).
   - **Battery optimization**: allow the exclusion, so it also downloads with the screen off.

## Usage

- Paste one or more links (also YouTube Music playlists and albums) and press **Download**.
- **From YouTube / YouTube Music / Chrome**: tap *Share* → **YT Grabber**. The link is already in the box.
- While it downloads there is a notification with the progress. You can close the app: downloads continue.
  To stop everything, tap **Close** in the notification.
- To resume after a stop or a phone restart: reopen the app and press **Resume** on the download.
- Files are in **Download/YT-Grabber**, numbered in order (`001 - Title.m4a`).

## Tips

- On the phone the default format is **M4A**: it does not re-encode, it is the fastest and uses less battery.
- Use Wi-Fi for big playlists (they use a lot of data).
- If YouTube stops responding: *Settings → Update yt-dlp and restart* (needs Internet).
- Android 12 or newer may limit background processes: if downloads stop by themselves, in *Developer options* turn on
  **Disable child process restrictions**.

## What has been tested

- **Tested in an Android 14 emulator (x86_64)**: first start with all permission requests, engine extraction, server
  start, sharing a link from another app, download of an 11-video playlist saved and numbered in
  `Download/YT-Grabber`, automatic restart of the service after the system killed the process.
- **Not tested on a physical phone**: the `arm64-v8a` APK (the one for phones) contains the same code and the same
  libraries as the emulator APK, but it is built for another processor and there was no way to run it here.
- If Android warns that the app "was not verified by Play Protect" or is "unknown", that is normal for a manually
  installed APK: choose *Install anyway*.

## Rebuild the APKs (for those who modify the program)

```
build-apk\build-apk.bat
```

It needs JDK 21 (17 on very recent Windows 11 has a local-network defect and Gradle does not start), the Android SDK
(platform 34, build-tools 34.0.0) and Gradle 8.7 in `C:\AndroidBuild\` (path changeable with the `ANDROID_BUILD_ROOT`
variable). The script automatically copies into the APK the files of `program\` (`server.py`, `ytworker.py`,
`ytcommon.py` and the `web\` folder); to bundle a newer yt-dlp, delete
`build-apk\app\src\main\assets\ytg-libs.zip` before building.

The APK is signed with the key in `build-apk\keystore\` (`ytgrabber.jks` plus `keystore.properties` with the password).
**Keep a safe copy of it**: the same key is needed to install updates over the version already installed, and if you
lose it you will have to uninstall the app (losing its data) before installing one signed differently. That folder is
excluded from git, so it never ends up in an archive by mistake. If the folder is missing, `build-apk.bat` creates a
new key with a random password.

### What is in this folder

| Path | What it is |
|---|---|
| `build-apk.bat` | the build script (finished APKs go to `..\APK\`) |
| `app\` | the Android app (Kotlin sources in `app\src\main\java`, resources, manifest) |
| `tools\make_libs.py` | prepares the bundled Python packages (`ytg-libs.zip`) |
| `keystore\` | the signing key (secret, not in git) |
| `build.gradle.kts`, `settings.gradle.kts`, `gradle.properties` | Gradle configuration |

## How it works (in short)

The app is a thin shell: a foreground service starts YT Grabber's Python server (the same code that runs on the
computer) using Python 3.12 and ffmpeg built for Android (the youtubedl-android project), and a WebView shows the
interface from `http://127.0.0.1:8765`. No data leaves the phone, except the requests to YouTube.
