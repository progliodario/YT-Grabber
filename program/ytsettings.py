"""Settings of the program: the defaults, the validation of what the page sends, and settings.json."""
import json
import os

from ytcommon import DATA, IS_ANDROID, atomic_write  # noqa: E402  (first: sets the paths and sys.path)

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
    'single_only': False,       # "video inside a playlist" link -> only that video
    'force': False,             # download again even if already present
    'cookies_browser': '',      # chrome | firefox | edge | ...
    'lang': '',                 # interface language chosen by the user ('' = detect it automatically)
    'check_updates': True,      # ask GitHub now and then whether a newer version of YT Grabber exists
    'notify_done': True,        # tell the user when a download has finished (browser notification, Windows tray)
    'auto_ytdlp': True,         # install a newer yt-dlp by itself (when nothing is downloading) and restart
}
LANG_CODES = ('', 'en', 'it', 'es', 'fr', 'de', 'pt', 'nl', 'pl', 'ru', 'tr', 'ar', 'hi', 'id', 'zh', 'ja', 'ko')
BROWSERS = ('', 'firefox', 'chrome', 'edge', 'brave', 'opera', 'vivaldi', 'chromium', 'whale', 'safari')

SETTINGS = dict(DEFAULT_SETTINGS)


def clean_opts(o, base=None):
    base = base or SETTINGS
    o = o or {}
    r = {}
    r['mode'] = o.get('mode') if o.get('mode') in ('audio', 'video') else base['mode']
    r['audio_format'] = o.get('audio_format') if o.get('audio_format') in ('mp3', 'm4a', 'opus') else base['audio_format']
    r['mp3_bitrate'] = str(o.get('mp3_bitrate')) if str(o.get('mp3_bitrate')) in ('128', '192', '256', '320') else base['mp3_bitrate']
    r['video_height'] = str(o.get('video_height')) if str(o.get('video_height')) in ('best', '2160', '1440', '1080', '720', '480', '360') else base['video_height']
    for k in ('embed', 'single_only', 'force'):
        r[k] = bool(o[k]) if k in o else bool(base[k])
    r['cookies_browser'] = o.get('cookies_browser') if o.get('cookies_browser') in BROWSERS else base['cookies_browser']
    r['lang'] = o.get('lang') if o.get('lang') in LANG_CODES else base.get('lang', '')
    for k in ('check_updates', 'notify_done', 'auto_ytdlp'):
        r[k] = bool(o[k]) if k in o else bool(base.get(k, True))
    return r


def load_settings():
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        d = {}
    s = clean_opts(d, DEFAULT_SETTINGS)
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
