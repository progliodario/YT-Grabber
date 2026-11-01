# Development guide

For people who want to understand, change, build or release YT Grabber. To use it, see the [usage guide](usage.md).

- [How it works](#how-it-works) · [Layout](#layout) · [Running from the sources](#running-from-the-sources) · [Tests](#tests)
- [Building the packages](#building-the-packages) · [Automatic builds](#automatic-builds-github-actions) ·
  [Making a release](#making-a-release) · [Distribution channels](#distribution-channels) · [Conventions](#conventions)

## How it works

YT Grabber is a small Python program (no framework) that serves a web page and drives [yt-dlp](https://github.com/yt-dlp/yt-dlp).
Every platform is the same program with a different shell around it: a console (`Start.bat`, `Start.sh`), a windowed app with a
tray icon (Windows), a launcher in Terminal (macOS), a foreground service with a WebView (Android).

| Part | Role |
|---|---|
| `program/server.py` | the HTTP server and the whole logic: jobs and items, the scheduler with **exactly 10 download slots**, subscriptions, settings, the update check, notifications hooks |
| `program/ytworker.py` | a download worker. The server starts 10 of them as **separate, persistent processes** (no repeated start-up cost, no limit from the GIL) and talks to them with JSON lines over stdin/stdout |
| `program/ytcommon.py` | what the server and the workers share: paths, the catalogue of errors and their causes, how a format is chosen |
| `program/setup_tools.py` | installs yt-dlp, the JavaScript runtime and ffmpeg on the first start |
| `program/web/` | the interface: `index.html`, `app.css`, `app.js` (no build step, no dependencies), `lang/*.js` (the 16 languages), icons, the web manifest |

How a download goes:

1. `POST /api/jobs` creates a **job** per link. The playlist is read in blocks in a thread, and each entry becomes an **item**
   (state `q` queued, `a` downloading, `p` converting, `d` done, `e` error, `s` already present, `c` cancelled, `k` skipped by
   an "only new videos" subscription). Items enter the queue as soon as they are read.
2. Ten supervisor threads take the next queued item (jobs in the order they were added; a paused job is skipped) and give it to their
   worker process, so never more than 10 items download at a time. When an item moves from downloading to converting its slot
   is released at once.
3. Files are numbered by their position in the playlist (`001 - Title.ext`). A **manifest** in each folder records what was
   downloaded so that a resumed or repeated job recognizes the files. Jobs are saved in `data/jobs/*.json` and survive a restart.
4. The page polls `GET /api/state` (and `GET /api/jobs/<id>?since=N` for the open list, with only the changed items).

**Subscriptions** are stored in `data/subscriptions.json`. A thread starts a normal job on the same link at each interval (one
due subscription every 20 seconds at most). In "only new videos" mode the subscription keeps the list of the video IDs it has
already seen; items in that list are created in state `k` and are never downloaded.

**Safety of the local server:** it listens on `127.0.0.1` unless started with `--host`; every request that changes something must
carry the header `X-YTG: 1` (so another web page cannot make the browser start a download); the `Host` header is checked; the
operations that touch the machine (choose a folder, open a folder, quit, update) are accepted only from the local computer.

The **interface** is translated with `window.I18N.<code> = {...}` files and `tr('key', {vars})`; plural forms are objects
(`{one, other}`) resolved with `Intl.PluralRules`; static texts use `data-i18n` attributes. See
[CONTRIBUTING.md](../CONTRIBUTING.md#translations).

## Layout

```
program/            the program (see above)
packaging/
  windows/          exe (PyInstaller) + installer (Inno Setup): build.bat, build_windows.py, exe_main.py, winapp.py, winlang.py,
                    installer.iss, version.txt, icon
  android/          the Android app (Gradle, Kotlin): build.bat, app/, tools/make_libs.py
  linux/            .deb and .rpm (nfpm): build.bat, build_packages.py, nfpm.yaml, launcher, .desktop, systemd unit
    appimage/       AppImage recipe
    flatpak/        Flatpak manifest and AppStream metadata
  macos/            the .app (assembled, no Mac needed): build.bat, build_app.py, launcher, run.sh
  termux/           installing on a phone with Termux: Share-to-phone.bat, share_to_phone.py, install-termux.sh
tools/              bump_version.py
tests/              test_core.py, test_accessibility.py, a11y/ (seed.py: sample data; audit.py: axe-core and keyboard audit in a browser)
docs/               guides, release-key.asc (public GPG key), screenshots/
.github/            workflows/ (ci, release, finalize), scripts/, issue and pull request templates, dependabot.yml
Start.bat Start.sh  run from the sources
dist/               (not in git) the packages you build locally
generated/          (not in git) data when running from the sources: yt-dlp, ffmpeg, settings, logs, build files
```

## Running from the sources

```
python program/setup_tools.py       # once: yt-dlp, the JavaScript runtime and ffmpeg go into generated/
python program/server.py            # http://localhost:8765/
```

(`Start.bat` / `Start.sh` do both.) Useful environment variables: `YTG_DATA_ROOT` moves everything the program creates
(settings, tools, logs) to another folder; `YTG_UPDATE_URL` replaces the address of the new-version check (for tests).

## Tests

```
python -m unittest discover -s tests -v
```

They need `yt-dlp` to be importable (`pip install "yt-dlp[default]"`, or run `setup_tools.py` once). They do not need the network:
links, error classification, format selection, settings, subscriptions (including "only new"), the new-version check, the finished-
download notices, the language files (every language has every key and the same placeholders, no key is unused), the Windows texts,
the version numbers and `tools/bump_version.py`. CI also checks the JavaScript syntax with Node and starts the server on Windows, macOS and Linux.

**Accessibility.** `tests/test_accessibility.py` (part of the same command) checks the markup of the page, the contrast of every colour pair
of the design and the CSS for the user's preferences. `tests/a11y/audit.py` is a real audit: it drives headless Chrome, Chromium or Edge
through the DevTools protocol, runs [axe-core](https://github.com/dequelabs/axe-core) (WCAG 2.0 to 2.2, A and AA, and best practices) in
light, dark, with a list and the settings window open, in Arabic and at 320 pixels, and checks by keyboard the skip link, the focus order,
the dialog and the zoom. `tests/a11y/seed.py` fills a data folder with sample downloads, so no network is needed:

```
python tests/a11y/seed.py /tmp/ytg-a11y
YTG_DATA_ROOT=/tmp/ytg-a11y python program/server.py --no-browser --port 8782 &
python tests/a11y/audit.py http://localhost:8782/        # needs: pip install websockets
```

The *Accessibility audit* job of `ci.yml` does exactly this. The rules to follow are in [CONTRIBUTING.md](../CONTRIBUTING.md#accessibility)
and the statement for users is [accessibility.md](accessibility.md).

## Building the packages

Everything is built by [GitHub Actions](#automatic-builds-github-actions) for the releases. To build one yourself:

| Package | Command | Needs | Result |
|---|---|---|---|
| Windows installer | `packaging\windows\build.bat` | Python, [Inno Setup 6](https://jrsoftware.org/isdl.php) (PyInstaller and yt-dlp are fetched) | `dist\windows\YT-Grabber-Setup-<version>.exe` |
| Android APKs | `packaging\android\build.bat` | JDK 21, Android SDK (platform 34, build-tools 34.0.0), Gradle 8.7 in `C:\AndroidBuild\` | `dist\android\*.apk` |
| `.deb` and `.rpm` | `packaging\linux\build.bat` (or `python3 packaging/linux/build_packages.py`) | Python (nfpm is downloaded and verified) | `dist/linux/*.deb`, `*.rpm` |
| AppImage | `python3 packaging/linux/appimage/build_appimage.py` | Linux | `dist/linux/*.AppImage` |
| Flatpak | `flatpak-builder` (see the header of `packaging/linux/flatpak/*.yml`) | Linux, flatpak-builder | a Flatpak repository, then `flatpak build-bundle` |
| macOS app | `packaging\macos\build.bat` (or `python3 packaging/macos/build_app.py`) | Python, Internet (no Mac needed) | `dist/macos/YT-Grabber-macOS.zip` |

Each folder in `packaging/` has a README with the details of that package.

## Automatic builds (GitHub Actions)

| Workflow | When | What it does |
|---|---|---|
| `ci.yml` | every push and pull request | unit tests, JavaScript syntax check, and a smoke test (start the server, call it) on Ubuntu, Windows and macOS; and the accessibility audit (axe-core in Chrome) |
| `release.yml` | a tag `v*` is pushed, or by hand | builds every package, **installs and starts each one** to prove it works (Windows: install, start, uninstall; Ubuntu: `.deb` and AppImage; Fedora: `.rpm`; Flatpak: build and run; Apple Silicon and Intel Macs), then attaches the files to the release |
| `finalize.yml` | called by `release.yml`, or by hand | signs the `.rpm`, writes `SHA256SUMS` and signs it with GPG, adds build attestations, builds the signed apt and dnf repositories, installs from them on Ubuntu and Fedora, and publishes them on GitHub Pages |

The helper scripts are in `.github/scripts/` (`wait_ping.sh`, `build_repos.sh`). Running `release.yml` by hand without a tag
only builds and tests: nothing is published.

## Making a release

1. Set the version everywhere: `python tools/bump_version.py 1.4.0` (it changes `program/server.py`, the Windows version file, the
   Flatpak metadata and the Android `versionName`/`versionCode`, and tells you if `CHANGELOG.md` has no section for it).
2. Write the section of `CHANGELOG.md`. Run the tests. Commit and push; wait for the **CI** to be green.
3. Push the tag: `git tag -a v1.4.0 -m "YT Grabber 1.4.0" && git push origin v1.4.0`. `release.yml` builds and tests everything and
   creates the GitHub release; `finalize.yml` adds the checksums, the signature and the repositories.
4. Build the APKs on the maintainer's computer (`packaging\android\build.bat`: the signing key lives only there), upload them to the
   release (`gh release upload v1.4.0 dist\android\*.apk`), and run **Finalize** again by hand
   (`gh workflow run finalize.yml -f tag=v1.4.0`) so that `SHA256SUMS` includes them.
5. Update the [distribution channels](#distribution-channels) with the new file hashes.
6. Check the release from outside: the signature (`gpg --verify SHA256SUMS.asc SHA256SUMS`), an attestation
   (`gh attestation verify`), and the apt and dnf repositories.

**Secrets and keys.** The repository secret `GPG_PRIVATE_KEY` is the release signing key (its public half is
[`docs/release-key.asc`](release-key.asc), fingerprint in [SECURITY.md](../SECURITY.md)); a backup of the private key must be kept
outside the repository. The Android signing key is in `packaging/android/keystore/` (ignored by git): **keep a copy**, because with a
different key Android refuses to update an installed app. The *github-pages* environment must allow the `main` branch and the tags `v*`.

## Distribution channels

| Channel | Where | How it is updated |
|---|---|---|
| GitHub releases | this repository | `release.yml` |
| apt and dnf repositories | GitHub Pages of this repository | `finalize.yml` |
| Homebrew | the tap [`progliodario/homebrew-tap`](https://github.com/progliodario/homebrew-tap) (`Casks/yt-grabber.rb`) | by hand: new `version` and `sha256` of the Mac zip (the tap has a workflow that installs the cask on a Mac) |
| Scoop | the bucket [`progliodario/scoop-bucket`](https://github.com/progliodario/scoop-bucket) | automatic (its *Excavator* workflow follows the new releases); it has a workflow that installs the app on Windows |
| winget | `microsoft/winget-pkgs`, package `progliodario.YTGrabber` | by hand: a pull request with the three manifest files (version, installer with the SHA-256 of the exe, locale), checked with `winget validate` |

## Conventions

- **English everywhere** in the repository: code, comments, documentation, commit messages. (The interface is translated.)
- **Line endings** are handled by `.gitattributes`: scripts that run on Linux, macOS or Android are always LF; `.bat` files are CRLF.
- **No secrets** in the repository: keys, passwords and local paths stay in ignored files.
- **Versions** are changed only with `tools/bump_version.py`.
- Keep the structure simple: no frameworks and no build step for the page, one program for every platform.
