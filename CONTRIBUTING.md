# Contributing to YT Grabber

Thank you for helping! Bug reports, corrected translations, ideas and code are all welcome.

- [Reporting a problem](#reporting-a-problem)
- [Suggesting something](#suggesting-something)
- [Translations](#translations)
- [Changing the code](#changing-the-code)

## Reporting a problem

[Open an issue](https://github.com/progliodario/YT-Grabber/issues/new/choose) and tell us:

- the **version** of YT Grabber (open `http://localhost:8765/api/ping` in the browser, or look at the first lines printed in the
  terminal; *Settings → Download engine* shows the yt-dlp version, which helps too), and how you installed it (installer, apt,
  AppImage, APK, from the sources...);
- your **system** (Windows 11, Ubuntu 24.04, macOS 15 on Apple Silicon, Android 14...);
- what you did, what you expected and what happened; the exact error shown for a video, if it is about a download;
- the **log**: `app.log` / the files in the `data/logs` folder (see [where things are stored](docs/usage.md#where-things-are-stored)).
  Remove anything private first.

Many download errors are solved by *Settings → Update yt-dlp and restart*: try it before reporting.
For **security problems** do not open a public issue: see [SECURITY.md](SECURITY.md).

## Suggesting something

Open an issue with the idea and, above all, **what you want to do with it**. The project is deliberately small: one program for
every platform, no accounts, nothing sent to a server. Ideas that fit that are more likely to be accepted.

## Translations

The interface is in 16 languages, written with an AI model, so a native speaker's corrections are very valuable. Each language is one
file, `program/web/lang/<code>.js`:

```js
window.I18N.it = {
  'compose.title': 'Scarica da YouTube e YouTube Music',
  'subs.new': {one: '{n} nuovo video', other: '{n} nuovi video'},
  ...
};
```

- **English (`en.js`) is the reference**: every key must exist in every language, with the same `{placeholders}`.
  The unit tests check it (`python -m unittest discover -s tests`).
- Values in `{one: ..., other: ...}` are plural forms; give the forms your language needs (`zero`, `one`, `two`, `few`, `many`, `other`).
- Keep the texts short: they must fit buttons and phones. Do not translate `YT Grabber`, `yt-dlp`, `ffmpeg`, `cookies.txt`.
- To **correct a text**, edit that file and send a pull request (or open an issue with the corrected text).
- To **add a language**, besides the new `lang/<code>.js`: add it to `LANGS` in `program/web/app.js` and `LANG_CODES` in
  `program/server.py`, to `CODES` and `TEXTS` in `packaging/windows/winlang.py` (the Windows tray menu and start-up window),
  to the languages of `packaging/windows/installer.iss`, and add `packaging/android/app/src/main/res/values-<code>/strings.xml`.
  The tests tell you if something is missing. Right-to-left languages work already (Arabic is the example).

## Accessibility

YT Grabber aims at WCAG 2.2 level AA (see [docs/accessibility.md](docs/accessibility.md)). When you change the page (`program/web/`):

- every control needs a name (a visible label, or `aria-label` for an icon), toggles are `role="switch"`, groups of options are labelled;
- a button is a `<button>`, a link is an `<a href>`: never a `<div>` with a click handler. Icons that only decorate get `aria-hidden="true"`;
- never take the outline off a focusable element; do not rely on colour alone (add a word, a mark or a shape);
- colours come from the tokens at the top of `app.css` (`--fg`, `--muted`, `--accent-ink`, `--ctrl`...), which have enough contrast in both
  themes: `tests/test_accessibility.py` fails if a pair does not. Do not use `opacity` on text;
- sizes of text in `rem`, never `px`; layouts must still work at 320 CSS pixels and with the text at 200%;
- when the page changes by itself (something finished, something failed), say it with `announce()` or a toast, not only visually;
  when you rebuild part of the page, keep the keyboard focus (`setH`, `setHtmlKeepFocus`);
- a new dialog needs a title, a focus trap, Escape to close and the focus returned to the button that opened it (copy the settings window);
- texts for screen readers (names, announcements) live in `en.js` and the other languages like any other text.

Check it: `python -m unittest discover -s tests` always, and, with the page running on sample data, the browser audit:

```
python tests/a11y/seed.py /tmp/ytg-a11y
YTG_DATA_ROOT=/tmp/ytg-a11y python program/server.py --no-browser --port 8782 &
python tests/a11y/audit.py http://localhost:8782/
```

It needs `pip install websockets` and a Chrome, Chromium or Edge, and it runs in CI as well.

## Changing the code

- Read [docs/development.md](docs/development.md): how it works, the layout, how to run it from the sources and the tests.
- Python 3 with only the standard library (plus yt-dlp); 4 spaces; short comments in **English** that say *why*. The page is plain
  JavaScript (ES5 style like the existing code, no framework, no build step) and CSS.
- Run the tests before you send a change: `python -m unittest discover -s tests`. Add a test for what you fix or add.
  If you can, run `python -m pyflakes program packaging tests` too.
- If you change texts of the page, change them in `en.js` and in the other languages (a machine translation is fine for a start,
  say so in the pull request).
- Keep a pull request about one thing, and describe what changed and how you tried it. Do not change the version number: the
  maintainer does it when releasing (`tools/bump_version.py`).

By contributing you agree that your work is released under the project's [MIT license](LICENSE).
