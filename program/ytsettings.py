"""Settings of the program: the defaults, the validation of what the page sends, and settings.json."""
import json
import os
import re
import time

from ytcommon import DATA, IS_ANDROID, atomic_write, subtitle_langs  # noqa: E402  (first: sets the paths and sys.path)

SETTINGS_FILE = os.path.join(DATA, 'settings.json')

def default_download_dir():
    if os.environ.get('YTG_DEFAULT_DIR'):   # Android app: the app chooses the folder (Download or private folder)
        return os.environ['YTG_DEFAULT_DIR']
    if IS_ANDROID:
        # the phone's "Download" folder (visible to other apps): needs the permission granted with termux-setup-storage
        for cand in (os.path.expanduser('~/storage/downloads'), '/storage/emulated/0/Download', '/sdcard/Download'):
            if os.path.isdir(cand) and os.access(cand, os.W_OK):
                return os.path.join(cand, 'YT-Grabber')
    xdg = os.environ.get('XDG_DOWNLOAD_DIR')   # Linux (set inside Flatpak, where ~ is not the real home folder)
    if xdg and os.path.isdir(xdg):
        return os.path.join(xdg, 'YT-Grabber')
    return os.path.join(os.path.expanduser('~'), 'Downloads', 'YT-Grabber')


DEFAULT_SETTINGS = {
    'download_dir': default_download_dir(),
    'mode': 'audio',            # audio | video
    'audio_format': 'm4a' if IS_ANDROID else 'mp3',   # mp3 | m4a | opus (on the phone M4A: no re-encoding, much less load)
    'mp3_bitrate': '192',
    'video_height': '1080',     # best | 2160 | 1440 | 1080 | 720 | 480 | 360
    'embed': True,              # copertina + metadati
    'subtitles': False,         # video only: put the subtitles in the MP4
    'sub_langs': 'en',          # language codes, separated by commas
    'sponsorblock': False,      # cut out the sponsor, self-promotion and reminder segments (SponsorBlock)
    'single_only': False,       # "video inside a playlist" link -> only that video
    'force': False,             # download again even if already present
    'cookies_browser': '',      # chrome | firefox | edge | ...
    'lang': '',                 # interface language chosen by the user ('' = detect it automatically)
    'check_updates': True,      # ask GitHub now and then whether a newer version of YT Grabber exists
    'notify_done': True,        # tell the user when a download has finished (browser notification, Windows tray)
    'auto_ytdlp': True,         # install a newer yt-dlp by itself (when nothing is downloading) and restart
    # settings of the program as a whole (not of a single download): see clean_global
    'speed_limit': 0,           # KB/s for each simultaneous download, 0 = no limit
    'proxy': '',                # http://host:port, https://..., socks5://... ('' = none)
    'hours_on': False,          # download only inside the allowed hours
    'hours_from': '00:00',
    'hours_to': '06:00',
    'skip_known': False,        # a video that is already in another folder is linked or copied, not downloaded again
}
GLOBAL_KEYS = ('speed_limit', 'proxy', 'hours_on', 'hours_from', 'hours_to', 'skip_known')
MAX_SPEED_LIMIT = 1000000   # KB/s (about 1 GB/s: more than any connection)
PROXY_RE = re.compile(r'(?:https?|socks4a?|socks5h?)://(?:[^\s/@:]+(?::[^\s/@]*)?@)?(?:[\w.-]+|\[[0-9a-fA-F:]+\]):\d{1,5}/?')
TIME_RE = re.compile(r'([01]\d|2[0-3]):([0-5]\d)')
AUDIO_FORMATS = ('mp3', 'm4a', 'opus', 'flac', 'wav', 'ogg')
LANG_CODES = ('', 'en', 'it', 'es', 'fr', 'de', 'pt', 'nl', 'pl', 'ru', 'tr', 'ar', 'hi', 'id', 'zh', 'ja', 'ko')
BROWSERS = ('', 'firefox', 'chrome', 'edge', 'brave', 'opera', 'vivaldi', 'chromium', 'whale', 'safari')

SETTINGS = dict(DEFAULT_SETTINGS)


