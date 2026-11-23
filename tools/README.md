# Tools for the maintainer

| File | What it does |
|---|---|
| [`check.py`](check.py) | runs the checks of the project in one go: unit tests, pyflakes, the links of the `.md` files, the syntax of the JavaScript, and with `--audit` the accessibility audit in a real browser. `python tools/check.py docs` runs only the links. A check whose tool is missing is shown as skipped, never as passed |
| [`bump_version.py`](bump_version.py) | sets the version of YT Grabber in every file that carries it (`program/server.py`, the Windows version file, the Flatpak metadata, the Android `versionName` and `versionCode`) and reports if `CHANGELOG.md` has no section for it. Run it as `python tools/bump_version.py 1.6.2`, never edit the numbers by hand |
| [`update_channels.py`](update_channels.py) | updates the Homebrew cask and the Scoop manifest with the checksums of a release; without `--apply` it only shows the changes |
| [`verify_release.py`](verify_release.py) | checks a published release from outside: its files, the GPG signature, the checksums, the build attestation and the apt repository |

The release procedure that uses them is in the [development guide](../docs/development.md#making-a-release); the same procedure, with the
mistakes to avoid, is in [`CLAUDE.md`](../CLAUDE.md). What the tools need (yt-dlp, pyflakes, websockets) is in
[`requirements-dev.txt`](../requirements-dev.txt).
