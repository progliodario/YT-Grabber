"""Code shared by server.py and the worker processes (ytworker.py)."""
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))   # folder with the code (program\)
# FROZEN: running inside YT-Grabber.exe (PyInstaller). There the program files live in a read-only temporary folder
# (RES) and everything that must be kept (settings, download list, ffmpeg, updates) goes to DATA_ROOT.
# From source code DATA_ROOT is the project's generated\ folder (created automatically, not in git); the Android app moves it
# with YTG_DATA_ROOT because there the code is copied into a flat folder.
FROZEN = bool(getattr(sys, 'frozen', False))
if FROZEN:
    RES = getattr(sys, '_MEIPASS', ROOT)
    DATA_ROOT = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'YT-Grabber')
    os.makedirs(DATA_ROOT, exist_ok=True)
else:
    RES = ROOT
    DATA_ROOT = os.environ.get('YTG_DATA_ROOT') or os.path.join(os.path.dirname(ROOT), 'generated')
VENDOR = os.path.join(DATA_ROOT, 'vendor')
BIN = os.path.join(DATA_ROOT, 'bin')
VBIN = os.path.join(VENDOR, 'bin')
DATA = os.path.join(DATA_ROOT, 'data')
CACHE_DIR = os.path.join(DATA, 'cache')

if not FROZEN and os.path.isdir(VENDOR) and VENDOR not in sys.path:
    sys.path.insert(0, VENDOR)
# yt-dlp version downloaded by the updater (Android app and exe): it takes precedence over the bundled one
YTDLP_UPDATE = os.path.join(DATA, 'ytdlp-update', 'yt-dlp')
if os.path.isfile(YTDLP_UPDATE) and YTDLP_UPDATE not in sys.path:
    sys.path.insert(0, YTDLP_UPDATE)

_update_finder = None
if FROZEN and os.path.isfile(YTDLP_UPDATE):
    # In the exe yt-dlp is already "frozen" inside the program and the PyInstaller importer takes precedence over sys.path:
    # without this, a version downloaded by the updater would never be used.
    import importlib.abc
    import importlib.machinery

    class _UpdateFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path, target=None):
            if name == 'yt_dlp' or name.startswith('yt_dlp.'):
                return importlib.machinery.PathFinder.find_spec(name, [YTDLP_UPDATE] if path is None else path)
            return None

    if not any(type(f).__name__ == '_UpdateFinder' for f in sys.meta_path):   # reload(ytcommon) must not add it twice
        _update_finder = _UpdateFinder()
        sys.meta_path.insert(0, _update_finder)


def disable_ytdlp_update():
    """If the updated copy of yt-dlp is broken: set it aside and go back to the bundled one. True if anything changed."""
    changed = False
    for f in [f for f in sys.meta_path if type(f).__name__ == '_UpdateFinder']:
        sys.meta_path.remove(f)
        changed = True
    if os.path.isfile(YTDLP_UPDATE):
        try:
            os.replace(YTDLP_UPDATE, YTDLP_UPDATE + '.broken')
            changed = True
        except OSError:
            pass
    while YTDLP_UPDATE in sys.path:
        sys.path.remove(YTDLP_UPDATE)
    for m in [m for m in sys.modules if m == 'yt_dlp' or m.startswith('yt_dlp.')]:
        del sys.modules[m]
    return changed


os.environ['PATH'] = os.pathsep.join([VBIN, BIN, os.environ.get('PATH', '')])

# YouTube client for the fast path: 'visionos' needs no JS and has no ad wait like
# 'tv_samsung' (5-6 s per video). If a video fails, the next attempt uses yt-dlp's default clients.
FAST_CLIENTS = ['visionos', 'web']

EXE = '.exe' if os.name == 'nt' else ''
# Android: inside the app (YTG_ANDROID_APP, set by the app) or inside Termux (ffmpeg and node installed with "pkg")
ANDROID_APP = os.name != 'nt' and bool(os.environ.get('YTG_ANDROID_APP'))
IS_ANDROID = ANDROID_APP or (os.name != 'nt' and bool(
    os.environ.get('YTG_FORCE_ANDROID') or os.environ.get('TERMUX_VERSION') or os.path.isdir('/data/data/com.termux')))
