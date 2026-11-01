#!/usr/bin/env python3
"""YT Grabber - local server to download YouTube and YouTube Music videos and playlists.

Start:  python program/server.py [--port 8765] [--host 127.0.0.1] [--dir FOLDER] [--no-browser] [--idle-exit MINUTES]
"""
import argparse
import atexit
import ctypes
import gzip
import hashlib
import heapq
import json
import mimetypes
import queue
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import urllib.request
import webbrowser
from collections import Counter, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ytcommon must be imported first: it sets the paths (also inside YT-Grabber.exe) and the sys.path of yt-dlp
from ytcommon import (ROOT, RES, DATA_ROOT, DATA, DENO, FROZEN, IS_ANDROID, ANDROID_APP,  # noqa: E402
                      HAVE_FFMPEG)

WEB = os.path.join(RES, 'web')
JOBS_DIR = os.path.join(DATA, 'jobs')
COOKIES_FILE = os.path.join(DATA, 'cookies.txt')
SETTINGS_FILE = os.path.join(DATA, 'settings.json')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import yt_dlp  # noqa: E402
from yt_dlp.utils import sanitize_filename  # noqa: E402

APP_NAME = 'yt-grabber'
APP_VERSION = '1.5.1'
CONCURRENCY = 10  # simultaneous downloads: fixed by requirement

LOCK = threading.RLock()
COND = threading.Condition(LOCK)
SHUTDOWN = threading.Event()


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# --------------------------------------------------------------------------- settings

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


def atomic_write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace(tmp, path)


# --------------------------------------------------------------------------- errors
from ytcommon import ERR, clean_msg, classify_text, human_title, base_ydl_params  # noqa: E402


def classify_error(e):
    """Exception -> (kind, cleaned message)."""
    m = clean_msg(e)
    eno = getattr(e, 'errno', None) if isinstance(e, OSError) and not isinstance(e, (ConnectionError, TimeoutError)) else None
    return classify_text(m, eno), m


class ItemFailure(Exception):
    def __init__(self, kind, msg):
        super().__init__(msg)
        self.kind = kind


# --------------------------------------------------------------------------- modello

class Item:
    __slots__ = ('idx', 'vid', 'url', 'title', 'duration', 'uploader', 'dupn', 'state', 'progress', 'speed', 'eta',
                 'size', 'stage', 'attempts', 'ekind', 'emsg', 'file', 'ver', 'not_before', 'files_seen', 'fb',
                 'lastp', 'reject', 'slot')

    def __init__(self, idx, vid, url, title='', duration=None, uploader='', dupn=1):
        self.idx = idx
        self.vid = vid
        self.url = url
        self.title = title or ''
        self.duration = duration
        self.uploader = uploader or ''
        self.dupn = dupn
        self.slot = False    # occupies one of the 10 download slots
        self.state = 'q'     # q queued | a downloading | p converting | d done | e error | s already present | c cancelled
        #                      k skipped: it was already there when the subscription ("only new videos") started
        self.progress = 0.0
        self.speed = 0
        self.eta = None
        self.size = None
        self.stage = ''
        self.attempts = 0
        self.ekind = ''
        self.emsg = ''
        self.file = ''
        self.ver = 0
        self.not_before = 0.0
        self.files_seen = []
        self.fb = False
        self.lastp = 0.0
        self.reject = ''

    def key(self):
        base = self.vid or ('idx%d' % self.idx)
        return base if self.dupn <= 1 else '%s#%d' % (base, self.dupn)

    def to_json(self, now):
        return {
            'i': self.idx, 's': self.state, 'v': self.vid, 't': self.title, 'p': round(self.progress, 1),
            'sp': int(self.speed or 0), 'eta': self.eta, 'sz': self.size, 'st': self.stage, 'a': self.attempts,
            'ek': self.ekind, 'em': self.emsg, 'f': self.file, 'd': self.duration, 'u': self.uploader,
            'rt': int(max(0, self.not_before - now)) if (self.state == 'q' and self.not_before > now) else 0,
            'ver': self.ver,
        }


class Job:
    def __init__(self, jid, url, opts, urls=None):
        self.id = jid
        self.url = url
        self.urls = urls or []       # for the "single videos"
        self.opts = opts
        self.title = ''
        self.kind = 'playlist'       # playlist | single
        self.status = 'enumerating'  # enumerating | running | done | cancelled | error
        self.paused = False
        self.interrupted = False
        self.items = []
        self.counts = Counter()
        self.seq = 0
        self.queue = deque()
        self.delayed = []
        self.declared = None
        self.pad = None              # None = not known yet; 0 = no numbering
        self.enum_done = False
        self.pid = ''
        self.dir = ''
        self.created = time.time()
        self.finished = None
        self.warning = ''
        self.message = ''
        self.recent = deque(maxlen=200)
        self.seen = Counter()
        self.run_started = time.time()
        self.cancel = False
        self.dirty = True
        self.enum_thread = None
        self.pp_done = False
        self.sub_id = ''             # set when this job is a run of a subscription
        self.sub_auto = False        # True for the checks started by the scheduler (they vanish if nothing is new)

    # all the following methods must be called with LOCK held
    def touch(self, it):
        self.seq += 1
        it.ver = self.seq

    def set_state(self, it, st):
        if it.state == st:
            self.touch(it)
            return
        self.counts[it.state] -= 1
        self.counts[st] += 1
        it.state = st
        self.touch(it)
        self.dirty = True

    def add_item(self, it, enqueue=True):
        self.items.append(it)
        self.counts[it.state] += 1
        self.touch(it)
        self.dirty = True
        if it.state == 'q' and enqueue:
            self.queue.append(it)

    def numbered(self):
        return bool(self.pad)

    def summary(self, now=None):
        now = now or time.time()
        c = self.counts
        total = len(self.items)
        speed = 0
        err_idx = []
        for it in self.items:
            if it.state == 'a':
                speed += it.speed or 0
            elif it.state == 'e' and len(err_idx) < 80:
                err_idx.append(it.idx)
        finished_n = c['d'] + c['s'] + c['e'] + c['c'] + c['k']
        eta = None
        if self.status in ('running', 'enumerating') and not self.paused:
            win = [t for t in self.recent if now - t <= 90]
            remaining = c['q'] + c['a'] + c['p']
            if len(win) >= 3 and remaining:
                span = max(5.0, now - win[0])
                rate = len(win) / span
                eta = int(remaining / rate) if rate > 0 else None
        return {
            'id': self.id, 'url': self.url, 'title': self.title or self.url, 'kind': self.kind, 'status': self.status,
            'paused': self.paused, 'interrupted': self.interrupted, 'dir': self.dir, 'created': self.created,
            'finished': self.finished, 'warning': self.warning, 'message': self.message, 'seq': self.seq,
            'declared': self.declared, 'enum_done': self.enum_done, 'total': total, 'pad': self.pad or 0,
            'counts': {k: c[k] for k in ('q', 'a', 'p', 'd', 'e', 's', 'c', 'k')}, 'speed': int(speed), 'eta': eta,
            'processed': finished_n, 'opts': self.opts, 'err_idx': err_idx,
            'cover': self.items[0].vid if self.items else '',
        }

    def to_disk(self):
        return {
            'v': 1, 'id': self.id, 'url': self.url, 'urls': self.urls, 'opts': self.opts, 'title': self.title,
            'kind': self.kind, 'status': self.status, 'paused': self.paused, 'declared': self.declared,
            'pad': self.pad, 'enum_done': self.enum_done, 'pid': self.pid, 'dir': self.dir, 'created': self.created,
            'finished': self.finished, 'warning': self.warning, 'message': self.message, 'sub': self.sub_id,
            'items': [[i.idx, i.vid, i.title, i.state, i.ekind, i.emsg, i.file, i.duration, i.uploader, i.attempts,
                       i.dupn, i.url] for i in self.items],
        }


MANAGER_JOBS = {}
JOB_ORDER = []


class Throttle:
    """Global slowdown when YouTube answers with 429 / anti-bot."""

    def __init__(self):
        self.until = 0.0
        self.level = 0
        self.reason = ''
        self.ok_streak = 0

    def hit(self, kind):
        with LOCK:
            now = time.time()
            if now < self.until - 1:
                return
            self.level = min(self.level + 1, 5)
            secs = min(240, 15 * (2 ** (self.level - 1))) + random.randint(0, 5)
            self.until = now + secs
            self.reason = ERR[kind][0]
            self.ok_streak = 0
            log('YouTube is limiting requests (%s): automatic pause of %ds' % (kind, secs))
            COND.notify_all()

    def success(self):
        with LOCK:
            self.ok_streak += 1
            if self.level and self.ok_streak >= 8 and time.time() > self.until:
                self.level -= 1
                self.ok_streak = 0


THROTTLE = Throttle()


# --------------------------------------------------------------------------- manifest (resume)

class Manifests:
    def __init__(self):
        self.data = {}
        self.dirty = set()

    def get(self, d):
        with LOCK:
            if d not in self.data:
                p = os.path.join(d, '.ytgrab_manifest.json')
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        self.data[d] = json.load(f)
                except Exception:
                    self.data[d] = {}
            return self.data[d]

    def mark(self, d):
        with LOCK:
            self.dirty.add(d)

    def flush(self):
        with LOCK:
            todo = [(d, json.dumps(self.data[d], ensure_ascii=False)) for d in list(self.dirty) if d in self.data]
            self.dirty.clear()
        for d, txt in todo:
            try:
                if os.path.isdir(d):
                    atomic_write(os.path.join(d, '.ytgrab_manifest.json'), txt)
            except Exception as e:
                log('manifest not saved:', e)


MANIFESTS = Manifests()


# --------------------------------------------------------------------------- URL

YT_HOSTS = ('youtube.com', 'm.youtube.com', 'music.youtube.com', 'youtu.be', 'youtube-nocookie.com', 'gaming.youtube.com')
CHANNEL_TABS = ('videos', 'shorts', 'streams', 'playlists', 'releases', 'podcasts', 'featured', 'live', 'courses')


