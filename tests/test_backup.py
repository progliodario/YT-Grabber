"""Saving the subscriptions and links to a file, and restoring them."""
import http.client
import json
import threading
import unittest

from support import server  # noqa: E402

PL1 = 'https://www.youtube.com/playlist?list=PLbackup00001'
PL2 = 'https://www.youtube.com/playlist?list=PLbackup00002'
CH = 'https://www.youtube.com/@backupchannel/videos'


class BackupTests(unittest.TestCase):
    def setUp(self):
        server.SUBS.clear()

    def test_the_export_holds_the_subscriptions_and_nothing_private(self):
        server.add_sub(PL1, dict(server.DEFAULT_SETTINGS, mode='video', video_height='720', cookies_browser='firefox'), 6, only_new=True)
        data = server.export_data()
        self.assertEqual((data['app'], data['format']), ('yt-grabber', 1))
        self.assertEqual(len(data['subscriptions']), 1)
        sub = data['subscriptions'][0]
        self.assertEqual((sub['url'], sub['hours'], sub['only_new'], sub['enabled']), (PL1, 6, True, True))
        self.assertEqual((sub['opts']['mode'], sub['opts']['video_height']), ('video', '720'))
        self.assertNotIn('cookies_browser', sub['opts'])   # the sign-in of the browser is not part of a backup
        self.assertNotIn('seen', sub)
        self.assertNotIn('cookie', json.dumps(data).lower())

    def test_a_round_trip(self):
        server.add_sub(PL1, dict(server.DEFAULT_SETTINGS, audio_format='opus'), 12)
        server.add_sub(CH, dict(server.DEFAULT_SETTINGS), 24, only_new=True)
        text = json.dumps(server.export_data())
        server.SUBS.clear()
        added, skipped, links = server.import_data(json.loads(text))
        self.assertEqual((added, skipped), (2, 0))
        subs = {s['url']: s for s in server.SUBS.values()}
        self.assertEqual(subs[PL1]['hours'], 12)
        self.assertEqual(subs[PL1]['opts']['audio_format'], 'opus')
        self.assertTrue(subs[CH]['only_new'])
        self.assertFalse(subs[PL1]['opts']['force'])
        due = sorted(s['next_check'] for s in subs.values())
        self.assertGreater(due[1] - due[0], 1)   # the checks do not all start at the same moment
        server.SUBS.clear()
        server.load_subs()   # and it was saved to disk
        self.assertEqual(len(server.SUBS), 2)

    def test_what_exists_is_kept_and_what_is_wrong_is_skipped(self):
        server.add_sub(PL1, dict(server.DEFAULT_SETTINGS), 3)
        data = {'app': 'yt-grabber', 'format': 1, 'links': [PL2, 'not a link', 5, 'x' * 600], 'subscriptions': [
            {'url': PL1, 'hours': 24},                       # already there: left as it is
            {'url': PL2, 'hours': 999},                      # an interval that does not exist: 24 hours
            {'url': 'https://example.com/watch?v=1'},        # not YouTube
            {'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'},   # a single video is not a subscription
            'nonsense', None]}
        added, skipped, links = server.import_data(data)
        self.assertEqual((added, skipped), (1, 5))
        self.assertEqual([s for s in server.SUBS.values() if s['url'] == PL1][0]['hours'], 3)
        self.assertEqual([s for s in server.SUBS.values() if s['url'] == PL2][0]['hours'], 24)
        self.assertEqual(links, [PL2])

    def test_a_file_that_is_not_a_backup_is_refused(self):
        for bad in (None, [], 'text', {}, {'app': 'other', 'format': 1}, {'app': 'yt-grabber', 'format': 99}):
            with self.assertRaises(ValueError):
                server.import_data(bad)
        self.assertEqual(len(server.SUBS), 0)

    def test_the_same_link_twice_in_a_file_makes_one_subscription(self):
        data = {'app': 'yt-grabber', 'format': 1, 'subscriptions': [{'url': PL1}, {'url': PL1}]}
        self.assertEqual(server.import_data(data)[:2], (1, 1))


class BackupHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = server.Server(('127.0.0.1', 0), server.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def call(self, method, path, body=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        headers = {'X-YTG': '1'} if method == 'POST' else {}
        if body is not None:
            body = json.dumps(body)
            headers['Content-Type'] = 'application/json'
        conn.request(method, path, body=body, headers=headers)
        r = conn.getresponse()
        data = r.read()
        out = (r.status, dict((k.lower(), v) for k, v in r.getheaders()), data)
        conn.close()
        return out

    def test_export_is_a_download_and_import_answers_with_the_links(self):
        server.SUBS.clear()
        status, headers, body = self.call('GET', '/api/export')
        self.assertEqual(status, 200)
        self.assertIn('attachment', headers['content-disposition'])
        backup = json.loads(body)
        backup.update(links=[PL1], subscriptions=[{'url': PL2, 'hours': 6}])
        status, _, body = self.call('POST', '/api/import', {'data': backup})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {'ok': True, 'added': 1, 'skipped': 0, 'links': [PL1]})
        self.assertEqual(self.call('POST', '/api/import', {'data': {'hello': 1}})[0], 400)
        server.SUBS.clear()


if __name__ == '__main__':
    unittest.main()
