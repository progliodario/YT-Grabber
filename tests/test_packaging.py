"""Packaging: the texts of the Windows app, the version numbers and tools/bump_version.py."""
import os
import re
import sys
import tempfile
import unittest

from support import ROOT, server  # noqa: E402


class WindowsTextTests(unittest.TestCase):
    def test_every_language_has_every_text(self):
        sys.path.insert(0, os.path.join(ROOT, 'packaging', 'windows'))
        try:
            import winlang
        finally:
            sys.path.pop(0)
        en = winlang.TEXTS['en']
        for code in winlang.CODES:
            self.assertEqual(sorted(set(en) - set(winlang.TEXTS[code])), [], code)
            for key, value in en.items():
                self.assertEqual(sorted(re.findall(r'\{(\w+)\}', value)),
                                 sorted(re.findall(r'\{(\w+)\}', winlang.TEXTS[code][key])), '%s %s' % (code, key))


class BumpVersionTests(unittest.TestCase):
    """tools/bump_version.py, run on a scratch copy of the files that carry the version."""
    FILES = ('program/server.py', 'packaging/windows/version.txt',
             'packaging/linux/flatpak/io.github.progliodario.YTGrabber.metainfo.xml',
             'packaging/android/app/build.gradle.kts', 'CHANGELOG.md')

    def test_every_file_follows(self):
        import importlib.util
        import shutil
        spec = importlib.util.spec_from_file_location('bump_version', os.path.join(ROOT, 'tools', 'bump_version.py'))
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        tmp = tempfile.mkdtemp(prefix='ytg_bump_')
        self.addCleanup(shutil.rmtree, tmp, True)
        for rel in self.FILES:
            os.makedirs(os.path.dirname(os.path.join(tmp, rel)), exist_ok=True)
            shutil.copy(os.path.join(ROOT, rel), os.path.join(tmp, rel))
        tool.ROOT = tmp
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(tool.main(['bump_version.py', '9.8.7']), 0)

        def read(rel):
            with open(os.path.join(tmp, rel), 'rb') as f:
                return f.read()
        self.assertIn(b"APP_VERSION = '9.8.7'", read('program/server.py'))
        win = read('packaging/windows/version.txt')
        self.assertTrue(win.startswith(b'\xef\xbb\xbf#') and b"'9.8.7'" in win and b'(9, 8, 7, 0)' in win)
        self.assertIn(b'<release version="9.8.7"', read('packaging/linux/flatpak/io.github.progliodario.YTGrabber.metainfo.xml'))
        gradle = read('packaging/android/app/build.gradle.kts')
        self.assertIn(b'versionName = "9.8.7"', gradle)
        self.assertIn(b'versionCode = 90807', gradle)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(tool.main(['bump_version.py', '9.8.7']), 0, 'running it twice changes nothing more')


class VersionTests(unittest.TestCase):
    def test_versions_agree(self):
        version = server.APP_VERSION
        with open(os.path.join(ROOT, 'packaging', 'windows', 'version.txt'), 'rb') as f:
            raw = f.read()
        self.assertFalse(raw.startswith(b'\xef\xbb\xbf\xef\xbb\xbf'), 'two byte-order marks: PyInstaller cannot read it')
        text = raw.decode('utf-8-sig')
        self.assertIn("'%s'" % version, text)
        self.assertIn('(%s, 0)' % version.replace('.', ', '), text)
        with open(os.path.join(ROOT, 'packaging', 'linux', 'flatpak', 'io.github.progliodario.YTGrabber.metainfo.xml'), encoding='utf-8') as f:
            self.assertIn('version="%s"' % version, f.read())
        with open(os.path.join(ROOT, 'packaging', 'android', 'app', 'build.gradle.kts'), encoding='utf-8') as f:
            self.assertIn('versionName = "%s"' % version, f.read())


if __name__ == '__main__':
    unittest.main()