def classify_url(raw, single_only=False):
    """-> (kind, url, vid) with kind in video | playlist | auto, or None if it is not a link."""
    raw = raw.strip().strip('<>"\'')
    if not raw:
        return None
    if re.fullmatch(r'[\w-]{11}', raw):
        return 'video', 'https://www.youtube.com/watch?v=' + raw, raw
    if re.fullmatch(r'(PL|OLAK5uy_|UU|FL|LL|RDCLAK5uy_|VL|PU)[\w-]{8,}', raw):
        return 'playlist', 'https://www.youtube.com/playlist?list=' + raw, None
    if not re.match(r'^https?://', raw, re.I):
        if re.match(r'^(www\.|m\.|music\.)?(youtube\.com|youtu\.be)', raw, re.I):
            raw = 'https://' + raw
        else:
            return None
    u = urllib.parse.urlparse(raw)
    host = u.netloc.lower().split(':')[0]
    host_nowww = host[4:] if host.startswith('www.') else host
    if host_nowww not in YT_HOSTS:
        return 'auto', raw, None
    q = urllib.parse.parse_qs(u.query)
    path = u.path or '/'
    v = (q.get('v') or [None])[0]
    lst = (q.get('list') or [None])[0]
    if host_nowww == 'youtu.be':
        v = path.strip('/').split('/')[0] or v
    m = re.match(r'^/(?:shorts|live|embed|v)/([\w-]{11})', path)
    if m:
        v = m.group(1)
    if v and not re.fullmatch(r'[\w-]{11}', v):
        v = None
    base = 'https://music.youtube.com' if host_nowww == 'music.youtube.com' else 'https://www.youtube.com'
    if path.startswith('/playlist') and lst:
        return 'playlist', '%s/playlist?list=%s' % (base, lst), None
    if lst and v:
        if single_only or lst.startswith(('RD', 'UL')):
            return 'video', 'https://www.youtube.com/watch?v=' + v, v
        return 'playlist', '%s/playlist?list=%s' % (base, lst), None
    if v:
        return 'video', 'https://www.youtube.com/watch?v=' + v, v
    if lst:
        return 'playlist', '%s/playlist?list=%s' % (base, lst), None
    if re.match(r'^/(@|channel/|c/|user/)', path):
        parts = [p for p in path.split('/') if p]
        if not parts[-1].lower() in CHANNEL_TABS:
            path = path.rstrip('/') + '/videos'
        return 'playlist', '%s%s' % (base, path), None
    if path.startswith('/browse/'):
        return 'playlist', raw, None
    return 'auto', raw, None


# --------------------------------------------------------------------------- file system

def hide_path(p):
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetFileAttributesW(p, 0x02)
        except Exception:
            pass


def safe_name(s, maxlen=150):
    s = sanitize_filename(s or '', restricted=False)
    s = re.sub(r'[\x00-\x1f]', '', s)
    s = re.sub(r'\s+', ' ', s).strip(' .')
    if len(s) > maxlen:
        s = s[:maxlen].rstrip(' .')
    return s or 'untitled'


def setup_dir(job, title, pid):
    base = SETTINGS['download_dir'] if not job.opts.get('_dir') else job.opts['_dir']
    os.makedirs(base, exist_ok=True)
    if job.kind == 'single':
        d = os.path.join(base, 'Singles')
        os.makedirs(d, exist_ok=True)
        job.dir = d
        check_disk(job)
        return
    name = safe_name(title or pid or 'Playlist', 90)
    n = 1
    while True:
        cand = os.path.join(base, name if n == 1 else '%s (%d)' % (name, n))
        meta = os.path.join(cand, '.ytgrab_playlist.json')
        if not os.path.exists(cand):
            os.makedirs(cand, exist_ok=True)
            break
        try:
            with open(meta, 'r', encoding='utf-8') as f:
                m = json.load(f)
            if m.get('id') and m.get('id') == pid:
                break
        except Exception:
            if not os.path.exists(meta):
                break  # folder without metadata: reuse it
        n += 1
    try:
        atomic_write(os.path.join(cand, '.ytgrab_playlist.json'), json.dumps({'id': pid, 'title': title, 'url': job.url}))
        hide_path(os.path.join(cand, '.ytgrab_playlist.json'))
    except Exception:
        pass
    job.dir = cand
    check_disk(job)


def check_disk(job):
    try:
        free = shutil.disk_usage(job.dir).free
    except OSError:
        return
    if free < 2 * 1024 ** 3 and not job.warning:
        job.warning = 'Low free disk space: %.1f GB. Downloads may fail.' % (free / 1024 ** 3)


def build_filename(job, it, title, ext):
    prefix = ('%0*d - ' % (job.pad, it.idx)) if job.numbered() else ''
    room = 245 - len(job.dir) - len(prefix) - len(ext) - 2
    name = safe_name(title, max(30, min(150, room)))
    return '%s%s%s' % (prefix, name, ext)


PREFIX_RE = re.compile(r'^\d+ - ')


def expected_for_existing(job, it, existing):
    """Recomputes the numeric prefix of an already present file (the playlist may have changed)."""
    if not job.numbered():
        return existing
    rest = PREFIX_RE.sub('', existing, count=1)
    return '%0*d - %s' % (job.pad, it.idx, rest)


# --------------------------------------------------------------------------- download engine (worker processes)

FALLBACK_KINDS = ('format', 'other', 'unavailable', 'age', 'members', 'premium', 'postproc')
SLOTS = {'used': 0}          # downloads in progress (max CONCURRENCY)
# up to 10 downloading + a few converting (~75 MB each). On Android fewer, to stay under the
# child-process limit that Android imposes on Termux.
MAX_PROCS = CONCURRENCY + (2 if IS_ANDROID else 4)
WATCHDOG = 900               # seconds without events before a worker is considered stuck
NOWIN = 0x08000000 if os.name == 'nt' else 0
LOG_DIR = os.path.join(DATA, 'logs')
PROCS = []   # all the worker processes started: on exit they must be stopped one by one


def release_slot(it):
    """With LOCK held."""
    if it.slot:
        it.slot = False
        SLOTS['used'] -= 1
        COND.notify_all()


def kill_tree(p):
    try:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(p.pid)], capture_output=True, timeout=15,
                           creationflags=NOWIN)
        else:
            os.killpg(p.pid, signal.SIGKILL)   # the worker and its ffmpeg processes are in a separate group
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


class Proc:
    """A persistent ytworker.py process, managed by a supervisor thread."""

    def __init__(self, n):
        self.n = n
        self.p = None
        self.q = None
        self.logf = None

    def alive(self):
        return self.p is not None and self.p.poll() is None

    def kill(self):
        if self.p is not None:
            if self.p.poll() is None:
                kill_tree(self.p)
            for f in (self.p.stdin, self.p.stdout):
                try:
                    f.close()
                except Exception:
                    pass
            self.p = None
        if self.logf:
            try:
                self.logf.close()
            except Exception:
                pass
            self.logf = None

    def ensure(self):
        if self.alive():
            return
        self.kill()
        os.makedirs(LOG_DIR, exist_ok=True)
        self.logf = open(os.path.join(LOG_DIR, 'worker_%d.log' % self.n), 'wb')
        env = dict(os.environ)
        env['PYTHONUTF8'] = '1'
        env['PYTHONIOENCODING'] = 'utf-8'
        if FROZEN:   # inside YT-Grabber.exe the worker is the same exe started with --worker
            cmd = [sys.executable, '--worker']
        else:
            cmd = [os.environ.get('YTG_PYTHON') or sys.executable, '-u', os.path.join(ROOT, 'ytworker.py')]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.logf,
                                  cwd=DATA_ROOT, env=env, creationflags=NOWIN, start_new_session=(os.name != 'nt'))
        if self not in PROCS:
            PROCS.append(self)
        q = queue.Queue()
        self.q = q

        def reader(p=self.p):
            try:
                for raw in p.stdout:
                    try:
                        q.put(json.loads(raw.decode('utf-8', 'replace')))
                    except ValueError:
                        pass
            except Exception:
                pass
            finally:
                q.put({'ev': 'eof'})
        threading.Thread(target=reader, daemon=True, name='reader-%d' % self.n).start()
        deadline = time.time() + 90
        while True:
            try:
                ev = q.get(timeout=1)
            except queue.Empty:
                if time.time() > deadline or not self.alive():
                    self.kill()
                    raise ItemFailure('other', 'Could not start the download process')
                continue
            if ev.get('ev') == 'ready':
                return
            if ev.get('ev') == 'eof':
                self.kill()
                raise ItemFailure('other', 'Could not start the download process (see data/logs)')

    def send(self, obj):
        try:
            self.p.stdin.write((json.dumps(obj, ensure_ascii=False) + '\n').encode('utf-8'))
            self.p.stdin.flush()
        except Exception:
            self.kill()
            raise ItemFailure('other', 'The download process stopped unexpectedly')


