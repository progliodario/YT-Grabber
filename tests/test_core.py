"""Unit tests for the parts of YT Grabber that do not need the network.

Run them with:   python -m unittest discover -s tests -v
(yt-dlp must be importable: pip install "yt-dlp[default]", or run `python program/setup_tools.py` once.)
"""
import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, 'program', 'web')
sys.path.insert(0, os.path.join(ROOT, 'program'))
os.environ['YTG_DATA_ROOT'] = tempfile.mkdtemp(prefix='ytg_test_')   # keep the tests away from the real data folder
# when yt-dlp is installed in the project's own vendor folder (setup_tools.py), use it
VENDOR = os.path.join(ROOT, 'generated', 'vendor')
if os.path.isdir(VENDOR):
    sys.path.insert(0, VENDOR)

import server  # noqa: E402
import ytcommon  # noqa: E402


class UrlTests(unittest.TestCase):
    def test_video_forms(self):
        for raw in ('https://www.youtube.com/watch?v=jNQXAC9IVRw', 'https://youtu.be/jNQXAC9IVRw',
                    'https://www.youtube.com/shorts/jNQXAC9IVRw', 'jNQXAC9IVRw', 'youtube.com/watch?v=jNQXAC9IVRw'):
            kind, url, vid = server.classify_url(raw)
            self.assertEqual((kind, vid), ('video', 'jNQXAC9IVRw'), raw)
            self.assertEqual(url, 'https://www.youtube.com/watch?v=jNQXAC9IVRw')

    def test_playlist_and_channel(self):
        self.assertEqual(server.classify_url('https://www.youtube.com/playlist?list=PLabcdefghijk')[0], 'playlist')
        self.assertEqual(server.classify_url('https://music.youtube.com/playlist?list=OLAK5uy_abcdefgh')[0], 'playlist')
        kind, url, _ = server.classify_url('https://www.youtube.com/@jawed')
        self.assertEqual(kind, 'playlist')
        self.assertTrue(url.endswith('/@jawed/videos'))

    def test_video_inside_playlist(self):
        raw = 'https://www.youtube.com/watch?v=jNQXAC9IVRw&list=PLabcdefghijk'
        self.assertEqual(server.classify_url(raw)[0], 'playlist')
        self.assertEqual(server.classify_url(raw, single_only=True)[0], 'video')
        self.assertEqual(server.classify_url('https://www.youtube.com/watch?v=jNQXAC9IVRw&list=RDjNQXAC9IVRw')[0], 'video')

    def test_not_links(self):
        self.assertIsNone(server.classify_url(''))
        self.assertIsNone(server.classify_url('hello world'))
        self.assertEqual(server.classify_url('https://example.com/video')[0], 'auto')


class ErrorTests(unittest.TestCase):
    CASES = {
        'Private video. Sign in if you have been granted access': 'private',
        'This video has been removed by the uploader': 'deleted',
        'The uploader has not made this video available in your country': 'geo',
        'Sign in to confirm your age': 'age',
        'Join this channel to get access to members-only content': 'members',
        'HTTP Error 429: Too Many Requests': 'ratelimit',
        "Sign in to confirm you're not a bot": 'bot',
        'Requested format is not available': 'format',
        'ERROR: unable to download video data: timed out': 'network',
        'Video unavailable': 'unavailable',
        'something nobody has ever seen': 'other',
    }

    def test_classification(self):
        for message, kind in self.CASES.items():
            self.assertEqual(ytcommon.classify_text(message), kind, message)

    def test_disk_errno(self):
        self.assertEqual(ytcommon.classify_text('x', errno=28), 'disk')

    def test_every_kind_has_a_label(self):
        for kind in set(self.CASES.values()) | {'disk', 'postproc', 'copyright', 'live', 'premium'}:
            self.assertIn(kind, ytcommon.ERR)

    def test_clean_message(self):
        self.assertEqual(ytcommon.clean_msg(Exception('ERROR:  \x1b[0;31mboom\x1b[0m   here')), 'boom here')


class FormatTests(unittest.TestCase):
    OPTS = {'mode': 'audio', 'audio_format': 'mp3', 'mp3_bitrate': '192', 'video_height': '1080', 'embed': True}

    def test_mp3(self):
        fmt, _sort, _fb, pps, extra = ytcommon.build_format(dict(self.OPTS))
        self.assertEqual(fmt, 'bestaudio/best')
        self.assertEqual(pps[0]['preferredcodec'], 'mp3')
        self.assertEqual(extra['postprocessor_args'], {'extractaudio': ['-compression_level', '7']})

    def test_video_height(self):
        opts = dict(self.OPTS, mode='video', video_height='720')
        _fmt, sort, _fb, _pps, extra = ytcommon.build_format(opts)
        self.assertEqual(sort[0], 'res:720')
        self.assertEqual(extra['merge_output_format'], 'mp4')

    def test_no_embed(self):
        _fmt, _sort, _fb, pps, extra = ytcommon.build_format(dict(self.OPTS, embed=False, audio_format='m4a'))
        self.assertEqual([p['key'] for p in pps], ['FFmpegExtractAudio'])
        self.assertNotIn('writethumbnail', extra)


