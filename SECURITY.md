# Security

- [Reporting a problem](#reporting-a-problem)
- [Checking that a download is genuine](#checking-that-a-download-is-genuine)
- [Antivirus and "unknown publisher" warnings](#antivirus-and-unknown-publisher-warnings)
- [What the program does and does not do](#what-the-program-does-and-does-not-do)

## Reporting a problem

Please open a private report at <https://github.com/progliodario/YT-Grabber/security/advisories/new>, or write to
proglio.dario.dal.2008@gmail.com. Do not publish the details before there is a fix.

## Checking that a download is genuine

Every release contains `SHA256SUMS` (the checksum of every file) and `SHA256SUMS.asc` (its GPG signature).

```
gpg --import docs/release-key.asc        # the public key is in this repository
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum --check --ignore-missing SHA256SUMS
```

On Windows, `certutil -hashfile <file> SHA256` prints the checksum to compare with the list.

Signing key: **YT Grabber Releases** `<proglio.dario.dal.2008@gmail.com>`, fingerprint
`CF836B9B61A77BCCF765D85EB542237049019AAF`. The apt and dnf repositories at <https://progliodario.github.io/YT-Grabber/>
are signed with the same key.

The Windows installer, the Linux packages and the Mac app are built by GitHub Actions from the code in this repository, and each
one has a **build attestation** that proves it:

```
gh attestation verify YT-Grabber-Setup-<version>.exe --repo progliodario/YT-Grabber
```

The Android APKs are built on the maintainer's computer and signed with the app's own key (`apksigner verify --print-certs`
shows it). They are covered by `SHA256SUMS`, but have no build attestation.

## Antivirus and "unknown publisher" warnings

The Windows installer is built with PyInstaller, which some antivirus programs flag by mistake, and it is not signed with a
paid code-signing certificate, so Windows SmartScreen may say "unknown publisher" at first. To reduce this:

- the release build compiles PyInstaller's launcher from source on GitHub's machines instead of using the prebuilt one;
- the installer is a normal per-user installer (no administrator rights) with a proper uninstaller;
- if you prefer not to trust the installer, you can run the program from the source code (`Start.bat`): all of it is readable Python.

Free code signing for open-source projects is offered by the [SignPath Foundation](https://signpath.org/); this project can be
submitted to it once it is established enough to be accepted. On macOS the app is signed "ad hoc" and not notarized (that needs a
paid Apple developer account): see the [installation guide](docs/install.md#macos) for the first-start prompt.

## What the program does and does not do

- It listens on `127.0.0.1` only, unless you start it with `--host 0.0.0.0` to use it from a phone on your network.
- Every request that changes something must carry a custom header, so other web pages cannot make your browser start downloads.
  Actions that touch the machine (choosing or opening a folder, quitting, updating yt-dlp) are accepted only from the computer
  that runs the program.
- It never sends your cookies, settings or download list anywhere. The only outside connections are to YouTube, to GitHub
  (yt-dlp updates and, twice a day, one request asking which is the latest YT Grabber release: it sends only the program name
  and version, and can be switched off in *Settings → Notifications and updates*) and, on the first start, to the site that
  provides the ffmpeg build for your system.
- Cookies you give it (a `cookies.txt` file, or read from a browser) are used only to talk to YouTube and are stored in the
  program's data folder, never in the download folder.
