"""The newer download options: FLAC, WAV and OGG, subtitles inside the video, and cutting out the sponsor segments."""
import unittest

from support import server, ytcommon  # noqa: E402
import yt_dlp  # noqa: E402


def opts(**kw):
    o = dict(server.DEFAULT_SETTINGS)
    o.update(kw)
    return server.clean_opts(o, server.DEFAULT_SETTINGS)


def keys(pps):
    return [p['key'] for p in pps]


class AudioFormatTests(unittest.TestCase):
    def test_the_formats_are_accepted(self):
        for af in ('mp3', 'm4a', 'opus', 'flac', 'wav', 'ogg'):
            self.assertEqual(opts(audio_format=af)['audio_format'], af)
        self.assertEqual(opts(audio_format='aiff')['audio_format'], server.DEFAULT_SETTINGS['audio_format'])

    def test_flac_wav_and_ogg_are_extracted_with_the_right_codec(self):
        for af, codec in (('flac', 'flac'), ('wav', 'wav'), ('ogg', 'vorbis')):
            fmt, _, fallback, pps, _ = ytcommon.build_format(opts(mode='audio', audio_format=af))
            self.assertEqual(fmt, 'bestaudio/best')
            self.assertEqual([p['preferredcodec'] for p in pps if p['key'] == 'FFmpegExtractAudio'], [codec], af)

    def test_a_wav_file_gets_no_cover_picture(self):
        _, _, _, pps, extra = ytcommon.build_format(opts(mode='audio', audio_format='wav', embed=True))
        self.assertNotIn('EmbedThumbnail', keys(pps))
        self.assertNotIn('writethumbnail', extra)
        _, _, _, pps, extra = ytcommon.build_format(opts(mode='audio', audio_format='flac', embed=True))
        self.assertIn('EmbedThumbnail', keys(pps))
        self.assertTrue(extra['writethumbnail'])


class SubtitleTests(unittest.TestCase):
    def test_language_codes(self):
        f = ytcommon.subtitle_langs
        self.assertEqual(f('en, it;pt-BR  es'), ['en', 'it', 'pt-BR', 'es'])
        self.assertEqual(f('EN en'), ['EN'])   # no repeats
        self.assertEqual(f('english, x, 123, en-'), [])   # not codes
        self.assertEqual(len(f(','.join(['aa', 'bb', 'cc', 'dd', 'ee', 'ff', 'gg', 'hh', 'ii', 'jj']))), 8)
        self.assertEqual(f(None), [])

    def test_the_setting_is_cleaned(self):
        self.assertEqual(opts(sub_langs='it,,  en;;xx9')['sub_langs'], 'it, en')
        self.assertEqual(opts(sub_langs='???')['sub_langs'], 'en')
        self.assertEqual(opts(sub_langs=5)['sub_langs'], 'en')
        self.assertIs(opts(subtitles=1)['subtitles'], True)

    def test_subtitles_are_embedded_in_a_video(self):
        _, _, _, pps, extra = ytcommon.build_format(opts(mode='video', subtitles=True, sub_langs='it, en'))
        self.assertEqual(extra['subtitleslangs'], ['it', 'en'])
        self.assertTrue(extra['writesubtitles'])
        self.assertEqual(keys(pps).index('FFmpegSubtitlesConvertor') < keys(pps).index('FFmpegEmbedSubtitle'), True)

    def test_subtitles_do_not_apply_to_audio(self):
        _, _, _, pps, extra = ytcommon.build_format(opts(mode='audio', subtitles=True))
        self.assertNotIn('writesubtitles', extra)
        self.assertNotIn('FFmpegEmbedSubtitle', keys(pps))


class SponsorBlockTests(unittest.TestCase):
    def test_off_by_default(self):
        _, _, _, pps, _ = ytcommon.build_format(opts(mode='video'))
        self.assertFalse({'SponsorBlock', 'ModifyChapters'} & set(keys(pps)))

    def test_the_order_is_the_one_yt_dlp_uses(self):
        _, _, _, pps, _ = ytcommon.build_format(opts(mode='audio', audio_format='mp3', sponsorblock=True, embed=True))
        k = keys(pps)
        self.assertLess(k.index('SponsorBlock'), k.index('FFmpegExtractAudio'))
        self.assertLess(k.index('FFmpegExtractAudio'), k.index('ModifyChapters'))
        self.assertLess(k.index('ModifyChapters'), k.index('FFmpegMetadata'))
        self.assertEqual(pps[0]['when'], 'after_filter')


class YtDlpAcceptsThemTests(unittest.TestCase):
    """The parameters are really understood by the installed yt-dlp (nothing is downloaded)."""

    def test_every_combination_builds(self):
        for mode, af in (('audio', 'mp3'), ('audio', 'flac'), ('audio', 'wav'), ('audio', 'ogg'), ('video', 'mp3')):
            for sb in (False, True):
                for subs in (False, True):
                    o = opts(mode=mode, audio_format=af, sponsorblock=sb, subtitles=subs, sub_langs='en, it')
                    fmt, sort, _, pps, extra = ytcommon.build_format(o)
                    p = ytcommon.base_ydl_params()
                    p.update(extra)
                    p.update({'format': fmt, 'postprocessors': pps})
                    with yt_dlp.YoutubeDL(p) as ydl:
                        self.assertEqual(len(ydl._pps['post_process']) + len(ydl._pps['after_filter']) + len(ydl._pps['before_dl']),
                                         len(pps), (mode, af, sb, subs))


if __name__ == '__main__':
    unittest.main()
