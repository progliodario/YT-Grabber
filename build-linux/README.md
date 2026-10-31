# Linux packages (.deb and .rpm)

*Part of [YT Grabber](../README.md). The ready-to-install packages are in the **`Linux\`** folder in the main folder;
this folder contains what is needed to **rebuild** them.*

Two packages with the same content, for the two big package families:

| File | For |
|---|---|
| `yt-grabber_1.0.0_all.deb` | Debian, Ubuntu, Linux Mint, Pop!_OS, Raspberry Pi OS... |
| `yt-grabber-1.0.0-1.noarch.rpm` | Fedora, RHEL / Rocky / Alma, openSUSE... |

They are "all" / "noarch" packages: the program is Python, so they work on every processor (PC, ARM, Raspberry Pi).

## Install

```
sudo apt install ./yt-grabber_1.0.0_all.deb          # Debian / Ubuntu family
sudo dnf install ./yt-grabber-1.0.0-1.noarch.rpm     # Fedora / RHEL family
```

They need **Python 3 and pip** (the package manager installs them if missing). `ffmpeg` and `python3-tk` (for the
*Browse...* button) are recommended: on Debian / Ubuntu they are installed with the package. On Fedora ffmpeg is not
in the default repositories; if the system has none, YT Grabber downloads a static copy on first start.

## Use

Open **YT Grabber** from the applications menu, or run `yt-grabber` in a terminal. A terminal window stays open while it
runs; the browser opens at `http://localhost:8765/`. Close the terminal (or press Ctrl+C) to quit.

- The program is installed in `/opt/yt-grabber` and is never modified. Everything it creates (yt-dlp, settings, the
  download list, cookies, logs) lives in `~/.local/share/yt-grabber`.
- Downloads go to `~/Downloads/YT-Grabber` (change it in *Settings*).
- The first start needs Internet: it installs yt-dlp (about a minute). Later starts are immediate.
- Options: `yt-grabber --port 9000`, `--dir ~/Music`, `--host 0.0.0.0` (see the main README for use from a phone).

## Remove

```
sudo apt remove yt-grabber        # or: sudo dnf remove yt-grabber
rm -rf ~/.local/share/yt-grabber  # optional: also delete your settings and the downloaded tools
```

## Rebuild the packages

```
build-linux\build-linux.bat
```

It only needs Python. The script downloads [nfpm](https://nfpm.goreleaser.com) (a packaging tool; the download is
checked against the checksums published with the release) into `generated\nfpm\`, prepares a staging folder in
`generated\linux-stage\` and builds both packages into `Linux\`. The same script works on Linux and macOS
(`python3 build-linux/build_packages.py`).

### What is in this folder

| File | What it is |
|---|---|
| `build-linux.bat` | the build script for Windows |
| `build_packages.py` | does the work (downloads nfpm, stages the files, builds `.deb` and `.rpm`) |
| `nfpm.yaml` | the package description: name, dependencies, which file goes where |
| `yt-grabber` | the launcher installed as `/usr/bin/yt-grabber` |
| `yt-grabber.desktop` | the menu entry |

## Status

The packages were built and their contents checked (file list, permissions, dependencies, metadata), but they were
**not installed on a real Linux system** because none was available when they were made. If something does not work,
please open an issue on GitHub.