class Manager:
    def __init__(self):
        self.workers = []

    # ---- creation / persistence
    def new_id(self):
        while True:
            jid = '%x%03x' % (int(time.time()), random.randint(0, 0xfff))
            if jid not in MANAGER_JOBS:
                return jid

    def add_job(self, job):
        with LOCK:
            MANAGER_JOBS[job.id] = job
            JOB_ORDER.append(job.id)
            job.dirty = True

    def start_enum(self, job):
        if job.enum_thread is not None and job.enum_thread.is_alive():
            return   # a read is already running (e.g. cancel + immediate resume): two reads would duplicate the items
        t = threading.Thread(target=enumerate_job, args=(job,), daemon=True, name='enum-' + job.id)
        job.enum_thread = t
        t.start()

    def load_jobs(self):
        os.makedirs(JOBS_DIR, exist_ok=True)
        for fn in sorted(os.listdir(JOBS_DIR)):
            if not fn.endswith('.json'):
                continue
            try:
                with open(os.path.join(JOBS_DIR, fn), 'r', encoding='utf-8') as f:
                    d = json.load(f)
                job = Job(d['id'], d['url'], d['opts'], d.get('urls'))
                job.title = d.get('title', '')
                job.kind = d.get('kind', 'playlist')
                job.status = d.get('status', 'running')
                job.declared = d.get('declared')
                job.pad = d.get('pad')
                job.enum_done = d.get('enum_done', False)
                job.pid = d.get('pid', '')
                job.dir = d.get('dir', '')
                job.created = d.get('created', time.time())
                job.finished = d.get('finished')
                job.warning = d.get('warning', '')
                job.message = d.get('message', '')
                job.sub_id = d.get('sub', '')
                for r in d.get('items', []):
                    it = Item(r[0], r[1], r[11] if len(r) > 11 else '', r[2], r[7], r[8], r[10])
                    it.state, it.ekind, it.emsg, it.file, it.attempts = r[3], r[4], r[5], r[6], r[9]
                    if it.state in ('a', 'p'):
                        it.state = 'q'
                    if it.state == 'q' and job.status in ('cancelled', 'done', 'error'):
                        it.state = 'c'
                    job.seen[it.vid] += 1
                    job.add_item(it, enqueue=False)
                    if it.state == 'q':
                        job.queue.append(it)
                if job.status in ('enumerating', 'running'):
                    job.paused = True
                    job.interrupted = True
                    job.status = 'running' if job.enum_done else 'enumerating'
                job.dirty = False
                MANAGER_JOBS[job.id] = job
                JOB_ORDER.append(job.id)
            except Exception as e:
                log('unreadable job', fn, e)
        JOB_ORDER.sort(key=lambda j: MANAGER_JOBS[j].created)

    def save_dirty(self):
        with LOCK:
            todo = []
            for job in MANAGER_JOBS.values():
                if job.dirty:
                    job.dirty = False
                    todo.append((job.id, job.to_disk()))
        for jid, data in todo:
            try:
                atomic_write(os.path.join(JOBS_DIR, jid + '.json'), json.dumps(data, ensure_ascii=False))
            except Exception as e:
                log('saving job failed', jid, e)
        MANIFESTS.flush()

    # ---- scheduler
    def next_work(self):
        with COND:
            while not SHUTDOWN.is_set():
                now = time.time()
                if now < THROTTLE.until:
                    COND.wait(min(1.0, THROTTLE.until - now))
                    continue
                if SLOTS['used'] >= CONCURRENCY:
                    COND.wait(1.0)
                    continue
                soonest = None
                for jid in JOB_ORDER:
                    job = MANAGER_JOBS.get(jid)
                    if not job or job.status not in ('enumerating', 'running') or job.paused or job.pad is None:
                        continue
                    while job.delayed and job.delayed[0][0] <= now:
                        _, idx = heapq.heappop(job.delayed)
                        job.queue.append(job.items[idx - 1])
                    while job.queue:
                        it = job.queue.popleft()
                        if it.state != 'q':
                            continue
                        job.set_state(it, 'a')
                        it.slot = True
                        SLOTS['used'] += 1
                        it.stage = 'Starting'
                        it.progress = 0.0
                        it.speed = 0
                        it.eta = None
                        return job, it
                    if job.delayed:
                        t = job.delayed[0][0]
                        soonest = t if soonest is None else min(soonest, t)
                COND.wait(max(0.05, min(1.0, soonest - now)) if soonest else 1.0)
        return None, None

    def worker(self, n):
        proc = Proc(n)
        time.sleep(random.random() * 0.6)
        while not SHUTDOWN.is_set():
            job, it = self.next_work()
            if job is None:
                break
            try:
                run_item(proc, job, it)
            except ItemFailure as e:
                with LOCK:
                    if it.state in ('a', 'p'):
                        fail_item(job, it, e.kind, str(e))
            except Exception as e:  # noqa: BLE001  safety net: a supervisor must never die
                log('supervisor error', n, e)
                traceback.print_exc()
                with LOCK:
                    if it.state in ('a', 'p'):
                        fail_item(job, it, 'other', clean_msg(e))
            finally:
                with COND:
                    release_slot(it)
                    maybe_finish(job)
                    COND.notify_all()
        proc.kill()

    def start(self):
        for n in range(MAX_PROCS):
            t = threading.Thread(target=self.worker, args=(n,), daemon=True, name='sup-%d' % n)
            t.start()
            self.workers.append(t)

        def saver():
            while not SHUTDOWN.is_set():
                time.sleep(2)
                try:
                    self.save_dirty()
                except Exception as e:
                    log('saver', e)
        threading.Thread(target=saver, daemon=True, name='saver').start()


MGR = Manager()


# --------------------------------------------------------------------------- download of one item

def run_item(proc, job, it):
    o = job.opts
    manifest = MANIFESTS.get(job.dir)
    key = it.key()
    # --- already downloaded? (no network)
    if not o.get('force'):
        m = manifest.get(key)
        if m and m.get('file'):
            src = os.path.join(job.dir, m['file'])
            if os.path.exists(src):
                newname = expected_for_existing(job, it, m['file'])
                if newname != m['file']:
                    dst = os.path.join(job.dir, newname)
                    if not os.path.exists(dst):
                        try:
                            os.replace(src, dst)
                            m['file'] = newname
                            MANIFESTS.mark(job.dir)
                        except OSError:
                            newname = m['file']
                    else:
                        newname = m['file']
                with LOCK:
                    it.file = newname
                    it.progress = 100.0
                    it.stage = 'Already present'
                    it.speed = 0
                    it.eta = None
                    if not it.title:
                        it.title = m.get('title') or newname
                    job.set_state(it, 's')
                    job.recent.append(time.time())
                return
    # --- download
    with LOCK:
        it.attempts += 1
        it.stage = 'Analyzing'
        job.touch(it)
    tmpd = os.path.join(job.dir, '.tmp', '%d' % it.idx)
    os.makedirs(tmpd, exist_ok=True)
    hide_path(os.path.join(job.dir, '.tmp'))
    proc.ensure()
    tid = '%s-%d-%d' % (job.id, it.idx, it.attempts)
    topts = {k: o[k] for k in ('mode', 'audio_format', 'mp3_bitrate', 'video_height', 'embed', 'cookies_browser')}
    if os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
        topts['cookies_file'] = COOKIES_FILE
        topts['cookies_mtime'] = os.path.getmtime(COOKIES_FILE)
    proc.send({'op': 'task', 'tid': tid, 'url': it.url, 'vid': it.vid, 'opts': topts, 'tmp': tmpd, 'fb': it.fb,
               'wid': proc.n})
    last = time.time()
    while True:
        if job.cancel or it.state == 'c':
            proc.kill()
            shutil.rmtree(tmpd, ignore_errors=True)
            return
        try:
            ev = proc.q.get(timeout=0.5)
        except queue.Empty:
            if time.time() - last > WATCHDOG:
                proc.kill()
                raise ItemFailure('network', 'No response for %d seconds' % WATCHDOG)
            if not proc.alive():
                raise ItemFailure('other', 'The download process stopped unexpectedly')
            continue
        t = ev.get('ev')
        if t == 'eof':
            raise ItemFailure('other', 'The download process stopped unexpectedly')
        if ev.get('tid') != tid:
            continue
        last = time.time()
        if t == 'progress':
            with LOCK:
                it.progress = ev.get('pct') or 0.0
                it.speed = ev.get('speed') or 0
                it.eta = ev.get('eta')
                if ev.get('size'):
                    it.size = ev['size']
                it.stage = ev.get('stage') or 'Download'
                job.touch(it)
        elif t == 'phase':
            with COND:   # download finished: release the slot, the file moves on to conversion
                release_slot(it)
                it.progress = 99.0
                it.speed = 0
                it.eta = None
                it.stage = ev.get('stage') or 'Converting'
                job.set_state(it, 'p')
                COND.notify_all()
        elif t == 'stage':
            with LOCK:
                it.stage = ev.get('stage') or it.stage
                job.touch(it)
        elif t == 'done':
            finalize_item(job, it, ev, tmpd, manifest, key)
            return
        elif t == 'error':
            msg = ev.get('msg') or 'unknown error'
            raise ItemFailure(ev.get('kind') or classify_text(msg, ev.get('errno')), msg)


def finalize_item(job, it, ev, tmpd, manifest, key):
    o = job.opts
    fp = ev['fp']
    info = ev.get('info') or {}
    title = human_title(info, o['mode'], it.title)
    ext = os.path.splitext(fp)[1]
    name = build_filename(job, it, title, ext)
    dst = os.path.join(job.dir, name)
    for n in range(1, 30):
        try:
            os.replace(fp, dst)
            break
        except PermissionError:
            if n >= 29:
                raise
            name = build_filename(job, it, '%s (%d)' % (title, n), ext)
            dst = os.path.join(job.dir, name)
    shutil.rmtree(tmpd, ignore_errors=True)
    with LOCK:
        manifest[key] = {'file': name, 'title': title, 'id': info.get('id') or it.vid}
        MANIFESTS.mark(job.dir)
        it.file = name
        if not it.vid:
            it.vid = info.get('id') or ''
        it.title = title
        it.progress = 100.0
        it.stage = 'Completed'
        it.speed = 0
        it.eta = None
        it.size = os.path.getsize(dst)
        it.ekind = ''
        it.emsg = ''
        job.set_state(it, 'd')
        job.recent.append(time.time())
    THROTTLE.success()


def fail_item(job, it, kind, msg):
    """With LOCK held. Schedules a new attempt or marks the final error."""
    label, retry, maxatt, hint = ERR[kind]
    it.speed = 0
    it.eta = None
    it.ekind = kind
    it.emsg = msg
    release_slot(it)
    if not it.fb and kind in FALLBACK_KINDS:
        # a single extra attempt with the default yt-dlp clients and the alternative format
        it.fb = True
        retry = True
        maxatt = max(maxatt, it.attempts + 1)
    if retry and it.attempts < maxatt and not job.cancel and job.status != 'cancelled':
        if kind in ('ratelimit', 'bot'):
            delay = 10 + 10 * it.attempts + random.randint(0, 8)
        elif kind == 'network':
            delay = 4 * it.attempts + random.randint(0, 3)
        else:
            delay = 3 + random.randint(0, 3)
        it.not_before = time.time() + delay
        it.stage = 'Retry %d/%d' % (it.attempts + 1, maxatt)
        job.set_state(it, 'q')
        heapq.heappush(job.delayed, (it.not_before, it.idx))
        if kind in ('ratelimit', 'bot'):
            THROTTLE.hit(kind)
        COND.notify_all()
    else:
        it.stage = 'Error'
        it.progress = 0.0
        job.set_state(it, 'e')
        if kind in ('ratelimit', 'bot'):
            THROTTLE.hit(kind)
        log('ERROR #%d %s [%s] %s' % (it.idx, it.vid, kind, msg[:160]))


# --------------------------------------------------------------------------- enumeration

def check_cookies(job):
    """If the cookies of the chosen browser cannot be read, carries on without them (and says so) instead of failing every video."""
    b = job.opts.get('cookies_browser')
    if not b:
        return
    try:
        from yt_dlp.cookies import extract_cookies_from_browser
        extract_cookies_from_browser(b)
    except Exception as e:  # noqa: BLE001
        with LOCK:
            job.opts['cookies_browser'] = ''
            job.warning = ('Could not read the cookies of %s (%s). Continuing without cookies: close the browser '
                           'or upload a cookies.txt file in Settings.') % (b, clean_msg(e)[:140])


