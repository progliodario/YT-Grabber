#!/usr/bin/env python3
"""Updates the package managers that follow the releases by hand: Homebrew (the cask) and Scoop (the manifest).

    python tools/update_channels.py 1.6.2              shows what would change (nothing is written)
    python tools/update_channels.py 1.6.2 --apply      changes the files, commits and pushes to the two repositories

The checksums come from the release itself (GitHub computes the SHA-256 of every asset). Run it after the release is complete,
that is after the APKs were uploaded and Finalize ran. The two repositories are cloned into a temporary folder (needs `gh` and `git`).

winget is not done here: its package has a pull request that waits for a moderator (see docs/ROADMAP.md). Do not open a new one for
every release; after the first one is merged, `wingetcreate update` or the komac action can do it.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = 'progliodario/YT-Grabber'
TAP = 'progliodario/homebrew-tap'
BUCKET = 'progliodario/scoop-bucket'
EMAIL = 'proglio.dario.dal.2008@gmail.com'


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise SystemExit('Command failed: %s\n%s' % (' '.join(cmd), (r.stderr or r.stdout).strip()))
    return r.stdout


def digest(assets, name):
    for a in assets:
        if a['name'] == name:
            d = a.get('digest') or ''
            if d.startswith('sha256:'):
                return d[7:].lower()
    raise SystemExit('The release has no asset %s with a SHA-256 digest (is it complete?)' % name)


def replace_once(text, pattern, repl, what):
    new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        raise SystemExit('Could not find %s to change' % what)
    return new


def main(argv):
    args = [a for a in argv[1:] if not a.startswith('--')]
    apply = '--apply' in argv
    if len(args) != 1 or not re.fullmatch(r'\d+\.\d+\.\d+', args[0]):
        print(__doc__)
        return 2
    version = args[0]
    release = json.loads(sh(['gh', 'api', 'repos/%s/releases/tags/v%s' % (REPO, version)]))
    assets = release['assets']
    if len(assets) < 12:
        raise SystemExit('The release has only %d files: the APKs and Finalize come first.' % len(assets))
    zip_sha = digest(assets, 'YT-Grabber-macOS.zip')
    exe_sha = digest(assets, 'YT-Grabber-Setup-%s.exe' % version)
    work = tempfile.mkdtemp(prefix='ytg_channels_')
    try:
        changed = []
        for repo, rel, edit in (
                (TAP, 'Casks/yt-grabber.rb', lambda t: replace_once(replace_once(t, r'^(\s*version )"[^"]+"', r'\g<1>"%s"' % version, 'the cask version'),
                                                                    r'^(\s*sha256 )"[0-9a-f]{64}"', r'\g<1>"%s"' % zip_sha, 'the cask sha256')),
                (BUCKET, 'bucket/yt-grabber.json', lambda t: replace_once(replace_once(t, r'^(\s*"version": )"[^"]+"', r'\g<1>"%s"' % version, 'the manifest version'),
                                                                          r'^(\s*"url": "[^"]*/v)[^/]+(/YT-Grabber-Setup-)[^"]+(\.exe",)', r'\g<1>%s\g<2>%s\g<3>' % (version, version), 'the manifest url'))):
            folder = os.path.join(work, repo.split('/')[1])
            sh(['gh', 'repo', 'clone', repo, folder])
            path = os.path.join(folder, *rel.split('/'))
            with open(path, encoding='utf-8', newline='') as f:
                old = f.read()
            new = edit(old)
            if repo == BUCKET:   # the hash of the manifest is the first "hash" (the one outside "autoupdate")
                new = replace_once(new, r'^(\s*"hash": )"[0-9a-f]{64}"', r'\g<1>"%s"' % exe_sha, 'the manifest hash')
            print('%s  %s: %s' % (repo, rel, 'already at %s' % version if new == old else 'will change'))
            if new != old:
                changed.append((folder, path, new, repo))
        if not apply:
            for folder, path, new, repo in changed:
                print('  (dry run) %s would get version %s, %s' % (repo, version, zip_sha if repo == TAP else exe_sha))
            return 0
        for folder, path, new, repo in changed:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(new)
            sh(['git', '-C', folder, '-c', 'user.email=' + EMAIL, '-c', 'user.name=progliodario', 'commit', '-qam', 'yt-grabber ' + version])
            sh(['git', '-C', folder, 'push', '-q'])
            print('  pushed %s' % repo)
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
