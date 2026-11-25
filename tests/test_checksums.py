"""Checking the downloaded components (ffmpeg, deno, yt-dlp) against the SHA-256 their makers publish."""
import hashlib
import http.server
import os
import tempfile
import threading
import unittest

from support import ytcommon  # noqa: E402

DATA = b'the content of a downloaded file'
GOOD = hashlib.sha256(DATA).hexdigest()
OTHER = hashlib.sha256(b'something else').hexdigest()


class ParseTests(unittest.TestCase):

    def test_a_list_of_checksums(self):
        text = '%s  yt-dlp\n%s *yt-dlp.exe\n' % (OTHER, GOOD)
        self.assertEqual(ytcommon.find_checksum(text, 'yt-dlp'), OTHER)
        self.assertEqual(ytcommon.find_checksum(text, 'yt-dlp.exe'), GOOD)   # the "*" of the binary mode is ignored
        self.assertIsNone(ytcommon.find_checksum(text, 'yt-dlp_x86'))

    def test_a_file_with_only_the_hash(self):
        self.assertEqual(ytcommon.find_checksum(GOOD.upper() + '\n', 'anything.zip'), GOOD)

    def test_the_powershell_format_of_deno(self):
        text = 'Algorithm : SHA256\r\nHash      : %s\r\nPath      : C:\\agent\\target\\release\\deno-x86_64-pc-windows-msvc.zip\r\n' % GOOD.upper()
        self.assertEqual(ytcommon.find_checksum(text, 'deno-x86_64-pc-windows-msvc.zip'), GOOD)
        self.assertIsNone(ytcommon.find_checksum(text, 'deno-aarch64-pc-windows-msvc.zip'))   # the hash of another file is not used

    def test_nonsense_gives_nothing(self):
        for text in ('', 'not a hash  yt-dlp', '1234  yt-dlp', '<html>404</html>'):
            self.assertIsNone(ytcommon.find_checksum(text, 'yt-dlp'), text)


class FileTests(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp(prefix='ytg_sum_')
        with os.fdopen(fd, 'wb') as f:
            f.write(DATA)
        self.addCleanup(os.remove, self.path)

    def test_the_right_file_passes(self):
        self.assertEqual(ytcommon.sha256_file(self.path), GOOD)
        ytcommon.verify_checksum(self.path, GOOD.upper())

    def test_another_file_is_refused(self):
        with self.assertRaises(ValueError):
            ytcommon.verify_checksum(self.path, OTHER)


class DownloadTests(unittest.TestCase):
    """verify_from_url against a small server that plays the part of the makers' page."""

    @classmethod
    def setUpClass(cls):
        cls.body = ('%s  file.zip\n' % GOOD).encode()

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/sums':
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(cls.body)
                else:
                    self.send_error(404)

            def log_message(self, *a):
                pass
        cls.srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
        cls.base = 'http://127.0.0.1:%d' % cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        fd, self.path = tempfile.mkstemp(prefix='ytg_sum_')
        with os.fdopen(fd, 'wb') as f:
            f.write(DATA)
        self.addCleanup(os.remove, self.path)
        self.said = []
        self.saved = os.environ.pop('YTG_REQUIRE_CHECKSUMS', None)
        self.addCleanup(self.restore)

    def restore(self):
        os.environ.pop('YTG_REQUIRE_CHECKSUMS', None)
        if self.saved is not None:
            os.environ['YTG_REQUIRE_CHECKSUMS'] = self.saved

    def test_a_match_is_reported(self):
        self.assertTrue(ytcommon.verify_from_url(self.path, 'file.zip', self.base + '/sums', self.said.append))
        self.assertEqual(self.said, [])

    def test_a_mismatch_raises(self):
        with open(self.path, 'wb') as f:
            f.write(b'a file that was changed on the way')
        with self.assertRaises(ValueError):
            ytcommon.verify_from_url(self.path, 'file.zip', self.base + '/sums', self.said.append)

    def test_a_list_that_cannot_be_read_only_warns(self):
        self.assertFalse(ytcommon.verify_from_url(self.path, 'file.zip', self.base + '/missing', self.said.append))
        self.assertTrue(any('WARNING' in s for s in self.said))

    def test_a_file_missing_from_the_list_only_warns(self):
        self.assertFalse(ytcommon.verify_from_url(self.path, 'other.zip', self.base + '/sums', self.said.append))

    def test_the_strict_mode_refuses_an_unverifiable_file(self):
        os.environ['YTG_REQUIRE_CHECKSUMS'] = '1'
        with self.assertRaises(ValueError):
            ytcommon.verify_from_url(self.path, 'file.zip', self.base + '/missing', self.said.append)


class TermuxInstallerTests(unittest.TestCase):
    """The script served to the phone carries the checksum of the zip and checks it before unpacking."""

    def test_the_checksum_is_put_into_the_script(self):
        import importlib.util
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(os.path.dirname(here), 'packaging', 'termux', 'share_to_phone.py')
        spec = importlib.util.spec_from_file_location('share_to_phone', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        script = mod.install_script('http://192.168.1.5:8800', GOOD).decode('utf-8')
        self.assertIn('ZIP_SHA256="%s"' % GOOD, script)
        self.assertIn('BASE="http://192.168.1.5:8800"', script)
        self.assertIn('sha256sum -c', script)


if __name__ == '__main__':
    unittest.main()
