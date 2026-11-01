"""Updates: new versions of YT Grabber itself (notice, one-click install on Windows) and automatic updates of yt-dlp.

This module does not know the server. The server hands over what it needs (see `hooks` and `configure`), so nothing here imports
`server` (which would load a second copy of it when it runs as a script).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

from ytcommon import ROOT, DATA, FROZEN, ANDROID_APP, atomic_write, clean_msg  # noqa: E402  (first: sets the paths and sys.path)
from ytsettings import SETTINGS  # noqa: E402
import yt_dlp  # noqa: E402


class _Hooks:
    """What the server provides: set by `configure`, replaced by the tests."""
    app_version = '0'
    stopping = threading.Event()                          # set when the program is ending

    @staticmethod
    def log(*args):
        pass

    @staticmethod
    def save():                                           # saves the list of downloads
        pass

    @staticmethod
    def shutdown(delay=0.4, close_window=False):          # saves everything and ends the program
        pass

    @staticmethod
    def restart_self():                                   # starts a new copy of the program (the exe) before this one ends
        pass

    @staticmethod
    def busy():                                           # True while something is being downloaded
        return False

    @staticmethod
    def last_post():                                      # when somebody last pressed something in the page
        return 0.0


hooks = _Hooks


def configure(**given):
    for name, value in given.items():
        setattr(hooks, name, value)


def version_tuple(text):
    parts = re.findall(r'\d+', str(text).split('-')[0].split('+')[0])[:4]
    return tuple(int(p) for p in parts) or (0,)


# --------------------------------------------------------------------------- new versions of YT Grabber

RELEASES_PAGE = 'https://github.com/progliodario/YT-Grabber/releases/latest'
UPDATE_API = os.environ.get('YTG_UPDATE_URL') or 'https://api.github.com/repos/progliodario/YT-Grabber/releases/latest'
UPDATE = {'checked': 0, 'latest': '', 'url': '', 'error': '', 'setup_url': '', 'setup_sha': '', 'setup_size': 0}
UPDATE_INSTALL = {'state': 'idle', 'pct': 0, 'error': ''}   # one-click update: idle | downloading | installing | error
SETUP_PREFIX = 'https://github.com/progliodario/YT-Grabber/releases/download/'


def setup_url_ok(url):
    if os.environ.get('YTG_UPDATE_URL'):   # tests: a small local server plays the part of GitHub
        return url.startswith('http://127.0.0.1:')
    return url.startswith(SETUP_PREFIX) and url.endswith('.exe')


def install_supported():
    """One-click update: only the Windows app installed with its setup (Scoop, the sources, Linux and the Mac update their own way)."""
    return bool(FROZEN) and sys.platform == 'win32' and '\\scoop\\' not in sys.executable.lower()


def check_update():
    """Asks GitHub for the latest release (the only thing sent is this program's name and version). True if it worked."""
    req = urllib.request.Request(UPDATE_API, headers={'User-Agent': 'YTGrabber/' + hooks.app_version,
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
    newer = bool(UPDATE['latest']) and version_tuple(UPDATE['latest']) > version_tuple(hooks.app_version)
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
        req = urllib.request.Request(url, headers={'User-Agent': 'YTGrabber/' + hooks.app_version})
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
        hooks.shutdown(1.0, close_window=True)
    except Exception as e:  # noqa: BLE001
        hooks.log('update failed', e)
        st.update(state='error', error=clean_msg(e))
        if folder:
            shutil.rmtree(folder, ignore_errors=True)


def update_loop():
    """Checks for a new version shortly after the start and then twice a day (once an hour after a failure)."""
    time.sleep(45)
    while not hooks.stopping.is_set():
        if SETTINGS.get('check_updates') and time.time() - UPDATE['checked'] > (12 * 3600 if not UPDATE['error'] else 3600):
            check_update()
        time.sleep(600)


# --------------------------------------------------------------------------- automatic updates of yt-dlp

YTDLP_API = os.environ.get('YTG_YTDLP_API') or 'https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest'
YTDLP_AUTO = {'checked': 0, 'latest': '', 'error': ''}
YTDLP_TRIES = os.path.join(DATA, 'ytdlp-auto.json')   # {"target": version, "time": when}: what was installed last, to never repeat it in a loop
YTDLP_QUIET = 120     # seconds without a click in the page before the program may restart by itself


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
    hooks.save()

    def later():
        time.sleep(1.0)
        hooks.save()
        if FROZEN:
            hooks.restart_self()
        os._exit(75)  # the launcher (Start.bat / Android app) restarts the server
    threading.Thread(target=later, daemon=True).start()


def ytdlp_decision(current, latest, tried, now):
    """What the automatic update should do: 'none' (up to date), 'wait' (it already tried this version in the last 24 hours) or 'update'."""
    if not latest or version_tuple(latest) <= version_tuple(current):
        return 'none'
    if tried and tried.get('target') == latest and now - float(tried.get('time') or 0) < 24 * 3600:
        return 'wait'
    return 'update'


def ytdlp_latest():
    """The version number of the latest yt-dlp release, from GitHub."""
    req = urllib.request.Request(YTDLP_API, headers={'User-Agent': 'YTGrabber/' + hooks.app_version, 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=20) as r:
        tag = str(json.loads(r.read().decode('utf-8')).get('tag_name') or '')
    if not re.fullmatch(r'\d{4}\.\d{2}\.\d{2}(\.\d+)?', tag):
        raise ValueError('unexpected answer from GitHub')
    return tag


def ytdlp_idle():
    """True when nothing is downloading and nobody is using the page, so that restarting costs nothing."""
    return not hooks.busy() and time.time() - hooks.last_post() > YTDLP_QUIET


def ytdlp_auto_loop():
    """Once a day: if there is a newer yt-dlp, installs it as soon as nothing is downloading, and restarts the program."""
    time.sleep(90)
    while not hooks.stopping.is_set():
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
                    hooks.log('yt-dlp %s -> %s (automatic update)' % (yt_dlp.version.__version__, YTDLP_AUTO['latest']))
                    atomic_write(YTDLP_TRIES, json.dumps({'target': YTDLP_AUTO['latest'], 'time': time.time()}))
                    install_ytdlp()
                    restart_program()
                    return
        except Exception as e:  # noqa: BLE001
            YTDLP_AUTO.update(error=clean_msg(e), checked=time.time())
            hooks.log('automatic yt-dlp update failed', e)
        time.sleep(300)
