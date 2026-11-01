## Install

| System | File |
|---|---|
| Windows 10/11 | `YT-Grabber-Setup-*.exe` (also `winget install progliodario.YTGrabber` or `scoop install yt-grabber`) |
| Android | `YT-Grabber-arm64-v8a.apk` (almost all phones; `armeabi-v7a` for very old 32-bit ones) |
| Debian / Ubuntu / Mint | `yt-grabber_*_all.deb`, or the apt repository (see below) |
| Fedora / RHEL / openSUSE | `yt-grabber-*.noarch.rpm`, or the dnf repository (see below) |
| Any Linux | `YT-Grabber-x86_64.AppImage`, `YT-Grabber-aarch64.AppImage` or `YT-Grabber-x86_64.flatpak` |
| macOS | `YT-Grabber-macOS.zip` (also `brew install --cask progliodario/tap/yt-grabber`) |

Step by step for every system: [installation guide](https://github.com/progliodario/YT-Grabber/blob/main/docs/install.md).
apt / dnf repositories: https://progliodario.github.io/YT-Grabber/

## Check what you downloaded

`SHA256SUMS` lists the checksum of every file and `SHA256SUMS.asc` is its GPG signature (key fingerprint in
[SECURITY.md](https://github.com/progliodario/YT-Grabber/blob/main/SECURITY.md)).
Files built by GitHub Actions also carry a build attestation: `gh attestation verify <file> --repo progliodario/YT-Grabber`.

What changed: see the [CHANGELOG](https://github.com/progliodario/YT-Grabber/blob/main/CHANGELOG.md).