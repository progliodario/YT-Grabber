# Changelog

## Unreleased

- **Only new videos** option for subscriptions: the videos that are already in the playlist, album or channel are not
  downloaded; only those published after you subscribed are. They are listed as *Skipped*.
- Fix: two saves of the subscription list at the same moment could fail on Windows.

## 1.2.0

- **New-version notice:** the page tells you when a newer YT Grabber has been released (one request to GitHub twice a day,
  only the program name and version are sent; switch it off in *Settings → Notifications and updates*).
- **Notification when a download finishes:** a bubble from the tray icon in the Windows app, a browser notification
  elsewhere. Subscription checks that find nothing new stay silent.
- Screenshots in the README, Dependabot for the workflow actions and the Android libraries.
- Android: the app version now follows the release (it was stuck at 1.0.0, which could stop updates from installing).

## 1.1.0

- **Subscriptions** to channels and playlists, checked automatically at the interval you choose.
- **16 languages** in the interface, the Windows app and installer, and the Android app.
- Linux: AppImage (x86_64 and ARM), Flatpak, a systemd user service, and signed apt / dnf repositories on GitHub Pages.
- Every release is built and tested on GitHub's machines, has `SHA256SUMS` signed with GPG and build attestations.
- winget, Homebrew and Scoop packages.

## 1.0.0

- First release: Python server and web page, Windows installer, Android APK, Termux, `.deb`, `.rpm` and macOS app.
  Exactly 10 simultaneous downloads, files numbered in playlist order, per-item error reporting.
