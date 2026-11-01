# Linux packages

*Part of [packaging](../README.md). To install and use them, see the [installation guide](../../docs/install.md#linux).*

| Format | Built by | Result |
|---|---|---|
| `.deb` and `.rpm` | `build.bat` / `build_packages.py` (with [nfpm](https://nfpm.goreleaser.com)) | `dist/linux/yt-grabber_<version>_all.deb`, `yt-grabber-<version>-1.noarch.rpm` |
| AppImage (x86_64 and aarch64) | `appimage/build_appimage.py` (Linux only) | `dist/linux/YT-Grabber-<arch>.AppImage` |
| Flatpak | `flatpak-builder` and `flatpak/io.github.progliodario.YTGrabber.yml` | a Flatpak repository, then `flatpak build-bundle` |
| apt and dnf repositories | `.github/scripts/build_repos.sh`, run by the `finalize.yml` workflow | published on GitHub Pages |

The `.deb` and `.rpm` are "all" / "noarch" packages: the program is Python, so they work on every processor. The AppImage contains its
own Python ([python-build-standalone](https://github.com/astral-sh/python-build-standalone), checked against the published
checksums) and `appimagetool`. The Flatpak builds its own CPython from source (the runtime has no pip).

## Build

```
packaging\linux\build.bat                           # .deb and .rpm, on Windows (or: python3 packaging/linux/build_packages.py)
python3 packaging/linux/appimage/build_appimage.py   # AppImage x86_64 and aarch64, on Linux
flatpak-builder --user --install-deps-from=flathub --force-clean --repo=repo build-dir packaging/linux/flatpak/io.github.progliodario.YTGrabber.yml
flatpak build-bundle repo dist/linux/YT-Grabber-x86_64.flatpak io.github.progliodario.YTGrabber
```

`build_packages.py` only needs Python: it downloads nfpm (checked against the checksums published with the release) into
`generated/nfpm/`, prepares a staging folder in `generated/linux-stage/` (it lists every folder of `program/` with mode 0755 and
every file with mode 0644 in the package description) and builds both packages.

## What is in this folder

| File | What it is |
|---|---|
| `build.bat`, `build_packages.py` | build the `.deb` and `.rpm` |
| `nfpm.yaml` | the package description: name, dependencies, which file goes where |
| `yt-grabber` | the launcher installed as `/usr/bin/yt-grabber` |
| `yt-grabber.desktop` | the applications-menu entry |
| `yt-grabber.service` | the systemd user service (`systemctl --user enable --now yt-grabber`) |
| `appimage/` | the AppImage recipe: `AppRun`, `.desktop`, `build_appimage.py` |
| `flatpak/` | the Flatpak manifest, `.desktop`, AppStream metadata (`.metainfo.xml`, set by `tools/bump_version.py`) and launcher |
