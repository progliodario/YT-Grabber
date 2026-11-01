"""Links: what a pasted link is, and the names of the files."""
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

    def test_not_links(self):
        self.assertIsNone(server.classify_url(''))
        self.assertIsNone(server.classify_url('hello world'))
        self.assertEqual(server.classify_url('https://example.com/video')[0], 'auto')
