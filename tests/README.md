# Tests

```
python -m unittest discover -s tests -v
```

The tests need `yt-dlp` to be importable (`pip install "yt-dlp[default]"`, or run `python program/setup_tools.py` once). They do not use
the network and they write only in a temporary folder.

| File | What it checks |
|---|---|
| [`support.py`](support.py) | not a test: the paths, a data folder of its own and the modules of the program, shared by the test files |
| `test_links.py` | what a pasted link is |
| `test_errors_and_formats.py` | error messages and their causes; the choice of the format |
| `test_settings.py` | the defaults and the validation of what the page sends |
| `test_subscriptions.py` | subscriptions, including "only new videos" |
| `test_jobs.py` | retrying items, choosing the videos of a playlist, the notice when a download has finished |
| `test_updates.py` | the check for new versions, the one-click install on Windows, the automatic update of yt-dlp |
| `test_interface.py` | the language files (every language has every key and the same placeholders; no key is unused) and the texts the page uses |
| `test_packaging.py` | the texts of the Windows app, the version numbers and `tools/bump_version.py` |
| `test_accessibility.py` | the markup of the page, the contrast of every colour pair, the CSS for the preferences of the user |
| [`a11y/`](a11y/audit.py) | the audit in a real browser (axe-core and the keyboard): `seed.py` fills a data folder with sample downloads, `audit.py` runs it; see [CONTRIBUTING.md](../CONTRIBUTING.md#accessibility) |

A test that needs something of the server replaces it in the module that owns it (for example `updates.hooks.shutdown`, not
`server.shutdown_now`). New tests go in the file of their subject, with a short docstring that says what the class protects.
