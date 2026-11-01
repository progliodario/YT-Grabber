#!/usr/bin/env python3
"""Prepares the required tools (only once): yt-dlp, JS runtime (deno) and ffmpeg.

Run automatically by Start.bat / Start.sh. It can also be run by hand:
    python program/setup_tools.py            # installs what is missing
    python program/setup_tools.py --update   # also updates yt-dlp
"""
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from ytcommon import IS_ANDROID, BIN, DENO, VENDOR  # noqa: E402

EXE = '.exe' if os.name == 'nt' else ''
BASE = 'https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/'
DENO_URL = 'https://github.com/denoland/deno/releases/latest/download/deno-%s-pc-windows-msvc.zip'
MAC_FFMPEG_URL = 'https://www.osxexperts.net/%s%s.zip'   # (ffmpeg|ffprobe) + (7arm|7intel)
# On Android (Termux) there is no deno and no packages to compile: these are enough, all pure Python.
ANDROID_PKGS = ['yt-dlp', 'yt-dlp-ejs', 'mutagen', 'requests', 'urllib3', 'websockets', 'certifi']


def say(msg):
    print('[setup] ' + msg, flush=True)


def download(url, dest, progress=None, tries=3):
    """urlretrieve with retries: a connection that drops half way (weak Wi-Fi, a busy server) must not stop the setup."""
    for attempt in range(1, tries + 1):
        try:
            return urllib.request.urlretrieve(url, dest, progress)
        except Exception as e:  # noqa: BLE001
            if attempt == tries:
                raise
            say('Download interrupted (%s): trying again (%d of %d)...' % (e, attempt + 1, tries))
            time.sleep(3 * attempt)


def deps_ok():
    if not os.path.isdir(os.path.join(VENDOR, 'yt_dlp')):
        return False
    if IS_ANDROID:
        return True
    return os.path.exists(os.path.join(VENDOR, 'bin', 'deno' + EXE))


def install_python_deps():
    say('Installing yt-dlp%s (about 1 minute)...' % ('' if IS_ANDROID else ' and the JavaScript runtime'))
    pkgs = ANDROID_PKGS if IS_ANDROID else ['yt-dlp[default]', 'deno']
    cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade', '--disable-pip-version-check', '--target', VENDOR] + pkgs
    env = dict(os.environ)
    env['PIP_BREAK_SYSTEM_PACKAGES'] = '1'   # Termux's Python is "externally managed" (PEP 668)
    r = subprocess.run(cmd, env=env)
    if r.returncode != 0:
        say('ERROR: yt-dlp installation failed. Check your Internet connection and try again.')
        return False
    return True


def ffmpeg_ok():
    return os.path.exists(os.path.join(BIN, 'ffmpeg' + EXE)) or bool(shutil.which('ffmpeg'))


def install_termux_pkg(name):
    say('Installing %s with pkg...' % name)
    r = subprocess.run(['pkg', 'install', '-y', name])
    return r.returncode == 0


def install_ffmpeg_macos(arm):
    """macOS: static ffmpeg and ffprobe builds from OSXExperts (osxexperts.net), one zip each."""
    suffix = '7arm' if arm else '7intel'
    say('Downloading ffmpeg and ffprobe (about 45 MB, only once)...')
    os.makedirs(BIN, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='ytgrab_ffmpeg_')
    try:
        for tool in ('ffmpeg', 'ffprobe'):
            arc = os.path.join(tmp, tool + '.zip')
            download(MAC_FFMPEG_URL % (tool, suffix), arc)
            with zipfile.ZipFile(arc) as z:
                member = next((m for m in z.namelist() if os.path.basename(m) == tool and '__MACOSX' not in m), None)
                if not member:
                    say('ERROR: %s not found in the downloaded archive.' % tool)
                    return False
                dst = os.path.join(BIN, tool)
                with z.open(member) as src, open(dst, 'wb') as out:
                    shutil.copyfileobj(src, out)
                os.chmod(dst, 0o755)
        say('ffmpeg installed.')
        return True
    except Exception as e:  # noqa: BLE001
        say('ERROR downloading ffmpeg: %s. You can also install it with:  brew install ffmpeg' % e)
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def use_bundled_certificates():
    """Python builds that do not use the system certificate store (e.g. the one inside the macOS app) can verify
    HTTPS with the certifi bundle that was just installed together with yt-dlp."""
    ca = os.path.join(VENDOR, 'certifi', 'cacert.pem')
    if os.path.exists(ca) and not os.environ.get('SSL_CERT_FILE'):
        os.environ['SSL_CERT_FILE'] = ca


