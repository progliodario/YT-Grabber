# Roadmap

What could be improved or added, in the order in which it is worth doing, with what is already done. It comes from a review of the
whole program (November 2026, version 1.6.0) and from what was learnt afterwards. Check an item off (move it to "Done") in the same
change that does it; add new ideas here instead of leaving them in a conversation.

Effort: **S** a few hours, **M** a day or two, **L** a week or more.

## Done in 1.6.1

Two videos with the same title no longer overwrite each other; Windows reserved names; a bad `Content-Length`; the choice of the
videos no longer refetches the whole list; other devices cannot choose the folder or upload cookies; security headers and a
Content-Security-Policy; no server version; idle timeout; private cookie files; checks of the installer name and path; the file
properties of the exe in English; the first HTTP tests.

## Done after 1.6.1 (waiting for the release of 1.7.0)

An access token for the page (on by itself with `--host 0.0.0.0`, also in the Android app); the SHA-256 of ffmpeg, deno and yt-dlp checked
against what their makers publish, and of the zip that the Termux installer receives; the download pipeline, the HTTP API and the
naming race tested without the network (the fake worker in `tests/fake_worker.py`); errors classified by exception type;
`do_POST` and `job_action` split into route and action tables; `THIRD_PARTY_NOTICES.md`; CI on Python 3.10, 3.12 and 3.14 with pyflakes,
bandit and CodeQL in CI, actions pinned by commit, Dependabot alerts and security updates; speed limit, allowed hours, proxy, pause all, invert
selection, range selection, and saving and restoring the subscriptions and links.

## Next: 1.7 (what is left of it)

| What | Why | Effort |
|---|---|---|
| **pip with `--require-hashes`** where possible (the first start installs yt-dlp with pip) | the hashes of the downloads are checked, but not the ones of pip packages | M |
| **Move the scheduler and the HTTP layer out of `server.py`** (`run_item` and `enumerate_playlist` are still the most complex functions) | maintainability index of `server.py` is the lowest grade | M |
| **Protect `main`** (tests required) | deliberately not done: it would stop direct pushes by the only maintainer; do it when there are contributors | S |
| **Have the licence combination reviewed** (mutagen GPL-2.0-or-later, FFmpeg GPL and the Android library GPL-3.0 inside MIT packages) | the notices list it, but only a lawyer can say whether it is right | S |
## Later: 2.0

| What | Why | Effort |
|---|---|---|
| **Incremental saving of the jobs** (a journal or SQLite) | every 2 s the whole JSON is rewritten: 130 ms and 8 MB at 50,000 items | M |
| **Live updates** (Server-Sent Events) instead of polling every 1.5 s | less work and traffic, a first load of 10 MB at 50,000 items becomes paged | M |
| **APKs built by CI** with the key in a protected environment, with a build attestation | today they are built by hand | M |
| **Code signing on Windows** (SignPath Foundation is free for open source); notarisation on macOS needs a paid developer account | SmartScreen and Gatekeeper warnings | M |
| **Native-speaker review of the 15 translations** and a way to report mistakes | they were written with a model | M |
| **Error classes instead of messages**: `classify_text` matches English strings of yt-dlp | breaks when yt-dlp rewords a message | M |

## Features people may want (by value)

1. Format and folder per subscription (S-M). 2. Subtitles and a template for the file names (M). 3. Better tags: track number and album
from the playlist, loudness normalisation, FLAC/OGG/WAV (M). 4. An archive that avoids downloading the same video twice from different
playlists (S-M). 5. SponsorBlock and splitting by chapters (M). 6. History and statistics (M). 7. "Keep the latest N" and notifications per subscription (S). 8. Reorder jobs and priorities (M).
(Done: speed limit, allowed hours, proxy, pause everything, range selection, "invert", and saving and restoring the subscriptions and links.)

## Distribution

- **winget:** the package `progliodario.YTGrabber` has never been merged. Pull request
  [#467932](https://github.com/microsoft/winget-pkgs/pull/467932) (version 1.6.0) passed every validation, including the installation,
  and waits for a moderator since 2026-11-01. **Do not open a new pull request for each release** (that is what restarted the queue six
  times). Wait for this one; if it stays unanswered, ask politely in a comment; after the merge, use `wingetcreate update` or the komac
  action for the following versions.
- Flathub (needs a review of the manifest and the owner's account), AUR and Chocolatey (accounts of the owner), Snap: not started.
- The Pages site only lists the apt and dnf repositories: a real landing page would help.

## Not verified yet

A real Android phone and TalkBack; a Mac by double-click; the per-machine Windows install and its one-click update (the UAC prompt
appears after the app has closed); a playlist of thousands of videos on the real network; the automatic update of yt-dlp with a real new
version; JAWS, Narrator, VoiceOver and voice control (NVDA was tested twice: see [accessibility.md](accessibility.md)).
Permissions of the cookie files on Linux were set by reading the code and tested only by a unit test that skips on Windows.

## Housekeeping

- The pictures of the main page and of the other languages in `docs/screenshots/` predate the "choose the videos" switch (they were made
  with simulated live data that was not kept); `choose-videos.png` and `settings.png` are current.
- The GPG key expires around 2032: set a reminder to extend it.
- Run `python tools/check.py --audit` before every release; `python -m bandit -r program -ll` and `python -m radon cc program -s -n C` from time to time.