DENO = os.path.join(BIN if FROZEN else VBIN, 'deno' + EXE)
# inside the app, ffmpeg and the JS runtime are executables provided by the app (native library folder)
APP_FFMPEG = os.environ.get('YTG_FFMPEG') if ANDROID_APP else None
APP_QJS = os.environ.get('YTG_QJS') if ANDROID_APP else None
FFMPEG_DIR = BIN if os.path.exists(os.path.join(BIN, 'ffmpeg' + EXE)) else None
HAVE_FFMPEG = bool(FFMPEG_DIR) or bool(shutil.which('ffmpeg')) or bool(APP_FFMPEG and os.path.exists(APP_FFMPEG))

# kind: (label, retryable, max attempts, hint)
ERR = {
    'private': ('Private video', False, 1, 'The video is private. If it is yours, set the browser cookies in Settings.'),
    'deleted': ('Deleted video', False, 1, 'The video was removed by YouTube or by its uploader.'),
    'unavailable': ('Video unavailable', False, 1, 'The video is no longer available or was removed.'),
    'geo': ('Blocked in your country', False, 1, 'The video is not available in your region.'),
    'age': ('Sign-in required (age)', False, 1, 'Age-restricted video: set the cookies of a browser where you are signed in to YouTube.'),
    'members': ('Members only', False, 1, 'Content reserved for members of the channel.'),
    'premium': ('Music Premium only', False, 1, 'Content reserved for YouTube Music Premium subscribers.'),
    'copyright': ('Blocked for copyright', False, 1, 'The video was blocked because of copyright.'),
    'live': ('Live / not aired yet', False, 1, 'Live streams and premieres that have not ended cannot be downloaded.'),
    'bot': ('YouTube bot check', True, 6, 'YouTube asks you to confirm you are not a bot: set the browser cookies.'),
    'ratelimit': ('Too many requests (429)', True, 6, 'YouTube is limiting requests. Downloads slow down by themselves and retry.'),
    'network': ('Network error', True, 4, 'Connection problem: try again later.'),
    'format': ('Format not available', True, 2, 'No suitable format found: retrying with an alternative format.'),
    'postproc': ('Conversion error (ffmpeg)', True, 2, 'The file conversion failed.'),
    'disk': ('Disk / permission error', False, 1, 'Cannot write the file: check the free space and the folder permissions.'),
    'other': ('Unknown error', True, 3, 'Unexpected error: see the technical details.'),
}

_ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')


def ask_directory(start):
    """Folder picker window (tkinter). Must run in a separate process: tkinter wants the main thread."""
    import tkinter as tk
    from tkinter import filedialog
    r = tk.Tk()
    r.withdraw()
    r.attributes('-topmost', True)
    return filedialog.askdirectory(initialdir=start, title='Choose the destination folder') or ''


def clean_msg(e):
    m = _ANSI.sub('', str(e) or e.__class__.__name__)
    m = re.sub(r'^\s*ERROR:\s*', '', m).strip()
    m = re.sub(r'\s+', ' ', m)
    return m[:500]


def classify_text(m, errno=None):
    """-> kind. m is the already cleaned message."""
    low = m.lower()
    if errno in (28, 13, 30):
        return 'disk'
    has = lambda *ks: any(k in low for k in ks)  # noqa: E731
    if has('private video', 'video is private', 'this video is private', 'private playlist'):
        return 'private'
    if has('has been removed', 'account associated with this video has been terminated', 'video has been removed',
           'removed by the uploader', 'deleted video'):
        return 'deleted'
    if has('not available in your country', 'blocked it in your country', 'not made this video available in your country',
           'geo restrict', 'geo-restrict'):
        return 'geo'
    if has('copyright', 'blocked it on copyright'):
        return 'copyright'
    if has('confirm your age', 'age-restricted', 'age restricted', 'inappropriate for some users'):
        return 'age'
    if has('members-only', 'members only', 'join this channel', 'available to this channel\'s members'):
        return 'members'
    if has('music premium', 'premium members'):
        return 'premium'
    if has('live event', 'premieres in', 'is live', 'will begin in', 'scheduled', 'upcoming'):
        return 'live'
    if has('not a bot', 'sign in to confirm'):
        return 'bot'
    if has('429', 'too many requests', 'rate-limit', 'rate limit', 'rate-limited'):
        return 'ratelimit'
    if has('requested format is not available', 'no video formats found', 'format is not available'):
        return 'format'
    if has('video unavailable', 'this video is unavailable', 'video is not available', 'unavailable', 'does not exist'):
        return 'unavailable'
    if has('postprocessing', 'ffmpeg', 'ffprobe', 'conversion failed'):
        return 'postproc'
    if has('no space left', 'permission denied', 'access is denied', 'disk full', 'errno 28', 'errno 13'):
        return 'disk'
    if has('timed out', 'timeout', 'connection', 'temporary failure', 'remote end closed', 'incompleteread',
           'http error 5', 'ssl', 'reset by peer', 'name or service not known', 'getaddrinfo', 'network is unreachable',
           'unable to download', 'transporterror', 'read error'):
        return 'network'
    return 'other'


