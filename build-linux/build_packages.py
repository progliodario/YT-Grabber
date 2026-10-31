#!/usr/bin/env python3
"""Builds the Linux packages (.deb and .rpm) into the Linux\\ folder.

Works on Windows, Linux and macOS: it downloads nfpm (https://nfpm.goreleaser.com, checked against the
checksums published with the release) into generated\\nfpm\\, fills a staging folder and runs nfpm twice.
"""
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEN = os.path.join(ROOT, 'generated')
OUT = os.path.join(ROOT, 'Linux')
NFPM_VERSION = '2.48.0'
NFPM_BASE = 'https://github.com/goreleaser/nfpm/releases/download/v%s/' % NFPM_VERSION


def app_version():
    with open(os.path.join(ROOT, 'program', 'server.py'), encoding='utf-8') as f:
        return re.search(r"APP_VERSION\s*=\s*'([^']+)'", f.read()).group(1)


def nfpm_archive():
    system, machine = platform.system(), platform.machine().lower()
    arch = 'arm64' if machine in ('arm64', 'aarch64') else 'x86_64'
    if system == 'Windows':
        return 'nfpm_%s_Windows_%s.zip' % (NFPM_VERSION, arch), 'nfpm.exe'
    return 'nfpm_%s_%s_%s.tar.gz' % (NFPM_VERSION, 'Darwin' if system == 'Darwin' else 'Linux', arch), 'nfpm'


def get_nfpm():
    archive, exe = nfpm_archive()
    folder = os.path.join(GEN, 'nfpm', NFPM_VERSION)
    path = os.path.join(folder, exe)
    if os.path.exists(path):
        return path
    os.makedirs(folder, exist_ok=True)
    print('Downloading nfpm %s ...' % NFPM_VERSION)
    sums = urllib.request.urlopen(NFPM_BASE + 'checksums.txt', timeout=60).read().decode()
    want = dict(line.split()[::-1] for line in sums.splitlines() if line.strip())[archive]
    arc = os.path.join(folder, archive)
    urllib.request.urlretrieve(NFPM_BASE + archive, arc)
    with open(arc, 'rb') as f:
        got = hashlib.sha256(f.read()).hexdigest()
    if got != want:
        os.remove(arc)
        raise SystemExit('Checksum mismatch for %s: refusing to use it.' % archive)
    if archive.endswith('.zip'):
        with zipfile.ZipFile(arc) as z:
            z.extract(exe, folder)
    else:
        with tarfile.open(arc) as t:
            t.extract(exe, folder)
        os.chmod(path, 0o755)
    os.remove(arc)
    return path


def copy_text(src, dst):
    """Copies a text file with Unix line endings (the launcher and the .desktop file must not have CRLF)."""
    with open(src, 'rb') as f:
        data = f.read().replace(b'\r\n', b'\n')
    with open(dst, 'wb') as f:
        f.write(data)


def build_stage(stage):
    shutil.rmtree(stage, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, 'program'), os.path.join(stage, 'program'),
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    icons = os.path.join(ROOT, 'program', 'web', 'icons')
    shutil.copy(os.path.join(icons, 'icon-512.png'), os.path.join(stage, 'icon-512.png'))
    shutil.copy(os.path.join(icons, 'icon-192.png'), os.path.join(stage, 'icon-192.png'))
    for name in ('yt-grabber', 'yt-grabber.desktop', 'yt-grabber.service'):
        copy_text(os.path.join(HERE, name), os.path.join(stage, name))
    for name in ('README.md', 'LICENSE'):
        copy_text(os.path.join(ROOT, name), os.path.join(stage, name))
    shutil.copy(os.path.join(HERE, 'nfpm.yaml'), os.path.join(stage, 'nfpm.yaml'))


def main():
    version = app_version()
    nfpm = get_nfpm()
    stage = os.path.join(GEN, 'linux-stage')
    build_stage(stage)
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        if old.startswith('yt-grabber') and old.endswith(('.deb', '.rpm')):
            os.remove(os.path.join(OUT, old))
    env = dict(os.environ, VERSION=version)
    for fmt in ('deb', 'rpm'):
        subprocess.run([nfpm, 'package', '--config', 'nfpm.yaml', '--packager', fmt, '--target', OUT],
                       cwd=stage, env=env, check=True)
    print()
    print('Packages ready in:', OUT)
    for name in sorted(os.listdir(OUT)):
        print('  %s  (%.1f KB)' % (name, os.path.getsize(os.path.join(OUT, name)) / 1024))
    return 0


if __name__ == '__main__':
    sys.exit(main())
