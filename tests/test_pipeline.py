"""The whole download pipeline without the network: the real scheduler, supervisors, files and HTTP API, with a fake worker
(tests/fake_worker.py) and fake lists of videos. What would need YouTube is replaced; everything else is the program itself."""
import http.client
import json
import os
import shutil
import tempfile
import threading
import time
import unittest

from support import server  # noqa: E402

FAKE_LISTS = {}
SAVED = {}


class FakeYdl:
    """What yt-dlp returns for a playlist: the information, without reading anything from the Internet."""

    def extract_info(self, url, download=False, process=False):
        return FAKE_LISTS[url]

    def close(self):
        pass


def playlist(list_id, vids):
    url = 'https://www.youtube.com/playlist?list=' + list_id
    FAKE_LISTS[url] = {'_type': 'playlist', 'id': list_id, 'title': 'List ' + list_id, 'playlist_count': len(vids),
                       'entries': [{'id': v, 'title': 'Title ' + v} for v in vids]}
    return url


def setUpModule():
    SAVED.update(env=os.environ.get('YTG_WORKER'), ydl=server.make_flat_ydl, scale=server.RETRY_SCALE, dir=server.SETTINGS['download_dir'])
    os.environ['YTG_WORKER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fake_worker.py')
    server.RETRY_SCALE = 0.05
    server.make_flat_ydl = lambda opts: FakeYdl()
    server.SETTINGS['download_dir'] = tempfile.mkdtemp(prefix='ytg_pipe_')
    server.MGR.start()


def tearDownModule():
    for p in list(server.PROCS):
        p.kill()
    server.make_flat_ydl = SAVED['ydl']
    server.RETRY_SCALE = SAVED['scale']
    server.SETTINGS['download_dir'] = SAVED['dir']
    if SAVED['env'] is None:
        os.environ.pop('YTG_WORKER', None)
    else:
        os.environ['YTG_WORKER'] = SAVED['env']
    shutil.rmtree(tempfile.gettempdir() + os.sep + 'ytg_pipe_unused', ignore_errors=True)


