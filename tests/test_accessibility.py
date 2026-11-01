"""Static accessibility checks of the page: markup, colour contrast of the design tokens, and the CSS that supports users' settings.

They do not replace a real audit (tests/a11y/audit.py runs axe-core in a browser) but they run everywhere and fail at once when a
change breaks something that was right: a control without a name, a duplicate id, a colour that no longer has enough contrast.
"""
import os
import re
import unittest
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, 'program', 'web')


def read(name):
    with open(os.path.join(WEB, name), encoding='utf-8') as f:
        return f.read()


class Page(HTMLParser):
    """Collects what the checks need from index.html."""

    def __init__(self):
        super().__init__()
        self.elements = []     # (tag, attrs dict, text)
        self.stack = []
        self.labels_for = set()
        self.lang = None
        self.title = ''
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = a.get('lang')
        if tag == 'title':
            self._in_title = True
        if tag == 'label' and a.get('for'):
            self.labels_for.add(a['for'])
        el = {'tag': tag, 'attrs': a, 'text': '', 'parents': [s['tag'] for s in self.stack], 'parent_el': list(self.stack)}
        self.elements.append(el)
        if tag not in ('meta', 'link', 'input', 'br', 'img', 'path', 'circle', 'rect', 'stop', 'hr'):
            self.stack.append(el)

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]['tag'] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        for el in self.stack:
            el['text'] += data


def parse():
    p = Page()
    p.feed(read('index.html'))
    return p


def has_name(el, page):
    a = el['attrs']
    if a.get('aria-label') or a.get('aria-labelledby') or a.get('title'):
        return True
    if 'data-i18n-attr' in a and 'aria-label:' in a['data-i18n-attr']:
        return True
    if el['text'].strip() or a.get('data-i18n'):
        return True
    if a.get('id') in page.labels_for:
        return True
    return any(p['tag'] == 'label' for p in el['parent_el'])


class MarkupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = parse()
        cls.els = cls.page.elements

    def test_language_and_title(self):
        self.assertTrue(self.page.lang, '<html lang> is missing')
        self.assertTrue(self.page.title.strip(), '<title> is empty')

    def test_the_page_can_be_zoomed(self):
        viewport = next(e for e in self.els if e['tag'] == 'meta' and e['attrs'].get('name') == 'viewport')['attrs']['content']
        self.assertNotIn('user-scalable=no', viewport.replace(' ', ''))
        self.assertNotIn('maximum-scale', viewport)

    def test_landmarks_and_one_h1(self):
        tags = [e['tag'] for e in self.els]
        for landmark in ('header', 'main', 'footer'):
            self.assertIn(landmark, tags)
        self.assertEqual(tags.count('h1'), 1)
        main = next(e for e in self.els if e['tag'] == 'main')
        self.assertEqual(main['attrs'].get('id'), 'main')
        self.assertFalse(any(e['tag'] == 'footer' and 'main' in e['parents'] for e in self.els), 'the footer must be outside <main>')

    def test_skip_link_is_first_and_points_to_main(self):
        first = next(e for e in self.els if e['tag'] in ('a', 'button', 'input', 'select', 'textarea'))
        self.assertEqual(first['attrs'].get('href'), '#main')

    def test_headings_do_not_skip_levels(self):
        last = 0
        for e in self.els:
            if re.fullmatch(r'h[1-6]', e['tag']):
                level = int(e['tag'][1])
                self.assertLessEqual(level, last + 1, 'heading %s follows h%d' % (e['tag'], last))
                last = level

    def test_ids_are_unique(self):
        ids = [e['attrs']['id'] for e in self.els if 'id' in e['attrs']]
        self.assertEqual(sorted(i for i in set(ids) if ids.count(i) > 1), [])

    def test_references_point_to_something(self):
        ids = {e['attrs'].get('id') for e in self.els}
        for e in self.els:
            for attr in ('aria-labelledby', 'aria-describedby', 'aria-controls'):
                for ref in (e['attrs'].get(attr) or '').split():
                    self.assertIn(ref, ids, '%s="%s" on <%s>' % (attr, ref, e['tag']))
            if e['tag'] == 'a' and (e['attrs'].get('href') or '').startswith('#') and len(e['attrs']['href']) > 1:
                self.assertIn(e['attrs']['href'][1:], ids)

    def test_every_control_has_a_name(self):
        for e in self.els:
            a = e['attrs']
            if e['tag'] in ('textarea', 'select') or (e['tag'] == 'input' and a.get('type', 'text') not in ('hidden', 'submit')):
                self.assertTrue(has_name(e, self.page), 'no name: <%s id=%s>' % (e['tag'], a.get('id')))
            if e['tag'] == 'button' or (e['tag'] == 'a' and 'href' in a):
                self.assertTrue(has_name(e, self.page), 'no name: <%s id=%s class=%s>' % (e['tag'], a.get('id'), a.get('class')))

    def test_no_positive_tabindex(self):
        for e in self.els:
            self.assertLessEqual(int(e['attrs'].get('tabindex', '0')), 0)

    def test_toggles_are_switches(self):
        for e in self.els:
            if e['tag'] == 'input' and e['attrs'].get('type') == 'checkbox':
                self.assertEqual(e['attrs'].get('role'), 'switch', e['attrs'].get('id'))

    def test_decorative_icons_are_hidden_from_screen_readers(self):
        for e in self.els:
            if e['tag'] == 'svg' and 'ic' in (e['attrs'].get('class') or '').split():
                self.assertEqual(e['attrs'].get('aria-hidden'), 'true')

    def test_radio_groups_are_labelled(self):
        for e in self.els:
            if e['attrs'].get('role') == 'radiogroup':
                self.assertTrue(e['attrs'].get('aria-labelledby') or e['attrs'].get('aria-label'))

    def test_dialog_is_modal_and_named(self):
        dlg = next(e for e in self.els if e['attrs'].get('role') == 'dialog')
        self.assertEqual(dlg['attrs'].get('aria-modal'), 'true')
        self.assertTrue(dlg['attrs'].get('aria-labelledby'))

    def test_live_regions_exist(self):
        roles = {e['attrs'].get('id'): e['attrs'].get('aria-live') for e in self.els}
        self.assertEqual(roles.get('toasts'), 'polite')
        self.assertEqual(roles.get('announce'), 'polite')


class ScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = read('app.js')

    def test_icon_only_controls_have_a_name(self):
        for m in re.finditer(r"'<(?:a|button)[^']*'[^;\n]*\+ IC\.\w+ \+ '</(?:a|button)>'", self.js):
            self.assertIn('aria-label', m.group(0), m.group(0)[:120])

    def test_titles_of_videos_are_not_assumed_to_be_in_the_interface_language(self):
        self.assertIn('dir="auto"', self.js)

    def test_jobs_are_headings_with_real_buttons(self):
        self.assertIn('<h3 class="jtitle"><button type="button" class="jtitle-btn"', self.js)
        self.assertNotIn('role="button" tabindex="0"', self.js)

    def test_status_messages_reach_screen_readers(self):
        self.assertIn('function announce(', self.js)
        self.assertRegex(self.js, r'announce\(tr\(')

    def test_dialog_traps_and_restores_the_focus(self):
        for needle in ('function keepFocusInDialog', 'settingsOpener', 'setBackgroundInert(true)', "key === 'Escape'"):
            self.assertIn(needle, self.js)

    def test_refreshing_the_page_keeps_the_focus(self):
        self.assertIn('function setHtmlKeepFocus', self.js)


# ---------------------------------------------------------------- colour contrast of the design tokens
def rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(c):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def over(rgba, base):
    r, g, b, a = rgba
    return tuple(round(c * a + base[i] * (1 - a)) for i, c in enumerate((r, g, b)))


def tokens(css, selector):
    """The custom properties of the block that starts with `selector`."""
    start = css.index(selector)
    block = css[css.index('{', start) + 1:css.index('}', start)]
    return dict(re.findall(r'--([\w-]+):\s*([^;]+);', block))


class ContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        css = read('app.css')
        cls.light = tokens(css, ':root {')
        dark = tokens(css, ':root[data-theme="dark"]')
        cls.dark = dict(cls.light, **dark)

    def color(self, theme, name):
        v = theme[name].strip()
        m = re.fullmatch(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', v)
        if m:
            return (int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4)))
        return rgb(v)

    def surfaces(self, theme):
        return [self.color(theme, n) for n in ('bg', 'card', 'card2', 'track', 'field')]

    def check_text(self, theme, label):
        surfaces = self.surfaces(theme)
        for name in ('fg', 'fg2', 'muted', 'accent-ink', 'ok', 'info', 'warn', 'err'):
            for s in surfaces:
                self.assertGreaterEqual(contrast(self.color(theme, name), s), 4.5, '%s: %s on %s' % (label, name, s))
        # text on the soft tints used for badges, banners and alerts
        for name in ('ok', 'info', 'warn', 'err'):
            tint = self.color(theme, name + '-soft')
            for base in surfaces:
                self.assertGreaterEqual(contrast(self.color(theme, name), over(tint, base)), 4.5, '%s: %s on its tint over %s' % (label, name, base))
        tint = self.color(theme, 'accent-soft')
        for base in surfaces:
            self.assertGreaterEqual(contrast(self.color(theme, 'accent-ink'), over(tint, base)), 4.5, '%s: accent-ink on its tint' % label)

    def test_text_light(self):
        self.check_text(self.light, 'light')

    def test_text_dark(self):
        self.check_text(self.dark, 'dark')

    def test_boundaries_of_controls_have_3_to_1(self):
        for label, theme in (('light', self.light), ('dark', self.dark)):
            ctrl = self.color(theme, 'ctrl')
            for name in ('card', 'field', 'card2', 'bg'):
                self.assertGreaterEqual(contrast(ctrl, self.color(theme, name)), 3.0, '%s: ctrl on %s' % (label, name))
            for name in ('card', 'bg'):
                self.assertGreaterEqual(contrast(self.color(theme, 'focus'), self.color(theme, name)), 3.0, '%s: focus ring on %s' % (label, name))

    def test_primary_button_text(self):
        for label, theme in (('light', self.light), ('dark', self.dark)):
            ends = re.findall(r'#[0-9a-fA-F]{6}', theme['grad'])
            self.assertEqual(len(ends), 2)
            for end in ends:
                self.assertGreaterEqual(contrast(self.color(theme, 'accent-fg'), rgb(end)), 4.5, '%s: button text on %s' % (label, end))

    def test_text_on_error_fill(self):
        for label, theme in (('light', self.light), ('dark', self.dark)):
            self.assertGreaterEqual(contrast(self.color(theme, 'err-fg'), self.color(theme, 'err')), 4.5, label)


class StyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = read('app.css')

    def test_font_sizes_follow_the_users_setting(self):
        self.assertEqual(re.findall(r'font-size:\s*[\d.]+px', self.css), [])

    def test_supports_the_systems_preferences(self):
        for query in ('prefers-reduced-motion: reduce', 'forced-colors: active', 'prefers-contrast: more', 'pointer: coarse', 'prefers-color-scheme: dark'):
            self.assertIn(query, self.css)

    def test_focus_is_never_removed(self):
        self.assertNotRegex(self.css, r':focus\s*\{[^}]*outline:\s*(0|none)')
        self.assertIn(':focus-visible', self.css)

    def test_no_transparency_on_text(self):
        for m in re.finditer(r'([^{}]+)\{([^}]*opacity:\s*\.[0-9]+[^}]*)\}', self.css):
            selector = m.group(1).strip()
            self.assertNotRegex(selector, r'^\.(foot|sub|row|meter|sw|empty|hint|lbl)\b', selector)


if __name__ == '__main__':
    unittest.main()