def clean_opts(o, base=None):
    base = base or SETTINGS
    o = o or {}
    r = {}
    r['mode'] = o.get('mode') if o.get('mode') in ('audio', 'video') else base['mode']
    r['audio_format'] = o.get('audio_format') if o.get('audio_format') in AUDIO_FORMATS else base['audio_format']
    r['mp3_bitrate'] = str(o.get('mp3_bitrate')) if str(o.get('mp3_bitrate')) in ('128', '192', '256', '320') else base['mp3_bitrate']
    r['video_height'] = str(o.get('video_height')) if str(o.get('video_height')) in ('best', '2160', '1440', '1080', '720', '480', '360') else base['video_height']
    for k in ('embed', 'single_only', 'force'):
        r[k] = bool(o[k]) if k in o else bool(base[k])
    r['cookies_browser'] = o.get('cookies_browser') if o.get('cookies_browser') in BROWSERS else base['cookies_browser']
    r['subtitles'] = bool(o['subtitles']) if 'subtitles' in o else bool(base.get('subtitles', False))
    r['sponsorblock'] = bool(o['sponsorblock']) if 'sponsorblock' in o else bool(base.get('sponsorblock', False))
    langs = o.get('sub_langs') if isinstance(o.get('sub_langs'), str) else base.get('sub_langs', 'en')
    r['sub_langs'] = ', '.join(subtitle_langs(langs)) or 'en'
    r['lang'] = o.get('lang') if o.get('lang') in LANG_CODES else base.get('lang', '')
    for k in ('check_updates', 'notify_done', 'auto_ytdlp'):
        r[k] = bool(o[k]) if k in o else bool(base.get(k, True))
    return r


def clean_global(o, base=None):
    """The settings that belong to the program as a whole: the speed limit, the proxy and the allowed hours (what is not valid is
    replaced by the value it had before)."""
    base = base or SETTINGS
    o = o or {}
    r = {}
    sl = o.get('speed_limit', base.get('speed_limit', 0))
    try:
        sl = int(float(sl))
    except (TypeError, ValueError):
        sl = base.get('speed_limit', 0)
    r['speed_limit'] = max(0, min(sl, MAX_SPEED_LIMIT))
    px = o.get('proxy', base.get('proxy', ''))
    px = px.strip() if isinstance(px, str) else base.get('proxy', '')
    r['proxy'] = px if px == '' or (len(px) <= 300 and PROXY_RE.fullmatch(px)) else base.get('proxy', '')
    r['hours_on'] = bool(o['hours_on']) if 'hours_on' in o else bool(base.get('hours_on', False))
    r['skip_known'] = bool(o['skip_known']) if 'skip_known' in o else bool(base.get('skip_known', False))
    for k in ('hours_from', 'hours_to'):
        v = o.get(k)
        r[k] = v if isinstance(v, str) and TIME_RE.fullmatch(v) else base.get(k, DEFAULT_SETTINGS[k])
    return r


def in_allowed_hours(s, now=None):
    """False if the allowed hours are on and the current time of the day is outside them. A window that ends before it starts
    (22:00 to 06:00) goes through midnight; equal times mean the whole day."""
    if not s.get('hours_on'):
        return True
    t = time.localtime(now)
    cur = t.tm_hour * 60 + t.tm_min
    a = [int(x) for x in s.get('hours_from', '00:00').split(':')]
    b = [int(x) for x in s.get('hours_to', '00:00').split(':')]
    start, end = a[0] * 60 + a[1], b[0] * 60 + b[1]
    if start == end:
        return True
    return start <= cur < end if start < end else (cur >= start or cur < end)


def load_settings():
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        d = {}
    s = clean_opts(d, DEFAULT_SETTINGS)
    s.update(clean_global(d, DEFAULT_SETTINGS))
    dd = d.get('download_dir')
    s['download_dir'] = dd if isinstance(dd, str) and dd.strip() else DEFAULT_SETTINGS['download_dir']
    if os.environ.get('YTG_DEFAULT_DIR'):
        # until the user picks a folder of their own, it follows the one proposed by the app (changes if they grant file access)
        s['dir_auto'] = bool(d.get('dir_auto', True))
        if s['dir_auto']:
            s['download_dir'] = DEFAULT_SETTINGS['download_dir']
    SETTINGS.clear()
    SETTINGS.update(s)


def save_settings():
    atomic_write(SETTINGS_FILE, json.dumps(SETTINGS, ensure_ascii=False, indent=1))
