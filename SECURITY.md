# Security

- [Reporting a problem](#reporting-a-problem)
- [Verifying that a download is genuine](#verifying-that-a-download-is-genuine)
- [Antivirus and "unknown publisher" warnings](#antivirus-and-unknown-publisher-warnings)
- [What the program does and does not do](#what-the-program-does-and-does-not-do)

## Reporting a problem

Please submit a private report at <https://github.com/progliodario/YT-Grabber/security/advisories/new>, or write to
proglio.dario.dal.2008@gmail.com. The details should not be made public until a fix is available.

## Verifying that a download is genuine

Every release contains `SHA256SUMS` (the checksum of each file) and `SHA256SUMS.asc` (its GPG signature).

```
gpg --import docs/release-key.asc        # the public key is stored in this repository
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum --check --ignore-missing SHA256SUMS
```

On Windows, `certutil -hashfile <file> SHA256` prints the checksum, which is then compared with the list.

Signing key: **YT Grabber Releases** `<proglio.dario.dal.2008@gmail.com>`, fingerprint
`CF836B9B61A77BCCF765D85EB542237049019AAF`. The apt and dnf repositories at <https://progliodario.github.io/YT-Grabber/>
are signed with the same key.

The Windows installer, the Linux packages and the Mac application are built by GitHub Actions from the code in this repository.
Each of them has a **build attestation**, which proves its origin:

```
gh attestation verify YT-Grabber-Setup-<version>.exe --repo progliodario/YT-Grabber
```

The Android APKs are built on the maintainer's computer and signed with the application's own key (`apksigner verify
--print-certs` shows its certificate). They are covered by `SHA256SUMS` but do not have a build attestation.

The **Update now** button of the Windows application downloads the installer only from the project's GitHub releases and
installs it only if its SHA-256 fingerprint matches the one published by GitHub.

## Antivirus and "unknown publisher" warnings

The Windows installer is built with PyInstaller, which some antivirus programs flag in error. It is also not signed with a
paid code-signing certificate, so Windows SmartScreen may initially report an "unknown publisher". To reduce these warnings:

- the release build compiles the PyInstaller launcher from source on GitHub's machines instead of using the prebuilt one;
- the installer is a standard per-user installer (it does not require administrator rights) with a proper uninstaller;
- users who prefer not to trust the installer can run the program from the source code (`Start.bat`): all of it is readable Python.

The [SignPath Foundation](https://signpath.org/) offers free code signing to open-source projects. This project may apply once it
is established enough to be accepted. On macOS the application is signed "ad hoc" and is not notarised, because notarisation
requires a paid Apple developer account; the [installation guide](docs/install.md#macos) describes the prompt shown at first start.

## What the program does and does not do

- It listens on `127.0.0.1` only, unless it is started with `--host 0.0.0.0` to allow use from a phone on the same network.
- Every request that changes something must carry a custom header, so that other web pages cannot make the browser start
  downloads. Actions that affect the machine (choosing or opening a folder, quitting, updating yt-dlp) are accepted only from the
  computer that runs the program.
- It never sends cookies, settings or the download list anywhere. The only outgoing connections are to YouTube; to GitHub (yt-dlp
  updates and, twice a day, one request asking for the latest YT Grabber release, which carries only the program name and
  version and can be disabled in *Settings → Notifications and updates*), including, once a day, one request asking for the latest
  yt-dlp release and, when there is one, the download of yt-dlp from the official yt-dlp releases (this can be disabled in
  *Settings → Download engine*); and, at the first start, to the site that provides the ffmpeg build for the system.
- Cookies supplied to the program (a `cookies.txt` file, or read from a browser) are used only to communicate with YouTube. They
  are stored in the program's data folder, never in the download folder.
