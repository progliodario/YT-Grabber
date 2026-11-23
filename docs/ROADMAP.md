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

## Next: 1.7 (security and confidence)

| What | Why | Effort |
|---|---|---|
| **A token for the page** (random per run, passed in the first URL, kept in a cookie, checked on every request) | any program on the same computer, or on the same phone, can use `127.0.0.1:8765`; it is also what makes `--host 0.0.0.0` safe | M |
| **Verify what is downloaded at the first start**: ffmpeg and deno against the checksums their makers publish, yt-dlp (exe and APK) against `SHA2-256SUMS`; pip with `--require-hashes` where possible | today a download is only checked for being a zip or an archive | M |
| **Termux installer over a trusted channel**: show a hash on the PC, check it on the phone (or serve over HTTPS) | `curl http://PC:8800/i \| sh` can be altered on the network | S |
| **Test the download without the network**: a fake yt-dlp that writes files, to run `run_item`, `finalize_item`, `fail_item`, retries, 429/bot pauses, resume after a restart | coverage is 34% (`server.py` 25%, `ytworker.py` 0%): the bug of the same-title files would have been found | M |
| **Test the HTTP API end to end** (create a job with a fake yt-dlp, skip, resume, cancel, remove) | most of `do_POST` is untested | M |
| **Split `do_POST`, `job_action`, `enumerate_playlist`, `run_item`** (complexity 48, 49, 47, 34) and move the scheduler and the HTTP layer out of `server.py` | maintainability index of `server.py` is the lowest grade | M |
| **`THIRD_PARTY_NOTICES`**: licences and versions of what is bundled (mutagen is GPL-2.0-or-later, certifi MPL-2.0, ffmpeg GPL); have the combination reviewed | the program is MIT but the exe, APK and AppImage bundle these | S |
| **CI**: pyflakes, bandit and the docs-links check as steps; Python 3.10 to 3.14 in the matrix (the docs say 3.10+, CI runs 3.12); actions pinned by commit | | S |
| **GitHub**: protect `main` (tests required), turn on Dependabot alerts and CodeQL | | S |

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

1. Speed limit and allowed hours (S-M). 2. Format and folder per subscription (S-M). 3. Subtitles and a template for the file names (M).
4. Better tags: track number and album from the playlist, loudness normalisation, FLAC/OGG/WAV (M). 5. An archive that avoids downloading the
same video twice from different playlists (S-M). 6. Proxy (S). 7. SponsorBlock and splitting by chapters (M). 8. Export and import of the
list of links and of the subscriptions (S). 9. History and statistics (M). 10. "Keep the latest N" and notifications per subscription (S).
11. Range selection ("from 20 to 50") and "invert" in the choice of the videos (S). 12. Pause everything, reorder jobs, priorities (M).

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
