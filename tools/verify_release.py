#!/usr/bin/env python3
"""Checks a published release from the outside, the way a user would: signature, checksums, build attestation, apt repository.

    python tools/verify_release.py 1.6.1

Needs the GitHub CLI (`gh`, signed in) and GnuPG (`gpg`; with Git for Windows it is in C:\\Program Files\\Git\\usr\\bin). It downloads
SHA256SUMS, SHA256SUMS.asc, the Windows installer and one APK into a temporary folder, and deletes them afterwards.
Exit code 0 only if every check passed.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = 'progliodario/YT-Grabber'
RESULTS = []


def report(name, ok, detail=''):
    RESULTS.append(ok)
    print('%-34s %s%s' % (name, 'OK' if ok else 'FAILED', ('  ' + detail) if detail else ''), flush=True)


def find(tool, extra=()):
    for p in (shutil.which(tool),) + tuple(os.path.join(d, tool + ('.exe' if os.name == 'nt' else '')) for d in extra):
        if p and os.path.exists(p):
            return p
    return None


def main(argv):
    if len(argv) != 2 or not re.fullmatch(r'\d+\.\d+\.\d+', argv[1]):
        print(__doc__)
        return 2
    version = argv[1]
    tag = 'v' + version
    gh = find('gh')
    gpg = find('gpg', (r'C:\Program Files\Git\usr\bin', r'C:\Program Files (x86)\GnuPG\bin', '/usr/bin'))
    if not gh or not gpg:
        print('Needs gh (GitHub CLI) and gpg: missing %s' % ', '.join(n for n, p in (('gh', gh), ('gpg', gpg)) if not p))
        return 2
    work = tempfile.mkdtemp(prefix='ytg_verify_')
    try:
        home = os.path.join(work, 'gnupg')
        os.makedirs(home)
        os.chmod(home, 0o700)
        names = ['SHA256SUMS', 'SHA256SUMS.asc', 'YT-Grabber-Setup-%s.exe' % version, 'YT-Grabber-arm64-v8a.apk']
        cmd = [gh, 'release', 'download', tag, '--repo', REPO, '-D', work] + sum((['-p', n] for n in names), [])
        r = subprocess.run(cmd, capture_output=True, text=True)
        report('release %s downloaded' % tag, r.returncode == 0, r.stderr.strip()[:200])
        if r.returncode != 0:
            return 1
        listing = subprocess.run([gh, 'release', 'view', tag, '--repo', REPO, '--json', 'isDraft,assets'], capture_output=True, text=True).stdout
        import json
        info = json.loads(listing)
        report('published, with the 12 files', (not info['isDraft']) and len(info['assets']) == 12, '(%d files)' % len(info['assets']))
        # the gpg that comes with Git for Windows is an MSYS program: it wants /c/Users/... in an environment variable
        posix = '/' + home[0].lower() + home[2:].replace('\\', '/') if os.name == 'nt' and re.match(r'^[A-Za-z]:', home) else home
        genv = dict(os.environ, GNUPGHOME=posix)
        subprocess.run([gpg, '--import', os.path.join(ROOT, 'docs', 'release-key.asc')], env=genv, capture_output=True)
        r = subprocess.run([gpg, '--verify', os.path.join(work, 'SHA256SUMS.asc'), os.path.join(work, 'SHA256SUMS')], env=genv, capture_output=True, text=True)
        out = r.stdout + r.stderr
        key = re.search(r'Primary key fingerprint: (.+)', out)
        report('GPG signature of SHA256SUMS', 'Good signature' in out, (key.group(1).replace(' ', '') if key else ''))
        import hashlib
        sums = dict((line.split()[1].lstrip('*'), line.split()[0]) for line in open(os.path.join(work, 'SHA256SUMS'), encoding='utf-8') if line.strip())
        for n in names[2:]:
            with open(os.path.join(work, n), 'rb') as f:
                got = hashlib.sha256(f.read()).hexdigest()
            report('checksum of ' + n, sums.get(n) == got)
        r = subprocess.run([gh, 'attestation', 'verify', os.path.join(work, names[2]), '--repo', REPO], capture_output=True, text=True)
        report('build attestation of the installer', r.returncode == 0)
        try:
            with urllib.request.urlopen('https://progliodario.github.io/YT-Grabber/apt/dists/stable/main/binary-amd64/Packages', timeout=30) as resp:
                text = resp.read().decode('utf-8', 'replace')
            m = re.search(r'^Version: (.+)$', text, flags=re.M)
            report('apt repository offers the version', bool(m) and m.group(1).strip() == version, '(%s)' % (m.group(1).strip() if m else 'none'))
        except Exception as e:  # noqa: BLE001
            report('apt repository offers the version', False, str(e)[:100])
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print()
    print('Result: %s' % ('everything checked out' if all(RESULTS) else 'SOMETHING FAILED'))
    return 0 if all(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
