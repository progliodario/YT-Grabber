"""Links: what a pasted link is, and the names of the files."""
import os
import tempfile
import unittest

from support import server  # noqa: E402


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

    def test_names_that_windows_cannot_create_are_changed(self):
        for name in ('CON', 'nul', 'Aux', 'PRN', 'COM1', 'lpt9', 'con.test', 'NUL.tar'):
            fixed = server.safe_name(name)
            self.assertTrue(fixed.startswith('_'), name)
            self.assertNotIn(fixed.split('.')[0].upper(), ('CON', 'NUL', 'AUX', 'PRN', 'COM1', 'LPT9'))
        for name in ('Console', 'Connect', 'AUX - Title', 'Intro'):   # only the whole name is reserved
            self.assertEqual(server.safe_name(name), name)

    def test_a_reserved_name_can_really_be_created(self):
        if os.name != 'nt':
            self.skipTest('a Windows rule')
        d = tempfile.mkdtemp(prefix='ytg_names_')
        path = os.path.join(d, server.safe_name('CON') + '.m4a')
        with open(path, 'wb') as f:
            f.write(b'x')
        self.assertTrue(os.path.exists(path))

    def test_not_links(self):
        self.assertIsNone(server.classify_url(''))
        self.assertIsNone(server.classify_url('hello world'))
        self.assertEqual(server.classify_url('https://example.com/video')[0], 'auto')
