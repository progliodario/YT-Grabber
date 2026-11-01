# Changelog

All notable changes, newest first. The version numbers follow `MAJOR.MINOR.PATCH`.

## 1.4.0

- **Accessibility (WCAG 2.2 AA):** the whole interface was reworked and is now checked automatically at every change.
  Keyboard: skip link, real buttons, a settings window that traps and returns the focus, focus that survives the page refreshing.
  Screen readers: names and states for every control, switches, progress bars, the list of items with positions, announcements
  when a download finishes or fails, labelled groups and regions. Visual: colours with enough contrast in both themes (the accent
  colour is darker), borders of controls at 3:1, marks besides colours, text sizes in `rem`, zoom up to 400%, 44-pixel touch targets,
  forced-colours and more-contrast modes, no animation with "reduce motion". Messages in the corner can be closed and wait for you.
  Android: pinch zoom, system font size, a start-up screen that screen readers follow. Windows: a sharper start-up window.
  See [docs/accessibility.md](docs/accessibility.md).
- Downloading ffmpeg and the other tools on the first start now **retries** when the connection drops half way (a weak network
  could stop the setup).
- **Repository reorganized.** The build folders now live under `packaging/` (`windows`, `android`, `linux`, `macos`, `termux`), the
  results of local builds go to `dist/`, the public signing key moved to `docs/release-key.asc`, and every `build-*.bat` is now
  `build.bat` in its folder. Nothing changes for people who install a release.
- **Documentation rewritten:** a shorter README, and guides in `docs/` (installing, using, development), `CONTRIBUTING.md`,
  a README for each folder in `packaging/`, issue and pull request templates.
- `tools/bump_version.py` sets the version in every file that carries it (with a test).

## 1.3.0

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
