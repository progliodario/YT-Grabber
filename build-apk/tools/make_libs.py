#!/usr/bin/env python3
"""Prepares the Python packages bundled in the APK (build-apk/app/src/main/assets/ytg-libs.zip).

They are all pure Python (no compiled code): the same for every Android processor. The app extracts them and
adds them to Python's path. Run this script again to bundle a newer yt-dlp.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'app', 'src', 'main', 'assets', 'ytg-libs.zip')
PKGS = ['yt-dlp', 'yt-dlp-ejs', 'mutagen', 'requests', 'urllib3', 'idna', 'charset-normalizer', 'certifi', 'websockets']


def main():
    tmp = tempfile.mkdtemp(prefix='ytg_libs_')
    try:
        target = os.path.join(tmp, 'site')
        cmd = [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', '--no-deps', '--target', target,
               '--platform', 'any', '--python-version', '3.12', '--implementation', 'py', '--only-binary=:all:'] + PKGS
        print(' '.join(cmd))
        if subprocess.run(cmd).returncode != 0:
            print('ERROR: pip could not download the packages.')
            return 1
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        n = 0
        with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for base, dirs, files in os.walk(target):
                dirs[:] = [d for d in dirs if d != '__pycache__' and d != 'bin']
                for fn in sorted(files):
                    if fn.endswith(('.pyc', '.pyd', '.exe')):
                        continue
                    full = os.path.join(base, fn)
                    z.write(full, os.path.relpath(full, target).replace(os.sep, '/'))
                    n += 1
        print('Created %s: %d files, %.1f MB' % (os.path.normpath(OUT), n, os.path.getsize(OUT) / 1048576))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
