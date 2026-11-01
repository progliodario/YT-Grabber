# YT Grabber

[![Latest release](https://img.shields.io/github/v/release/progliodario/YT-Grabber?label=release)](https://github.com/progliodario/YT-Grabber/releases/latest)
[![CI](https://github.com/progliodario/YT-Grabber/actions/workflows/ci.yml/badge.svg)](https://github.com/progliodario/YT-Grabber/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

YT Grabber downloads **videos, playlists (including those with thousands of items), albums and entire channels** from YouTube
and YouTube Music. It runs on the user's own computer or phone and is operated through a local web page in any browser.

![The main page: paste links, choose the format, press Download](docs/screenshots/main-light.png)

## Features

- **Exactly 10 simultaneous downloads**, even when several playlists are queued.
- Files are **numbered in playlist order** (`001 - Title.mp3`, `002 - ...`).
- Each video that fails is **listed with its number and the exact reason**, and can be retried with one click.
- Downloads can be **stopped and resumed** at any time: files that are already complete are recognised and skipped.
- **Subscriptions**: a channel or playlist can be followed, and its new videos are downloaded automatically. Optionally, only the
  **new videos** are downloaded, leaving out what was published before the subscription.
- **Notifications** when a download finishes and when a new version of YT Grabber is available (both can be disabled).
- **16 languages**: English, Italiano, Español, Français, Deutsch, Português, Nederlands, Polski, Русский, Türkçe,
  العربية, हिन्दी, Bahasa Indonesia, 中文, 日本語, 한국어. The interface follows the language of the device and can be changed
  from the page.
- Audio (MP3, M4A, Opus) or video (up to 4K), with cover art and tags.
- **Accessible**: usable entirely with the keyboard and with screen readers, with high-contrast and forced-colours modes, zoom up
  to 400%, adjustable text size, reduced motion and touch screens. The project aims at WCAG 2.2 level AA, and conformance is checked
  automatically at every change (see the [accessibility statement](docs/accessibility.md)).
- Free and open source ([MIT licence](LICENSE)). No data is sent anywhere except to YouTube and GitHub
  (see [SECURITY.md](SECURITY.md)).

| The list of a playlist, dark theme | On a phone |
|---|---|
| ![The numbered list of a playlist, in the dark theme](docs/screenshots/list-dark.png) | ![The page on a phone](docs/screenshots/phone.png) |

Further screenshots are available in the [usage guide](docs/usage.md).

## Installation

Ready-made files are available on the [releases page](https://github.com/progliodario/YT-Grabber/releases/latest).
Step-by-step instructions for every platform are given in **[docs/install.md](docs/install.md)**.

| System | Recommended method |
|---|---|
| **Windows** | `YT-Grabber-Setup-<version>.exe` (a standard installer), `winget install progliodario.YTGrabber` or `scoop install yt-grabber` |
| **macOS** (Intel and Apple Silicon) | `brew install --cask progliodario/tap/yt-grabber`, or the `YT-Grabber-macOS.zip` application |
| **Debian, Ubuntu, Mint** | the signed **apt repository** (updated automatically), or the `.deb` package |
| **Fedora, RHEL, openSUSE** | the signed **dnf repository** (updated automatically), or the `.rpm` package |
| **Any Linux** | the **AppImage** (a single file) or the **Flatpak** |
| **Android** | the `YT-Grabber-arm64-v8a.apk` application (no computer required), or Termux |
| **iPhone / iPad** | the page served by a computer or a Raspberry Pi; an iOS application is not possible |
| **Any system with Python 3** | `Start.bat` (Windows) or `./Start.sh` (Linux, macOS, Termux), run from this folder |

## Quick start

1. Start YT Grabber (from the Start menu, the applications menu, the application icon, or with `Start.bat` / `./Start.sh`).
   The page opens automatically at `http://localhost:8765/`.
2. Paste one or more links, one per line, and press **Download**.
3. The files are saved in the `Downloads/YT-Grabber` folder of the user. The folder can be changed in *Settings*.

The first start installs the required components (yt-dlp, a JavaScript runtime and ffmpeg). This requires an Internet connection
and approximately 200 MB, once only.

## Documentation

| Document | Content |
|---|---|
| [docs/install.md](docs/install.md) | installation, updating and removal, for every platform |
| [docs/usage.md](docs/usage.md) | the interface, numbering, errors, resuming, cookies, subscriptions, command-line options, troubleshooting |
| [docs/accessibility.md](docs/accessibility.md) | keyboard use, screen readers, the measures taken and the checks performed, known limitations |
| [docs/development.md](docs/development.md) | internal architecture, running from source, tests, building and releasing |
| [CONTRIBUTING.md](CONTRIBUTING.md) | reporting problems, correcting a translation, submitting a change |
| [SECURITY.md](SECURITY.md) | verifying that a download is genuine, antivirus and "unknown publisher" warnings, privacy |
| [CHANGELOG.md](CHANGELOG.md) | the changes made in each version |

### Verifying that a downloaded file is genuine

Every release includes `SHA256SUMS` and a GPG signature (`SHA256SUMS.asc`). The files built on GitHub carry a build attestation
(`gh attestation verify <file> --repo progliodario/YT-Grabber`), and the apt and dnf repositories are signed.
[SECURITY.md](SECURITY.md) describes the verification procedure.

## Repository layout

```
YT-Grabber/
├─ README.md  CHANGELOG.md  SECURITY.md  CONTRIBUTING.md  LICENSE
├─ Start.bat  Start.sh      run from the sources (requires Python 3)
├─ program/                 the program: server.py, ytworker.py, ytcommon.py, setup_tools.py, web/ (the interface)
├─ packaging/               everything needed to build each package: windows/ android/ linux/ macos/ termux/
├─ tools/                   helper scripts for the maintainer (bump_version.py)
├─ tests/                   automated tests
├─ docs/                    guides, the release signing key and the screenshots
├─ .github/                 automated tests and release builds (GitHub Actions), issue templates
├─ dist/                    (not in git) packages built locally
└─ generated/               (not in git) data created when running from the sources: tools, settings, logs
```

## Building and contributing

Running the program from the sources does not require a build. The packages are built by GitHub Actions for every release
(see [docs/development.md](docs/development.md)), and each folder in `packaging/` contains a guide for building its package
locally. Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence and third-party components

YT Grabber is released under the [MIT Licence](LICENSE). It relies on other projects, each distributed under its own licence:
[yt-dlp](https://github.com/yt-dlp/yt-dlp) (downloading), [FFmpeg](https://ffmpeg.org/) (conversion, downloaded on first
start from [yt-dlp/FFmpeg-Builds](https://github.com/yt-dlp/FFmpeg-Builds)), [Deno](https://deno.com/) (JavaScript runtime),
[PyInstaller](https://pyinstaller.org/) and [Inno Setup](https://jrsoftware.org/isinfo.php) (the Windows application and its
installer), [youtubedl-android](https://github.com/yausername/youtubedl-android) (Python and FFmpeg for the Android application)
and [python-build-standalone](https://github.com/astral-sh/python-build-standalone) (the Python of the AppImage and of the Mac
application). Packages and applications that include these components are also subject to their licences.

## Responsible use

Only content that the user has the right to save should be downloaded (the user's own, freely licensed, or for personal use where
the law permits it). Downloading may violate the YouTube Terms of Service. This project is not affiliated with YouTube or Google.
