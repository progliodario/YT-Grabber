"""Links and file names: what a pasted link is, and how the files of a playlist are named."""
import ctypes
import os
import re
import urllib.parse

import ytcommon  # noqa: E402  (first: it puts yt-dlp on sys.path)
from yt_dlp.utils import sanitize_filename  # noqa: E402

assert ytcommon.ROOT   # (ytcommon is imported for its effect on sys.path)

YT_HOSTS = ('youtube.com', 'm.youtube.com', 'music.youtube.com', 'youtu.be', 'youtube-nocookie.com', 'gaming.youtube.com')
CHANNEL_TABS = ('videos', 'shorts', 'streams', 'playlists', 'releases', 'podcasts', 'featured', 'live', 'courses')


def classify_url(raw, single_only=False):
    """-> (kind, url, vid) with kind in video | playlist | auto, or None if it is not a link."""
    raw = raw.strip().strip('<>"\'')
    if not raw:
        return None
    if re.fullmatch(r'[\w-]{11}', raw):
        return 'video', 'https://www.youtube.com/watch?v=' + raw, raw
    if re.fullmatch(r'(PL|OLAK5uy_|UU|FL|LL|RDCLAK5uy_|VL|PU)[\w-]{8,}', raw):
        return 'playlist', 'https://www.youtube.com/playlist?list=' + raw, None
    if not re.match(r'^https?://', raw, re.I):
        if re.match(r'^(www\.|m\.|music\.)?(youtube\.com|youtu\.be)', raw, re.I):
            raw = 'https://' + raw
        else:
            return None
    u = urllib.parse.urlparse(raw)
    host = u.netloc.lower().split(':')[0]
    host_nowww = host[4:] if host.startswith('www.') else host
    if host_nowww not in YT_HOSTS:
        return 'auto', raw, None
    q = urllib.parse.parse_qs(u.query)
    path = u.path or '/'
    v = (q.get('v') or [None])[0]
    lst = (q.get('list') or [None])[0]
    if host_nowww == 'youtu.be':
        v = path.strip('/').split('/')[0] or v
    m = re.match(r'^/(?:shorts|live|embed|v)/([\w-]{11})', path)
    if m:
        v = m.group(1)
    if v and not re.fullmatch(r'[\w-]{11}', v):
        v = None
    base = 'https://music.youtube.com' if host_nowww == 'music.youtube.com' else 'https://www.youtube.com'
    if path.startswith('/playlist') and lst:
        return 'playlist', '%s/playlist?list=%s' % (base, lst), None
    if lst and v:
        if single_only or lst.startswith(('RD', 'UL')):
            return 'video', 'https://www.youtube.com/watch?v=' + v, v
        return 'playlist', '%s/playlist?list=%s' % (base, lst), None
    if v:
        return 'video', 'https://www.youtube.com/watch?v=' + v, v
    if lst:
        return 'playlist', '%s/playlist?list=%s' % (base, lst), None
    if re.match(r'^/(@|channel/|c/|user/)', path):
        parts = [p for p in path.split('/') if p]
        if not parts[-1].lower() in CHANNEL_TABS:
            path = path.rstrip('/') + '/videos'
        return 'playlist', '%s%s' % (base, path), None
    if path.startswith('/browse/'):
        return 'playlist', raw, None
    return 'auto', raw, None


def hide_path(p):
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetFileAttributesW(p, 0x02)
        except Exception:
            pass


def safe_name(s, maxlen=150):
    s = sanitize_filename(s or '', restricted=False)
    s = re.sub(r'[\x00-\x1f]', '', s)
    s = re.sub(r'\s+', ' ', s).strip(' .')
    if len(s) > maxlen:
        s = s[:maxlen].rstrip(' .')
    return s or 'untitled'


def build_filename(job, it, title, ext):
    prefix = ('%0*d - ' % (job.pad, it.idx)) if job.numbered() else ''
    room = 245 - len(job.dir) - len(prefix) - len(ext) - 2
    name = safe_name(title, max(30, min(150, room)))
    return '%s%s%s' % (prefix, name, ext)


PREFIX_RE = re.compile(r'^\d+ - ')


def expected_for_existing(job, it, existing):
    """Recomputes the numeric prefix of an already present file (the playlist may have changed)."""
    if not job.numbered():
        return existing
    rest = PREFIX_RE.sub('', existing, count=1)
    return '%0*d - %s' % (job.pad, it.idx, rest)
