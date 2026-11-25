"""Settings: the defaults and the validation of what the page sends; and how private files are written."""
import os
import stat
import tempfile
import time
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

    def test_the_speed_limit(self):
        g = server.clean_global
        base = dict(server.DEFAULT_SETTINGS)
        self.assertEqual(g({'speed_limit': 500}, base)['speed_limit'], 500)
        self.assertEqual(g({'speed_limit': '250'}, base)['speed_limit'], 250)
        self.assertEqual(g({'speed_limit': -5}, base)['speed_limit'], 0)
        self.assertEqual(g({'speed_limit': 10 ** 12}, base)['speed_limit'], 1000000)
        self.assertEqual(g({'speed_limit': 'fast'}, dict(base, speed_limit=300))['speed_limit'], 300)   # nonsense keeps the old value
        self.assertEqual(g({}, dict(base, speed_limit=300))['speed_limit'], 300)

    def test_the_proxy(self):
        g = server.clean_global
        base = dict(server.DEFAULT_SETTINGS)
        for ok in ('http://proxy.local:8080', 'https://10.0.0.1:3128', 'socks5://127.0.0.1:1080', 'socks5h://user:pa55@host.example:9050',
                   'socks4a://[::1]:1080', ''):
            self.assertEqual(g({'proxy': ok}, base)['proxy'], ok, ok)
        for bad in ('proxy.local:8080', 'ftp://host:21', 'http://host', 'http://host:80 --evil', 'javascript:alert(1)', 'http://a b:80',
                    'http://host:80/path?x', 'x' * 400):
            self.assertEqual(g({'proxy': bad}, dict(base, proxy='http://old:1'))['proxy'], 'http://old:1', bad)
        self.assertEqual(g({'proxy': '  http://h:1  '}, base)['proxy'], 'http://h:1')
        self.assertEqual(g({'proxy': 5}, base)['proxy'], '')

    def test_the_allowed_hours(self):
        def at(h, m):
            return time.mktime((2026, 5, 20, h, m, 0, 0, 0, -1))
        off = {'hours_on': False, 'hours_from': '09:00', 'hours_to': '17:00'}
        day = {'hours_on': True, 'hours_from': '09:00', 'hours_to': '17:00'}
        night = {'hours_on': True, 'hours_from': '22:00', 'hours_to': '06:00'}
        self.assertTrue(server.in_allowed_hours(off, at(3, 0)))   # not switched on: always allowed
        self.assertTrue(server.in_allowed_hours(day, at(9, 0)))
        self.assertTrue(server.in_allowed_hours(day, at(16, 59)))
        self.assertFalse(server.in_allowed_hours(day, at(17, 0)))   # the end is not included
        self.assertFalse(server.in_allowed_hours(day, at(8, 59)))
        self.assertTrue(server.in_allowed_hours(night, at(23, 30)))   # it goes through midnight
        self.assertTrue(server.in_allowed_hours(night, at(2, 0)))
        self.assertFalse(server.in_allowed_hours(night, at(12, 0)))
        self.assertTrue(server.in_allowed_hours(dict(day, hours_to='09:00'), at(13, 0)))   # equal times: the whole day

    def test_the_times_of_the_day_are_checked(self):
        g = server.clean_global
        base = dict(server.DEFAULT_SETTINGS)
        r = g({'hours_on': True, 'hours_from': '7:5', 'hours_to': '25:00'}, base)
        self.assertEqual((r['hours_from'], r['hours_to']), (base['hours_from'], base['hours_to']))
        r = g({'hours_on': True, 'hours_from': '07:05', 'hours_to': '23:59'}, base)
        self.assertEqual((r['hours_on'], r['hours_from'], r['hours_to']), (True, '07:05', '23:59'))

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
