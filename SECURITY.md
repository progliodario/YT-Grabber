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
  In that case an **access token** is required (a long random text kept in `token.txt` of the data folder, readable only by the
  owner): every request except `/api/ping` must carry it, as the cookie `ytg_token` (`HttpOnly`, `SameSite=Strict`) or the header
  `X-YTG-Token`. The address printed at start contains it (`?t=...`); the server sets the cookie and removes it from the address. The
  token can be switched off with `--no-token`, which should be done only on a network that is trusted. The token is compared in constant
  time. Even with the token, other devices cannot choose another destination folder or upload cookies, and the actions that affect the
  machine (opening a folder, quitting, updating) are refused.
- The Android application starts its server with a **new token at every start**, so that the other applications of the phone, which
  share `127.0.0.1`, cannot use it. `--token` asks for the same protection on a computer, for example when other users share it.
- Every request that changes something must carry a custom header, so that other web pages cannot make the browser start
  downloads. The `Host` and `Origin` headers are checked, cross-site requests (CORS) are not allowed, and the page is served with a
  Content-Security-Policy (no inline script, only this server and the YouTube thumbnails), `X-Frame-Options: DENY` and
  `Referrer-Policy: no-referrer`. The server does not tell its version and closes connections that stay idle.
- Without `--token`, on the computer that runs it any other program or user can still reach `127.0.0.1` (the page is meant for
  one person on their own computer).
- It never sends cookies, settings or the download list anywhere. The only outgoing connections are to YouTube; to GitHub (yt-dlp
  updates and, twice a day, one request asking for the latest YT Grabber release, which carries only the program name and
  version and can be disabled in *Settings → Notifications and updates*), including, once a day, one request asking for the latest
  yt-dlp release and, when there is one, the download of yt-dlp from the official yt-dlp releases (this can be disabled in
  *Settings → Download engine*); and, at the first start, to the site that provides the ffmpeg build for the system. If a proxy is set
  in the settings, the downloads go through it. Only when *Cut out sponsor segments* is selected, the identifier of each video is
  also sent to the SponsorBlock service (`sponsor.ajay.app`) to ask for its marks.
- What is downloaded at the first start is **verified**: ffmpeg and deno against the SHA-256 that their makers publish next to
  each build, and yt-dlp (the single-file version used by the exe and the APK) against the `SHA2-256SUMS` of its release. A file that
  does not match is deleted and not used; if the list of checksums cannot be read the program says so and goes on (set the
  environment variable `YTG_REQUIRE_CHECKSUMS=1` to refuse instead). The Termux installer served by `share_to_phone.py` carries the
  SHA-256 of the zip and the phone refuses a different file.
- Cookies supplied to the program (a `cookies.txt` file, or read from a browser) are used only to communicate with YouTube. They
  are stored in the program's data folder, never in the download folder; on Linux and macOS that folder and the cookie files are
  readable only by the owner.
