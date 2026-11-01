#!/usr/bin/env python3
"""Sets the version of YT Grabber in every file that carries it, so that they can never disagree.

    python tools/bump_version.py 1.4.0

Files changed:
  program/server.py                                  APP_VERSION (shown in the page, used by the update check)
  packaging/windows/version.txt                      the version shown by Windows in the exe's properties
  packaging/linux/flatpak/*.metainfo.xml             a <release> entry for the software centres
  packaging/android/app/build.gradle.kts             versionName and versionCode (must grow with every release)
  CHANGELOG.md                                       checks that the version has a section (write it yourself)

Afterwards run the tests (python -m unittest discover -s tests), commit, push, wait for CI and push the tag.
See docs/development.md for the whole release procedure.
"""
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path(*parts):
    return os.path.join(ROOT, *parts)


def read(p):
    with open(p, 'rb') as f:
        raw = f.read()
    return raw.decode('utf-8-sig'), raw.startswith(b'\xef\xbb\xbf')


def write(p, text, bom=False):
    with open(p, 'wb') as f:
        f.write((b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8'))


def sub_once(text, pattern, repl, what):
    new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        raise SystemExit('Could not find %s' % what)
    return new


def main(argv):
    if len(argv) != 2 or not re.fullmatch(r'\d+\.\d+\.\d+', argv[1]):
        raise SystemExit(__doc__)
    version = argv[1]
    major, minor, patch = (int(x) for x in version.split('.'))
    code = major * 10000 + minor * 100 + patch

    p = path('program', 'server.py')
    text, bom = read(p)
    write(p, sub_once(text, r"^APP_VERSION = '[^']*'", "APP_VERSION = '%s'" % version, 'APP_VERSION in server.py'), bom)

    p = path('packaging', 'windows', 'version.txt')
    text, _ = read(p)   # PyInstaller wants exactly one byte-order mark at the start
    text = sub_once(text, r'filevers=\([\d, ]+\)', 'filevers=(%d, %d, %d, 0)' % (major, minor, patch), 'filevers')
    text = sub_once(text, r'prodvers=\([\d, ]+\)', 'prodvers=(%d, %d, %d, 0)' % (major, minor, patch), 'prodvers')
    text = sub_once(text, r"StringStruct\('FileVersion', '[^']*'\)", "StringStruct('FileVersion', '%s')" % version, 'FileVersion')
    text = sub_once(text, r"StringStruct\('ProductVersion', '[^']*'\)", "StringStruct('ProductVersion', '%s')" % version, 'ProductVersion')
    write(p, text, bom=True)

    p = path('packaging', 'linux', 'flatpak', 'io.github.progliodario.YTGrabber.metainfo.xml')
    text, bom = read(p)
    if 'version="%s"' % version not in text:
        entry = '    <release version="%s" date="%s"/>\n' % (version, datetime.date.today().isoformat())
        text = sub_once(text, r'^(\s*)<release ', lambda m: entry + m.group(0), 'the first <release> in the metainfo')
        write(p, text, bom)

    p = path('packaging', 'android', 'app', 'build.gradle.kts')
    text, bom = read(p)
    text = sub_once(text, r'versionCode = \d+[^\n]*', 'versionCode = %d   // %s: must grow with every release, or Android refuses to update the installed app' % (code, version), 'versionCode')
    text = sub_once(text, r'versionName = "[^"]*"', 'versionName = "%s"' % version, 'versionName')
    write(p, text, bom)

    text, _ = read(path('CHANGELOG.md'))
    if not re.search(r'^## %s\b' % re.escape(version), text, flags=re.M):
        print('NOTE: CHANGELOG.md has no "## %s" section yet: add it before releasing.' % version)
    print('Version set to %s (Android versionCode %d).' % (version, code))
    print('Next: python -m unittest discover -s tests, commit, push, and when CI is green push the tag v%s.' % version)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
