# The program

This folder is the whole program: a Python server, the download workers and the web page. It runs the same way on every platform;
the folders in [`../packaging`](../packaging/README.md) only add what each platform needs around it.

| File | Role |
|---|---|
| `server.py` | the entry point and the logic that ties everything together: the scheduler with exactly 10 download slots, the download of one item, the reading of playlists, the actions on a job, subscriptions, the HTTP API, shutdown |
| `ytworker.py` | one download worker. The server starts 10 of them as persistent processes and talks to them with JSON lines |
| `ytcommon.py` | what the server and the workers share: paths, the catalogue of errors and their causes, how a format is chosen, `atomic_write` |
| `ytsettings.py` | the settings: defaults, validation of what the page sends, `settings.json` |
| `ytmodel.py` | what a download is: `Item` (one video, with its state) and `Job` (a link and its items). Data only |
| `ytlinks.py` | what a pasted link is (video, playlist, channel) and how the files of a playlist are named |
| `ytupdates.py` | new versions of YT Grabber (the notice and the one-click install on Windows) and the automatic update of yt-dlp. It never imports `server`: the server gives it what it needs with `configure()` |
| `setup_tools.py` | installs yt-dlp, the JavaScript runtime and ffmpeg at the first start |
| `web/` | the interface: `index.html`, `app.css`, `app.js` (no build step, no dependencies), `lang/*.js` (16 languages), icons, the web manifest |

## Rules for the modules

- Every module starts with `import ytcommon` (directly or through another `yt*` module): it sets the paths, also inside the Windows exe,
  and puts yt-dlp on `sys.path`.
- A module never imports `server`. When the server runs as a script, its name is `__main__`, and importing it by name would load a
  second copy with its own state. Whatever a module needs from the server is passed in (see `ytupdates.configure`).
- The names start with `yt` so they cannot be confused with other packages on `sys.path`.
- New modules need no change to the packaging: the Android build includes `*.py`, the other packages copy this folder, and the
  Windows build finds them through the imports of `server.py` (their names are also listed in `packaging/windows/build_windows.py`).

## The states of an item

`q` queued · `a` downloading · `p` converting · `d` done · `e` error · `s` already present · `c` cancelled · `k` skipped. A skipped
item is one that was already there when an "only new videos" subscription started, or one that the user left out (its message is
`ytmodel.SKIP_BY_USER`).

See the [development guide](../docs/development.md) for how a download goes, the tests and the releases.
