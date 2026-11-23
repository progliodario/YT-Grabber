"""Jobs: retrying, the names of the files, choosing the videos, and the notice when a download has finished."""
import os
import shutil
import tempfile
import unittest

from support import server  # noqa: E402


class DownloadRetryTests(unittest.TestCase):
    """setup_tools.download: a connection that drops half way is retried, a permanent failure is reported."""

    def setUp(self):
        import setup_tools
        self.tool = setup_tools
        self.calls = 0
        self.old = (setup_tools.urllib.request.urlretrieve, setup_tools.time.sleep, setup_tools.say)
        setup_tools.time.sleep = lambda s: None
        setup_tools.say = lambda msg: None
        self.addCleanup(self.restore)

    def restore(self):
        self.tool.urllib.request.urlretrieve, self.tool.time.sleep, self.tool.say = self.old

    def test_retries_after_an_interruption(self):
        def flaky(url, dest, progress=None):
            self.calls += 1
            if self.calls < 3:
                raise OSError('retrieval incomplete: got only 5 out of 20 bytes')
            return dest, None
        self.tool.urllib.request.urlretrieve = flaky
        self.assertEqual(self.tool.download('http://x/y', 'z')[0], 'z')
        self.assertEqual(self.calls, 3)

    def test_gives_up_after_the_last_try(self):
        def broken(url, dest, progress=None):
            self.calls += 1
            raise OSError('no route')
        self.tool.urllib.request.urlretrieve = broken
        with self.assertRaises(OSError):
            self.tool.download('http://x/y', 'z', tries=2)
        self.assertEqual(self.calls, 2)


class SameTitleTests(unittest.TestCase):
    """Two different videos with the same title (in a folder without numbers) must both be kept."""

    def finish(self, job, idx, vid, content):
        it = server.Item(idx, vid, 'https://www.youtube.com/watch?v=' + vid, 'Intro')
        job.add_item(it)
        tmp = os.path.join(job.dir, '.tmp', str(idx))
        os.makedirs(tmp)
        fp = os.path.join(tmp, vid + '.m4a')
        with open(fp, 'wb') as f:
            f.write(content)
        server.finalize_item(job, it, {'fp': fp, 'info': {'id': vid, 'title': 'Intro'}}, tmp, server.MANIFESTS.get(job.dir), it.key())
        return it

    def make_job(self):
        job = server.Job('same', '2 videos', dict(server.DEFAULT_SETTINGS), ['u1', 'u2'])
        job.kind, job.pad, job.status = 'single', 0, 'running'
        job.dir = tempfile.mkdtemp(prefix='ytg_same_')
        self.addCleanup(shutil.rmtree, job.dir, True)
        return job

    def read(self, job, name):
        with open(os.path.join(job.dir, name), 'rb') as f:
            return f.read()

    def test_the_second_video_does_not_overwrite_the_first(self):
        job = self.make_job()
        a = self.finish(job, 1, 'AAAAAAAAAAA', b'first video')
        b = self.finish(job, 2, 'BBBBBBBBBBB', b'second video')
        self.assertNotEqual(a.file, b.file)
        self.assertEqual(self.read(job, a.file), b'first video')
        self.assertEqual(self.read(job, b.file), b'second video')

    def test_a_video_downloaded_again_replaces_its_own_file(self):
        job = self.make_job()
        a = self.finish(job, 1, 'AAAAAAAAAAA', b'old')
        name = a.file
        tmp = os.path.join(job.dir, '.tmp', '1')
        os.makedirs(tmp)
        fp = os.path.join(tmp, 'AAAAAAAAAAA.m4a')
        with open(fp, 'wb') as f:
            f.write(b'new')
        server.finalize_item(job, a, {'fp': fp, 'info': {'id': 'AAAAAAAAAAA', 'title': 'Intro'}}, tmp, server.MANIFESTS.get(job.dir), a.key())
        self.assertEqual(a.file, name)
        self.assertEqual(self.read(job, name), b'new')
        self.assertEqual([f for f in os.listdir(job.dir) if not f.startswith('.')], [name])


