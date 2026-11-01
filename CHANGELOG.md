# Changelog

All notable changes are listed here, newest first. Version numbers follow `MAJOR.MINOR.PATCH`.

## Unreleased

- **Update now (Windows application):** the new-version notice offers a button that downloads the installer from the releases,
  verifies its SHA-256 fingerprint, closes the application, installs the new version and reopens it. The button is not shown for
  installations made with Scoop, winget or Chocolatey.
- **Android:** a notification is shown when a download finishes (it can be disabled in the settings).
- **Arrow keys in the list of items** (Up, Down, Home, End, Page Up, Page Down), with a single Tab stop for the whole list.
- **Settings → Text size** (100% to 200%).
- The tick mark inside the selected option is no longer read by screen readers as part of its name.

## 1.4.0

- **Accessibility (WCAG 2.2 AA):** the whole interface was reworked and is now checked automatically at every change.
  Keyboard: skip link, genuine buttons, a settings window that retains the focus and returns it on closing, and a focus that is
  preserved when the page refreshes. Screen readers: names and states for every control, switches, progress bars, a list of items
  with positions, announcements when a download finishes or fails, and labelled groups and regions. Visual presentation: colours
  with sufficient contrast in both themes (the accent colour is darker), control borders at 3:1, marks in addition to colour,
  text sizes in `rem`, zoom up to 400%, 44-pixel touch targets, forced-colours and increased-contrast modes, and no animation when
  "reduce motion" is set. Messages in the corner can be closed and remain visible while they are being read. Android: pinch zoom,
  the system font size, and a start-up screen that screen readers can follow. Windows: a sharper start-up window.
  See [docs/accessibility.md](docs/accessibility.md).
- Downloading ffmpeg and the other tools at the first start now **retries** when the connection is interrupted (a weak network
  could previously stop the setup).
- **Repository reorganised.** The build folders are now under `packaging/` (`windows`, `android`, `linux`, `macos`, `termux`), the
  results of local builds go to `dist/`, the public signing key moved to `docs/release-key.asc`, and each `build-*.bat` is now
  `build.bat` in its folder. Nothing changes for users who install a release.
- **Documentation rewritten:** a shorter README; guides in `docs/` (installation, usage, development); `CONTRIBUTING.md`; a README
  for each folder in `packaging/`; and issue and pull request templates.
- `tools/bump_version.py` sets the version in every file that carries it (covered by a test).

## 1.3.0

- **Only new videos** option for subscriptions: videos already present in the playlist, album or channel are not downloaded, only
  those published after the subscription. They are listed as *Skipped*.
- Fix: two simultaneous saves of the subscription list could fail on Windows.

## 1.2.0

- **New-version notice:** the page reports when a newer YT Grabber has been released (one request to GitHub twice a day, carrying
  only the program name and version; it can be disabled in *Settings → Notifications and updates*).
- **Notification when a download finishes:** a bubble from the tray icon in the Windows application, a browser notification
  elsewhere. Subscription checks that find nothing new remain silent.
- Screenshots in the README, and Dependabot for the workflow actions and the Android libraries.
- Android: the application version now follows the release (it had remained at 1.0.0, which could prevent updates from installing).

## 1.1.0

- **Subscriptions** to channels and playlists, checked automatically at a chosen interval.
- **16 languages** in the interface, the Windows application and installer, and the Android application.
- Linux: AppImage (x86_64 and ARM), Flatpak, a systemd user service, and signed apt and dnf repositories on GitHub Pages.
- Every release is built and tested on GitHub's machines and has a GPG-signed `SHA256SUMS` and build attestations.
- winget, Homebrew and Scoop packages.

## 1.0.0

- First release: Python server and web page, Windows installer, Android APK, Termux, `.deb`, `.rpm` and macOS application.
  Exactly 10 simultaneous downloads, files numbered in playlist order, and per-item error reporting.
