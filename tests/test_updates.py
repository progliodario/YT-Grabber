"""Updates: new versions of YT Grabber, the one-click install, and the automatic update of yt-dlp."""
import json
import os
import unittest

from support import server, updates  # noqa: E402


class UpdateCheckTests(unittest.TestCase):
    """The check for a new version, against a small local server that plays the part of GitHub."""

    def serve(self, payload, status=200):
        import http.server
        import threading

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        srv = http.server.HTTPServer(('127.0.0.1', 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        updates.UPDATE_API = 'http://127.0.0.1:%d/latest' % srv.server_address[1]

    def setUp(self):
        self.old_api = updates.UPDATE_API
        self.addCleanup(setattr, server, 'UPDATE_API', self.old_api)
        updates.UPDATE.update(checked=0, latest='', url='', error='')

    def test_version_order(self):
        self.assertGreater(updates.version_tuple('v1.10.0'), updates.version_tuple('1.9.3'))
        self.assertGreater(updates.version_tuple('1.2.0'), updates.version_tuple('1.1.9'))
        self.assertEqual(updates.version_tuple('1.2.0'), updates.version_tuple('v1.2.0'))

    def test_newer_version_is_reported(self):
        self.serve({'tag_name': 'v99.0.0', 'html_url': 'https://github.com/progliodario/YT-Grabber/releases/tag/v99.0.0'})
        self.assertTrue(updates.check_update())
        s = updates.update_state()
        self.assertTrue(s['newer'])
        self.assertEqual(s['latest'], '99.0.0')
        self.assertTrue(s['url'].startswith('https://github.com/progliodario/YT-Grabber/'))

    def test_same_version_is_not_news(self):
        self.serve({'tag_name': 'v' + server.APP_VERSION, 'html_url': 'https://github.com/progliodario/YT-Grabber/releases/tag/x'})
        self.assertTrue(updates.check_update())
        self.assertFalse(updates.update_state()['newer'])

    def test_foreign_link_is_replaced(self):
        self.serve({'tag_name': 'v99.0.0', 'html_url': 'https://evil.example/download'})
        updates.check_update()
        self.assertEqual(updates.update_state()['url'], updates.RELEASES_PAGE)

    def test_bad_answers_are_ignored(self):
        self.serve({'tag_name': 'nightly'})
        self.assertFalse(updates.check_update())
        self.assertFalse(updates.update_state()['newer'])
        self.assertTrue(updates.update_state()['error'])


class UpdateInstallTests(unittest.TestCase):
    """The one-click update of the Windows app: what is offered, what is downloaded, what is checked, what is started."""
    PAYLOAD = b'MZ this stands for the setup program'

    def setUp(self):
        import hashlib
        import http.server
        import threading
        payload = self.PAYLOAD
        self.digest = hashlib.sha256(payload).hexdigest()
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith('/latest'):
                    base = 'http://127.0.0.1:%d' % self.server.server_address[1]
                    body = json.dumps({
                        'tag_name': 'v99.0.0', 'html_url': 'https://github.com/progliodario/YT-Grabber/releases/tag/v99.0.0',
                        'assets': [{'name': 'YT-Grabber-Setup-99.0.0.exe', 'digest': 'sha256:' + outer.served_digest, 'size': len(payload),
                                    'browser_download_url': outer.served_url or base + '/YT-Grabber-Setup-99.0.0.exe'}]}).encode()
                else:
                    body = payload
                self.send_response(200)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.served_digest, self.served_url = self.digest, None
        srv = http.server.HTTPServer(('127.0.0.1', 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        self.saved = (updates.UPDATE_API, updates.install_supported, updates.launch_installer, updates.hooks.shutdown, os.environ.get('YTG_UPDATE_URL'))
        self.addCleanup(self.restore)
        updates.UPDATE_API = 'http://127.0.0.1:%d/latest' % srv.server_address[1]
        os.environ['YTG_UPDATE_URL'] = updates.UPDATE_API   # lets the program accept a download from the local server
        updates.install_supported = lambda: True
        self.launched, self.closed = [], []

        def fake_launch(path):
            with open(path, 'rb') as f:
                self.launched.append((path, f.read()))
        updates.launch_installer = fake_launch
        updates.hooks.shutdown = lambda *a, **k: self.closed.append(True)
        updates.UPDATE.update(checked=0, latest='', url='', error='', setup_url='', setup_sha='', setup_size=0)
        updates.UPDATE_INSTALL.update(state='idle', pct=0, error='')

    def restore(self):
        updates.UPDATE_API, updates.install_supported, updates.launch_installer, updates.hooks.shutdown, old = self.saved
        if old is None:
            os.environ.pop('YTG_UPDATE_URL', None)
        else:
            os.environ['YTG_UPDATE_URL'] = old

    def test_it_is_offered_when_a_newer_setup_exists(self):
        self.assertTrue(updates.check_update())
        s = updates.update_state()
        self.assertTrue(s['newer'] and s['can_install'])

    def test_it_is_not_offered_outside_the_windows_app(self):
        updates.install_supported = self.saved[1]   # the real check: not frozen here
        updates.check_update()
        self.assertFalse(updates.update_state()['can_install'])

    def test_download_check_start_close(self):
        updates.check_update()
        updates.run_update_install()
        self.assertEqual(updates.UPDATE_INSTALL['state'], 'installing')
        self.assertEqual(self.launched[0][1], self.PAYLOAD)
        self.assertEqual(self.closed, [True])

    def test_a_file_that_does_not_match_its_checksum_is_never_run(self):
        self.served_digest = '0' * 64
        updates.check_update()
        updates.run_update_install()
        self.assertEqual(updates.UPDATE_INSTALL['state'], 'error')
        self.assertIn('checksum', updates.UPDATE_INSTALL['error'])
        self.assertEqual((self.launched, self.closed), ([], []))

    def test_a_download_from_another_place_is_ignored(self):
        self.served_url = 'https://evil.example/YT-Grabber-Setup-99.0.0.exe'
        updates.check_update()
        self.assertFalse(updates.update_state()['can_install'])


class YtdlpAutoUpdateTests(unittest.TestCase):
    """The automatic yt-dlp update: when it acts, and that it can never restart in a loop."""

    def test_up_to_date_or_newer_does_nothing(self):
        d = updates.ytdlp_decision
        self.assertEqual(d('2026.10.31', '2026.10.31', {}, 0), 'none')
        self.assertEqual(d('2026.10.31', '2026.10.01', {}, 0), 'none')
        self.assertEqual(d('2026.10.31.123456', '2026.10.31', {}, 0), 'none')   # a nightly of the same day is not older
        self.assertEqual(d('2026.10.31', '', {}, 0), 'none')

    def test_newer_version_is_installed(self):
        self.assertEqual(updates.ytdlp_decision('2026.10.31', '2026.11.02', {}, 1000), 'update')
        self.assertEqual(updates.ytdlp_decision('2026.10.31', '2026.10.31.1', {}, 1000), 'update')

    def test_same_target_is_not_repeated_within_a_day(self):
        tried = {'target': '2026.11.02', 'time': 1000}
        self.assertEqual(updates.ytdlp_decision('2026.10.31', '2026.11.02', tried, 1000 + 3600), 'wait')
        self.assertEqual(updates.ytdlp_decision('2026.10.31', '2026.11.02', tried, 1000 + 25 * 3600), 'update')
        self.assertEqual(updates.ytdlp_decision('2026.10.31', '2026.11.03', tried, 1000 + 3600), 'update')

    def test_the_setting_is_on_by_default_and_can_be_switched_off(self):
        self.assertTrue(server.DEFAULT_SETTINGS['auto_ytdlp'])
        self.assertFalse(server.clean_opts({'auto_ytdlp': False}, server.DEFAULT_SETTINGS)['auto_ytdlp'])
        self.assertTrue(server.clean_opts({}, server.DEFAULT_SETTINGS)['auto_ytdlp'])