class ChooseVideosTests(unittest.TestCase):
    """Deselecting videos of a playlist: the queued ones can be left out and added back; a job that waits for the choice starts on Start."""

    def make_job(self, n=5):
        job = server.Job('t' + str(id(self)), 'https://www.youtube.com/playlist?list=PLx', dict(server.DEFAULT_SETTINGS))
        job.status, job.enum_done, job.pad, job.pp_done = 'running', True, 2, True   # pp_done: no reports are written
        for i in range(1, n + 1):
            job.add_item(server.Item(i, 'vid%d' % i, 'https://www.youtube.com/watch?v=vid%d' % i, 'Song %d' % i))
        return job

    def test_skip_leaves_out_only_queued_items(self):
        job = self.make_job()
        with server.LOCK:
            job.set_state(job.items[0], 'a')   # already downloading: cannot be left out any more
        server.job_action(job, 'skip', [1, 2, 3])
        self.assertEqual([i.state for i in job.items], ['a', 'k', 'k', 'q', 'q'])
        self.assertEqual(job.counts['k'], 2)
        self.assertEqual(job.counts['q'], 2)
        self.assertEqual(job.items[1].emsg, server.SKIP_BY_USER)
        self.assertEqual(job.summary()['skipped_by_user'], 2)

    def test_skip_without_ids_leaves_out_every_queued_item(self):
        job = self.make_job()
        server.job_action(job, 'skip', None)
        self.assertEqual(job.counts['k'], 5)
        self.assertEqual(job.counts['q'], 0)

    def test_skipped_items_are_never_handed_to_a_worker(self):
        job = self.make_job(3)
        server.job_action(job, 'skip', [1, 2])
        queued = [it for it in job.queue if it.state == 'q']
        self.assertEqual([it.idx for it in queued], [3])

    def test_unskip_puts_them_back_in_the_queue(self):
        job = self.make_job()
        server.job_action(job, 'skip', None)
        server.job_action(job, 'unskip', [2, 4])
        self.assertEqual([i.state for i in job.items], ['k', 'q', 'k', 'q', 'k'])
        self.assertEqual(job.items[1].emsg, '')
        self.assertEqual(sorted({it.idx for it in job.queue if it.state == 'q'}), [2, 4])   # (the scheduler ignores a repeated entry)

    def test_a_finished_job_runs_again_when_something_is_added_back(self):
        job = self.make_job(2)
        server.job_action(job, 'skip', None)
        server.job_action(job, 'resume')
        self.assertEqual(job.status, 'done')   # nothing was left to download
        server.job_action(job, 'unskip', [1])
        self.assertEqual(job.status, 'running')
        self.assertIsNone(job.finished)

    def test_a_job_that_waits_for_the_choice_starts_on_resume(self):
        job = self.make_job()
        job.paused = job.choosing = True
        self.assertTrue(job.summary()['choosing'])
        self.assertTrue(job.to_disk()['choosing'])
        server.job_action(job, 'skip', [1])
        server.job_action(job, 'resume')
        self.assertFalse(job.paused)
        self.assertFalse(job.choosing)
        self.assertEqual(job.status, 'running')

    def test_cancel_ends_the_waiting(self):
        job = self.make_job()
        job.paused = job.choosing = True
        server.job_action(job, 'cancel')
        self.assertFalse(job.choosing)


class FinishNoticeTests(unittest.TestCase):
    def setUp(self):
        self.seen = []
        server.FINISH_HOOKS.append(self.seen.append)
        self.addCleanup(server.FINISH_HOOKS.remove, self.seen.append)
        self.old = server.SETTINGS.get('notify_done')
        self.addCleanup(server.SETTINGS.__setitem__, 'notify_done', self.old)

    def job(self, done, errors):
        job = server.Job('n1', 'https://www.youtube.com/playlist?list=PLabcdefghijk', dict(server.DEFAULT_SETTINGS))
        job.title = 'My list'
        job.counts['d'], job.counts['e'] = done, errors
        return job

    def test_hook_gets_the_numbers(self):
        server.SETTINGS['notify_done'] = True
        server.notify_finished(self.job(5, 1))
        self.assertEqual(self.seen[0]['title'], 'My list')
        self.assertEqual((self.seen[0]['done'], self.seen[0]['errors']), (5, 1))

    def test_nothing_new_is_silent(self):
        server.SETTINGS['notify_done'] = True
        server.notify_finished(self.job(0, 0))
        self.assertEqual(self.seen, [])

    def test_can_be_switched_off(self):
        server.SETTINGS['notify_done'] = False
        server.notify_finished(self.job(5, 0))
        self.assertEqual(self.seen, [])
