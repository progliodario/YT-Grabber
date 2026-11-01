# Linux packages

*Part of [YT Grabber](../README.md). The ready-to-install files are attached to each
[release](https://github.com/progliodario/YT-Grabber/releases/latest) (and are built into the **`Linux\`** folder when you
rebuild them); this folder contains what is needed to **rebuild** them.*

| Format | For | How to get it |
|---|---|---|
| apt repository / `yt-grabber_<version>_all.deb` | Debian, Ubuntu, Linux Mint, Pop!_OS, Raspberry Pi OS... | repository below, or the file from the release |
| dnf repository / `yt-grabber-<version>-1.noarch.rpm` | Fedora, RHEL / Rocky / Alma, openSUSE... | repository below, or the file from the release |
| `YT-Grabber-x86_64.AppImage`, `YT-Grabber-aarch64.AppImage` | any distribution, PC or ARM (Raspberry Pi) | one file: `chmod +x` and run it |
| `YT-Grabber-x86_64.flatpak` | any distribution with Flatpak | `flatpak install --user YT-Grabber-x86_64.flatpak` |

The `.deb` and `.rpm` are "all" / "noarch" packages: the program is Python, so they work on every processor.
The AppImage contains its own Python, so it needs nothing from the system.

## Install

**With the repositories** (recommended: updates arrive with the normal system updates; the repositories are signed):

```
# Debian / Ubuntu / Mint / Raspberry Pi OS
sudo install -d /etc/apt/keyrings
curl -fsSL https://progliodario.github.io/YT-Grabber/yt-grabber.gpg | sudo tee /etc/apt/keyrings/yt-grabber.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/yt-grabber.gpg] https://progliodario.github.io/YT-Grabber/apt stable main" | sudo tee /etc/apt/sources.list.d/yt-grabber.list
sudo apt update && sudo apt install yt-grabber

# Fedora / RHEL / openSUSE
sudo curl -fsSL -o /etc/yum.repos.d/yt-grabber.repo https://progliodario.github.io/YT-Grabber/yt-grabber.repo
sudo dnf install yt-grabber
```

**From a downloaded file:**

```
sudo apt install ./yt-grabber_<version>_all.deb        # Debian / Ubuntu family
sudo dnf install ./yt-grabber-<version>-1.noarch.rpm   # Fedora / RHEL family
chmod +x YT-Grabber-x86_64.AppImage && ./YT-Grabber-x86_64.AppImage
flatpak install --user YT-Grabber-x86_64.flatpak && flatpak run io.github.progliodario.YTGrabber
```

The packages need **Python 3 and pip** (the package manager installs them if missing). `ffmpeg` and `python3-tk` (for the
*Browse...* button) are recommended: on Debian / Ubuntu they are installed with the package. On Fedora ffmpeg is not
in the default repositories; if the system has none, YT Grabber downloads a static copy on first start.

## Use

Open **YT Grabber** from the applications menu, or run `yt-grabber` in a terminal. The browser opens at
`http://localhost:8765/`. With the `.deb` / `.rpm`, a terminal window stays open while it runs: close it (or press Ctrl+C)
to quit. The AppImage and the Flatpak have no window to close: they quit by themselves after 10 minutes without use.

- The program is installed in `/opt/yt-grabber` and is never modified. Everything it creates (yt-dlp, settings, the
  download list, cookies, logs) lives in `~/.local/share/yt-grabber` (Flatpak: `~/.var/app/io.github.progliodario.YTGrabber`).
- Downloads go to the `Downloads` folder of your user, in `YT-Grabber` (change it in *Settings*).
- The first start needs Internet: it installs yt-dlp (about a minute). Later starts are immediate.
- Options: `yt-grabber --port 9000`, `--dir ~/Music`, `--host 0.0.0.0` (see the main README for use from a phone).

### Subscriptions in the background

Subscriptions (new videos downloaded automatically) need the program to be running. The `.deb` and `.rpm` include a
systemd user service that keeps it running without a window:

```
systemctl --user enable --now yt-grabber
```

Then open `http://localhost:8765/` whenever you want to look. Stop it with `systemctl --user disable --now yt-grabber`.

## Remove

```
sudo apt remove yt-grabber        # or: sudo dnf remove yt-grabber
rm -rf ~/.local/share/yt-grabber  # optional: also delete your settings and the downloaded tools
```

## Rebuild the packages

```
build-linux\build-linux.bat                          # .deb and .rpm (works on Windows, Linux, macOS)
python3 build-linux/appimage/build_appimage.py       # AppImage x86_64 and aarch64 (Linux only)
flatpak-builder --user --install-deps-from=flathub --force-clean fp-build build-linux/flatpak/io.github.progliodario.YTGrabber.yml
```

`build_packages.py` only needs Python: it downloads [nfpm](https://nfpm.goreleaser.com) (a packaging tool; the download is
checked against the checksums published with the release) into `generated\nfpm\`, prepares a staging folder in
`generated\linux-stage\` and builds both packages into `Linux\`. The AppImage script downloads a portable Python
(python-build-standalone) and appimagetool, both checked against published digests.

The official files are built and tested by GitHub Actions (`.github/workflows/release.yml`): the `.deb` is installed and
started on Ubuntu, the `.rpm` on Fedora, the AppImage on Ubuntu, the Flatpak is built and run, and the signed
apt / dnf repositories are installed from on Ubuntu and Fedora before they are published.

### What is in this folder

| File | What it is |
|---|---|
| `build-linux.bat` | the build script for Windows |
| `build_packages.py` | does the work (downloads nfpm, stages the files, builds `.deb` and `.rpm`) |
| `nfpm.yaml` | the package description: name, dependencies, which file goes where |
| `yt-grabber` | the launcher installed as `/usr/bin/yt-grabber` |
| `yt-grabber.desktop` | the menu entry |
| `yt-grabber.service` | the systemd user service |
| `appimage/` | recipe of the AppImage (`AppRun`, `.desktop`, `build_appimage.py`) |
| `flatpak/` | recipe of the Flatpak (manifest, `.desktop`, AppStream metadata, launcher) |

## Status

Built and started by GitHub Actions on Ubuntu 24.04 and Fedora before every release (see above). Not yet tried on every
distribution and desktop: if something does not work, please open an issue on GitHub.
