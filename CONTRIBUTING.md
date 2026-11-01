# Contributing to YT Grabber

Contributions are welcome and appreciated: bug reports, corrected translations, ideas and code.

- [Reporting a problem](#reporting-a-problem)
- [Suggesting a change](#suggesting-a-change)
- [Translations](#translations)
- [Accessibility](#accessibility)
- [Changing the code](#changing-the-code)

## Reporting a problem

[Open an issue](https://github.com/progliodario/YT-Grabber/issues/new/choose) and include the following information:

- the **version** of YT Grabber (open `http://localhost:8765/api/ping` in the browser, or read the first lines printed in the
  terminal; *Settings → Download engine* shows the yt-dlp version, which is also useful), and the installation method (installer,
  apt, AppImage, APK, sources, and so on);
- the **system** in use (for example Windows 11, Ubuntu 24.04, macOS 15 on Apple Silicon, Android 14);
- the steps performed, the expected result and the actual result; for a download problem, the exact error shown for the video;
- the **log**: `app.log` and the other files in the `data/logs` folder (see [where things are stored](docs/usage.md#where-things-are-stored)).
  Any private information should be removed beforehand.

Many download errors are resolved by *Settings → Update yt-dlp and restart*, which should be tried before reporting.
**Security problems** must not be reported in a public issue; see [SECURITY.md](SECURITY.md).

## Suggesting a change

Open an issue describing the idea and, above all, **the purpose it would serve**. The project is deliberately small: one program for
every platform, no accounts, and nothing sent to a server. Proposals that respect these principles are more likely to be accepted.

## Translations

The interface is available in 16 languages. The texts were written with an AI model, so corrections by native speakers are very
valuable. Each language is a single file, `program/web/lang/<code>.js`:

```js
window.I18N.it = {
  'compose.title': 'Scarica da YouTube e YouTube Music',
  'subs.new': {one: '{n} nuovo video', other: '{n} nuovi video'},
  ...
};
```

- **English (`en.js`) is the reference.** Every key must exist in every language, with the same `{placeholders}`.
  The unit tests verify this (`python -m unittest discover -s tests`).
- Values of the form `{one: ..., other: ...}` are plural forms. Provide the forms that the language requires (`zero`, `one`, `two`,
  `few`, `many`, `other`).
- Texts should be short, because they must fit on buttons and on phones. The names `YT Grabber`, `yt-dlp`, `ffmpeg` and
  `cookies.txt` are not translated.
- To **correct a text**, edit the relevant file and submit a pull request, or open an issue containing the corrected text.
- To **add a language**, create `lang/<code>.js` and also: add the language to `LANGS` in `program/web/app.js` and to `LANG_CODES` in
  `program/ytsettings.py`; to `CODES` and `TEXTS` in `packaging/windows/winlang.py` (the Windows tray menu and start-up window); to the
  languages of `packaging/windows/installer.iss`; and create `packaging/android/app/src/main/res/values-<code>/strings.xml`.
  The tests report anything that is missing. Right-to-left languages are already supported (Arabic is the example).

## Accessibility

YT Grabber aims at WCAG 2.2 level AA (see [docs/accessibility.md](docs/accessibility.md)). Changes to the page (`program/web/`) must
observe the following rules:

- Every control has a name (a visible label, or `aria-label` for an icon). Toggles use `role="switch"`, and groups of options are labelled.
- A button is a `<button>` and a link is an `<a href>`; a `<div>` with a click handler is not acceptable. Purely decorative icons
  receive `aria-hidden="true"`.
- The outline of a focusable element is never removed, and colour is never the only means of conveying information (a word, a mark
  or a shape is added).
- Colours come from the tokens at the top of `app.css` (`--fg`, `--muted`, `--accent-ink`, `--ctrl`, and so on), which have sufficient
  contrast in both themes: `tests/test_accessibility.py` fails if a pair does not. `opacity` is not used on text.
- Text sizes are expressed in `rem`, never in `px`. Layouts must work at 320 CSS pixels and with text at 200%.
- When the page changes without user action (something finished or failed), the change is communicated with `announce()` or a toast,
  not only visually. When part of the page is rebuilt, the keyboard focus is preserved (`setH`, `setHtmlKeepFocus`).
- A new dialog requires a title, a focus trap, Escape to close it and the return of the focus to the button that opened it (the
  settings window is the model).
- Texts intended for screen readers (names, announcements) are kept in `en.js` and in the other languages, like any other text.

To check a change, always run `python -m unittest discover -s tests` and, with the page running on sample data, the browser audit:

```
python tests/a11y/seed.py /tmp/ytg-a11y
YTG_DATA_ROOT=/tmp/ytg-a11y python program/server.py --no-browser --port 8782 &
python tests/a11y/audit.py http://localhost:8782/
```

The audit requires `pip install websockets` and Chrome, Chromium or Edge. It also runs in CI.

## Changing the code

- Read [docs/development.md](docs/development.md), which describes the architecture, the layout, how to run the program from the
  sources and the tests, and [program/README.md](program/README.md), which explains the modules and the rules for adding one.
- The program is written in Python 3 using only the standard library (plus yt-dlp), with 4-space indentation and short comments in
  **English** that explain *why*. The page uses plain JavaScript (in the style of the existing code, without a framework or a build
  step) and CSS.
- Run the tests before submitting a change: `python -m unittest discover -s tests`. Add a test for each fix or new feature, in the file of its subject (see [tests/README.md](tests/README.md)).
  When possible, also run `python -m pyflakes program packaging tests`.
- When the texts of the page are changed, update them in `en.js` and in the other languages (a machine translation is acceptable as
  a first version; the pull request should say so).
- A pull request should address one subject only and should describe what changed and how it was tested. The version number must not
  be changed: the maintainer sets it when releasing (`tools/bump_version.py`).

By contributing, authors agree that their work is released under the project's [MIT licence](LICENSE).
