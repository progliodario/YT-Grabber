# Development guide

This guide is intended for anyone who wishes to understand, change, build or release YT Grabber. For instructions on using the
program, see the [usage guide](usage.md).

- [How it works](#how-it-works) · [Layout](#layout) · [Running from the sources](#running-from-the-sources) · [Tests](#tests)
- [Building the packages](#building-the-packages) · [Automatic builds](#automatic-builds-github-actions) ·
  [Making a release](#making-a-release) · [Distribution channels](#distribution-channels) · [Conventions](#conventions)

## How it works

YT Grabber is a small Python program (without a framework) that serves a web page and drives
[yt-dlp](https://github.com/yt-dlp/yt-dlp). Every platform runs the same program with a different shell around it: a console
(`Start.bat`, `Start.sh`), a windowed application with a tray icon (Windows), a launcher in Terminal (macOS), and a foreground service
with a WebView (Android).

| Part | Role |
|---|---|
| `program/server.py` | the entry point and the logic that ties everything together: the scheduler with **exactly 10 download slots**, the download of one item, the reading of playlists, the actions on a job, subscriptions, the HTTP API, shutdown |
| `program/ytsettings.py`, `ytmodel.py`, `ytlinks.py` | self-contained parts: the settings, `Item` and `Job` (data only), and links and file names |
| `program/ytupdates.py` | new versions of YT Grabber (the notice and the one-click install) and the automatic update of yt-dlp; it never imports `server` |
| `program/ytworker.py` | a download worker. The server starts 10 of them as **separate, persistent processes** (no repeated start-up cost and no limit from the GIL) and communicates with them through JSON lines over stdin/stdout |
| `program/ytcommon.py` | what the server and the workers share: paths, the catalogue of errors and their causes, and the way a format is chosen |
| `program/setup_tools.py` | installs yt-dlp, the JavaScript runtime and ffmpeg at the first start |
| `program/web/` | the interface: `index.html`, `app.css`, `app.js` (no build step and no dependencies), `lang/*.js` (the 16 languages), icons, and the web manifest |

The course of a download:

1. `POST /api/jobs` creates a **job** for each link. The playlist is read in blocks in a thread, and each entry becomes an **item**
   (state `q` queued, `a` downloading, `p` converting, `d` done, `e` error, `s` already present, `c` cancelled, `k` skipped: by an
   "only new videos" subscription, or by the user). Items enter the queue as soon as they are read.
2. Ten supervisor threads take the next queued item (jobs in the order in which they were added; a paused job is skipped) and pass it
   to their worker process, so that never more than 10 items download at a time. When an item moves from downloading to converting,
   its slot is released at once.
3. Files are numbered by their position in the playlist (`001 - Title.ext`). A **manifest** in each folder records what was downloaded,
   so that a resumed or repeated job recognises the files. Jobs are saved in `data/jobs/*.json` and survive a restart.
4. When the user asks to **choose the videos first** (`choose` in `POST /api/jobs`), the job is created paused with `choosing` set: the list is read
   but nothing is downloaded. The actions `skip` and `unskip` (with a list of item numbers, or none for all) move queued items to `k`
   (their message is `SKIP_BY_USER`) and back; `resume` starts the job. The same two actions work on a running job for the items
   that are still queued. The scheduler ignores queued entries whose state is no longer `q`, so nothing has to be removed from the queue.
5. The page polls `GET /api/state` (and `GET /api/jobs/<id>?since=N` for the open list, which returns only the changed items).

**Subscriptions** are stored in `data/subscriptions.json`. A thread starts a normal job on the same link at each interval (at most
one due subscription every 20 seconds). In "only new videos" mode, the subscription keeps the list of the video identifiers it has
already seen. Items in that list are created in state `k` and are never downloaded.

**Updates** (`program/ytupdates.py`). `check_update()` queries the GitHub releases API twice a day and records the latest version and, when present, the
address, SHA-256 fingerprint and size of the Windows installer asset. In the frozen Windows application (not under Scoop),
`POST /api/appupdate/install` runs `run_update_install()`: it downloads the installer (only from
`https://github.com/progliodario/YT-Grabber/releases/download/`), verifies the fingerprint, starts it detached with
`/SILENT /RELAUNCH=1` and quits the application. The installer reopens the program when it has finished.

**Security of the local server:** it listens on `127.0.0.1` unless started with `--host`. Every request that changes something must
carry the header `X-YTG: 1` (so that another web page cannot make the browser start a download). The `Host` header is checked. The
operations that affect the machine (choosing a folder, opening a folder, quitting, updating) are accepted only from the local
computer.

The **interface** is translated by `window.I18N.<code> = {...}` files and `tr('key', {vars})`. Plural forms are objects
(`{one, other}`) resolved with `Intl.PluralRules`, and static texts use `data-i18n` attributes. See
[CONTRIBUTING.md](../CONTRIBUTING.md#translations).

## Layout

```
program/            the program: server.py, the yt*.py modules, setup_tools.py, web/ (see program/README.md)
packaging/
  windows/          exe (PyInstaller) + installer (Inno Setup): build.bat, build_windows.py, exe_main.py, winapp.py, winlang.py,
                    installer.iss, version.txt, icon
  android/          the Android application (Gradle, Kotlin): build.bat, app/, tools/make_libs.py
  linux/            .deb and .rpm (nfpm): build.bat, build_packages.py, nfpm.yaml, launcher, .desktop, systemd unit
    appimage/       AppImage recipe
    flatpak/        Flatpak manifest and AppStream metadata
  macos/            the .app (assembled, no Mac needed): build.bat, build_app.py, launcher, run.sh
  termux/           installation on a phone with Termux: Share-to-phone.bat, share_to_phone.py, install-termux.sh
tools/              bump_version.py
tests/              one test file per subject, support.py (shared set-up), a11y/ (seed.py: sample data; audit.py: axe-core and keyboard audit)
docs/               guides, release-key.asc (public GPG key), screenshots/
.github/            workflows/ (ci, release, finalize), scripts/, issue and pull request templates, dependabot.yml
Start.bat Start.sh  run from the sources
dist/               (not in git) the packages built locally
generated/          (not in git) data created when running from the sources: yt-dlp, ffmpeg, settings, logs, build files
```

## Running from the sources

```
python program/setup_tools.py       # once: yt-dlp, the JavaScript runtime and ffmpeg are placed in generated/
python program/server.py            # http://localhost:8765/
```

(`Start.bat` and `Start.sh` perform both steps.) Useful environment variables: `YTG_DATA_ROOT` moves everything the program creates
(settings, tools, logs) to another folder, and `YTG_UPDATE_URL` replaces the address of the new-version check (for tests).

## Tests

```
python -m unittest discover -s tests -v
```

The tests require `yt-dlp` to be importable (`pip install "yt-dlp[default]"`, or run `setup_tools.py` once). They do not require the
network. There is one file per subject (see [`tests/README.md`](../tests/README.md)). They cover links, error classification, format selection, settings, subscriptions (including "only new"), the new-version
check and the one-click update, the notices for finished downloads, the language files (every language has every key and the same
placeholders, and no key is unused), the Windows texts, the version numbers and `tools/bump_version.py`. CI also checks the
JavaScript syntax with Node and starts the server on Windows, macOS and Linux.

**Accessibility.** `tests/test_accessibility.py` (part of the same command) checks the markup of the page, the contrast of every
colour pair of the design, and the CSS for the preferences of the user. `tests/a11y/audit.py` is a real audit: it drives headless
Chrome, Chromium or Edge through the DevTools protocol, runs [axe-core](https://github.com/dequelabs/axe-core) (WCAG 2.0 to 2.2,
levels A and AA, and best practices) in the light and dark themes, with a list and the settings window open, in Arabic and at 320
pixels, and checks by keyboard the skip link, the focus order, the dialog, the arrow keys in the list, the text size and the zoom.
`tests/a11y/seed.py` fills a data folder with sample downloads, so no network is needed:

```
python tests/a11y/seed.py /tmp/ytg-a11y
YTG_DATA_ROOT=/tmp/ytg-a11y python program/server.py --no-browser --port 8782 &
python tests/a11y/audit.py http://localhost:8782/        # requires: pip install websockets
```

The *Accessibility audit* job of `ci.yml` performs exactly these steps. The rules to follow are in
[CONTRIBUTING.md](../CONTRIBUTING.md#accessibility), and the statement for users is [accessibility.md](accessibility.md).

## Building the packages

For releases, everything is built by [GitHub Actions](#automatic-builds-github-actions). To build a package locally:

| Package | Command | Requirements | Result |
|---|---|---|---|
| Windows installer | `packaging\windows\build.bat` | Python, [Inno Setup 6](https://jrsoftware.org/isdl.php) (PyInstaller and yt-dlp are fetched) | `dist\windows\YT-Grabber-Setup-<version>.exe` |
| Android APKs | `packaging\android\build.bat` | JDK 21, Android SDK (platform 37.0, build-tools 36.0.0), Gradle 9.6.0 in `C:\AndroidBuild\` | `dist\android\*.apk` |
| `.deb` and `.rpm` | `packaging\linux\build.bat` (or `python3 packaging/linux/build_packages.py`) | Python (nfpm is downloaded and verified) | `dist/linux/*.deb`, `*.rpm` |
| AppImage | `python3 packaging/linux/appimage/build_appimage.py` | Linux | `dist/linux/*.AppImage` |
| Flatpak | `flatpak-builder` (see the header of `packaging/linux/flatpak/*.yml`) | Linux, flatpak-builder | a Flatpak repository, then `flatpak build-bundle` |
| macOS application | `packaging\macos\build.bat` (or `python3 packaging/macos/build_app.py`) | Python, Internet (no Mac needed) | `dist/macos/YT-Grabber-macOS.zip` |

Each folder in `packaging/` has a README with the details of its package.

## Automatic builds (GitHub Actions)

| Workflow | When | What it does |
|---|---|---|
| `ci.yml` | every push and pull request | unit tests, JavaScript syntax check, and a smoke test (start the server and call it) on Ubuntu, Windows and macOS; the accessibility audit (axe-core in Chrome); and a build of the Android application (unsigned), to catch compilation errors |
| `release.yml` | a tag `v*` is pushed, or manually | builds every package and **installs and starts each one** to prove that it works (Windows: install, start, silent update over the existing installation, uninstall; Ubuntu: `.deb` and AppImage; Fedora: `.rpm`; Flatpak: build and run; Apple Silicon and Intel Macs), then attaches the files to the release |
| `finalize.yml` | called by `release.yml`, or manually | signs the `.rpm`, writes `SHA256SUMS` and signs it with GPG, adds build attestations, builds the signed apt and dnf repositories, installs from them on Ubuntu and Fedora, and publishes them on GitHub Pages |

The helper scripts are in `.github/scripts/` (`wait_ping.sh`, `build_repos.sh`). Running `release.yml` manually without a tag only
builds and tests; nothing is published.

## Making a release

1. Set the version everywhere: `python tools/bump_version.py 1.6.0`. The script changes `program/server.py`, the Windows version file,
   the Flatpak metadata and the Android `versionName` and `versionCode`, and reports if `CHANGELOG.md` has no section for the version.
2. Write the section of `CHANGELOG.md` and run the tests. Commit and push, then wait for the **CI** to pass.
3. Push the tag: `git tag -a v1.6.0 -m "YT Grabber 1.6.0" && git push origin v1.6.0`. `release.yml` builds and tests everything and
   creates the GitHub release; `finalize.yml` adds the checksums, the signature and the repositories.
4. Build the APKs on the maintainer's computer (`packaging\android\build.bat`; the signing key exists only there), upload them to the
   release (`gh release upload v1.6.0 dist\android\*.apk`), and run **Finalize** again manually
   (`gh workflow run finalize.yml -f tag=v1.6.0`) so that `SHA256SUMS` includes them.
5. Update the [distribution channels](#distribution-channels) with the new file hashes.
6. Verify the release from outside: the signature (`gpg --verify SHA256SUMS.asc SHA256SUMS`), an attestation
   (`gh attestation verify`), and the apt and dnf repositories.

**Secrets and keys.** The repository secret `GPG_PRIVATE_KEY` is the release signing key. Its public half is
[`docs/release-key.asc`](release-key.asc), and the fingerprint is given in [SECURITY.md](../SECURITY.md). A backup of the private key
must be kept outside the repository. The Android signing key is in `packaging/android/keystore/` (ignored by git). **A copy must be
kept**, because Android refuses to update an installed application that was signed with a different key. The *github-pages*
environment must allow the `main` branch and the tags `v*`.

## Distribution channels

| Channel | Location | How it is updated |
|---|---|---|
| GitHub releases | this repository | `release.yml` |
| apt and dnf repositories | GitHub Pages of this repository | `finalize.yml` |
| Homebrew | the tap [`progliodario/homebrew-tap`](https://github.com/progliodario/homebrew-tap) (`Casks/yt-grabber.rb`) | manually: new `version` and `sha256` of the Mac zip (the tap has a workflow that installs the cask on a Mac) |
| Scoop | the bucket [`progliodario/scoop-bucket`](https://github.com/progliodario/scoop-bucket) | automatically (its *Excavator* workflow follows the new releases); it has a workflow that installs the application on Windows |
| winget | `microsoft/winget-pkgs`, package `progliodario.YTGrabber` | manually: a pull request with the three manifest files (version, installer with the SHA-256 of the exe, locale), checked with `winget validate` |

## Conventions

- **English everywhere** in the repository: code, comments, documentation and commit messages. (The interface is translated.)
- **Line endings** are handled by `.gitattributes`: scripts that run on Linux, macOS or Android are always LF, and `.bat` files are CRLF.
- **No secrets** in the repository: keys, passwords and local paths remain in ignored files.
- **Versions** are changed only with `tools/bump_version.py`.
- The structure is kept simple: no frameworks and no build step for the page, and one program for every platform.
