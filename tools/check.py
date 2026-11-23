#!/usr/bin/env python3
"""Runs the checks of the project in one go, the same ones CI runs.

    python tools/check.py              unit tests, pyflakes (if installed), links of the .md files, syntax of the JavaScript (if Node is installed)
    python tools/check.py --audit      also the accessibility audit in a real browser (needs: pip install websockets, and Chrome or Edge)
    python tools/check.py docs         only the links of the .md files (fast, needs nothing)

The exit code is 0 only if everything that ran passed. A check whose tool is missing is reported as "skipped", never as passed.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, 'generated', 'vendor')
RESULTS = []


def report(name, status, detail=''):
    RESULTS.append((name, status))
    print('%-22s %s%s' % (name, status, ('  ' + detail) if detail else ''), flush=True)


def env():
    e = dict(os.environ)
    if os.path.isdir(VENDOR):   # yt-dlp installed by setup_tools.py (the tests and the server import it)
        e['PYTHONPATH'] = VENDOR + os.pathsep + e.get('PYTHONPATH', '')
    return e


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, env=env(), capture_output=True, text=True, **kw)


def unit_tests():
    r = run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'])
    last = (r.stderr.strip().splitlines() or ['?'])[-1]
    if r.returncode == 0:
        count = re.search(r'Ran (\d+) tests', r.stderr)
        report('unit tests', 'passed', '(%s tests; %s)' % (count.group(1) if count else '?', last))
    else:
        report('unit tests', 'FAILED')
        print(r.stderr[-3000:])


def pyflakes():
    probe = run([sys.executable, '-m', 'pyflakes', '--version'])
    if probe.returncode != 0:
        report('pyflakes', 'skipped', '(pip install pyflakes)')
        return
    r = run([sys.executable, '-m', 'pyflakes', 'program', 'tests', 'packaging', 'tools'])
    if r.stdout.strip() or r.returncode != 0:
        report('pyflakes', 'FAILED')
        print(r.stdout[-3000:], r.stderr[-1000:])
    else:
        report('pyflakes', 'passed')


def slug(heading):
    h = re.sub(r'[`*_]', '', heading.strip().lower())
    return re.sub(r'[^\w\- ]', '', h, flags=re.UNICODE).replace(' ', '-')


def docs_links():
    """Every relative link of every .md file points to a file that exists and, if it has #anchor, to a heading that exists."""
    files = []
    for folder, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', 'generated', 'dist', 'build', 'vendor', '.gradle', 'node_modules', '__pycache__')]
        files += [os.path.join(folder, n) for n in names if n.endswith('.md')]
    anchors = {}
    for f in files:
        with open(f, encoding='utf-8') as fh:
            text = re.sub(r'```.*?```', '', fh.read(), flags=re.S)
        seen, found = {}, set()
        for m in re.finditer(r'^#{1,6}\s+(.*)$', text, flags=re.M):
            s = slug(m.group(1))
            n = seen.get(s, 0)
            seen[s] = n + 1
            found.add(s if n == 0 else '%s-%d' % (s, n))
        anchors[os.path.normpath(f)] = found
    problems = []
    for f in files:
        with open(f, encoding='utf-8') as fh:
            text = re.sub(r'```.*?```', '', fh.read(), flags=re.S)
        for m in re.finditer(r'\]\(([^)\s]+)\)', text):
            url = m.group(1)
            if re.match(r'^(https?:|mailto:)', url):
                continue
            path, _, frag = url.partition('#')
            target = os.path.normpath(os.path.join(os.path.dirname(f), path)) if path else os.path.normpath(f)
            rel = os.path.relpath(f, ROOT)
            if not os.path.exists(target):
                problems.append('%s: missing file %s' % (rel, url))
            elif frag and target.endswith('.md') and frag not in anchors.get(target, set()):
                problems.append('%s: missing heading for %s' % (rel, url))
    if problems:
        report('links of the .md files', 'FAILED')
        print('\n'.join('  ' + p for p in problems))
    else:
        report('links of the .md files', 'passed', '(%d files)' % len(files))


def javascript():
    node = shutil.which('node')
    if not node:
        report('JavaScript syntax', 'skipped', '(Node is not installed; CI checks it)')
        return
    bad = []
    for f in [os.path.join(ROOT, 'program', 'web', 'app.js')] + sorted(glob.glob(os.path.join(ROOT, 'program', 'web', '*.js'))) \
            + sorted(glob.glob(os.path.join(ROOT, 'program', 'web', 'lang', '*.js'))):
        if subprocess.run([node, '--check', f], capture_output=True).returncode != 0:
            bad.append(os.path.relpath(f, ROOT))
    report('JavaScript syntax', 'FAILED' if bad else 'passed', ', '.join(bad))


def audit():
    """The accessibility audit: sample data, a server on a free port, headless Chrome or Edge (tests/a11y)."""
    import importlib.util
    if importlib.util.find_spec('websockets') is None:
        report('accessibility audit', 'skipped', '(pip install websockets)')
        return
    data = tempfile.mkdtemp(prefix='ytg_audit_')
    srv = None
    try:
        sys.path.insert(0, os.path.join(ROOT, 'tests', 'a11y'))
        import seed
        seed.seed(data)
        port = 8782
        e = env()
        e['YTG_DATA_ROOT'] = data
        srv = subprocess.Popen([sys.executable, os.path.join(ROOT, 'program', 'server.py'), '--no-browser', '--port', str(port)],
                               cwd=ROOT, env=e, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import urllib.request
        for _ in range(100):
            try:
                urllib.request.urlopen('http://127.0.0.1:%d/api/ping' % port, timeout=1)
                break
            except Exception:
                time.sleep(0.2)
        r = run([sys.executable, os.path.join('tests', 'a11y', 'audit.py'), 'http://localhost:%d/' % port], timeout=600)
        ok = r.returncode == 0 and 'All accessibility checks passed' in r.stdout
        report('accessibility audit', 'passed' if ok else 'FAILED')
        if not ok:
            print(r.stdout[-3000:], r.stderr[-1000:])
    finally:
        if srv:
            srv.terminate()
            try:
                srv.wait(10)
            except Exception:
                srv.kill()
        time.sleep(1)
        shutil.rmtree(data, ignore_errors=True)


def main(argv):
    args = argv[1:]
    if 'docs' in args:
        docs_links()
    else:
        unit_tests()
        pyflakes()
        docs_links()
        javascript()
        if '--audit' in args:
            audit()
    failed = [n for n, s in RESULTS if s == 'FAILED']
    skipped = [n for n, s in RESULTS if s == 'skipped']
    print()
    print('Result: %s%s' % ('FAILED (%s)' % ', '.join(failed) if failed else 'all that ran passed',
                            ('; skipped: ' + ', '.join(skipped)) if skipped else ''))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