def build_format(opts):
    """-> (format, format_sort, fallback_format, postprocessors, extra_params)"""
    pps = []
    extra = {}
    if opts['mode'] == 'audio':
        af = opts['audio_format']
        if af == 'mp3':
            fmt = 'bestaudio/best'
            pps.append({'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': opts['mp3_bitrate']})
            # lame -q 7: encodes 2x faster, difference not audible at >=128 kbps on already compressed sources
            extra['postprocessor_args'] = {'extractaudio': ['-compression_level', '7']}
        elif af == 'm4a':
            fmt = 'bestaudio[ext=m4a]/bestaudio/best'
            pps.append({'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a', 'preferredquality': '192'})
        else:
            fmt = 'bestaudio[acodec=opus]/bestaudio/best'
            pps.append({'key': 'FFmpegExtractAudio', 'preferredcodec': 'opus', 'preferredquality': '192'})
        fallback = 'bestaudio/best'
        sort = None
    else:
        h = opts['video_height']
        fmt = 'bv*+ba/b'
        fallback = 'b'
        sort = None if h == 'best' else ['res:' + h, 'vcodec:h264', 'acodec:aac']
        extra['merge_output_format'] = 'mp4'
    if opts['embed']:
        pps.append({'key': 'FFmpegMetadata', 'add_metadata': True, 'add_chapters': opts['mode'] == 'video',
                    'add_infojson': None})
        extra['writethumbnail'] = True
        pps.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg', 'when': 'before_dl'})
        pps.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
    return fmt, sort, fallback, pps, extra


def human_title(info, mode, fallback=''):
    t = info.get('title') or fallback or info.get('id') or 'untitled'
    if mode == 'audio':
        artist = (info.get('artist') or '').strip()
        track = (info.get('track') or '').strip()
        if artist and track:
            return '%s - %s' % (artist[:80], track)
    return t


class QuietLogger:
    def debug(self, m): pass
    def info(self, m): pass
    def warning(self, m): pass
    def error(self, m): pass


def base_ydl_params():
    p = {
        'quiet': True, 'no_warnings': True, 'noprogress': True, 'logger': QuietLogger(),
        'cachedir': CACHE_DIR, 'socket_timeout': 30, 'retries': 5, 'fragment_retries': 10, 'extractor_retries': 3,
        'file_access_retries': 5, 'windowsfilenames': True, 'color': {'stdout': 'never', 'stderr': 'never'},
        'ignoreerrors': False, 'noplaylist': True, 'continuedl': True,
    }
    if APP_FFMPEG and os.path.exists(APP_FFMPEG):
        p['ffmpeg_location'] = APP_FFMPEG
    elif FFMPEG_DIR:
        p['ffmpeg_location'] = FFMPEG_DIR
    if os.path.exists(DENO):
        p['js_runtimes'] = {'deno': {'path': DENO}}
    elif APP_QJS and os.path.exists(APP_QJS):
        p['js_runtimes'] = {'quickjs': {'path': APP_QJS}}   # Android app: QuickJS provided by the app
    elif shutil.which('node'):
        p['js_runtimes'] = {'node': {}}   # Termux: deno does not exist, node is used
    return p


def atomic_write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace(tmp, path)
