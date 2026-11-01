# Accessibility statement

YT Grabber is designed to be usable by everyone: with a keyboard instead of a mouse, with a screen reader or a screen magnifier, with
large text, in high contrast, with a touch screen, with reduced motion, and in the user's own language. This page describes what has
been done, how it was checked, what has **not** been checked, and what is known to be imperfect.

**Target:** the [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/), level **AA**. This is a
self-assessment: the interface has not been audited by an independent body, and the maintainer has not tried it with real screen
readers (see [What has not been tested](#what-has-not-been-tested)).

*Last reviewed: November 2026, for version 1.3.0 and the changes that follow it.*

## Scope

Every edition of YT Grabber presents the same web interface: the Windows application (in its own window), the Mac application, the
Linux packages, the AppImage and the Flatpak (all in the browser), and the Android application (a WebView). The accessibility of
that page is the most important aspect, and it is the same everywhere. The surrounding parts (the Windows tray icon and start-up
window, the installers, the Android start-up screen and notification, and the messages in the terminal) are described
[further down](#around-the-page).

## Keyboard use

Every function can be used without a mouse. The order of the Tab key follows the order on the screen, and the control that has the
focus always has a visible outline (3 pixels, with a contrast of at least 3:1 against its surroundings).

| Key | Action |
|---|---|
| Tab / Shift+Tab | next / previous control. The first stop is **Skip to the main content**, which becomes visible when it has the focus |
| Enter or Space | press a button, open or close the list of a download, switch a toggle |
| Arrow keys | change the choice within a group of options (audio or video, the format, the quality) |
| Ctrl+Enter (⌘+Enter on a Mac) | start the download from the box that contains the links |
| Escape | close the settings window; the focus returns to the button that opened it |
| Arrow Up / Down, Home, End, Page Up / Down | in the list of items: move from row to row (the list is a single stop of the Tab key; the buttons of the current row are reached with Tab) |

No shortcut uses a single letter, so there is no conflict with the shortcuts of a screen reader or of speech recognition software.

The **settings window** is modal. When it opens, the focus moves into it, Tab and Shift+Tab remain inside it, and everything behind it
is unavailable (including to screen readers) until it closes.

## Screen reader use

- The page has a language (`lang`) that changes with the selected language, a title, a main landmark, a header and a footer, one main
  heading, and a heading for every section and every download.
- Every control has a name. Toggles are announced as switches, groups of options are announced with their question ("What to
  download", "Format", and so on), icon-only buttons have a text name, and decorative icons are hidden.
- The list of a download announces the position of each item ("12 of 1216") even though only the visible rows exist on the page, and
  the filters announce which one is pressed.
- A download card is announced with its title, and the button that opens its list states whether the list is open.
- Progress is exposed as a progress bar with a value. It is **not** announced every second, because that would be unusable. What is
  announced, politely, is what matters: a download that finished ("Title: 25 downloaded, 1 failed"), a download that stopped with an
  error, every message in the corner of the screen, and the preview of the pasted links ("1 playlist, 2 videos").
- Video titles are shown as they are provided by YouTube, in any language and in any direction (`dir="auto"`).

## Visual presentation

- **Contrast:** text has a contrast of at least 4.5:1 against its background, including on tinted badges and alerts, in both the
  light and the dark theme. The borders of fields and buttons and the state of the switches have at least 3:1. The colours are
  checked by a unit test.
- **Not only colour:** every state also has a word or a shape (the chosen option has a tick mark, an error says "Error", and a
  paused subscription says "Paused" and has a dashed border).
- **Themes:** light, dark, or automatic (following the system setting). The **forced colours** mode of Windows ("contrast themes")
  and the "more contrast" preference are supported.
- **Zoom and text size:** the page works up to 400% zoom (320 CSS pixels wide) without horizontal scrolling, and all text follows the
  font size of the browser (it is sized in `rem`). *Settings → Text size* enlarges everything to 125%, 150% or 200% in addition to
  that, and is checked by the automatic audit. The rows of the lists grow with the text. Text spacing set by the user (line height,
  letter spacing and word spacing) does not cause any content to be cut off. In the Android application the page follows the system
  font size.
- **Motion:** when "reduce motion" is enabled, the animations (moving progress bars, pulsing dots, transitions) stop.
- **Touch:** on a touch screen the controls are at least 44 by 44 pixels (24 by 24 with a mouse), and no function requires a gesture
  other than a tap (pinch zoom also remains available).

## Language and clarity

The interface is written in plain words and translated into 16 languages (Arabic is displayed right to left). Error messages state
what happened and what to do. Actions that cannot be undone (cancel, remove, download again, update) ask for confirmation. Messages
in the corner remain visible long enough to be read (7 seconds, and 15 seconds for errors), wait while the pointer or the focus is on
them, and can be closed. The same elements are always in the same places.

## Around the page

| Component | Details |
|---|---|
| **Windows application** | the window is Microsoft Edge in application mode, so it behaves like the page. The tray icon opens the window with a click and has a standard context menu (keyboard: Win+B, then the arrow keys). The start-up window (first start only) is sized according to the Windows scale setting, has a descriptive title and takes the focus. The installer is the standard Windows wizard |
| **Android application** | pinch zoom is allowed; the start-up screen announces its status (TalkBack) and its title is a heading; the notification has readable text and a "Close" button; the page follows the system font size |
| **macOS, Linux** | the page is displayed in the browser; the Terminal window that remains open contains plain text |
| **Linux packages** | the menu entry has a name, a description and keywords |
| **This repository** | the documentation has headings in order, descriptive links and alternative text for every picture. The page of the apt and dnf repositories has a language, landmarks, a skip link and sufficient contrast |

## How conformance is checked

- **Automatically, at every change** ([`ci.yml`](../.github/workflows/ci.yml), job *Accessibility audit*): the
  [axe-core](https://github.com/dequelabs/axe-core) engine runs on the real page in Chrome, with the rules of WCAG 2.0, 2.1 and 2.2
  levels A and AA and the best practices. It runs in eight situations (light and dark, each with the page alone, with the list of a
  download open and with the settings window open; Arabic; and 320 pixels wide), using sample downloads, errors, skipped items and
  subscriptions. The same script operates the keyboard: skip link, focus order, the settings window (the focus enters it, remains in
  it and returns), the list, and zoom to 200%.
- **Unit tests** (`tests/test_accessibility.py`): the markup (names, labels, landmarks, headings, unique identifiers, references), the
  colour contrast of every colour pair of the design, and the CSS that supports the preferences of the user (reduced motion, forced
  colours, increased contrast, touch, `rem`).
- **Manually**, by the maintainer: keyboard walk-through, 200% text, text spacing, forced colours, and reflow at 320 pixels.

Automated tools find only about a third of the possible problems, so this is **not** a guarantee of conformance.

## What has not been tested

YT Grabber has **not** been tested with a real screen reader (NVDA, JAWS, Windows Narrator, VoiceOver, TalkBack or Orca), nor with
voice control or switch devices. An attempt was made with NVDA (portable version, official download, signature verified), but it
could not work in the automated session used for development, because that session provides no foreground window to the screen
reader. The **accessibility tree** of the page in Chromium was checked instead; this is the data that every screen reader on Windows
reads. It covers the names, roles and states of the controls, the headings and the landmarks, and no control without a name was
found. The check revealed one real problem (a tick mark was read as part of the name of the chosen option), which has been fixed.
Reports from screen reader users are the most valuable contribution that can be made.

## Known limitations

- The list of items is *virtual*: only the rows that are on the screen exist on the page, so that a playlist of thousands of items
  remains fast. Screen reader users reach the other rows with the arrow keys (the list scrolls to the row that receives the focus),
  and each row announces its position. Long video titles are truncated with "…" on the screen when they do not fit; the complete text
  is in the page (and in the tooltip) and becomes visible when the page is zoomed or the window is widened.
- Video thumbnails have no text alternative on purpose, because the title is next to each one.
- The questions that begin with "Are you sure?" are dialogs of the browser (or, in the Android application, of the system), so they
  follow the accessibility of the platform.
- The small start-up window of the Windows application is drawn with Tk, which supports screen readers only partially. It appears
  only at the first start, and its text is also its title.
- The translations were made with an AI model, and a mistake can make a text confusing. Corrections are welcome
  ([CONTRIBUTING.md](../CONTRIBUTING.md#translations)).
- Images and files from YouTube itself (thumbnails, and the pages opened from the list) are outside the control of this project.
- In the Android application the page follows the system font size only when it is opened; after the font size is changed, the
  application must be closed and reopened.

## Feedback

Anyone who encounters a difficulty is asked to [open an issue](https://github.com/progliodario/YT-Grabber/issues/new/choose)
stating what is used (the screen reader or the setting, the browser and the system) and what happened, or to write to
proglio.dario.dal.2008@gmail.com. Accessibility problems are treated as bugs, not as requests for new features.

## For contributors

To preserve the current level, read the rules in [CONTRIBUTING.md](../CONTRIBUTING.md#accessibility) and run
`python -m unittest discover -s tests` and, with the page running on sample data, `python tests/a11y/audit.py`
([instructions](development.md#tests)).
