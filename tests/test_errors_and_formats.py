"""Error messages and their causes, and the choice of the format."""
import unittest

from support import ytcommon  # noqa: E402


class ErrorTests(unittest.TestCase):
    CASES = {
        'Private video. Sign in if you have been granted access': 'private',
        'This video has been removed by the uploader': 'deleted',
        'The uploader has not made this video available in your country': 'geo',
        'Sign in to confirm your age': 'age',
        'Join this channel to get access to members-only content': 'members',
        'HTTP Error 429: Too Many Requests': 'ratelimit',
        "Sign in to confirm you're not a bot": 'bot',
        'Requested format is not available': 'format',
        'ERROR: unable to download video data: timed out': 'network',
        'Video unavailable': 'unavailable',
        'something nobody has ever seen': 'other',
    }

    def test_classification(self):
        for message, kind in self.CASES.items():
            self.assertEqual(ytcommon.classify_text(message), kind, message)

    def test_disk_errno(self):
        self.assertEqual(ytcommon.classify_text('x', errno=28), 'disk')

    def test_the_type_of_the_exception_comes_first(self):
        """yt-dlp rewords its messages from time to time; the type of the exception does not change."""
        import yt_dlp.utils as U
        kind = ytcommon.classify_exception
        self.assertEqual(kind(U.GeoRestrictedError('whatever the words are')), 'geo')
        self.assertEqual(kind(U.PostProcessingError('whatever')), 'postproc')
        self.assertEqual(kind(ConnectionResetError('whatever')), 'network')
        self.assertEqual(kind(TimeoutError()), 'network')
        wrapped = U.DownloadError('ERROR: the words say nothing', exc_info=(U.GeoRestrictedError, U.GeoRestrictedError('x'), None))
        self.assertEqual(kind(wrapped), 'geo')   # yt-dlp wraps the real exception

    def test_an_http_error_is_told_by_its_status(self):
        class HTTPError(Exception):   # the same name and shape as the one of yt-dlp
            def __init__(self, status):
                super().__init__('HTTP Error %d' % status)
                self.status = status
        kind = ytcommon.classify_exception
        self.assertEqual(kind(HTTPError(429)), 'ratelimit')
        self.assertEqual(kind(HTTPError(503)), 'network')
        self.assertIsNone(kind(HTTPError(403)))   # says nothing: the words of the message decide

    def test_a_type_that_says_nothing_falls_back_to_the_words(self):
        self.assertIsNone(ytcommon.classify_exception(ValueError('Private video')))
        self.assertIsNone(ytcommon.classify_exception(OSError(28, 'No space left on device')))   # the disk case goes by errno
        self.assertEqual(ytcommon.classify_text('Private video', None), 'private')

    def test_every_type_maps_to_a_real_kind(self):
        for kind in ytcommon.TYPE_KINDS.values():
            self.assertIn(kind, ytcommon.ERR)

    def test_every_kind_has_a_label(self):
        for kind in set(self.CASES.values()) | {'disk', 'postproc', 'copyright', 'live', 'premium'}:
            self.assertIn(kind, ytcommon.ERR)

    def test_clean_message(self):
        self.assertEqual(ytcommon.clean_msg(Exception('ERROR:  \x1b[0;31mboom\x1b[0m   here')), 'boom here')


class FormatTests(unittest.TestCase):
    OPTS = {'mode': 'audio', 'audio_format': 'mp3', 'mp3_bitrate': '192', 'video_height': '1080', 'embed': True}

    def test_mp3(self):
        fmt, _sort, _fb, pps, extra = ytcommon.build_format(dict(self.OPTS))
        self.assertEqual(fmt, 'bestaudio/best')
        self.assertEqual(pps[0]['preferredcodec'], 'mp3')
        self.assertEqual(extra['postprocessor_args'], {'extractaudio': ['-compression_level', '7']})

    def test_video_height(self):
        opts = dict(self.OPTS, mode='video', video_height='720')
        _fmt, sort, _fb, _pps, extra = ytcommon.build_format(opts)
        self.assertEqual(sort[0], 'res:720')
        self.assertEqual(extra['merge_output_format'], 'mp4')

    def test_no_embed(self):
        _fmt, _sort, _fb, pps, extra = ytcommon.build_format(dict(self.OPTS, embed=False, audio_format='m4a'))
        self.assertEqual([p['key'] for p in pps], ['FFmpegExtractAudio'])
        self.assertNotIn('writethumbnail', extra)
