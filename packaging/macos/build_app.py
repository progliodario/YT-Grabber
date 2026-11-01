#!/usr/bin/env python3
"""Builds YT-Grabber.app for macOS (Intel and Apple Silicon) and zips it into dist\\macos\\YT-Grabber-macOS.zip.

It runs on Windows, Linux or macOS. The app is a folder of files, so no Mac is needed to assemble it:
  - program\\           the YT Grabber program (copied from the repository)
  - python-arm64\\, python-x86_64\\   portable Python 3.12 from python-build-standalone (checked against the
                      SHA256SUMS published with the release), copied straight from the downloaded archives into
                      the zip so that symbolic links and file permissions are kept
  - run.sh, launcher  start scripts; icon.icns, Info.plist
yt-dlp, the JavaScript runtime and ffmpeg are downloaded on first start into ~/Library/Application Support/YT-Grabber.
"""
import hashlib
import os
import re
import stat
import struct
import sys
import tarfile
import time
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(ROOT, 'generated', 'macos-cache')
OUT = os.path.join(ROOT, 'dist', 'macos')

PBS_TAG = '20261026'
PY_VERSION = '3.12.16'
PBS_BASE = 'https://github.com/astral-sh/python-build-standalone/releases/download/%s/' % PBS_TAG
ARCHS = {'arm64': 'aarch64', 'x86_64': 'x86_64'}      # folder suffix -> name used by python-build-standalone
APP = 'YT-Grabber.app/'

PLIST = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>YT Grabber</string>
  <key>CFBundleDisplayName</key><string>YT Grabber</string>
  <key>CFBundleIdentifier</key><string>io.github.progliodario.ytgrabber</string>
  <key>CFBundleVersion</key><string>{version}</string>
  <key>CFBundleShortVersionString</key><string>{version}</string>
  <key>CFBundleExecutable</key><string>launcher</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
  <key>LSMinimumSystemVersion</key><string>10.15</string>
  <key>LSApplicationCategoryType</key><string>public.app-category.video</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
'''


def app_version():
    with open(os.path.join(ROOT, 'program', 'server.py'), encoding='utf-8') as f:
        return re.search(r"APP_VERSION\s*=\s*'([^']+)'", f.read()).group(1)


def download(url, dest):
    print('Downloading %s ...' % os.path.basename(dest))
    urllib.request.urlretrieve(url, dest)


def get_python(arch):
    """Returns the path of the verified python-build-standalone archive for this architecture."""
    os.makedirs(CACHE, exist_ok=True)
    name = 'cpython-%s+%s-%s-apple-darwin-install_only.tar.gz' % (PY_VERSION, PBS_TAG, ARCHS[arch])
    sums_path = os.path.join(CACHE, 'SHA256SUMS-%s' % PBS_TAG)
    if not os.path.exists(sums_path):
        download(PBS_BASE + 'SHA256SUMS', sums_path)
    with open(sums_path, encoding='utf-8') as f:
        want = dict(line.split()[::-1] for line in f if line.strip())[name]
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        download(PBS_BASE + name.replace('+', '%2B'), path)
    with open(path, 'rb') as f:
        if hashlib.sha256(f.read()).hexdigest() != want:
            os.remove(path)
            raise SystemExit('Checksum mismatch for %s: refusing to use it.' % name)
    return path


def make_icns(png_path):
    """icon.icns with a single 512x512 PNG entry ('ic09'), which macOS scales for every size."""
    with open(png_path, 'rb') as f:
        png = f.read()
    chunk = b'ic09' + struct.pack('>I', len(png) + 8) + png
    return b'icns' + struct.pack('>I', len(chunk) + 8) + chunk


class AppZip:
    def __init__(self, path):
        self.z = zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9)
        self.now = time.localtime()[:6]

    def _info(self, arc, mode):
        info = zipfile.ZipInfo(arc, self.now)
        info.create_system = 3
        info.external_attr = mode << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        return info

    def dir(self, arc):
        self.z.writestr(self._info(arc.rstrip('/') + '/', stat.S_IFDIR | 0o755), b'')

    def file(self, arc, data, executable=False):
        self.z.writestr(self._info(arc, stat.S_IFREG | (0o755 if executable else 0o644)), data)

    def symlink(self, arc, target):
        self.z.writestr(self._info(arc, stat.S_IFLNK | 0o755), target.encode())

    def close(self):
        self.z.close()


def text_bytes(path):
    with open(path, 'rb') as f:
        return f.read().replace(b'\r\n', b'\n')


def add_program(z):
    base = os.path.join(ROOT, 'program')
    for folder, dirs, files in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d != '__pycache__')
        rel = os.path.relpath(folder, base).replace(os.sep, '/')
        arc_dir = APP + 'Contents/Resources/program' + ('' if rel == '.' else '/' + rel)
        z.dir(arc_dir)
        for fn in sorted(files):
            if fn.endswith('.pyc'):
                continue
            with open(os.path.join(folder, fn), 'rb') as f:
                z.file(arc_dir + '/' + fn, f.read())


def skip_python_member(name):
    parts = name.split('/')
    return ('__pycache__' in parts or 'test' in parts or 'idlelib' in parts or 'tests' in parts
            or name.endswith('.a'))


def add_python(z, arch):
    root = APP + 'Contents/Resources/python-%s' % arch
    z.dir(root)
    with tarfile.open(get_python(arch)) as t:
        for m in t.getmembers():
            rel = m.name.split('/', 1)[1] if '/' in m.name else ''
            if not rel or skip_python_member(rel):
                continue
            arc = root + '/' + rel
            if m.isdir():
                z.dir(arc)
            elif m.issym():
                z.symlink(arc, m.linkname)
            elif m.isfile() or m.islnk():
                z.file(arc, t.extractfile(m).read(), executable=bool(m.mode & 0o111))


def main():
    version = app_version()
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, 'YT-Grabber-macOS.zip')
    z = AppZip(out)
    z.dir(APP)
    z.dir(APP + 'Contents')
    z.file(APP + 'Contents/Info.plist', PLIST.format(version=version).encode())
    z.dir(APP + 'Contents/MacOS')
    z.file(APP + 'Contents/MacOS/launcher', text_bytes(os.path.join(HERE, 'launcher')), executable=True)
    z.dir(APP + 'Contents/Resources')
    z.file(APP + 'Contents/Resources/icon.icns', make_icns(os.path.join(ROOT, 'program', 'web', 'icons', 'icon-512.png')))
    z.file(APP + 'Contents/Resources/run.sh', text_bytes(os.path.join(HERE, 'run.sh')), executable=True)
    add_program(z)
    for arch in ARCHS:
        add_python(z, arch)
    z.close()
    print()
    print('App ready: %s  (%.1f MB)' % (out, os.path.getsize(out) / 1048576))
    return 0


if __name__ == '__main__':
    sys.exit(main())
