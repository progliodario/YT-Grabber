#!/usr/bin/env python3
"""Prepares YT Grabber for the Android phone.

Usage (on the PC):
    python termux/share_to_phone.py            # builds the zip and makes it downloadable from the phone (Wi-Fi), only once
    python termux/share_to_phone.py --zip-only # only builds generated/YT-Grabber-android.zip (to copy by hand)

The PC is needed ONLY for this first installation: afterwards the program runs by itself on the phone.
Only the program files are shared, never your downloads, cookies or settings.
"""
import argparse
import http.server
import io
import os
import socket
import socketserver
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# the zip has the same structure as the project: Start.sh and README.md in the root, the code in program/, the instructions in termux/
FILES = ['Start.sh', 'README.md']
DIRS = ['program', 'termux']
SKIP_DIRS = {'__pycache__'}
SKIP_SUFFIX = ('.zip', '.pyc')
PORT = 8800


def build_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        def add(path, arc):
            with open(path, 'rb') as f:
                data = f.read()
            if arc.endswith(('.sh', '.py', '.md', '.json', '.webmanifest', '.js', '.css', '.html', '.bat')) and b'\r\n' in data:
                data = data.replace(b'\r\n', b'\n')   # Android needs Unix line endings
            info = zipfile.ZipInfo(arc.replace(os.sep, '/'))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if arc.endswith('.sh') else 0o644) << 16
            z.writestr(info, data)
        for name in FILES:
            p = os.path.join(ROOT, name)
            if os.path.exists(p):
                add(p, name)
        for d in DIRS:
            for base, dirs, files in os.walk(os.path.join(ROOT, d)):
                dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
                for fn in files:
                    if fn.endswith(SKIP_SUFFIX):
                        continue
                    full = os.path.join(base, fn)
                    add(full, os.path.relpath(full, ROOT))
    return buf.getvalue()


def lan_ips():
    ips = []
    try:   # the address used to reach the local network
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ips.append(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if ip not in ips and not ip.startswith('127.'):
                ips.append(ip)
    except OSError:
        pass
    return ips


def install_script(base):
    with open(os.path.join(HERE, 'install-termux.sh'), 'rb') as f:
        text = f.read().decode('utf-8').replace('\r\n', '\n')
    # the line BASE="${YTG_BASE:-}" becomes the real address of the PC
    return text.replace('BASE="${YTG_BASE:-}"', 'BASE="%s"' % base).encode('utf-8')


class Handler(http.server.BaseHTTPRequestHandler):
    zip_bytes = b''

    def log_message(self, fmt, *args):
        print('  phone:', self.client_address[0], self.path)

    def do_GET(self):
        host = self.headers.get('Host') or ''
        base = 'http://%s' % host
        if self.path in ('/i', '/install.sh'):
            body, ctype = install_script(base), 'text/x-shellscript'
        elif self.path == '/yt-grabber-android.zip':
            body, ctype = self.zip_bytes, 'application/zip'
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zip-only', action='store_true')
    ap.add_argument('--port', type=int, default=PORT)
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(line_buffering=True, encoding='utf-8', errors='replace')
    except Exception:
        pass

    data = build_zip()
    out_dir = os.path.join(ROOT, 'generated')
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, 'YT-Grabber-android.zip')
    with open(out, 'wb') as f:
        f.write(data)
    print('Created %s (%d KB)' % (out, len(data) // 1024))
    if a.zip_only:
        print('Copy it to the phone and follow termux/README.md (section "Without a shared Wi-Fi").')
        return 0

    Handler.zip_bytes = data
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    try:
        srv = socketserver.ThreadingTCPServer(('0.0.0.0', a.port), Handler)
    except OSError as e:
        print('Cannot open port %d: %s' % (a.port, e))
        return 1
    ips = lan_ips() or ['PC-IP-ADDRESS']
    print()
    print('=' * 64)
    print(' On the phone, in Termux, paste ONE of these commands')
    print(' (phone and PC must be on the same Wi-Fi network):')
    print()
    for ip in ips:
        print('     curl -s http://%s:%d/i | sh' % (ip, a.port))
    print()
    print(' If Windows asks for firewall permission, allow private networks.')
    print(' When the installation on the phone is finished, press Ctrl+C here.')
    print('=' * 64)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
