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