def enumerate_job(job):
    try:
        check_cookies(job)
        if job.kind == 'single':
            enumerate_singles(job)
        else:
            for attempt in range(3):   # a read interrupted by a network problem resumes where it stopped
                try:
                    enumerate_playlist(job)
                    break
                except Exception as e:  # noqa: BLE001
                    kind, _m = classify_error(e)
                    if attempt < 2 and not job.cancel and kind in ('network', 'ratelimit', 'bot', 'other'):
                        log('playlist read interrupted, retrying:', clean_msg(e)[:120])
                        time.sleep(5 * (attempt + 1))
                        continue
                    raise
    except Exception as e:  # noqa: BLE001
        kind, msg = classify_error(e)
        log('enumeration failed', job.url, msg)
        with LOCK:
            if job.cancel:
                job.status = 'cancelled'
            else:
                job.status = 'error'
                job.message = '%s - %s' % (ERR[kind][0], msg) if kind != 'other' else msg
                if kind in ('private', 'age', 'bot'):
                    job.message += ' | ' + ERR[kind][3]
                if job.items:
                    job.message = 'Playlist reading stopped after %d items (%s). Press Resume to continue.' % (
                        len(job.items), job.message[:160])
            if not job.items:
                job.enum_done = True
            job.dirty = True
            COND.notify_all()
        if job.sub_id and not job.cancel:
            sub_run_failed(job)


def enumerate_singles(job):
    with LOCK:
        job.title = 'Single videos'
        setup_dir(job, '', '')
        job.pad = 0
        job.declared = len(job.urls)
        for n, u in enumerate(job.urls, 1):
            if n <= len(job.items):
                continue
            c = classify_url(u, job.opts.get('single_only'))
            vid = c[2] if c else None
            url = c[1] if c else u
            it = Item(n, vid or '', url, '', None, '')
            if not c:
                it.state = 'e'
                it.ekind = 'unavailable'
                it.emsg = 'Link not recognized: ' + u
            job.seen[vid] += 1
            it.dupn = job.seen[vid] if vid else 1
            job.add_item(it)
        job.enum_done = True
        job.status = 'running'
        job.dirty = True
        COND.notify_all()
        maybe_finish(job)


def make_flat_ydl(opts):
    p = base_ydl_params()
    p.update({'extract_flat': 'in_playlist', 'skip_download': True, 'noplaylist': False, 'lazy_playlist': True})
    if opts.get('cookies_browser'):
        p['cookiesfrombrowser'] = (opts['cookies_browser'],)
    elif os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
        cp = os.path.join(DATA, 'cookies_enum.txt')
        try:
            shutil.copyfile(COOKIES_FILE, cp)
            p['cookiefile'] = cp
        except Exception:
            pass
    return yt_dlp.YoutubeDL(p)


def iter_entries(ydl, info, depth=0):
    for e in info.get('entries') or []:
        if e is None:
            continue
        if e.get('ie_key') == 'YoutubeTab' or e.get('_type') == 'playlist':
            if depth < 2 and e.get('url'):
                try:
                    sub = ydl.extract_info(e['url'], download=False, process=False)
                except Exception as ex:  # noqa: BLE001
                    log('sub-playlist ignored', e.get('url'), clean_msg(ex))
                    continue
                for x in iter_entries(ydl, sub, depth + 1):
                    yield x
            continue
        yield e


def enumerate_playlist(job):
    ydl = make_flat_ydl(job.opts)
    try:
        info = ydl.extract_info(job.url, download=False, process=False)
        if not info:
            raise ItemFailure('unavailable', 'No content found for this link')
        if info.get('_type') not in ('playlist', 'multi_video') and not info.get('entries'):
            # "auto" link that is actually a single video
            with LOCK:
                job.kind = 'single'
                job.title = 'Single videos'
                job.urls = [job.url]
                job.opts = dict(job.opts)
            enumerate_singles(job)
            return
        title = info.get('title') or info.get('id') or 'Playlist'
        with LOCK:
            job.title = title
            job.pid = info.get('id') or ''
            if not job.dir:
                setup_dir(job, title, job.pid)
            declared = info.get('playlist_count') or info.get('n_entries')
            if isinstance(declared, int) and declared > 0:
                job.declared = declared
                if job.pad is None:
                    job.pad = max(2, len(str(declared)))
            job.status = 'enumerating'
            job.dirty = True
            COND.notify_all()
        n = 0
        have = len(job.items)
        # "only new videos" subscriptions: what was already there is listed but never downloaded
        sub = SUBS.get(job.sub_id) if job.sub_id else None
        only_new = bool(sub and sub.get('only_new'))
        baseline = only_new and sub.get('seen') is None   # first look: everything that is there now counts as old
        known = set(sub.get('seen') or ()) if only_new and not baseline else set()
        for e in iter_entries(ydl, info):
            if job.cancel:
                with LOCK:
                    job.status = 'cancelled'
                    job.dirty = True
                return
            n += 1
            if n <= have:
                continue  # resume: items already known
            vid = e.get('id') or ''
            t = e.get('title') or ''
            url = e.get('url') or ''
            if vid and (not url or not url.startswith('http')):
                url = 'https://www.youtube.com/watch?v=' + vid
            it = Item(n, vid, url, t, e.get('duration'), e.get('uploader') or e.get('channel') or '')
            with LOCK:
                if vid:
                    job.seen[vid] += 1
                    it.dupn = job.seen[vid]
                tl = t.strip().lower()
                if not vid:
                    it.state = 'e'
                    it.ekind = 'unavailable'
                    it.emsg = 'Entry without a video ID in the playlist'
                elif tl in ('[private video]', '[deleted video]', '[unavailable video]'):
                    it.state = 'e'
                    it.ekind = 'private' if 'private' in tl else ('deleted' if 'deleted' in tl else 'unavailable')
                    it.emsg = t + ' (already reported as unavailable in the playlist)'
                    it.stage = 'Error'
                elif only_new and (baseline or vid in known):
                    it.state = 'k'
                    it.stage = 'Skipped'
                job.add_item(it)
                COND.notify_all()
        with LOCK:
            if n == 0:
                job.status = 'error'
                job.message = 'No videos found: the playlist is empty or private (try setting the browser cookies).'
            else:
                need = max(2, len(str(n)))
                if job.pad is None:
                    job.pad = need
                elif need > job.pad:
                    job.opts['_renumber'] = True
                    job.pad_old = job.pad
                    job.pad = need
                job.enum_done = True
                if job.status == 'enumerating':
                    job.status = 'running'
                job.dirty = True
                if baseline:   # remember what was there: from now on only the videos that are not in this list are new
                    sub['seen'] = sorted({i.vid for i in job.items if i.state == 'k' and i.vid})
            COND.notify_all()
            maybe_finish(job)
        if baseline:
            save_subs()
    finally:
        try:
            ydl.close()
        except Exception:
            pass


# --------------------------------------------------------------------------- end of job

def maybe_finish(job):
    """With LOCK held."""
    if job.status not in ('enumerating', 'running') or not job.enum_done:
        return
    c = job.counts
    if c['q'] == 0 and c['a'] == 0 and c['p'] == 0:
        job.status = 'done'
        job.finished = time.time()
        job.dirty = True
        if not job.pp_done:
            job.pp_done = True
            threading.Thread(target=post_finish, args=(job,), daemon=True).start()
        log('Job %s completed: %d ok, %d already present, %d errors' % (job.id, c['d'], c['s'], c['e']))


def errors_text(job):
    with LOCK:
        errs = [i for i in job.items if i.state == 'e']
        total = len(job.items)
        title, url = job.title, job.url
    lines = ['YT Grabber - error list', 'Playlist: %s' % title, 'Link: %s' % url,
             'Total items: %d | Errors: %d' % (total, len(errs)), '']
    w = max(3, len(str(total)))
    for i in errs:
        label = ERR.get(i.ekind, ERR['other'])[0]
        link = 'https://www.youtube.com/watch?v=%s' % i.vid if i.vid else i.url
        lines.append('#%0*d | %s | %s | %s' % (w, i.idx, i.title or '(unknown title)', label, link))
        if i.emsg:
            lines.append('      details: %s' % i.emsg)
    return '\n'.join(lines) + '\n'


def m3u_text(job):
    with LOCK:
        done = sorted([i for i in job.items if i.state in ('d', 's') and i.file], key=lambda x: x.idx)
    out = ['#EXTM3U']
    for i in done:
        out.append('#EXTINF:%d,%s' % (int(i.duration or -1), os.path.splitext(i.file)[0]))
        out.append(i.file)
    return '\n'.join(out) + '\n'


def renumber_files(job):
    old = getattr(job, 'pad_old', None)
    if not old or not job.numbered():
        return
    manifest = MANIFESTS.get(job.dir)
    for it in list(job.items):
        if it.state in ('d', 's') and it.file and PREFIX_RE.match(it.file):
            new = expected_for_existing(job, it, it.file)
            if new != it.file:
                try:
                    os.replace(os.path.join(job.dir, it.file), os.path.join(job.dir, new))
                    m = manifest.get(it.key())
                    if m:
                        m['file'] = new
                    it.file = new
                except OSError:
                    pass
    MANIFESTS.mark(job.dir)


def post_finish(job):
    try:
        renumber_files(job)
        write_reports(job)
        shutil.rmtree(os.path.join(job.dir, '.tmp'), ignore_errors=True)
        MANIFESTS.flush()
    except Exception as e:  # noqa: BLE001
        log('post_finish', e)
    finally:
        job.pp_done = False
    if job.sub_id:
        sub_run_finished(job)
    notify_finished(job)


def write_reports(job):
    if not job.dir or not os.path.isdir(job.dir) or job.kind == 'single':
        return
    ep = os.path.join(job.dir, '_ERRORS.txt')
    mp = os.path.join(job.dir, '_playlist.m3u8')
    with LOCK:
        nerr = job.counts['e']
        ndone = job.counts['d'] + job.counts['s']
    try:
        if nerr:
            atomic_write(ep, errors_text(job))
        elif os.path.exists(ep):
            os.remove(ep)
        if ndone and job.kind != 'single':
            atomic_write(mp, m3u_text(job))
    except Exception as e:  # noqa: BLE001
        log('reports not written', e)


# --------------------------------------------------------------------------- job actions

