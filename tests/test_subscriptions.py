"""Subscriptions, including the "only new videos" mode."""
import tempfile
import unittest

from support import server  # noqa: E402


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


class OnlyNewTests(unittest.TestCase):
    """Subscriptions in "only new videos" mode: what is already in the playlist is listed but never downloaded."""
    URL = 'https://www.youtube.com/playlist?list=PLabcdefghijk'

    def setUp(self):
        server.SUBS.clear()
        self.tmp = tempfile.mkdtemp(prefix='ytg_dl_')
        self.old_dir = server.SETTINGS['download_dir']
        server.SETTINGS['download_dir'] = self.tmp
        self.addCleanup(server.SETTINGS.__setitem__, 'download_dir', self.old_dir)
        self.old_flat = server.make_flat_ydl
        self.addCleanup(setattr, server, 'make_flat_ydl', self.old_flat)

    def playlist(self, ids):
        entries = [{'id': i, 'title': 'Video ' + i, 'url': 'https://www.youtube.com/watch?v=' + i} for i in ids]

        class FakeYdl:
            def extract_info(self, *a, **k):
                return {'_type': 'playlist', 'id': 'PLabcdefghijk', 'title': 'My list', 'entries': entries,
                        'playlist_count': len(entries)}

            def close(self):
                pass

        server.make_flat_ydl = lambda opts: FakeYdl()

    def run_check(self, sid, ids):
        self.playlist(ids)
        job = server.Job('t' + str(len(server.MANAGER_JOBS)), self.URL, dict(server.DEFAULT_SETTINGS))
        job.sub_id = sid
        server.enumerate_playlist(job)
        return job

    def test_first_look_downloads_nothing(self):
        sid = server.add_sub(self.URL, dict(server.DEFAULT_SETTINGS), 24, only_new=True)
        job = self.run_check(sid, ['aaaaaaaaaaa', 'bbbbbbbbbbb', 'ccccccccccc'])
        self.assertEqual((job.counts['k'], job.counts['q']), (3, 0))
        self.assertEqual(job.status, 'done')
        self.assertEqual(server.SUBS[sid]['seen'], ['aaaaaaaaaaa', 'bbbbbbbbbbb', 'ccccccccccc'])

    def test_only_the_new_video_is_queued(self):
        sid = server.add_sub(self.URL, dict(server.DEFAULT_SETTINGS), 24, only_new=True)
        self.run_check(sid, ['aaaaaaaaaaa', 'bbbbbbbbbbb'])
        job = self.run_check(sid, ['nnnnnnnnnnn', 'aaaaaaaaaaa', 'bbbbbbbbbbb'])   # newest first, like a channel
        states = {i.vid: i.state for i in job.items}
        self.assertEqual(states, {'nnnnnnnnnnn': 'q', 'aaaaaaaaaaa': 'k', 'bbbbbbbbbbb': 'k'})
        self.assertEqual([i.idx for i in job.items if i.state == 'q'], [1], 'numbering still follows the playlist order')
        # once it has been downloaded it counts as old for the next check
        with server.LOCK:
            job.set_state(job.items[0], 'd')
        server.sub_run_finished(job)
        self.assertIn('nnnnnnnnnnn', server.SUBS[sid]['seen'])
        again = self.run_check(sid, ['nnnnnnnnnnn', 'aaaaaaaaaaa', 'bbbbbbbbbbb'])
        self.assertEqual(again.counts['q'], 0)

    def test_normal_subscription_still_downloads_everything(self):
        sid = server.add_sub(self.URL, dict(server.DEFAULT_SETTINGS), 24)
        job = self.run_check(sid, ['aaaaaaaaaaa', 'bbbbbbbbbbb'])
        self.assertEqual((job.counts['q'], job.counts['k']), (2, 0))

    def test_changing_the_mode_looks_again(self):
        sid = server.add_sub(self.URL, dict(server.DEFAULT_SETTINGS), 24)
        self.assertFalse(server.SUBS[sid]['only_new'])
        server.add_sub(self.URL, dict(server.DEFAULT_SETTINGS), 24, only_new=True)
        self.assertTrue(server.SUBS[sid]['only_new'])
        self.assertIsNone(server.SUBS[sid]['seen'])

    def test_mode_survives_a_restart(self):
        sid = server.add_sub(self.URL, dict(server.DEFAULT_SETTINGS), 24, only_new=True)
        self.run_check(sid, ['aaaaaaaaaaa'])
        server.save_subs()
        server.SUBS.clear()
        server.load_subs()
        self.assertTrue(server.SUBS[sid]['only_new'])
        self.assertEqual(server.SUBS[sid]['seen'], ['aaaaaaaaaaa'])
        self.assertTrue(server.subs_state()[0]['only_new'])
