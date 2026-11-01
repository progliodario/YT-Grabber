"""The page: the language files (every language has every key) and the texts it uses."""
import os
import re
import unittest

from support import WEB, server, ytcommon, settings  # noqa: E402


class InterfaceTests(unittest.TestCase):
    """The web interface: every language file must translate every English key, with the same placeholders."""
    LINE = re.compile(r"^  '([\w.]+)': (.*?),?\s*$")

    def load(self, code):
        out = {}
        with open(os.path.join(WEB, 'lang', code + '.js'), encoding='utf-8') as f:
            for line in f:
                m = self.LINE.match(line)
                if m:
                    out[m.group(1)] = m.group(2)
        return out

    def languages(self):
        return sorted(f[:-3] for f in os.listdir(os.path.join(WEB, 'lang')) if f.endswith('.js'))

    def test_all_languages_complete(self):
        en = self.load('en')
        self.assertGreater(len(en), 200)
        for code in self.languages():
            if code == 'en':
                continue
            tr = self.load(code)
            self.assertEqual(sorted(set(en) - set(tr)), [], '%s: missing keys' % code)
            self.assertEqual(sorted(set(tr) - set(en)), [], '%s: unknown keys' % code)
            for key, value in en.items():
                if value.startswith('{'):   # plural forms: placeholders may differ ("one" has no {n})
                    continue
                self.assertEqual(sorted(set(re.findall(r'\{(\w+)\}', value))), sorted(set(re.findall(r'\{(\w+)\}', tr[key]))),
                                 '%s: placeholders of %s' % (code, key))

    def test_language_list_matches_files(self):
        with open(os.path.join(WEB, 'app.js'), encoding='utf-8') as f:
            js = f.read()
        listed = sorted(re.findall(r"\['(\w\w)', '[^']+'\]", js[js.index('var LANGS'):js.index('var LANG =')]))
        self.assertEqual(listed, self.languages())
        self.assertEqual(sorted(c for c in settings.LANG_CODES if c), self.languages())

    def test_keys_used_by_the_page_exist(self):
        en = self.load('en')
        with open(os.path.join(WEB, 'app.js'), encoding='utf-8') as f:
            js = f.read()
        with open(os.path.join(WEB, 'index.html'), encoding='utf-8') as f:
            html = f.read()
        used = set(re.findall(r"tr\('([\w.]+)'", js)) | set(re.findall(r'data-i18n(?:-html)?="([\w.]+)"', html))
        for spec in re.findall(r'data-i18n-attr="([^"]+)"', html):
            used |= {p.split(':')[1] for p in spec.split(',')}
        used |= {'ek.' + k for k in ytcommon.ERR} | {'eh.' + k for k in ytcommon.ERR}
        used |= {'tab.' + k for k in 'apqdec'} | {'tab.all'} | {'every.%d' % h for h in server.SUB_INTERVALS}
        used |= {'theme.auto', 'theme.light', 'theme.dark'}
        used = {k for k in used if not k.endswith('.') and k != 'key'}   # prefixes of keys built at run time, and a comment
        self.assertEqual(sorted(k for k in used if k not in en), [])

    def test_unused_english_keys(self):
        """A key nobody uses is a leftover: it would be translated for nothing."""
        en = self.load('en')
        with open(os.path.join(WEB, 'app.js'), encoding='utf-8') as f:
            js = f.read()
        with open(os.path.join(WEB, 'index.html'), encoding='utf-8') as f:
            html = f.read()
        dynamic = ('ek.', 'eh.', 'tab.', 'every.', 'theme.', 'stage.', 'text.')
        unused = [k for k in en if k not in js and k not in html and not k.startswith(dynamic) and k != 'lang.name']
        self.assertEqual(unused, [])