def job_action(job, action, arg=None):
    with COND:
        if action == 'pause':
            job.paused = True
            job.interrupted = False
        elif action == 'resume':
            job.paused = False
            job.interrupted = False
            if job.status == 'cancelled' or job.cancel:
                job.cancel = False
                job.status = 'running' if job.enum_done else 'enumerating'
                job.finished = None
                for it in job.items:
                    if it.state == 'c':
                        it.attempts = 0
                        job.set_state(it, 'q')
                        job.queue.append(it)
                if not job.enum_done:
                    MGR.start_enum(job)
            elif job.status == 'enumerating' and not (job.enum_thread and job.enum_thread.is_alive()):
                MGR.start_enum(job)
            elif job.status == 'error' and not job.enum_done:
                job.status = 'enumerating'
                job.message = ''
                MGR.start_enum(job)
            elif job.status == 'error' and not job.items:
                job.status = 'enumerating'
                job.enum_done = False
                job.message = ''
                MGR.start_enum(job)
        elif action == 'cancel':
            job.cancel = True
            job.paused = False
            job.status = 'cancelled'
            job.finished = time.time()
            job.queue.clear()
            job.delayed.clear()
            for it in job.items:
                if it.state in ('q', 'a', 'p'):
                    it.stage = 'Cancelled'
                    job.set_state(it, 'c')
        elif action == 'retry_failed':
            ids = None if arg is None else set(arg)
            n = 0
            for it in job.items:
                if it.state == 'e' and (ids is None or it.idx in ids):
                    it.attempts = 0
                    it.fb = False
                    it.ekind = ''
                    it.emsg = ''
                    it.progress = 0.0
                    it.stage = ''
                    job.set_state(it, 'q')
                    job.queue.append(it)
                    n += 1
            if n:
                job.cancel = False
                job.paused = False
                job.interrupted = False
                job.finished = None
                if job.status in ('done', 'cancelled'):
                    job.status = 'running'
                    job.enum_done = True
        elif action == 'redownload':
            ids = None if arg is None else set(arg)
            for it in job.items:
                if it.state in ('d', 's', 'e', 'c') and (ids is None or it.idx in ids):
                    mf = MANIFESTS.get(job.dir)
                    mf.pop(it.key(), None)
                    MANIFESTS.mark(job.dir)
                    it.attempts = 0
                    it.fb = False
                    it.ekind = it.emsg = it.file = ''
                    it.progress = 0.0
                    job.set_state(it, 'q')
                    job.queue.append(it)
            job.cancel = False
            job.paused = False
            job.finished = None
            if job.status in ('done', 'cancelled'):
                job.status = 'running'
        job.dirty = True
        COND.notify_all()


def remove_job(job):
    job_action(job, 'cancel')
    with LOCK:
        MANAGER_JOBS.pop(job.id, None)
        if job.id in JOB_ORDER:
            JOB_ORDER.remove(job.id)
    try:
        os.remove(os.path.join(JOBS_DIR, job.id + '.json'))
    except OSError:
        pass


def create_jobs(raw_urls, opts, subscribe=None, only_new=False):
    opts = clean_opts(opts)
    hours = subscribe if subscribe in SUB_INTERVALS else None
    parsed, rejected = [], []
    seen = set()
    duplicates = []
    with LOCK:   # same link already in progress: two jobs on the same folder would trample each other's files
        busy = {MANAGER_JOBS[j].url: j for j in JOB_ORDER
                if j in MANAGER_JOBS and MANAGER_JOBS[j].kind != 'single'
                and MANAGER_JOBS[j].status in ('enumerating', 'running')}
    for chunk in re.split(r'[\s,;]+', raw_urls or ''):
        chunk = chunk.strip()
        if not chunk or chunk in seen:
            continue
        seen.add(chunk)
        c = classify_url(chunk, opts['single_only'])
        if not c:
            rejected.append(chunk)
        elif c[0] in ('playlist', 'auto') and c[1] in busy:
            duplicates.append(busy[c[1]])
        else:
            parsed.append((chunk, c))
    singles = [c[1] for _, c in parsed if c[0] == 'video']
    created = []
    if singles:
        job = Job(MGR.new_id(), singles[0] if len(singles) == 1 else '%d videos' % len(singles), dict(opts), singles)
        job.kind = 'single'
        MGR.add_job(job)
        MGR.start_enum(job)
        created.append(job.id)
    for chunk, c in parsed:
        if c[0] in ('playlist', 'auto'):
            job = Job(MGR.new_id(), c[1], dict(opts))
            job.kind = 'playlist'
            if hours:
                job.sub_id = add_sub(c[1], opts, hours, only_new)   # this job is the first run of the subscription
            MGR.add_job(job)
            MGR.start_enum(job)
            created.append(job.id)
    return created, rejected, duplicates


# --------------------------------------------------------------------------- subscriptions (playlists and channels kept up to date)

SUBS_FILE = os.path.join(DATA, 'subscriptions.json')
SUB_INTERVALS = (1, 3, 6, 12, 24, 72, 168)   # hours between two checks
SUBS = {}


SUBS_SAVE = threading.Lock()   # two threads writing the file at the same moment would fight over its temporary copy


def save_subs():
    with SUBS_SAVE:
        with LOCK:
            text = json.dumps(list(SUBS.values()), ensure_ascii=False, indent=1)
        atomic_write(SUBS_FILE, text)


