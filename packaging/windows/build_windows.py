#!/usr/bin/env python3
"""Builds the Windows installer: dist\\windows\\YT-Grabber-Setup-<version>.exe

  1. the app (windowed, packaged with PyInstaller as a folder)     -> generated\\exe-build\\dist\\YT-Grabber\\
  2. the installer that contains it (Inno Setup)                   -> dist\\windows\\

Needs Python and Inno Setup 6 (https://jrsoftware.org/isdl.php, or:  winget install JRSoftware.InnoSetup).
PyInstaller and yt-dlp are fetched automatically the first time.
"""
import os
import re
import shutil
import subprocess
import sys

PYINSTALLER_VERSION = '6.22.3'   # used when the launcher is compiled from source (YTG_PYINSTALLER_FROM_SOURCE=1)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, 'program')
GEN = os.path.join(ROOT, 'generated')
OUT = os.path.join(GEN, 'exe-build')
INSTALLER_DIR = os.path.join(ROOT, 'dist', 'windows')


def run(cmd, **kw):
    print('>', ' '.join('"%s"' % c if ' ' in c else c for c in cmd))
    subprocess.run(cmd, check=True, **kw)


def app_version():
    with open(os.path.join(SRC, 'server.py'), encoding='utf-8') as f:
        return re.search(r"APP_VERSION\s*=\s*'([^']+)'", f.read()).group(1)


def find_iscc():
    candidates = []
    if os.environ.get('INNO_SETUP_DIR'):
        candidates.append(os.path.join(os.environ['INNO_SETUP_DIR'], 'ISCC.exe'))
    for base in (os.environ.get('LOCALAPPDATA'), os.environ.get('ProgramFiles(x86)'), os.environ.get('ProgramFiles')):
        if base:
            candidates.append(os.path.join(base, 'Programs', 'Inno Setup 6', 'ISCC.exe'))
            candidates.append(os.path.join(base, 'Inno Setup 6', 'ISCC.exe'))
    for c in candidates:
        if os.path.isfile(c):
            return c
    raise SystemExit('Inno Setup 6 was not found. Install it (winget install JRSoftware.InnoSetup) or set INNO_SETUP_DIR.')


def build_exe():
    py = sys.executable
    if not os.path.isdir(os.path.join(GEN, 'vendor', 'yt_dlp')):
        run([py, os.path.join(SRC, 'setup_tools.py')])
    pyi = os.path.join(OUT, 'pyinstaller')
    if not os.path.isdir(os.path.join(pyi, 'PyInstaller')):
        target = 'pyinstaller'
        if os.environ.get('YTG_PYINSTALLER_FROM_SOURCE'):
            # Compile PyInstaller's small launcher on this machine (it needs a C compiler: Visual Studio) instead of
            # using the prebuilt one, which many antivirus programs flag. Installing from a git checkout builds it.
            checkout = os.path.join(OUT, 'pyinstaller-src')
            shutil.rmtree(checkout, ignore_errors=True)
            run(['git', 'clone', '--quiet', '--depth', '1', '--branch', 'v' + PYINSTALLER_VERSION,
                 'https://github.com/pyinstaller/pyinstaller.git', checkout])
            target = checkout
        run([py, '-m', 'pip', 'install', '--disable-pip-version-check', '--target', pyi, target])
    icon = os.path.join(HERE, 'icon.ico')
    if not os.path.exists(icon):
        run([py, os.path.join(HERE, 'make_icon.py')])
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([pyi, os.path.join(GEN, 'vendor')]))
    # One folder instead of a single file: an installed app does not need to unpack itself at every start
    run([py, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--noconsole', '--name', 'YT-Grabber',
         '--icon', icon, '--version-file', os.path.join(HERE, 'version.txt'),
         '--distpath', os.path.join(OUT, 'dist'), '--workpath', os.path.join(OUT, 'work'), '--specpath', OUT,
         '--paths', SRC, '--paths', HERE, '--paths', os.path.join(GEN, 'vendor'),
         '--add-data', SRC + os.sep + 'web' + os.pathsep + 'web',
         '--add-data', icon + os.pathsep + '.',
         '--hidden-import', 'server', '--hidden-import', 'ytworker', '--hidden-import', 'ytcommon',
         '--hidden-import', 'setup_tools', '--hidden-import', 'winapp', '--hidden-import', 'winlang',
         '--collect-all', 'yt_dlp', '--collect-all', 'yt_dlp_ejs', '--collect-all', 'certifi',
         '--hidden-import', 'mutagen', '--hidden-import', 'websockets', '--hidden-import', 'requests',
         '--hidden-import', 'brotli', '--hidden-import', 'Cryptodome',
         '--exclude-module', 'pytest', '--exclude-module', 'unittest', '--exclude-module', 'pydoc',
         os.path.join(HERE, 'exe_main.py')], env=env)
    return os.path.join(OUT, 'dist', 'YT-Grabber')


def folder_size(path):
    return sum(os.path.getsize(os.path.join(b, f)) for b, _, files in os.walk(path) for f in files)


def build_installer(app_dir, version):
    os.makedirs(INSTALLER_DIR, exist_ok=True)
    for old in os.listdir(INSTALLER_DIR):
        if old.startswith('YT-Grabber-Setup-') and old.endswith('.exe'):
            os.remove(os.path.join(INSTALLER_DIR, old))
    run([find_iscc(), '/Qp', '/DAppVersion=' + version, '/DSourceDir=' + app_dir,
         '/DIconFile=' + os.path.join(HERE, 'icon.ico'), '/DLicenseFile=' + os.path.join(ROOT, 'LICENSE'),
         '/DOutDir=' + INSTALLER_DIR, os.path.join(HERE, 'installer.iss')])
    return os.path.join(INSTALLER_DIR, 'YT-Grabber-Setup-%s.exe' % version)


def main():
    if os.name != 'nt':
        raise SystemExit('The Windows installer can only be built on Windows.')
    version = app_version()
    app_dir = build_exe()
    setup = build_installer(app_dir, version)
    print()
    print('DONE')
    print('  app:        %s  (%.1f MB unpacked)' % (app_dir, folder_size(app_dir) / 1048576))
    print('  installer:  %s  (%.1f MB)' % (setup, os.path.getsize(setup) / 1048576))
    return 0


if __name__ == '__main__':
    sys.exit(main())
