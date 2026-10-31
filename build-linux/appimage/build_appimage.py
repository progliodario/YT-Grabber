#!/usr/bin/env python3
"""Builds the AppImage files (x86_64 and aarch64) into the Linux/ folder. Run it on Linux (it needs mksquashfs via appimagetool).

  python3 build-linux/appimage/build_appimage.py [x86_64] [aarch64]

Each AppImage is one file that bundles a portable Python 3.12 (python-build-standalone, checked against the
SHA256SUMS published with the release) and the program. yt-dlp and ffmpeg are fetched on first start into
~/.local/share/yt-grabber, like in the .deb and .rpm packages.
"""
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GEN = os.path.join(ROOT, 'generated')
OUT = os.path.join(ROOT, 'Linux')
PBS_TAG, PY_VERSION = '20261026', '3.12.16'
PBS_BASE = 'https://github.com/astral-sh/python-build-standalone/releases/download/%s/' % PBS_TAG
TOOL_URL = 'https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage'
TOOL_API = 'https://api.github.com/repos/AppImage/appimagetool/releases/tags/continuous'
PBS_ARCH = {'x86_64': 'x86_64', 'aarch64': 'aarch64'}


def download(url, dest):
    print('Downloading', os.path.basename(dest))
    urllib.request.urlretrieve(url, dest)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def get_python(arch):
    cache = os.path.join(GEN, 'appimage-cache')
    os.makedirs(cache, exist_ok=True)
    name = 'cpython-%s+%s-%s-unknown-linux-gnu-install_only.tar.gz' % (PY_VERSION, PBS_TAG, PBS_ARCH[arch])
    sums = os.path.join(cache, 'SHA256SUMS-%s' % PBS_TAG)
    if not os.path.exists(sums):
        download(PBS_BASE + 'SHA256SUMS', sums)
    with open(sums, encoding='utf-8') as f:
        want = dict(line.split()[::-1] for line in f if line.strip())[name]
    path = os.path.join(cache, name)
    if not os.path.exists(path):
        download(PBS_BASE + name.replace('+', '%2B'), path)
    if sha256(path) != want:
        os.remove(path)
        raise SystemExit('Checksum mismatch for %s: refusing to use it.' % name)
    return path


def get_tool():
    """appimagetool (it runs on the build machine, which is x86_64), checked against the digest GitHub reports."""
    cache = os.path.join(GEN, 'appimage-cache')
    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, 'appimagetool-x86_64.AppImage')
    if not os.path.exists(path):
        download(TOOL_URL, path)
    with urllib.request.urlopen(TOOL_API, timeout=60) as r:
        assets = json.loads(r.read().decode())['assets']
    want = next(a['digest'] for a in assets if a['name'] == 'appimagetool-x86_64.AppImage').split(':', 1)[1]
    if sha256(path) != want:
        os.remove(path)
        raise SystemExit('Checksum mismatch for appimagetool: refusing to use it.')
    os.chmod(path, 0o755)
    return path


def build(arch, tool):
    app = os.path.join(GEN, 'appdir-' + arch)
    shutil.rmtree(app, ignore_errors=True)
    os.makedirs(os.path.join(app, 'usr', 'share', 'yt-grabber'))
    with tarfile.open(get_python(arch)) as t:
        t.extractall(app)   # the archive has a top-level "python" folder
    os.rename(os.path.join(app, 'python'), os.path.join(app, 'usr', 'python'))
    shutil.copytree(os.path.join(ROOT, 'program'), os.path.join(app, 'usr', 'share', 'yt-grabber', 'program'),
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy(os.path.join(HERE, 'AppRun'), os.path.join(app, 'AppRun'))
    os.chmod(os.path.join(app, 'AppRun'), 0o755)
    shutil.copy(os.path.join(HERE, 'yt-grabber.desktop'), os.path.join(app, 'yt-grabber.desktop'))
    shutil.copy(os.path.join(ROOT, 'program', 'web', 'icons', 'icon-512.png'), os.path.join(app, 'yt-grabber.png'))
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, 'YT-Grabber-%s.AppImage' % arch)
    env = dict(os.environ, ARCH=arch, APPIMAGE_EXTRACT_AND_RUN='1')
    subprocess.run([tool, app, out], check=True, env=env)
    os.chmod(out, os.stat(out).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print('Built %s (%.1f MB)' % (out, os.path.getsize(out) / 1048576))


def main():
    archs = [a for a in sys.argv[1:] if a in PBS_ARCH] or list(PBS_ARCH)
    if not sys.platform.startswith('linux'):
        raise SystemExit('Build the AppImage on Linux (GitHub Actions does it for the releases).')
    tool = get_tool()
    for arch in archs:
        build(arch, tool)
    return 0


if __name__ == '__main__':
    sys.exit(main())