def load_subs():
    try:
        with open(SUBS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = []
    for s in data if isinstance(data, list) else []:
        if isinstance(s, dict) and s.get('id') and s.get('url'):
            s['opts'] = clean_opts(s.get('opts') or {})
            s['opts']['force'] = False   # a check must never download everything again
            if s.get('hours') not in SUB_INTERVALS:
                s['hours'] = 24
            s['only_new'] = bool(s.get('only_new'))
            if not isinstance(s.get('seen'), list):
                s['seen'] = None   # None = the videos that are there now have not been looked at yet
            SUBS[s['id']] = s


def add_sub(url, opts, hours, only_new=False):
    """Creates (or updates) the subscription for this link. Its first run is the job that is being created now.
    only_new: do not download what is already in the playlist or channel, only the videos that appear later."""
    now = time.time()
    only_new = bool(only_new)
    with LOCK:
        sid = next((s['id'] for s in SUBS.values() if s['url'] == url), None)
        if sid:
            s = SUBS[sid]
            s.update(hours=hours, enabled=True, next_check=now + hours * 3600)
            if only_new != bool(s.get('only_new')):   # the mode changed: look at what is there now once more
                s.update(only_new=only_new, seen=None)
        else:
            sid = 's%x%02x' % (int(now), random.randint(0, 255))
            while sid in SUBS:
                sid += 'x'
            o = dict(opts)
            o['force'] = False
            SUBS[sid] = {'id': sid, 'url': url, 'title': '', 'opts': o, 'hours': hours, 'enabled': True,
                         'created': now, 'last_check': now, 'next_check': now + hours * 3600, 'last_new': None,
                         'status': 'checking', 'message': '', 'only_new': only_new, 'seen': None}
    save_subs()
    return sid


def run_sub(sub):
    """Starts a check of a subscription: a normal job on the same link (same folder; the files already there are
    skipped without touching the network). Returns False if that link is already being downloaded."""
    with LOCK:
        now = time.time()
        for jid in JOB_ORDER:
            j = MANAGER_JOBS.get(jid)
            if j and j.url == sub['url'] and j.status in ('enumerating', 'running'):
                sub['next_check'] = now + 300
                return False
        sub.update(last_check=now, next_check=now + sub['hours'] * 3600, status='checking', message='')
        job = Job(MGR.new_id(), sub['url'], dict(sub['opts']))
        job.kind = 'playlist'
        job.sub_id = sub['id']
        job.sub_auto = True
    MGR.add_job(job)
    MGR.start_enum(job)
    save_subs()
    return True


def sub_run_finished(job):
    with LOCK:
        sub = SUBS.get(job.sub_id)
        if not sub:
            return
        sub['title'] = job.title or sub.get('title', '')
        new, errs = job.counts['d'], job.counts['e']
        sub.update(last_new=new, status='errors' if errs else 'ok', message='')
        if sub.get('only_new') and isinstance(sub.get('seen'), list):   # what was downloaded now is old for the next check
            sub['seen'] = sorted(set(sub['seen']) | {i.vid for i in job.items if i.state in ('d', 's', 'k') and i.vid})
        quiet = job.sub_auto and new == 0 and errs == 0 and job.status == 'done'
    save_subs()
    if quiet:   # nothing new: do not leave a card in the list after every check
        time.sleep(1.5)
        remove_job(job)


def sub_run_failed(job):
    with LOCK:
        sub = SUBS.get(job.sub_id)
        if sub:
            sub.update(status='error', message=(job.message or '')[:300])
    save_subs()


def subs_loop():
    while not SHUTDOWN.is_set():
        SHUTDOWN.wait(20)
        now = time.time()
        with LOCK:
            due = next((s for s in SUBS.values() if s.get('enabled') and now >= s.get('next_check', 0)), None)
        if due:   # one per round, so that many subscriptions do not all start at the same moment
            run_sub(due)


def subs_state():
    with LOCK:
        return [{'id': s['id'], 'url': s['url'], 'title': s.get('title') or '', 'hours': s['hours'],
                 'enabled': bool(s.get('enabled')), 'last_check': s.get('last_check'),
                 'next_check': s.get('next_check'), 'last_new': s.get('last_new'), 'status': s.get('status', ''),
                 'message': s.get('message', ''), 'only_new': bool(s.get('only_new'))}
                for s in sorted(SUBS.values(), key=lambda x: x.get('created', 0))]


# --------------------------------------------------------------------------- HTTP

LOCAL_NAMES = ('localhost', '127.0.0.1', '[::1]', '::1')


def inside(base, path):
    """True if path is inside the base folder (compared by whole folders, not by text prefix)."""
    try:
        b = os.path.normcase(os.path.realpath(base))
        return os.path.commonpath([b, os.path.normcase(os.path.realpath(path))]) == b
    except ValueError:   # different drives
        return False


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'YTGrabber/' + APP_VERSION

    def log_message(self, fmt, *args):
        pass

    # --- utilities
    def host_ok(self):
        h = (self.headers.get('Host') or '').rsplit(':', 1)[0] if not (self.headers.get('Host') or '').startswith('[') \
            else (self.headers.get('Host') or '').split(']')[0] + ']'
        if self.server.allow_remote:
            return True
        return h.lower() in LOCAL_NAMES

    def is_local_client(self):
        return self.client_address[0] in ('127.0.0.1', '::1', '::ffff:127.0.0.1')

    def send_bytes(self, code, body, ctype, extra=None, gz=True):
        if isinstance(body, str):
            body = body.encode('utf-8')
        headers = {'Content-Type': ctype, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'}
        if extra:
            headers.update(extra)
        if gz and len(body) > 1024 and 'gzip' in (self.headers.get('Accept-Encoding') or ''):
            body = gzip.compress(body, 4)
            headers['Content-Encoding'] = 'gzip'
        self.send_response(code)
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def send_json(self, obj, code=200):
        self.send_bytes(code, json.dumps(obj, ensure_ascii=False, separators=(',', ':')), 'application/json; charset=utf-8')

    def err(self, code, msg):
        self.send_json({'error': msg}, code)

    def read_json(self):
        n = int(self.headers.get('Content-Length') or 0)
        if n > 8 * 1024 * 1024:
            raise ValueError('request too large')
        raw = self.rfile.read(n) if n else b''
        return json.loads(raw.decode('utf-8')) if raw else {}

    def check_post(self):
        if self.headers.get('X-YTG') != '1':
            self.err(403, 'Invalid request')
            return False
        org = self.headers.get('Origin')
        if org:
            oh = urllib.parse.urlparse(org).netloc
            if oh != self.headers.get('Host'):
                self.err(403, 'Origin not allowed')
                return False
        return True

    # --- routing
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        LAST_ACTIVITY[0] = time.time()
        try:
            if not self.host_ok():
                return self.err(403, 'Host not allowed')
            u = urllib.parse.urlparse(self.path)
            path = u.path
            qs = urllib.parse.parse_qs(u.query)
            if path == '/api/ping':
                return self.send_json({'app': APP_NAME, 'version': APP_VERSION})
            if path == '/api/state':
                return self.send_json(self.state())
            m = re.fullmatch(r'/api/jobs/([\w]+)', path)
            if m:
                return self.job_detail(m.group(1), int((qs.get('since') or ['0'])[0] or 0))
            m = re.fullmatch(r'/api/jobs/([\w]+)/(errors\.txt|playlist\.m3u8)', path)
            if m:
                job = MANAGER_JOBS.get(m.group(1))
                if not job:
                    return self.err(404, 'Job not found')
                if m.group(2) == 'errors.txt':
                    return self.send_bytes(200, errors_text(job), 'text/plain; charset=utf-8',
                                           {'Content-Disposition': "attachment; filename*=UTF-8''" + urllib.parse.quote('errors - %s.txt' % safe_name(job.title, 60))})
                return self.send_bytes(200, m3u_text(job), 'audio/x-mpegurl; charset=utf-8',
                                       {'Content-Disposition': "attachment; filename*=UTF-8''" + urllib.parse.quote('%s.m3u8' % safe_name(job.title, 60))})
            m = re.fullmatch(r'/api/jobs/([\w]+)/file/(\d+)', path)
            if m:
                return self.serve_item_file(m.group(1), int(m.group(2)))
            return self.serve_static(path)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            try:
                self.err(500, clean_msg(e))
            except Exception:
                pass

    def do_POST(self):
        LAST_ACTIVITY[0] = LAST_POST[0] = time.time()
        try:
            if not self.host_ok():
                return self.err(403, 'Host not allowed')
            if not self.check_post():
                return
            path = urllib.parse.urlparse(self.path).path
            body = self.read_json()
            if path == '/api/jobs':
                sub_hours = body.get('subscribe')
                created, rejected, dups = create_jobs(body.get('urls', ''), body.get('opts') or {},
                                                      sub_hours if isinstance(sub_hours, int) else None,
                                                      bool(body.get('only_new')))
                if not created:
                    if dups:
                        return self.err(409, 'This link is already in progress: you can find it in the list below.')
                    return self.err(400, 'No valid YouTube link found' + (': ' + ', '.join(rejected[:3]) if rejected else ''))
                return self.send_json({'created': created, 'rejected': rejected, 'duplicates': dups})
            m = re.fullmatch(r'/api/jobs/([\w]+)/action', path)
            if m:
                job = MANAGER_JOBS.get(m.group(1))
                if not job:
                    return self.err(404, 'Job not found')
                act = body.get('action')
                if act == 'remove':
                    remove_job(job)
                elif act == 'open_folder':
                    if not self.is_local_client():
                        return self.err(403, 'Only from the computer running the server')
                    open_folder(job.dir)
                elif act in ('pause', 'resume', 'cancel', 'retry_failed', 'redownload'):
                    job_action(job, act, body.get('ids'))
                else:
                    return self.err(400, 'Unknown action')
                return self.send_json({'ok': True})
            m = re.fullmatch(r'/api/subs/([\w]+)/action', path)
            if m:
                sub = SUBS.get(m.group(1))
                if not sub:
                    return self.err(404, 'Subscription not found')
                act, now = body.get('action'), time.time()
                if act == 'remove':
                    with LOCK:
                        SUBS.pop(sub['id'], None)
                elif act == 'toggle':
                    with LOCK:
                        sub['enabled'] = not sub.get('enabled')
                        if sub['enabled']:
                            sub['next_check'] = min(sub.get('next_check') or now, now + 60)
                elif act == 'interval':
                    hours = body.get('hours')
                    if hours not in SUB_INTERVALS:
                        return self.err(400, 'Invalid interval')
                    with LOCK:
                        sub['hours'] = hours
                        sub['next_check'] = (sub.get('last_check') or now) + hours * 3600
                elif act == 'check':
                    if not run_sub(sub):
                        return self.err(409, 'This link is already being downloaded.')
                else:
                    return self.err(400, 'Unknown action')
                save_subs()
                return self.send_json({'ok': True})
            if path == '/api/settings':
                return self.save_settings_req(body)
            if path == '/api/cookies':
                txt = body.get('text', '')
                if txt.strip():
                    if '# Netscape' not in txt[:200] and '\t' not in txt:
                        return self.err(400, 'Invalid format: a cookies.txt file in Netscape format is required')
                    atomic_write(COOKIES_FILE, txt.replace('\r\n', '\n'))
                else:
                    if os.path.exists(COOKIES_FILE):
                        os.remove(COOKIES_FILE)
                return self.send_json({'ok': True, 'has_cookies': os.path.exists(COOKIES_FILE)})
            if path == '/api/choose-dir':
                if not self.is_local_client():
                    return self.err(403, 'Only from the computer running the server')
                return self.send_json({'path': choose_dir(body.get('start') or SETTINGS['download_dir'])})
            if path == '/api/update':
                return self.update_ytdlp()
            if path == '/api/appupdate':   # "check now" for a new version of YT Grabber itself
                if time.time() - UPDATE['checked'] > 30:
                    check_update()
                return self.send_json(update_state())
            if path == '/api/quit':   # clean shutdown (used by the Android app when "Close" is pressed)
                if not self.is_local_client():
                    return self.err(403, 'Only from the device running the server')
                self.send_json({'ok': True})
                shutdown_now()
                return
            if path == '/api/appupdate/install':   # "Update now" (Windows app): download, check, install, restart
                if not self.is_local_client():
                    return self.err(403, 'Only from the computer running the server')
                if not install_supported():
                    return self.err(400, 'The one-click update is only available in the Windows app installed with its setup.')
                if not update_state()['can_install']:
                    return self.err(409, 'There is no update ready to install.')
                if UPDATE_INSTALL['state'] not in ('downloading', 'installing'):
                    threading.Thread(target=run_update_install, daemon=True, name='update-install').start()
                return self.send_json({'ok': True})
            return self.err(404, 'Not found')
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            try:
                self.err(500, clean_msg(e))
            except Exception:
                pass

    # --- specific handlers
    def state(self):
        now = time.time()
        with LOCK:
            jobs = [MANAGER_JOBS[j].summary(now) for j in JOB_ORDER if j in MANAGER_JOBS]
            thr = {'until': THROTTLE.until if THROTTLE.until > now else 0, 'reason': THROTTLE.reason}
        return {
            'app': APP_NAME, 'version': APP_VERSION, 'ytdlp': yt_dlp.version.__version__, 'concurrency': CONCURRENCY,
            'settings': SETTINGS, 'jobs': jobs, 'throttle': thr, 'now': now,
            'tools': {'ffmpeg': HAVE_FFMPEG, 'deno': os.path.exists(DENO)},
            'has_cookies': os.path.exists(COOKIES_FILE), 'local': self.is_local_client(),
            'errmeta': {k: [v[0], v[3]] for k, v in ERR.items()}, 'android': IS_ANDROID,
            'browsers': [b for b in BROWSERS if b], 'subs': subs_state(), 'sub_intervals': list(SUB_INTERVALS),
            'update': update_state(), 'native_notify': bool(FINISH_HOOKS) or ANDROID_APP,
        }

    def job_detail(self, jid, since):
        job = MANAGER_JOBS.get(jid)
        if not job:
            return self.err(404, 'Job not found')
        now = time.time()
        with LOCK:
            s = job.summary(now)
            items = [i.to_json(now) for i in job.items if i.ver > since or (i.state == 'q' and i.not_before > now and i.stage)]
            thr = {'until': THROTTLE.until if THROTTLE.until > now else 0, 'reason': THROTTLE.reason}
        s['items'] = items
        s['throttle'] = thr
        s['now'] = now
        self.send_json(s)

    def serve_item_file(self, jid, idx):
        job = MANAGER_JOBS.get(jid)
        if not job or idx < 1 or idx > len(job.items):
            return self.err(404, 'File not found')
        it = job.items[idx - 1]
        if not it.file:
            return self.err(404, 'File not available yet')
        full = os.path.realpath(os.path.join(job.dir, it.file))
        if not inside(job.dir, full) or not os.path.isfile(full):
            return self.err(404, 'File not found')
        size = os.path.getsize(full)
        ctype = mimetypes.guess_type(full)[0] or 'application/octet-stream'
        start, end, code = 0, size - 1, 200
        rng = self.headers.get('Range')
        if rng:
            m = re.fullmatch(r'bytes=(\d*)-(\d*)', rng.strip())
            if m and (m.group(1) or m.group(2)):
                if m.group(1):
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else size - 1
                else:
                    start = max(0, size - int(m.group(2)))
                end = min(end, size - 1)
                if start > end:
                    self.send_response(416)
                    self.send_header('Content-Range', 'bytes */%d' % size)
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                code = 206
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(end - start + 1))
        if code == 206:
            self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
        self.send_header('Content-Disposition', "inline; filename*=UTF-8''" + urllib.parse.quote(it.file))
        self.end_headers()
        if self.command == 'HEAD':
            return
        with open(full, 'rb') as f:
            f.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = f.read(min(256 * 1024, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    def serve_static(self, path):
        if path in ('', '/'):
            path = '/index.html'
        rel = os.path.normpath(urllib.parse.unquote(path).lstrip('/'))
        full = os.path.realpath(os.path.join(WEB, rel))
        if not inside(WEB, full) or not os.path.isfile(full):
            return self.err(404, 'Not found')
        with open(full, 'rb') as f:
            data = f.read()
        ctype = mimetypes.guess_type(full)[0] or 'application/octet-stream'
        if full.endswith('.webmanifest'):
            ctype = 'application/manifest+json'
        if ctype.startswith('text/') or ctype in ('application/javascript', 'application/json', 'application/manifest+json', 'image/svg+xml'):
            ctype += '; charset=utf-8'
        self.send_bytes(200, data, ctype, {'Cache-Control': 'no-cache'})

    def save_settings_req(self, body):
        s = clean_opts(body, SETTINGS)
        dd = body.get('download_dir')
        if isinstance(dd, str) and dd.strip():
            dd = os.path.abspath(os.path.expanduser(dd.strip()))
            try:
                os.makedirs(dd, exist_ok=True)
                probe = os.path.join(dd, '.ytgrab_probe')
                with open(probe, 'w') as f:
                    f.write('x')
                os.remove(probe)
            except Exception as e:  # noqa: BLE001
                return self.err(400, 'Folder not writable: %s' % clean_msg(e))
            s['download_dir'] = dd
        else:
            s['download_dir'] = SETTINGS['download_dir']
        if os.environ.get('YTG_DEFAULT_DIR'):
            s['dir_auto'] = s['download_dir'] == DEFAULT_SETTINGS['download_dir']
        with LOCK:
            SETTINGS.clear()
            SETTINGS.update(s)
        save_settings()
        log('settings saved from %s: %s/%s %s' % (self.client_address[0], s['mode'], s['audio_format'], s['mp3_bitrate']))
        self.send_json({'ok': True, 'settings': SETTINGS})

    def update_ytdlp(self):
        if not self.is_local_client():
            return self.err(403, 'Only from the computer running the server')
        try:
            install_ytdlp()
        except Exception as e:  # noqa: BLE001
            return self.err(500, 'Update failed: ' + clean_msg(e))
        self.send_json({'ok': True, 'restart': True})
        restart_program()


def install_ytdlp():
    """Installs the latest yt-dlp for this kind of installation. Raises if it fails."""
    if ANDROID_APP or FROZEN:
        # Android app and exe: no pip, the latest yt-dlp (single file) is downloaded and takes precedence over the bundled one
        dst_dir = os.path.join(DATA, 'ytdlp-update')
        os.makedirs(dst_dir, exist_ok=True)
        tmp = os.path.join(dst_dir, 'yt-dlp.new')
        req = urllib.request.Request('https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp',
                                     headers={'User-Agent': 'YT-Grabber'})
        with urllib.request.urlopen(req, timeout=90) as r, open(tmp, 'wb') as f:
            shutil.copyfileobj(r, f)
        import zipfile
        with zipfile.ZipFile(tmp) as z:
            if not any(n.startswith('yt_dlp/') for n in z.namelist()):
                raise ValueError('downloaded file is not valid')
        os.replace(tmp, os.path.join(dst_dir, 'yt-dlp'))
    else:
        # setup_tools.py knows which packages are needed on this platform (on Android/Termux nothing is compiled)
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'setup_tools.py'), '--update'], capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout)[-400:])


