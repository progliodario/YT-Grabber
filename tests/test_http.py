"""The HTTP server: what it refuses, the headers it sends, and what only the computer running it may do."""
import http.client
import json
import threading
import unittest

from support import server  # noqa: E402


class HttpTests(unittest.TestCase):
    """A real server on a free port, with the real handler."""

    @classmethod
    def setUpClass(cls):
        cls.srv = server.Server(('127.0.0.1', 0), server.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.saved_dir = server.SETTINGS['download_dir']

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def call(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        h = dict(headers or {})
        if body is not None:
            body = json.dumps(body)
            h.setdefault('Content-Type', 'application/json')
        conn.request(method, path, body=body, headers=h)
        r = conn.getresponse()
        data = r.read()
        out = (r.status, dict((k.lower(), v) for k, v in r.getheaders()), data)
        conn.close()
        return out

    def post(self, path, body, **headers):
        h = {'X-YTG': '1'}
        h.update(headers)
        return self.call('POST', path, body, h)

    def test_the_page_comes_with_the_security_headers(self):
        status, h, _ = self.call('GET', '/')
        self.assertEqual(status, 200)
        csp = h['content-security-policy']
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("'unsafe-inline'", csp.split('style-src')[0])   # no inline script
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertEqual(h['x-frame-options'], 'DENY')
        self.assertEqual(h['x-content-type-options'], 'nosniff')
        self.assertEqual(h['referrer-policy'], 'no-referrer')

    def test_the_server_does_not_tell_its_version(self):
        _, h, _ = self.call('GET', '/api/ping')
        self.assertEqual(h['server'], 'YTGrabber')

    def test_the_page_has_no_inline_script(self):
        _, _, body = self.call('GET', '/')
        html = body.decode('utf-8')
        import re
        for tag in re.findall(r'<script\b[^>]*>', html):
            self.assertIn('src=', tag, 'an inline script would be blocked by the Content-Security-Policy')
        self.assertNotRegex(html, r'\son[a-z]+="')   # no inline event handlers either

    def test_another_host_name_is_refused(self):
        self.assertEqual(self.call('GET', '/api/state', headers={'Host': 'evil.example'})[0], 403)

    def test_a_post_needs_the_header_and_the_same_origin(self):
        self.assertEqual(self.call('POST', '/api/jobs', {}, {})[0], 403)
        self.assertEqual(self.post('/api/jobs', {}, Origin='http://evil.example')[0], 403)

    def test_a_bad_body_size_is_a_400_not_a_crash(self):
        self.assertEqual(self.post('/api/jobs', {}, **{'Content-Length': '-5'})[0], 400)
        self.assertEqual(self.post('/api/jobs', {}, **{'Content-Length': 'abc'})[0], 400)
        self.assertEqual(self.post('/api/jobs', {}, **{'Content-Length': str(9 * 1024 * 1024)})[0], 400)

    def test_the_browser_may_not_make_a_cross_site_request(self):
        self.assertEqual(self.call('OPTIONS', '/api/jobs', headers={'Origin': 'http://evil.example'})[0], 501)

    def test_files_outside_the_page_cannot_be_read(self):
        for path in ('/..%2f..%2fserver.py', '/%2e%2e/server.py', '/lang/../../server.py', '/..\\..\\server.py'):
            self.assertEqual(self.call('GET', path)[0], 404, path)


class TokenTests(unittest.TestCase):
    """With an access token set, nothing works without it (except the ping that tells which program is on the port)."""
    TOKEN = 'a-long-secret-text-for-the-tests'

    def setUp(self):
        self.srv = server.Server(('127.0.0.1', 0), server.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.addCleanup(setattr, server, 'TOKEN', server.TOKEN)
        server.TOKEN = self.TOKEN

    def call(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.srv.server_address[1], timeout=10)
        h = dict(headers or {})
        if body is not None:
            body = json.dumps(body)
            h['Content-Type'] = 'application/json'
        conn.request(method, path, body=body, headers=h)
        r = conn.getresponse()
        data = r.read()
        conn.close()
        return r.status, dict((k.lower(), v) for k, v in r.getheaders()), data

    def test_nothing_works_without_the_token(self):
        status, h, body = self.call('GET', '/', headers={'Accept': 'text/html'})
        self.assertEqual(status, 401)
        self.assertIn(b'access link', body.lower())
        self.assertEqual(self.call('GET', '/api/state')[0], 401)
        self.assertEqual(self.call('GET', '/app.js')[0], 401)
        self.assertEqual(self.call('POST', '/api/jobs', {'urls': 'x'}, {'X-YTG': '1'})[0], 401)
        self.assertEqual(self.call('GET', '/api/state', headers={'X-YTG-Token': 'wrong'})[0], 401)
        self.assertEqual(self.call('GET', '/api/state', headers={'Cookie': 'ytg_token=wrong'})[0], 401)

    def test_the_ping_stays_open(self):
        status, _, body = self.call('GET', '/api/ping')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['app'], 'yt-grabber')   # (only the name of the program, no data)

    def test_the_link_with_the_token_starts_a_session(self):
        status, h, _ = self.call('GET', '/?t=%s&u=https%%3A%%2F%%2Fyoutu.be%%2Fabc' % self.TOKEN)
        self.assertEqual(status, 302)
        self.assertEqual(h['location'], '/?u=https%3A%2F%2Fyoutu.be%2Fabc')   # the token is gone from the address, the rest stays
        cookie = h['set-cookie']
        self.assertIn('ytg_token=' + self.TOKEN, cookie)
        for flag in ('HttpOnly', 'SameSite=Strict', 'Path=/'):
            self.assertIn(flag, cookie)
        status, _, body = self.call('GET', '/', headers={'Cookie': 'ytg_token=' + self.TOKEN})
        self.assertEqual(status, 200)
        self.assertIn(b'<title>YT Grabber</title>', body)

    def test_a_wrong_token_in_the_link_gives_no_session(self):
        status, h, _ = self.call('GET', '/?t=wrong', headers={'Accept': 'text/html'})
        self.assertEqual(status, 401)
        self.assertNotIn('set-cookie', h)

    def test_the_cookie_or_the_header_opens_the_api(self):
        self.assertEqual(self.call('GET', '/api/state', headers={'Cookie': 'a=1; ytg_token=%s; b=2' % self.TOKEN})[0], 200)
        self.assertEqual(self.call('GET', '/api/state', headers={'X-YTG-Token': self.TOKEN})[0], 200)
        status, _, _ = self.call('POST', '/api/jobs', {'urls': 'hello'}, {'X-YTG': '1', 'X-YTG-Token': self.TOKEN})
        self.assertEqual(status, 400)   # let in (the text has no link), not refused with 401

    def test_without_a_token_set_nothing_changes(self):
        server.TOKEN = ''
        self.assertEqual(self.call('GET', '/api/state')[0], 200)


class TokenFileTests(unittest.TestCase):
    """The token kept in the data folder: made once, private, the same on the next run; the environment wins."""

    def setUp(self):
        import os
        from support import ytcommon
        self.yc = ytcommon
        self.saved_env = os.environ.pop('YTG_TOKEN', None)
        self.saved_file = ytcommon.TOKEN_FILE
        ytcommon.TOKEN_FILE = os.path.join(__import__('tempfile').mkdtemp(prefix='ytg_tok_'), 'token.txt')
        self.addCleanup(self.restore)

    def restore(self):
        import os
        self.yc.TOKEN_FILE = self.saved_file
        if self.saved_env is None:
            os.environ.pop('YTG_TOKEN', None)
        else:
            os.environ['YTG_TOKEN'] = self.saved_env

    def test_made_once_and_kept(self):
        import os
        import stat
        self.assertEqual(self.yc.current_token(), '')
        first = self.yc.load_or_create_token()
        self.assertGreaterEqual(len(first), 30)
        self.assertEqual(self.yc.load_or_create_token(), first)
        self.assertEqual(self.yc.current_token(), first)
        if os.name != 'nt':
            self.assertEqual(stat.S_IMODE(os.stat(self.yc.TOKEN_FILE).st_mode), 0o600)

    def test_the_environment_wins(self):
        import os
        self.yc.load_or_create_token()
        os.environ['YTG_TOKEN'] = 'from-the-app'
        self.assertEqual(self.yc.current_token(), 'from-the-app')


class RemoteClientTests(unittest.TestCase):
    """What another device on the network (--host 0.0.0.0) may not do: the folder and the cookies belong to the computer."""

    def setUp(self):
        self.srv = server.Server(('127.0.0.1', 0), server.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.saved = server.Handler.is_local_client
        server.Handler.is_local_client = lambda handler: False
        self.addCleanup(setattr, server.Handler, 'is_local_client', self.saved)

    def post(self, path, body):
        conn = http.client.HTTPConnection('127.0.0.1', self.srv.server_address[1], timeout=10)
        conn.request('POST', path, body=json.dumps(body), headers={'X-YTG': '1', 'Content-Type': 'application/json'})
        r = conn.getresponse()
        r.read()
        conn.close()
        return r.status

    def test_cookies_cannot_be_uploaded(self):
        self.assertEqual(self.post('/api/cookies', {'text': '# Netscape HTTP Cookie File\n'}), 403)

    def test_the_folder_cannot_be_changed(self):
        self.assertEqual(self.post('/api/settings', {'download_dir': 'C:/somewhere/else'}), 403)

    def test_the_same_folder_is_accepted(self):
        self.assertEqual(self.post('/api/settings', {'download_dir': server.SETTINGS['download_dir']}), 200)

    def test_the_actions_on_the_machine_are_refused(self):
        for path in ('/api/choose-dir', '/api/update', '/api/quit', '/api/appupdate/install'):
            self.assertEqual(self.post(path, {}), 403, path)


if __name__ == '__main__':
    unittest.main()
