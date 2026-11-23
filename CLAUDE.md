# YT Grabber: notes for whoever continues the work

This file is read first by Claude Code and is just as useful to a person. It says what the project is, how to work on it, how to
release it and what went wrong before. The user-facing documentation is in [README.md](README.md) and [docs/](docs/README.md); the
plan of what to do next is in [docs/ROADMAP.md](docs/ROADMAP.md).

## What it is

A downloader for YouTube and YouTube Music: a Python server (`program/server.py`) with a web page (`program/web/`) as its interface,
packaged for Windows (installer), Android (APK), Linux (`.deb`, `.rpm`, AppImage, Flatpak), macOS (zip) and Termux. Exactly 10
simultaneous downloads, files numbered in playlist order, subscriptions, 16 languages, WCAG 2.2 AA accessibility. MIT licence.
Repository: <https://github.com/progliodario/YT-Grabber> (single maintainer). The map of the code is in
[program/README.md](program/README.md) and [docs/development.md](docs/development.md).

## Conventions (the owner's rules)

- **Everything in the repository is in English**: code, comments, documentation, commit messages. The interface is translated (16
  languages); the replies to the owner are in Italian.
- Tone of the `.md` files: formal, impersonal, but easy to understand.
- Git identity for commits and manifests: `proglio.dario.dal.2008@gmail.com`. Commit messages end with
  `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; pull request descriptions end with
  `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- The version number is changed only with `python tools/bump_version.py X.Y.Z`. `CHANGELOG.md` gets a section for it first.
- Never print, paste or commit a secret (see "Secrets"). Never delete or overwrite the Android keystore.
- Texts of the page go in `program/web/lang/en.js` **and** in the other 15 files (a test fails if a key is missing or unused).
- Accessibility rules for the page: [CONTRIBUTING.md](CONTRIBUTING.md#accessibility). The audit must stay at zero violations.
- The program uses only the standard library (plus yt-dlp). No framework, no build step for the page.

## Commands

```
python -m pip install -r requirements-dev.txt     # once (yt-dlp, pyflakes, websockets, ...)
python tools/check.py                             # unit tests + pyflakes + links of the .md files + JavaScript syntax
python tools/check.py --audit                     # also the accessibility audit in a real browser (Chrome or Edge)
python program/server.py --no-browser             # run it: http://localhost:8765/
python tests/a11y/seed.py DIR                     # sample data; then YTG_DATA_ROOT=DIR python program/server.py --port 8782
python tools/verify_release.py 1.6.1              # check a published release from outside
python tools/update_channels.py 1.6.1 --apply     # Homebrew and Scoop
```

Tests need yt-dlp importable. On this machine it lives in `generated/vendor` (installed by `program/setup_tools.py`): `tools/check.py`
sets `PYTHONPATH` for you; when running Python by hand, set `PYTHONPATH=generated/vendor` (including for a server started as a child
process with another `YTG_DATA_ROOT`, which otherwise cannot find yt-dlp and dies silently).

## Making a release

The full procedure with the reasons is in [docs/development.md](docs/development.md#making-a-release). In short:

1. `python tools/bump_version.py X.Y.Z`; rename `## Unreleased` in `CHANGELOG.md` to `## X.Y.Z`; `python tools/check.py --audit`; commit; push;
   wait for CI to be green (it also compiles the Android app).
2. Tag `vX.Y.Z` and push it: `release.yml` builds and tests every package and creates the release, `finalize.yml` signs the checksums and
   publishes the apt and dnf repositories.
3. Build the APKs on the owner's computer (`packaging\android\build.bat`; the signing key exists only there), check their version with
   `aapt2 dump badging` and their certificate (SHA-256 must end `…bc22370cb60c`), upload them
   (`gh release upload vX.Y.Z dist\android\*.apk`), then run `gh workflow run finalize.yml -f tag=vX.Y.Z` so `SHA256SUMS` lists them.
4. `python tools/update_channels.py X.Y.Z --apply` (Homebrew, Scoop), then `python tools/verify_release.py X.Y.Z`.
5. winget: see [docs/ROADMAP.md](docs/ROADMAP.md): do not open a new pull request for every version.
6. A dry run that publishes nothing: `gh workflow run release.yml --ref main` (builds and tests every package; worth it after a change to packaging).

## Secrets and where things are (none of them is in the repository)

- **Android signing key:** `packaging/android/keystore/` (ignored by git) and a backup in `C:\Users\progliodario\YT-Grabber-keys\`.
  A different key means Android refuses to update an installed app. Certificate SHA-256: `0267927b…cb60c`.
- **GPG release key:** the private half is the repository secret `GPG_PRIVATE_KEY` and a local backup in the same keys folder; the
  public half is `docs/release-key.asc` (fingerprint `CF83 6B9B 61A7 7BCC F765 D85E B542 2370 4901 9AAF`, valid until about 2032).
- The `github-pages` environment must allow `main` and the tags `v*`.

## Things that went wrong before (so they do not happen again)

- **Windows PowerShell 5.1 quoting:** multi-line Python in `-c`, here-strings with quotes and `$` inside double quotes break. Write
  a file and run it. A PowerShell helper that takes `@(@(old, new))` with one pair is flattened and replaces single characters: use
  `@(,@(old, new))`, or better the editor tools.
- `[IO.File]::ReadAllText("relative")` resolves against the process folder, not the PowerShell location: use absolute paths.
  `ReadAllText`/`WriteAllText` drop the UTF-8 BOM: `packaging/windows/version.txt` needs exactly one BOM (a test checks it).
- The working tree is CRLF on Windows and LF in git (`.gitattributes`); "LF will be replaced by CRLF" warnings are normal.
- The default `python` here may be a very new version, while `generated/vendor` has wheels for 3.13: use `PYTHONPATH=generated/vendor`.
- Gradle 9 forks a second process unless `org.gradle.jvmargs` equals `GRADLE_OPTS` (including `-Xms64m`); the fork dies with
  "Unable to establish loopback connection" on this machine. See `packaging/android/gradle.properties`.
- Port 8765 may already be taken by an installed copy of YT Grabber: use another port for tests and for `adb forward`.
- The installed NVDA needs administrator rights to restart; to test with it, start it with `--debug-logging -f <log>` from a `.cmd`
  opened through `explorer.exe`, read what it says from the log, then delete the log (it holds everything that was read aloud).
- The Android emulator (`ytg_test`, Android 14) needs a tap on "Wait" and "Not now" at the first start of the app on a slow machine.
- Leftover servers and `ytworker` processes after a test: stop them (`Get-CimInstance Win32_Process` by command line).
- Do not open a new winget pull request per release (it resets the review queue); see the roadmap.
- `git status` on a clean tree must be empty: keep scratch files out of the repository (`tests/.coverage`, `*.bak`).

## What to do next

[docs/ROADMAP.md](docs/ROADMAP.md): bugs found, security work, tests, features, distribution, with what is done and what is not.