def restart_program():
    """Saves the list and restarts the server after a short pause (the answer to the page gets out first)."""
    MGR.save_dirty()

    def later():
        time.sleep(1.0)
        MGR.save_dirty()
        if FROZEN:
            restart_self()
        os._exit(75)  # the launcher (Start.bat / Android app) restarts the server
    threading.Thread(target=later, daemon=True).start()


# --------------------------------------------------------------------------- automatic yt-dlp updates

YTDLP_API = os.environ.get('YTG_YTDLP_API') or 'https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest'
YTDLP_AUTO = {'checked': 0, 'latest': '', 'error': ''}
YTDLP_TRIES = os.path.join(DATA, 'ytdlp-auto.json')   # {"target": version, "time": when}: what was installed last, to never repeat it in a loop
YTDLP_QUIET = 120     # seconds without a click in the page before the program may restart by itself
LAST_POST = [0.0]     # last time somebody pressed something in the page (reading the state does not count)


def ytdlp_decision(current, latest, tried, now):
    """What the automatic update should do: 'none' (up to date), 'wait' (it already tried this version in the last 24 hours) or 'update'."""
    if not latest or version_tuple(latest) <= version_tuple(current):
        return 'none'
    if tried and tried.get('target') == latest and now - float(tried.get('time') or 0) < 24 * 3600:
        return 'wait'
    return 'update'


def ytdlp_latest():
    """The version number of the latest yt-dlp release, from GitHub."""
    req = urllib.request.Request(YTDLP_API, headers={'User-Agent': 'YTGrabber/' + APP_VERSION, 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=20) as r:
        tag = str(json.loads(r.read().decode('utf-8')).get('tag_name') or '')
    if not re.fullmatch(r'\d{4}\.\d{2}\.\d{2}(\.\d+)?', tag):
        raise ValueError('unexpected answer from GitHub')
    return tag


def ytdlp_idle():
    """True when nothing is downloading and nobody is using the page, so that restarting costs nothing."""
    with LOCK:
        busy = any(j.status in ('enumerating', 'running') and not j.paused for j in MANAGER_JOBS.values())
    return not busy and time.time() - LAST_POST[0] > YTDLP_QUIET


def ytdlp_auto_loop():
    """Once a day: if there is a newer yt-dlp, installs it as soon as nothing is downloading, and restarts the program."""
    time.sleep(90)
    while not SHUTDOWN.is_set():
        try:
            if SETTINGS.get('auto_ytdlp', True):
                if time.time() - YTDLP_AUTO['checked'] > (24 * 3600 if not YTDLP_AUTO['error'] else 3600):
                    YTDLP_AUTO.update(latest=ytdlp_latest(), error='', checked=time.time())
                try:
                    with open(YTDLP_TRIES, 'r', encoding='utf-8') as f:
                        tried = json.load(f)
                except Exception:
                    tried = {}
                what = ytdlp_decision(yt_dlp.version.__version__, YTDLP_AUTO['latest'], tried, time.time())
                if what == 'update' and ytdlp_idle():
                    log('yt-dlp %s -> %s (automatic update)' % (yt_dlp.version.__version__, YTDLP_AUTO['latest']))
                    atomic_write(YTDLP_TRIES, json.dumps({'target': YTDLP_AUTO['latest'], 'time': time.time()}))
                    install_ytdlp()
                    restart_program()
                    return
        except Exception as e:  # noqa: BLE001
            YTDLP_AUTO.update(error=clean_msg(e), checked=time.time())
            log('automatic yt-dlp update failed', e)
        time.sleep(300)


def open_folder(d):
    if not d or not os.path.isdir(d):
        return
    try:
        if os.name == 'nt':
            os.startfile(d)  # noqa: S606
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', d])
        elif IS_ANDROID and shutil.which('termux-open'):
            subprocess.Popen(['termux-open', d])
        else:
            subprocess.Popen(['xdg-open', d])
    except Exception as e:  # noqa: BLE001
        log('opening the folder failed', e)


def open_browser(url):
    """Opens the page in the browser. On Android it goes through Termux (webbrowser does not know the phone's browser)."""
    try:
        if IS_ANDROID and shutil.which('termux-open-url'):
            subprocess.Popen(['termux-open-url', url])
        else:
            webbrowser.open(url)
    except Exception as e:  # noqa: BLE001
        log('opening the browser failed', e)


def choose_dir(start):
    """The folder picker window runs in a separate process (tkinter wants the main thread)."""
    if FROZEN:
        cmd = [sys.executable, '--choose-dir', start]
    else:
        cmd = [sys.executable, '-c',
               "import sys; sys.path.insert(0, %r); import ytcommon; print(ytcommon.ask_directory(%r))" % (ROOT, start)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, creationflags=NOWIN)
        out = r.stdout.strip().splitlines()
        return os.path.normpath(out[-1]) if out and out[-1].strip() else ''
    except Exception:
        return ''


def restart_self():
    """Restarts the program (exe): starts a new copy, which waits for the port to be freed, and closes this one."""
    env = {k: v for k, v in os.environ.items() if not k.startswith('_PYI') and k != '_MEIPASS2'}
    env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'   # a completely new copy: do not reuse this one's extraction folder
    env['YTG_RESTARTED'] = '1'
    try:
        subprocess.Popen([sys.executable] + sys.argv[1:], env=env, cwd=DATA_ROOT, creationflags=0x00000010 if os.name == 'nt' else 0)
    except Exception as e:  # noqa: BLE001
        log('restart failed', e)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 64
    allow_remote = False

    def handle_error(self, request, client_address):
        et = sys.exc_info()[0]
        if et is not None and issubclass(et, (ConnectionError, TimeoutError)):
            return  # the browser closed the connection: normal
        super().handle_error(request, client_address)


# --------------------------------------------------------------------------- new versions, "finished" notices

RELEASES_PAGE = 'https://github.com/progliodario/YT-Grabber/releases/latest'
UPDATE_API = os.environ.get('YTG_UPDATE_URL') or 'https://api.github.com/repos/progliodario/YT-Grabber/releases/latest'
UPDATE = {'checked': 0, 'latest': '', 'url': '', 'error': '', 'setup_url': '', 'setup_sha': '', 'setup_size': 0}
UPDATE_INSTALL = {'state': 'idle', 'pct': 0, 'error': ''}   # one-click update: idle | downloading | installing | error
SETUP_PREFIX = 'https://github.com/progliodario/YT-Grabber/releases/download/'
FINISH_HOOKS = []   # functions called with a dict when a download has finished (the Windows app adds its tray balloon)


def version_tuple(text):
    parts = re.findall(r'\d+', str(text).split('-')[0].split('+')[0])[:4]
    return tuple(int(p) for p in parts) or (0,)


def setup_url_ok(url):
    if os.environ.get('YTG_UPDATE_URL'):   # tests: a small local server plays the part of GitHub
        return url.startswith('http://127.0.0.1:')
    return url.startswith(SETUP_PREFIX) and url.endswith('.exe')


def install_supported():
    """One-click update: only the Windows app installed with its setup (Scoop, the sources, Linux and the Mac update their own way)."""
    return bool(FROZEN) and sys.platform == 'win32' and '\\scoop\\' not in sys.executable.lower()


def check_update():
    """Asks GitHub for the latest release (the only thing sent is this program's name and version). True if it worked."""
    req = urllib.request.Request(UPDATE_API, headers={'User-Agent': 'YTGrabber/' + APP_VERSION,
                                                      'Accept': 'application/vnd.github+json'})
    ok = False
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode('utf-8'))
        tag = str(d.get('tag_name') or '')
        if not re.fullmatch(r'v?\d+(\.\d+){1,3}', tag):
            raise ValueError('unexpected answer from the update server')
        url = str(d.get('html_url') or '')
        latest = tag.lstrip('v')
        UPDATE.update(latest=latest, error='', setup_url='', setup_sha='', setup_size=0,
                      url=url if url.startswith('https://github.com/progliodario/YT-Grabber/') else RELEASES_PAGE)
        for a in d.get('assets') or []:   # the Windows installer of this release, with the SHA-256 GitHub computed for it
            sha = str(a.get('digest') or '')
            if a.get('name') == 'YT-Grabber-Setup-%s.exe' % latest and sha.startswith('sha256:') and setup_url_ok(str(a.get('browser_download_url') or '')):
                UPDATE.update(setup_url=a['browser_download_url'], setup_sha=sha[7:].lower(), setup_size=int(a.get('size') or 0))
        ok = True
    except Exception as e:  # noqa: BLE001
        UPDATE['error'] = clean_msg(e)
    UPDATE['checked'] = time.time()
    return ok


