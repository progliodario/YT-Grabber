## Install

| System | File |
|---|---|
| Windows 10/11 | `YT-Grabber-Setup-*.exe` (installs the app; also `winget install progliodario.YTGrabber`) |
| Android | `YT-Grabber-*.apk` |
| Debian / Ubuntu / Mint | `yt-grabber_*_all.deb`, or the apt repository (see below) |
| Fedora / RHEL / openSUSE | `yt-grabber-*.noarch.rpm`, or the dnf repository (see below) |
| Any Linux | `YT-Grabber-x86_64.AppImage`, `YT-Grabber-aarch64.AppImage` or `YT-Grabber-x86_64.flatpak` |
| macOS | `YT-Grabber-macOS.zip` (also `brew install --cask progliodario/tap/yt-grabber`) |

apt / dnf repositories: https://progliodario.github.io/YT-Grabber/

## Check what you downloaded

`SHA256SUMS` lists the checksum of every file and `SHA256SUMS.asc` is its GPG signature (key fingerprint on the repository page).
Files built by GitHub Actions also carry a build attestation: `gh attestation verify <file> --repo progliodario/YT-Grabber`.

See the [README](https://github.com/progliodario/YT-Grabber#readme) for details.
