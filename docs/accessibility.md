# Accessibility statement

YT Grabber is meant to be usable by everyone: with a keyboard instead of a mouse, with a screen reader or a screen magnifier,
with large text, in high contrast, with a touch screen, with reduced motion, and in your own language. This page says what has
been done, how it was checked, what is **not** checked, and what is known to be imperfect.

**Target:** the [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/), level **AA**. This is a
self-assessment: the interface has not been audited by an independent body, and it has not been tried by the maintainer with real
screen readers (see [What has not been tested](#what-has-not-been-tested)).

*Last reviewed: November 2026, for version 1.3.0 and the changes that follow it.*

## What it covers

Every edition of YT Grabber shows the same web interface: the Windows app (its own window), the Mac app, the Linux packages,
the AppImage and Flatpak (all in your browser), and the Android app (a WebView). The accessibility of that page is what matters
most, and it is the same everywhere. The parts around it (the Windows tray icon and start-up window, the installers, the Android
start-up screen and notification, the messages in the terminal) are described [further down](#around-the-page).

## Using it with the keyboard

Everything can be done without a mouse. The order of the Tab key follows the order on the screen, and the focused control always has a
visible outline (3 pixels, at least 3:1 against what is around it).

| Key | What it does |
|---|---|
| Tab / Shift+Tab | next / previous control. The first stop is **Skip to the main content** (it appears when it has the focus) |
| Enter or Space | press a button, open or close the list of a download, switch a toggle |
| Arrow keys | change the choice inside a group of options (audio or video, the format, the quality) |
| Ctrl+Enter (⌘+Enter on a Mac) | start the download from the box with the links |
| Escape | close the settings window; the focus goes back to the button that opened it |
| Page Up, Page Down, Home, End, arrows | scroll the list of items (it is a region that takes the focus) |

No shortcut uses a single letter, so nothing clashes with the shortcuts of a screen reader or of the speech recognition software.

The **settings window** is modal: when it opens the focus moves into it, Tab and Shift+Tab stay inside it, and everything behind it is
unavailable (also to screen readers) until it closes.

## Using it with a screen reader

- The page has a language (`lang`) that changes with the language you choose, a title, a main landmark, a header and a footer, one
  main heading and a heading for every section and every download.
- Every control has a name; toggles are announced as switches; groups of options are announced with their question ("What to
  download", "Format", ...); icon-only buttons have a text name; decorative icons are hidden.
- The list of a download tells the position of each item ("12 of 1216") even though only the visible rows exist on the page, and
  the filters tell which one is pressed.
- A download card is announced with its title; the button that opens its list says whether the list is open.
- Progress is a progress bar with a value. It is **not** announced every second: that would be unbearable. What is announced, politely,
  is what matters: a download that finished ("Title: 25 downloaded, 1 failed"), a download that stopped with an error, every message in
  the corner of the screen, and the preview of the links you paste ("1 playlist, 2 videos").
- Titles of videos are shown as they come from YouTube, in any language and any direction (`dir="auto"`).

## Seeing it

- **Contrast:** text has at least 4.5:1 against its background, also on the tinted badges and alerts, in the light and in the dark
  theme; the borders of fields and buttons and the state of the switches have at least 3:1. Colours are checked by a unit test.
- **Not only colour:** every state has a word or a shape as well (the chosen option has a tick mark, an error says "Error", a
  paused subscription says "Paused" and has a dashed border).
- **Themes:** light, dark, or automatic (the setting of your system). The **forced colours** mode of Windows ("contrast themes")
  and the "more contrast" preference are supported.
- **Zoom and text size:** the page works up to 400% zoom (320 CSS pixels wide) without horizontal scrolling, and all text follows
  the font size of your browser (it is sized in `rem`). The rows of the lists grow with the text. Text spacing set by the user
  (line height, letter and word spacing) does not cut anything off. In the Android app the page follows the font size of the system.
- **Motion:** with "reduce motion" on, the animations (the moving progress bars, the pulsing dots, transitions) stop.
- **Touch:** on a touch screen the controls are at least 44 by 44 pixels (24 by 24 with a mouse), and nothing needs a gesture
  other than a tap (and pinch zoom, which stays available).

## Reading it

The interface is written in plain words and translated into 16 languages (Arabic is right to left). Errors say what happened and
what to do. Actions that cannot be undone (cancel, remove, download again, update) ask for confirmation. Messages in the corner stay
long enough to be read (7 seconds, errors 15), wait while you point at them or have the focus on them, and can be closed.
The same things are always in the same places.

## Around the page

| Where | What |
|---|---|
| **Windows app** | the window is Microsoft Edge in app mode, so it behaves as the page does. The tray icon opens the window with a click and has a normal context menu (keyboard: Win+B, then the arrow keys). The start-up window (first start only) sizes itself with the Windows scale setting, has a descriptive title and takes the focus. The installer is the standard Windows wizard |
| **Android app** | pinch zoom is allowed; the start-up screen announces its status (TalkBack) and its title is a heading; the notification has readable text and a "Close" button; the page follows the system font size |
| **macOS, Linux** | the page in your browser; the Terminal window that stays open is plain text |
| **Linux packages** | the menu entry has a name, a description and keywords |
| **This repository** | the documentation has headings in order, descriptive links and alternative text for every picture. The page of the apt and dnf repositories has a language, landmarks, a skip link and enough contrast |

## How it is checked

- **Automatically, at every change** ([`ci.yml`](../.github/workflows/ci.yml), job *Accessibility audit*): the
  [axe-core](https://github.com/dequelabs/axe-core) engine runs on the real page in Chrome, with the rules of WCAG 2.0, 2.1 and 2.2
  levels A and AA and the best practices, in eight situations (light and dark, each with the page alone, with the list of a download open
  and with the settings window open; Arabic; 320 pixels wide), with sample downloads, errors, skipped items and subscriptions. The same script drives the
  keyboard: skip link, focus order, the settings window (focus goes in, stays in, comes back), the list, and zoom to 200%.
- **Unit tests** (`tests/test_accessibility.py`): the markup (names, labels, landmarks, headings, unique ids, references), the colour
  contrast of every colour pair of the design, and the CSS that supports the preferences of the user (reduced motion, forced colours,
  more contrast, touch, rem).
- **By hand**, by the maintainer: keyboard walk-through, 200% text, text spacing, forced colours, 320-pixel reflow.

Automated tools find about a third of the possible problems, so this is **not** a guarantee.

## What has not been tested

The maintainer has **not** tried YT Grabber with NVDA, JAWS, Windows Narrator, VoiceOver, TalkBack or Orca, with voice control, or with a
switch device, because none was available. If you use one, your report is the most valuable thing you can send.

## Known limitations

- The list of items is *virtual*: only the rows on the screen exist on the page, so that a playlist of thousands of items stays fast.
  Screen reader users reach the other rows by scrolling (the list takes the focus and scrolls with the usual keys), and each row
  tells its position. The long titles of videos are cut with "…" on the screen when they do not fit; the whole text is in the page
  (and in the tooltip) and appears when you zoom or widen the window.
- The thumbnails of videos have no text alternative on purpose: the title is next to each one.
- The questions that start with "Are you sure?" are the dialogs of the browser (or, in the Android app, of the system): they follow the
  accessibility of the platform.
- The small start-up window of the Windows app is drawn with Tk, which supports screen readers only partially. It appears only on the
  first start, and its text is also its title.
- The translations were made with an AI model: a mistake can make a text confusing. Corrections are welcome
  ([CONTRIBUTING.md](../CONTRIBUTING.md#translations)).
- Pictures and files of YouTube itself (thumbnails, the pages you open from the list) are outside the control of this project.
- In the Android app the page follows the system font size only when it is opened; after changing the font size, close and reopen the app.

## Tell us

If something does not work for you, please [open an issue](https://github.com/progliodario/YT-Grabber/issues/new/choose) saying what
you use (the screen reader or the setting, the browser, the system) and what happened, or write to proglio.dario.dal.2008@gmail.com.
Accessibility problems are treated as bugs, not as wishes.

## For people who change the code

Keep it this way: read the checklist in [CONTRIBUTING.md](../CONTRIBUTING.md#accessibility), and run
`python -m unittest discover -s tests` and, with the page running on sample data, `python tests/a11y/audit.py`
([how](development.md#tests)).