def update_state():
    newer = bool(UPDATE['latest']) and version_tuple(UPDATE['latest']) > version_tuple(APP_VERSION)
    can_install = bool(newer and UPDATE['setup_url'] and UPDATE['setup_sha'] and install_supported())
    return {'latest': UPDATE['latest'], 'newer': newer, 'url': UPDATE['url'] if newer else '',
            'checked': UPDATE['checked'], 'error': UPDATE['error'], 'can_install': can_install, 'install': dict(UPDATE_INSTALL)}


def launch_installer(path):
    """Starts the downloaded setup so that it installs silently and starts the new version. It waits a few seconds: this program
    closes first (a running program cannot be replaced), and Setup is not a child of it, so it survives."""
    exe = os.path.abspath(sys.executable).lower()
    program_files = (os.environ.get('ProgramFiles') or '').lower()
    mode = '/ALLUSERS' if program_files and exe.startswith(program_files) else '/CURRENTUSER'   # keep the kind of installation it already has
    cmd = 'cmd /c ping -n 4 127.0.0.1 >nul & "%s" /SILENT /SUPPRESSMSGBOXES /NORESTART /RELAUNCH=1 %s' % (path, mode)
    subprocess.Popen(cmd, shell=True, creationflags=0x00000008 | 0x00000200, close_fds=True)


def run_update_install():
    """Downloads the new setup, checks it against the SHA-256 that GitHub published for it, starts it and closes this program."""
    st = UPDATE_INSTALL
    st.update(state='downloading', pct=0, error='')
    folder = None
    try:
        url, want, size = UPDATE['setup_url'], UPDATE['setup_sha'], UPDATE['setup_size']
        if not (url and want and setup_url_ok(url)):
            raise ValueError('There is no update to install.')
        folder = tempfile.mkdtemp(prefix='ytgrab_update_')
        path = os.path.join(folder, os.path.basename(url))
        digest = hashlib.sha256()
        got = 0
        req = urllib.request.Request(url, headers={'User-Agent': 'YTGrabber/' + APP_VERSION})
        with urllib.request.urlopen(req, timeout=60) as r, open(path, 'wb') as f:
            total = int(r.headers.get('Content-Length') or size or 0)
            while True:
                chunk = r.read(256 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                digest.update(chunk)
                got += len(chunk)
                st['pct'] = min(99, got * 100 // total) if total else 0
        if digest.hexdigest() != want:
            raise ValueError('The downloaded file does not match the checksum published for it: it was not installed.')
        st.update(state='installing', pct=100)
        launch_installer(path)
        shutdown_now(1.0, close_window=True)
    except Exception as e:  # noqa: BLE001
        log('update failed', e)
        st.update(state='error', error=clean_msg(e))
        if folder:
            shutil.rmtree(folder, ignore_errors=True)


def shutdown_now(delay=0.4, close_window=False):
    """Saves the list, stops the download processes and ends the program (after a short pause, so that the answer to the page gets out)."""
    def bye():
        time.sleep(delay)
        if close_window:   # the window of the Windows app: the new version opens one of its own
            try:
                sys.modules['winapp'].close_window()
            except Exception:
                pass
        MGR.save_dirty()
        for pr in list(PROCS):
            try:
                pr.kill()
            except Exception:
                pass
        os._exit(0)
    threading.Thread(target=bye, daemon=True).start()


def update_loop():
    """Checks for a new version shortly after the start and then twice a day (once an hour after a failure)."""
    time.sleep(45)
    while not SHUTDOWN.is_set():
        wait = 600
        if SETTINGS.get('check_updates') and time.time() - UPDATE['checked'] > (12 * 3600 if not UPDATE['error'] else 3600):
            check_update()
        time.sleep(wait)


def notify_finished(job):
    if not SETTINGS.get('notify_done'):
        return
    with LOCK:
        info = {'id': job.id, 'title': job.title or job.url, 'done': job.counts['d'], 'errors': job.counts['e'],
                'sub': bool(job.sub_id)}
    if not info['done'] and not info['errors']:
        return   # nothing new was downloaded (for example a subscription check without news)
    for hook in list(FINISH_HOOKS):
        try:
            hook(info)
        except Exception as e:  # noqa: BLE001
            log('notification hook failed', e)


LAST_ACTIVITY = [time.time()]   # last time somebody used the web page


def idle_watch(seconds):
    """For launchers without a window to close (AppImage, Flatpak): ends the program when it has nothing to do."""
    while not SHUTDOWN.is_set():
        time.sleep(30)
        with LOCK:
            busy = any(j.status in ('enumerating', 'running') and not j.paused for j in MANAGER_JOBS.values())
            subs = any(s.get('enabled') for s in SUBS.values())
        if busy or subs or time.time() - LAST_ACTIVITY[0] < seconds:
            continue
        log('idle for %d minutes: quitting' % (seconds // 60))
        MGR.save_dirty()
        for pr in list(PROCS):
            try:
                pr.kill()
            except Exception:
                pass
        os._exit(0)


def lan_address():
    """The address of this computer on the local network (no packet is actually sent), or '' if unknown."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip if not ip.startswith('127.') else ''
    except OSError:
        return ''


def already_running(port):
    try:
        with urllib.request.urlopen('http://127.0.0.1:%d/api/ping' % port, timeout=1.5) as r:
            return json.loads(r.read().decode()).get('app') == APP_NAME
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--dir', default=None, help='destination folder for downloads')
    ap.add_argument('--no-browser', action='store_true')
    ap.add_argument('--idle-exit', type=int, default=0, metavar='MINUTES',
                    help='quit when nothing is downloading and nobody has used the page for this many minutes '
                         '(ignored while subscriptions are active)')
    a = ap.parse_args()

    os.makedirs(DATA, exist_ok=True)
    load_settings()
    load_subs()
    if a.dir:
        SETTINGS['download_dir'] = os.path.abspath(a.dir)
        save_settings()

    if os.environ.get('YTG_RESTARTED'):
        # restart after an update: the previous copy is shutting down, wait for it to free the port
        for _ in range(60):
            if not already_running(a.port):
                break
            time.sleep(0.5)

    if already_running(a.port):
        url = 'http://localhost:%d/' % a.port
        print('YT Grabber is already running: opening', url)
        if not a.no_browser:
            open_browser(url)
        return

    srv = None
    port = a.port
    for p in range(a.port, a.port + 20):
        try:
            srv = Server((a.host, p), Handler)
            port = p
            break
        except OSError:
            continue
    if not srv:
        print('No free port found')
        sys.exit(1)
    srv.allow_remote = a.host not in ('127.0.0.1', 'localhost', '::1')

    MGR.load_jobs()
    MGR.start()
    threading.Thread(target=subs_loop, daemon=True, name='subs').start()
    threading.Thread(target=update_loop, daemon=True, name='updates').start()
    threading.Thread(target=ytdlp_auto_loop, daemon=True, name='ytdlp-auto').start()
    if a.idle_exit > 0:
        threading.Thread(target=idle_watch, args=(a.idle_exit * 60,), daemon=True, name='idle').start()
    atexit.register(MGR.save_dirty)

    url = 'http://localhost:%d/' % port
    print('=' * 60)
    print(' YT Grabber %s  -  yt-dlp %s' % (APP_VERSION, yt_dlp.version.__version__))
    print(' Open in the browser:  %s' % url)
    print(' Simultaneous downloads: %d   |   Folder: %s' % (CONCURRENCY, SETTINGS['download_dir']))
    if ANDROID_APP:
        print(' Android app: the server runs in a foreground service')
    elif IS_ANDROID:
        print(' Android (Termux): keep this window open while downloading')
    if FROZEN:
        print(' Data and settings: %s' % DATA_ROOT)
    if not HAVE_FFMPEG:
        print(' WARNING: ffmpeg not found - conversions not available')
    if srv.allow_remote:
        print(' WARNING: server reachable from other devices on the network')
        ip = lan_address()
        if ip:
            print(' From a phone or tablet on the same Wi-Fi, open:  http://%s:%d/' % (ip, port))
    print(' Press Ctrl+C to quit (downloads in progress can be resumed)')
    print('=' * 60)
    if not a.no_browser:
        threading.Timer(0.8, lambda: open_browser(url)).start()
    try:
        srv.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        pass
    finally:
        SHUTDOWN.set()
        with COND:
            COND.notify_all()
        MGR.save_dirty()
        for pr in list(PROCS):   # explicitly stop the workers (and their ffmpeg processes): no leftover processes
            try:
                pr.kill()
            except Exception:
                pass
        os._exit(0)


if __name__ == '__main__':
    main()