class SettingsTests(unittest.TestCase):
    def test_invalid_values_fall_back(self):
        o = server.clean_opts({'mode': 'nope', 'audio_format': 'wav', 'mp3_bitrate': '999', 'video_height': '17',
                               'cookies_browser': 'ie6', 'lang': 'xx'}, server.DEFAULT_SETTINGS)
        self.assertEqual(o['mode'], 'audio')
        self.assertEqual(o['mp3_bitrate'], '192')
        self.assertEqual(o['video_height'], '1080')
        self.assertEqual(o['cookies_browser'], '')
        self.assertEqual(o['lang'], '')

    def test_valid_values_kept(self):
        o = server.clean_opts({'mode': 'video', 'audio_format': 'opus', 'mp3_bitrate': '320', 'lang': 'ja'}, server.DEFAULT_SETTINGS)
        self.assertEqual((o['mode'], o['audio_format'], o['mp3_bitrate'], o['lang']), ('video', 'opus', '320', 'ja'))

    def test_file_names(self):
        self.assertEqual(server.safe_name('a/b:c*?'), server.safe_name('a/b:c*?'))
        self.assertNotIn('/', server.safe_name('a/b'))
        self.assertEqual(server.safe_name(''), 'untitled')
        self.assertLessEqual(len(server.safe_name('x' * 500)), 150)

    def test_numbering(self):
        job = server.Job('t1', 'u', dict(server.DEFAULT_SETTINGS))
        job.pad = 3
        item = server.Item(7, 'abc', 'u')
        self.assertEqual(server.build_filename(job, item, 'Song', '.mp3'), '007 - Song.mp3')


class SubscriptionTests(unittest.TestCase):
    def setUp(self):
        server.SUBS.clear()

    def test_create_and_update(self):
        sid = server.add_sub('https://www.youtube.com/playlist?list=PLabcdefghijk', dict(server.DEFAULT_SETTINGS, force=True), 6)
        sub = server.SUBS[sid]
        self.assertFalse(sub['opts']['force'], 'a check must never download everything again')
        self.assertEqual(sub['hours'], 6)
        self.assertEqual(server.add_sub(sub['url'], dict(server.DEFAULT_SETTINGS), 24), sid, 'same link, same subscription')
        self.assertEqual(server.SUBS[sid]['hours'], 24)
        self.assertEqual(len(server.SUBS), 1)

    def test_persistence(self):
        sid = server.add_sub('https://www.youtube.com/@jawed/videos', dict(server.DEFAULT_SETTINGS), 12)
        server.SUBS.clear()
        server.load_subs()
        self.assertIn(sid, server.SUBS)
        self.assertEqual(server.SUBS[sid]['hours'], 12)

    def test_state_summary(self):
        server.add_sub('https://www.youtube.com/@jawed/videos', dict(server.DEFAULT_SETTINGS), 1)
        s = server.subs_state()[0]
        self.assertTrue(s['enabled'])
        self.assertIn(1, server.SUB_INTERVALS)
        self.assertEqual(s['hours'], 1)


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
        self.assertEqual(sorted(c for c in server.LANG_CODES if c), self.languages())

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
        dynamic = ('ek.', 'eh.', 'tab.', 'every.', 'theme.', 'stage.')
        unused = [k for k in en if k not in js and k not in html and not k.startswith(dynamic) and k != 'lang.name']
        self.assertEqual(unused, [])


class VersionTests(unittest.TestCase):
    def test_versions_agree(self):
        version = server.APP_VERSION
        with open(os.path.join(ROOT, 'build-windows', 'version.txt'), encoding='utf-8') as f:
            text = f.read()
        self.assertIn("'%s'" % version, text)
        self.assertIn('(%s, 0)' % version.replace('.', ', '), text)
        with open(os.path.join(ROOT, 'build-linux', 'flatpak', 'io.github.progliodario.YTGrabber.metainfo.xml'), encoding='utf-8') as f:
            self.assertIn('version="%s"' % version, f.read())


if __name__ == '__main__':
    unittest.main()