def install_ffmpeg():
    if IS_ANDROID:
        return install_termux_pkg('ffmpeg')
    system = platform.system()
    machine = platform.machine().lower()
    arm = machine in ('arm64', 'aarch64')
    if system == 'Windows':
        name = 'ffmpeg-master-latest-winarm64-gpl.zip' if arm else 'ffmpeg-master-latest-win64-gpl.zip'
    elif system == 'Linux':
        name = 'ffmpeg-master-latest-linuxarm64-gpl.tar.xz' if arm else 'ffmpeg-master-latest-linux64-gpl.tar.xz'
    elif system == 'Darwin':
        return install_ffmpeg_macos(arm)
    else:
        say('ffmpeg not found. Install it with your package manager.')
        return False
    say('Downloading ffmpeg (about 190 MB, only once)...')
    os.makedirs(BIN, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='ytgrab_ffmpeg_')
    try:
        arc = os.path.join(tmp, name)
        last = [0]

        def prog(blocks, bs, total):
            if total > 0:
                pct = min(100, blocks * bs * 100 // total)
                if pct >= last[0] + 10:
                    last[0] = pct
                    say('  %d%%' % pct)
        download(BASE + name, arc, prog)
        want = ('ffmpeg' + EXE, 'ffprobe' + EXE)
        found = 0
        if name.endswith('.zip'):
            with zipfile.ZipFile(arc) as z:
                for m in z.namelist():
                    base = os.path.basename(m)
                    if base in want and '/bin/' in m:
                        with z.open(m) as src, open(os.path.join(BIN, base), 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                        found += 1
        else:
            with tarfile.open(arc) as t:
                for m in t.getmembers():
                    base = os.path.basename(m.name)
                    if base in want and '/bin/' in m.name and m.isfile():
                        with t.extractfile(m) as src, open(os.path.join(BIN, base), 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                        os.chmod(os.path.join(BIN, base), 0o755)
                        found += 1
        if found < 1:
            say('ERROR: ffmpeg not found in the downloaded archive.')
            return False
        say('ffmpeg installed.')
        return True
    except Exception as e:  # noqa: BLE001
        say('ERROR downloading ffmpeg: %s' % e)
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def install_deno():
    """yt-dlp JavaScript runtime (only needed on the fallback path): the exe has no pip, so it is downloaded separately."""
    arch = 'aarch64' if platform.machine().lower() in ('arm64', 'aarch64') else 'x86_64'
    say('Downloading the JavaScript runtime (about 40 MB, only once)...')
    os.makedirs(BIN, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='ytgrab_deno_')
    try:
        arc = os.path.join(tmp, 'deno.zip')
        download(DENO_URL % arch, arc)
        with zipfile.ZipFile(arc) as z:
            with z.open('deno.exe') as src, open(DENO, 'wb') as dst:
                shutil.copyfileobj(src, dst)
        say('JavaScript runtime installed.')
        return True
    except Exception as e:  # noqa: BLE001
        say('JavaScript runtime not installed (%s): the fast path works anyway.' % e)
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def ensure_frozen_tools():
    """For YT-Grabber.exe: ffmpeg (required) and deno (optional) are downloaded on first start."""
    ok = True
    if not ffmpeg_ok():
        ok = install_ffmpeg()
    if os.name == 'nt' and not os.path.exists(DENO):
        install_deno()
    return ok


def main():
    update = '--update' in sys.argv
    ok = True
    if update or not deps_ok():
        ok = install_python_deps() and ok
    use_bundled_certificates()
    if not ffmpeg_ok():
        ok = install_ffmpeg() and ok
    if IS_ANDROID and not shutil.which('node'):
        install_termux_pkg('nodejs')   # optional: only needed on yt-dlp's fallback path
    if ok:
        say('All set.')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
