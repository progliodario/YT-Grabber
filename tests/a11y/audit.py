#!/usr/bin/env python3
"""Accessibility audit of the running page: axe-core in several states, plus keyboard and reflow checks.

    python tests/a11y/seed.py ROOT
    YTG_DATA_ROOT=ROOT python program/server.py --no-browser --port 8782 &
    python tests/a11y/audit.py http://localhost:8782/

It drives a headless Chromium-based browser (Chrome, Chromium or Edge; set CHROME to choose one) through the DevTools protocol,
runs axe-core (WCAG 2.0, 2.1 and 2.2 level A and AA, plus best practices) on the page in light and dark, with the list of a
download open, with the settings dialog open, in Arabic (right to left) and at 320 CSS pixels wide, and checks by keyboard that
the skip link, the focus order, the dialog (focus goes in, stays in, returns) and the list work. Exits with 1 if anything fails.
Needs the "websockets" package.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import warnings

from websockets.sync.client import connect

warnings.simplefilter('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8782/'
AXE_URL = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js'
AXE_SHA256 = 'b511cd9dec01c76f4b2ad1723b66b6db37d4c2eb4ed199076e1829d9ee7b75e3'
TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']
PORT = 9337


def find_browser():
    names = [os.environ.get('CHROME'), 'google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'microsoft-edge', 'msedge']
    paths = [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', r'C:\Program Files\Google\Chrome\Application\chrome.exe',
             '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
    for n in names:
        if n and (shutil.which(n) or os.path.exists(n)):
            return shutil.which(n) or n
    for p in paths:
        if os.path.exists(p):
            return p
    raise SystemExit('No Chrome, Chromium or Edge found (set CHROME to its path).')


def axe_source():
    cache = os.path.join(tempfile.gettempdir(), 'axe-core-4.10.2.min.js')
    if not os.path.exists(cache):
        urllib.request.urlretrieve(AXE_URL, cache)
    with open(cache, 'rb') as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != AXE_SHA256:
        os.remove(cache)
        raise SystemExit('axe-core: unexpected checksum, refusing to run it.')
    return data.decode('utf-8')


class Browser:
    def __init__(self):
        self.profile = tempfile.mkdtemp(prefix='ytg_a11y_')
        args = [find_browser(), '--headless=new', '--remote-debugging-port=%d' % PORT, '--user-data-dir=' + self.profile, '--lang=en-US',
                '--hide-scrollbars', '--no-first-run', '--disable-gpu', '--no-sandbox', 'about:blank']
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        page = None
        for _ in range(100):
            try:
                page = next(t for t in json.load(urllib.request.urlopen('http://127.0.0.1:%d/json' % PORT)) if t['type'] == 'page')
                break
            except Exception:
                time.sleep(0.3)
        if not page:
            raise SystemExit('The browser did not start.')
        self.ws = connect(page['webSocketDebuggerUrl'], max_size=64 * 1024 * 1024)
        self.n = 0
        self.call('Page.enable')

    def close(self):
        try:
            self.ws.close()
        finally:
            self.proc.terminate()
            shutil.rmtree(self.profile, ignore_errors=True)

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({'id': self.n, 'method': method, 'params': params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get('id') == self.n:
                if 'error' in msg:
                    raise RuntimeError('%s: %s' % (method, msg['error']))
                return msg.get('result', {})

    def js(self, code):
        r = self.call('Runtime.evaluate', expression=code, awaitPromise=True, returnByValue=True)
        if 'exceptionDetails' in r:
            raise RuntimeError('JavaScript error: ' + json.dumps(r['exceptionDetails'])[:300])
        return r.get('result', {}).get('value')

    def view(self, width, height=900, dark=False):
        self.call('Emulation.setDeviceMetricsOverride', width=width, height=height, deviceScaleFactor=1, mobile=False)
        self.call('Emulation.setEmulatedMedia', features=[{'name': 'prefers-color-scheme', 'value': 'dark' if dark else 'light'}])

    def load(self, lang='en'):
        self.call('Page.navigate', url=URL)
        time.sleep(2.5)
        self.js("localStorage.setItem('ytg-lang', '%s'); localStorage.removeItem('ytg-theme')" % lang)
        self.call('Page.navigate', url=URL)
        for _ in range(40):   # wait for the cards
            time.sleep(0.25)
            if self.js("document.querySelectorAll('.job').length > 0"):
                break
        time.sleep(0.5)

    def key(self, name, shift=False):
        codes = {'Tab': 9, 'Enter': 13, 'Escape': 27, 'PageUp': 33, 'PageDown': 34, 'End': 35, 'Home': 36, 'ArrowUp': 38, 'ArrowDown': 40}
        for t in ('keyDown', 'keyUp'):
            self.call('Input.dispatchKeyEvent', type=t, key=name, code=name, windowsVirtualKeyCode=codes[name], modifiers=8 if shift else 0,
                      text='\r' if (name == 'Enter' and t == 'keyDown') else '')
        time.sleep(0.12)

    def active(self):
        return self.js("(function(){var e=document.activeElement; return e && e!==document.body ? e.tagName.toLowerCase()+(e.id?'#'+e.id:'') : 'body';})()")


FAILS = []


def check(ok, what):
    print('  %s %s' % ('ok  ' if ok else 'FAIL', what))
    if not ok:
        FAILS.append(what)


def axe(b, axe_js, label):
    b.js(axe_js)
    res = b.js("axe.run(document, {runOnly: {type: 'tag', values: %s}, resultTypes: ['violations']}).then(function (r) { return JSON.stringify(r.violations.map(function (v) { return {id: v.id, impact: v.impact, help: v.help, n: v.nodes.length, nodes: v.nodes.slice(0, 3).map(function (x) { return {t: x.target.join(' '), m: (x.any[0] || x.all[0] || x.none[0] || {}).message}; })}; })); })" % json.dumps(TAGS))
    v = json.loads(res or '[]')
    print('%s: %d rule(s) violated' % (label, len(v)))
    for x in v:
        print('  FAIL [%s] %s (%d): %s' % (x['impact'], x['id'], x['n'], x['help']))
        for nd in x['nodes']:
            print('       - %s | %s' % (nd['t'], (nd['m'] or '')[:140]))
        FAILS.append('%s: %s' % (label, x['id']))


def main():
    axe_js = axe_source()
    b = Browser()
    try:
        b.view(1280)
        b.load()
        axe(b, axe_js, 'light')
        b.js("document.querySelector('.jtitle-btn').click()")
        time.sleep(1.5)
        axe(b, axe_js, 'light, list of a download open')
        b.js("document.getElementById('btnSettings').click()")
        time.sleep(0.6)
        axe(b, axe_js, 'light, settings dialog')

        b.view(1280, dark=True)
        b.load()
        axe(b, axe_js, 'dark')
        b.js("document.querySelector('.jtitle-btn').click()")
        time.sleep(1.5)
        axe(b, axe_js, 'dark, list of a download open')
        b.js("document.getElementById('btnSettings').click()")
        time.sleep(0.6)
        axe(b, axe_js, 'dark, settings dialog')

        b.view(1280)
        b.load('ar')
        check(b.js("document.documentElement.lang === 'ar' && document.documentElement.dir === 'rtl'"), 'Arabic: lang="ar" and dir="rtl"')
        axe(b, axe_js, 'Arabic (right to left)')

        b.view(320, 700)
        b.load()
        axe(b, axe_js, '320 CSS pixels wide')
        check(not b.js("document.documentElement.scrollWidth > document.documentElement.clientWidth"), 'no horizontal scrolling at 320 CSS pixels (reflow)')

        print('keyboard')
        b.view(1280)
        b.load()
        b.js("document.activeElement.blur()")
        b.key('Tab')
        check(b.js("document.activeElement.className === 'skip'"), 'the first Tab stop is the "skip to the main content" link')
        b.key('Enter')
        check(b.js("document.activeElement.id === 'main' || document.getElementById('main').contains(document.activeElement)"), 'the skip link moves the focus to the main content')
        outline = b.js("(function(){b=document.getElementById('btnSettings'); b.focus(); var s=getComputedStyle(b); return parseFloat(s.outlineWidth);})()")
        check(outline >= 2, 'a focused control has a visible outline (at least 2 px)')
        b.key('Enter')
        time.sleep(0.4)
        check(b.js("document.activeElement.id === 'setTitle'"), 'opening the settings moves the focus into the dialog')
        check(b.js("document.getElementById('main').hasAttribute('inert')"), 'the page behind the dialog is inert')
        for _ in range(40):
            b.key('Tab')
        check(b.js("!!document.activeElement.closest('.modal')"), 'Tab stays inside the dialog')
        b.key('Escape')
        time.sleep(0.3)
        check(b.active() == 'button#btnSettings', 'Escape closes the dialog and the focus returns to the button that opened it')
        b.js("document.querySelector('.jtitle-btn').focus()")
        b.key('Enter')
        time.sleep(1.2)
        check(b.js("document.querySelector('.jtitle-btn').getAttribute('aria-expanded') === 'true'"), 'the title button of a download reports aria-expanded')
        check(b.js("(function(){var r=document.querySelector('.row'); return !!r && r.getAttribute('role')==='listitem' && +r.getAttribute('aria-setsize') > 0;})()"), 'the rows of a list have a position and a size')

        print('list: arrow keys')
        b.js("(function(){var bs=[].slice.call(document.querySelectorAll('.jtitle-btn')).filter(function(e){return /Demo album/.test(e.textContent);}); bs[0].click();})()")
        time.sleep(1.5)

        def row():
            return b.js("(function(){var e=document.activeElement; return e && e.classList.contains('row') ? +e.getAttribute('aria-posinset') : 0;})()")
        b.js("document.querySelector('.vbox').focus()")
        b.key('ArrowDown')
        check(row() == 1, 'Arrow down from the list goes to the first item')
        b.key('ArrowDown')
        b.key('ArrowDown')
        check(row() == 3, 'Arrow down goes to the next item')
        b.key('ArrowUp')
        check(row() == 2, 'Arrow up goes to the previous item')
        b.key('End')
        check(row() == 12, 'End goes to the last item')
        b.key('Home')
        check(row() == 1, 'Home goes to the first item')
        b.key('PageDown')
        check(row() > 1, 'Page down jumps')
        b.key('Home')
        for _ in range(8):
            b.key('ArrowDown')
        check(row() == 9, 'the item with an error is reachable by arrows')
        b.key('Tab')
        check(b.js("(function(){var e=document.activeElement; var r=e.closest('.row'); return e.tagName==='BUTTON' && !!r && +r.getAttribute('aria-posinset')===9;})()"), 'Tab from an item goes to its own buttons')
        b.key('Tab')
        b.key('Tab')
        check(b.js("!document.activeElement.closest('.row')"), 'and the buttons of the other items are not in the Tab order')

        print('text size setting')
        b.js("document.getElementById('btnSettings').click()")
        time.sleep(0.5)
        b.js("(function(){var s=document.getElementById('setTextSize'); s.value='200'; s.dispatchEvent(new Event('change', {bubbles: true}));})()")
        time.sleep(0.5)
        check(b.js("document.documentElement.style.fontSize === '200%'"), 'the setting enlarges the text at once')
        b.key('Escape')
        check(not b.js("document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"), 'no horizontal scrolling with the text at 200%')
        b.call('Page.navigate', url=URL)
        time.sleep(3)
        check(b.js("document.documentElement.style.fontSize === '200%'"), 'the chosen size is remembered')
        axe(b, axe_js, 'text size 200%')
        b.js("localStorage.removeItem('ytg-textsize'); document.documentElement.style.fontSize = ''")
    finally:
        b.close()
    print()
    if FAILS:
        print('%d accessibility check(s) failed:' % len(FAILS))
        for f in FAILS:
            print('  -', f)
        return 1
    print('All accessibility checks passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
