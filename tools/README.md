# Tools for the maintainer

| File | What it does |
|---|---|
| [`bump_version.py`](bump_version.py) | sets the version of YT Grabber in every file that carries it (`program/server.py`, the Windows version file, the Flatpak metadata, the Android `versionName` and `versionCode`) and reports if `CHANGELOG.md` has no section for it. Run it as `python tools/bump_version.py 1.6.0`, never edit the numbers by hand |

The release procedure that uses it is in the [development guide](../docs/development.md#making-a-release).