def wait(cond, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


def start(urls, choose=False):
    created, rejected, dups = server.create_jobs(urls, dict(server.DEFAULT_SETTINGS), choose=choose)
    assert created, (rejected, dups)
    return server.MANAGER_JOBS[created[0]]


def finished(job, timeout=60):
    ok = wait(lambda: job.status in ('done', 'cancelled', 'error'), timeout)
    if job.status == 'done':
        wait(lambda: not job.pp_done, 10)   # pp_done is true while the thread that writes the reports (playlist file, errors) runs
    wait(lambda: server.SLOTS['used'] == 0, 10)
    return ok


def files(job):
    return sorted(f for f in os.listdir(job.dir) if not f.startswith('.'))


def read(job, name):
    with open(os.path.join(job.dir, name), encoding='utf-8') as f:
        return f.read()


class PipelineTests(unittest.TestCase):
    def test_a_playlist_is_downloaded_and_numbered(self):
        job = start(playlist('PLpipe00000001', ['OKA00000001', 'OKB00000001', 'OKC00000001', 'OKD00000001']))
        self.assertTrue(finished(job))
        self.assertEqual(job.status, 'done')
        self.assertEqual([i.state for i in job.items], ['d'] * 4)
        names = files(job)
        self.assertEqual(names[:4], ['01 - Title OKA00000001.m4a', '02 - Title OKB00000001.m4a', '03 - Title OKC00000001.m4a',
                                     '04 - Title OKD00000001.m4a'])
        self.assertIn('_playlist.m3u8', names)
        self.assertEqual(read(job, names[1]), 'content of OKB00000001')
        self.assertIn('02 - Title OKB00000001.m4a', read(job, '_playlist.m3u8'))
        self.assertFalse(os.path.exists(os.path.join(job.dir, '.tmp', '1')))   # the working folders are gone

    def test_a_private_video_is_reported_and_the_others_still_download(self):
        job = start(playlist('PLpipe00000002', ['OKA00000002', 'ERRPRIV0002', 'OKB00000002']))
        self.assertTrue(finished(job))
        self.assertEqual([i.state for i in job.items], ['d', 'e', 'd'])
        bad = job.items[1]
        self.assertEqual((bad.ekind, bad.attempts), ('private', 1))   # not retried: it would fail again
        self.assertTrue(wait(lambda: os.path.exists(os.path.join(job.dir, '_ERRORS.txt')), 5))
        self.assertIn('ERRPRIV0002', read(job, '_ERRORS.txt'))
        self.assertEqual(job.summary()['counts']['e'], 1)

    def test_a_network_error_is_retried(self):
        job = start(playlist('PLpipe00000003', ['FLAKY000003', 'ERRNET00003']))
        self.assertTrue(finished(job))
        flaky, hopeless = job.items
        self.assertEqual((flaky.state, flaky.attempts), ('d', 2))
        self.assertEqual((hopeless.state, hopeless.ekind), ('e', 'network'))
        self.assertGreater(hopeless.attempts, 2)   # it was tried again and again before giving up

    def test_failed_items_can_be_retried_by_the_user(self):
        job = start(playlist('PLpipe00000004', ['ERRNET00004']))
        self.assertTrue(finished(job))
        self.assertEqual(job.items[0].state, 'e')
        first_attempts = job.items[0].attempts
        server.job_action(job, 'retry_failed', None)
        self.assertEqual((job.status, job.items[0].state, job.items[0].attempts), ('running', 'q', 0))   # a fresh start, at once
        self.assertTrue(finished(job))
        self.assertEqual((job.items[0].state, job.items[0].attempts), ('e', first_attempts))   # and it failed the same way again

    def test_two_videos_with_one_title_are_both_kept(self):
        job = start('SAME0000001\nSAME0000002')
        self.assertTrue(finished(job))
        self.assertEqual(job.kind, 'single')
        names = files(job)
        self.assertEqual(names, ['Same (2).m4a', 'Same.m4a'])
        self.assertEqual({read(job, n) for n in names}, {'content of SAME0000001', 'content of SAME0000002'})

    def test_exactly_ten_downloads_at_a_time(self):
        job = start(playlist('PLpipe00000005', ['SLOW%07d' % i for i in range(23)]))
        top = [0]
        stop = threading.Event()

        def sample():
            while not stop.is_set():
                top[0] = max(top[0], server.SLOTS['used'])
                self.assertLessEqual(server.SLOTS['used'], server.CONCURRENCY)
                time.sleep(0.01)
        t = threading.Thread(target=sample, daemon=True)
        t.start()
        self.assertTrue(finished(job, 120))
        stop.set()
        t.join()
        self.assertEqual(top[0], 10)
        self.assertEqual(job.summary()['counts']['d'], 23)

    def test_cancel_stops_everything(self):
        job = start(playlist('PLpipe00000006', ['SLOW%07d' % i for i in range(6)]))
        self.assertTrue(wait(lambda: any(i.state == 'a' for i in job.items), 30))
        server.job_action(job, 'cancel')
        self.assertTrue(finished(job))
        self.assertEqual(job.status, 'cancelled')
        self.assertFalse([i for i in job.items if i.state in ('a', 'p', 'q')])
        self.assertEqual(server.SLOTS['used'], 0)

    def test_choosing_the_videos_first(self):
        job = start(playlist('PLpipe00000007', ['OKA00000007', 'OKB00000007', 'OKC00000007', 'OKD00000007']), choose=True)
        self.assertTrue(wait(lambda: job.enum_done, 30))
        time.sleep(0.5)
        self.assertEqual((job.summary()['counts']['d'], job.choosing, job.paused), (0, True, True))   # nothing starts by itself
        server.job_action(job, 'skip', [2, 3])
        server.job_action(job, 'resume')
        self.assertTrue(finished(job))
        self.assertEqual([i.state for i in job.items], ['d', 'k', 'k', 'd'])
        self.assertEqual(files(job)[:2], ['01 - Title OKA00000007.m4a', '04 - Title OKD00000007.m4a'])

    def test_a_job_survives_a_restart_and_goes_on_where_it_stopped(self):
        job = start(playlist('PLpipe00000008', ['SLOW%07d' % i for i in range(24)]))
        self.assertTrue(wait(lambda: sum(1 for i in job.items if i.state == 'd') >= 2, 60))
        server.job_action(job, 'pause')
        wait(lambda: not any(i.state in ('a', 'p') for i in job.items), 30)   # what was on its way finishes (a pause does not stop it)
        wait(lambda: server.SLOTS['used'] == 0, 20)
        server.MGR.save_dirty()
        done_before = sum(1 for i in job.items if i.state == 'd')
        jid = job.id
        with server.LOCK:   # as if the program had been closed and opened again
            server.MANAGER_JOBS.clear()
            del server.JOB_ORDER[:]
        server.MGR.load_jobs()
        again = server.MANAGER_JOBS[jid]
        self.assertTrue(again.paused and again.interrupted)
        self.assertEqual(sum(1 for i in again.items if i.state == 'd'), done_before)
        server.job_action(again, 'resume')
        self.assertTrue(finished(again, 120))
        self.assertEqual(again.summary()['counts']['d'], 24)
        self.assertEqual(len([f for f in files(again) if f.endswith('.m4a')]), 24)


class ApiTests(unittest.TestCase):
    """The same thing through HTTP, the way the page does it."""

    @classmethod
    def setUpClass(cls):
        cls.srv = server.Server(('127.0.0.1', 0), server.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def call(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=15)
        h = {'X-YTG': '1'}
        h.update(headers or {})
        if body is not None:
            body = json.dumps(body)
            h['Content-Type'] = 'application/json'
        conn.request(method, path, body=body, headers=h)
        r = conn.getresponse()
        data = r.read()
        conn.close()
        return r.status, dict((k.lower(), v) for k, v in r.getheaders()), data

    def test_create_watch_download_and_remove(self):
        url = playlist('PLpipe00000009', ['OKA00000009', 'ERRPRIV0009', 'OKB00000009'])
        status, _, data = self.call('POST', '/api/jobs', {'urls': url, 'opts': {'mode': 'audio', 'audio_format': 'm4a'}})
        self.assertEqual(status, 200)
        jid = json.loads(data)['created'][0]
        self.assertTrue(wait(lambda: json.loads(self.call('GET', '/api/jobs/' + jid)[2])['status'] == 'done', 60))
        detail = json.loads(self.call('GET', '/api/jobs/' + jid + '?since=0')[2])
        self.assertEqual(detail['counts']['d'], 2)
        self.assertEqual(detail['counts']['e'], 1)
        self.assertEqual([i['s'] for i in detail['items']], ['d', 'e', 'd'])
        self.assertIn(jid, [j['id'] for j in json.loads(self.call('GET', '/api/state')[2])['jobs']])
        # only what changed comes back
        later = json.loads(self.call('GET', '/api/jobs/%s?since=%d' % (jid, detail['seq']))[2])
        self.assertEqual(later['items'], [])
        # the files can be fetched, also in pieces
        status, h, body = self.call('GET', '/api/jobs/%s/file/1' % jid)
        self.assertEqual((status, body), (200, b'content of OKA00000009'))
        self.assertEqual(h['content-security-policy'], 'sandbox')
        status, h, body = self.call('GET', '/api/jobs/%s/file/3' % jid, headers={'Range': 'bytes=0-6'})
        self.assertEqual((status, body, h['content-range']), (206, b'content', 'bytes 0-6/22'))
        self.assertEqual(self.call('GET', '/api/jobs/%s/file/2' % jid)[0], 404)   # the one that failed has no file
        self.assertIn(b'ERRPRIV0009', self.call('GET', '/api/jobs/%s/errors.txt' % jid)[2])
        self.assertIn(b'01 - Title OKA00000009.m4a', self.call('GET', '/api/jobs/%s/playlist.m3u8' % jid)[2])
        # leaving a video out, adding it back, and removing the job
        self.assertEqual(self.call('POST', '/api/jobs/%s/action' % jid, {'action': 'redownload', 'ids': [1]})[0], 200)
        self.assertTrue(wait(lambda: json.loads(self.call('GET', '/api/jobs/' + jid)[2])['status'] == 'done', 30))
        self.assertEqual(self.call('POST', '/api/jobs/%s/action' % jid, {'action': 'remove'})[0], 200)
        self.assertEqual(self.call('GET', '/api/jobs/' + jid)[0], 404)

    def test_a_link_in_progress_cannot_be_added_twice(self):
        url = playlist('PLpipe00000010', ['SLOW%07d' % i for i in range(3)])
        self.assertEqual(self.call('POST', '/api/jobs', {'urls': url})[0], 200)
        self.assertEqual(self.call('POST', '/api/jobs', {'urls': url})[0], 409)

    def test_a_text_without_links_is_refused(self):
        status, _, data = self.call('POST', '/api/jobs', {'urls': 'hello there'})
        self.assertEqual(status, 400)
        self.assertIn('error', json.loads(data))

    def test_an_unknown_job_and_an_unknown_action(self):
        self.assertEqual(self.call('POST', '/api/jobs/nothing/action', {'action': 'pause'})[0], 404)
        job = start(playlist('PLpipe00000011', ['OKA00000011']))
        self.assertEqual(self.call('POST', '/api/jobs/%s/action' % job.id, {'action': 'explode'})[0], 400)
        finished(job)


if __name__ == '__main__':
    unittest.main()
