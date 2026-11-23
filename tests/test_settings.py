"""Settings: the defaults and the validation of what the page sends; and how private files are written."""
import os
import stat
import tempfile
import unittest

from support import server, ytcommon  # noqa: E402


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

    def test_private_files_are_for_the_owner_only(self):
        if os.name == 'nt':
            self.skipTest('Windows has no such mode bits')
        path = os.path.join(tempfile.mkdtemp(prefix='ytg_priv_'), 'cookies.txt')
        ytcommon.atomic_write(path, 'secret', private=True)
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
        ytcommon.atomic_write(path, 'secret again', private=True)   # a second write keeps the mode
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)

    def test_a_normal_write_still_works(self):
        path = os.path.join(tempfile.mkdtemp(prefix='ytg_plain_'), 'sub', 'a.json')
        ytcommon.atomic_write(path, '{}')
        with open(path, encoding='utf-8') as f:
            self.assertEqual(f.read(), '{}')

    def test_numbering(self):
        job = server.Job('t1', 'u', dict(server.DEFAULT_SETTINGS))
        job.pad = 3
        item = server.Item(7, 'abc', 'u')
        self.assertEqual(server.build_filename(job, item, 'Song', '.mp3'), '007 - Song.mp3')
