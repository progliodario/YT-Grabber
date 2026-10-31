"""Worker process: downloads ONE video at a time on behalf of server.py.

Protocol: JSON lines on stdin (tasks) and on stdout (events). Everything yt-dlp
writes to stdout is redirected to stderr so it does not pollute the channel.
"""
import json
import os
import shutil
import sys
import time

PROTO = sys.stdout
sys.stdout = sys.stderr
try:
    sys.stdin.reconfigure(encoding='utf-8')
    PROTO.reconfigure(encoding='utf-8')
except Exception:
    pass

import ytcommon as C  # noqa: E402
import yt_dlp  # noqa: E402
from yt_dlp.utils import DownloadCancelled  # noqa: E402

PP_STAGE = (('ExtractAudio', 'Converting audio'), ('Merger', 'Merging video+audio'), ('EmbedThumbnail', 'Cover art'),
            ('Metadata', 'Metadata'), ('ThumbnailsConvertor', 'Cover art'), ('MoveFiles', 'Saving'),
            ('VideoRemuxer', 'Converting video'), ('FixupM4a', 'Fixing file'), ('Fixup', 'Fixing file'))


def send(obj):
    PROTO.write(json.dumps(obj, ensure_ascii=False) + '\n')
    PROTO.flush()


class State:
    ydl = None
    sig = None
    tid = None
    last = 0.0
    files_seen = []
    in_pp = False
    reject = ''


S = State()


def hook(d):
    st = d.get('status')
    now = time.time()
    if st == 'downloading':
        if now - S.last < 0.5:
            return
        S.last = now
        info = d.get('info_dict') or {}
        nparts = len(info.get('requested_formats') or []) or 1
        fn = d.get('filename') or ''
        if fn not in S.files_seen:
            S.files_seen.append(fn)
        part = min(len(S.files_seen) - 1, nparts - 1)
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        done = d.get('downloaded_bytes') or 0
        pct = (done / total) if total else 0.0
        send({'ev': 'progress', 'tid': S.tid, 'pct': min(98.5, (part + min(pct, 1.0)) / nparts * 100.0),
              'speed': d.get('speed') or 0, 'eta': d.get('eta'), 'size': int(total) if total else None,
              'stage': 'Download' if nparts == 1 else 'Download (%d/%d)' % (part + 1, nparts)})


def pphook(d):
    if d.get('status') != 'started':
        return
    name = d.get('postprocessor') or ''
    if 'ThumbnailsConvertor' in name:
        return   # runs before the download (when=before_dl): it is not the start of the conversion
    stage = None
    for k, v in PP_STAGE:
        if k in name:
            stage = v
            break
    if stage is None:
        return
    if not S.in_pp:
        S.in_pp = True
        send({'ev': 'phase', 'tid': S.tid, 'stage': stage})
    else:
        send({'ev': 'stage', 'tid': S.tid, 'stage': stage})


def match_filter(info, incomplete=False):
    if info.get('is_live') or info.get('live_status') in ('is_live', 'is_upcoming'):
        S.reject = 'live'
        return 'live stream'
    return None


def get_ydl(opts, wid):
    sig = json.dumps([opts['mode'], opts['audio_format'], opts['mp3_bitrate'], opts['video_height'], opts['embed'],
                      opts['cookies_browser'], opts.get('cookies_mtime', 0)])
    if S.ydl is not None and S.sig == sig:
        return S.ydl
    if S.ydl is not None:
        try:
            S.ydl.close()
        except Exception:
            pass
        S.ydl = None
    fmt, sort, _fb, pps, extra = C.build_format(opts)
    p = C.base_ydl_params()
    p.update(extra)
    p.update({'format': fmt, 'postprocessors': pps, 'outtmpl': {'default': '%(id)s.%(ext)s'}})
    if sort:
        p['format_sort'] = sort
    if opts.get('cookies_browser'):
        p['cookiesfrombrowser'] = (opts['cookies_browser'],)
    elif opts.get('cookies_file') and os.path.exists(opts['cookies_file']):
        cp = os.path.join(C.DATA, 'cookies_w%s.txt' % wid)
        try:
            shutil.copyfile(opts['cookies_file'], cp)
            p['cookiefile'] = cp
        except Exception:
            pass
    p['progress_hooks'] = [hook]
    p['postprocessor_hooks'] = [pphook]
    p['match_filter'] = match_filter
    S.ydl = yt_dlp.YoutubeDL(p)
    S.sig = sig
    return S.ydl


def find_output(tmpd, vid):
    best = None
    try:
        for fn in os.listdir(tmpd):
            low = fn.lower()
            if low.endswith(('.part', '.ytdl', '.jpg', '.jpeg', '.png', '.webp', '.json', '.temp')) or '.part-' in low:
                continue
            if vid and not fn.startswith(vid):
                continue
            p = os.path.join(tmpd, fn)
            if best is None or os.path.getsize(p) > os.path.getsize(best):
                best = p
    except OSError:
        pass
    return best


def handle(task):
    S.tid = task['tid']
    S.files_seen = []
    S.in_pp = False
    S.reject = ''
    S.last = 0.0
    opts = task['opts']
    tmpd = task['tmp']
    try:
        os.makedirs(tmpd, exist_ok=True)
        ydl = get_ydl(opts, task['wid'])
        fmt, sort, fallback, _pps, _x = C.build_format(opts)
        ydl.params['format'] = fallback if task.get('fb') else fmt
        if task.get('fb') or not sort:
            ydl.params.pop('format_sort', None)
        else:
            ydl.params['format_sort'] = sort
        ydl.params['paths'] = {'home': tmpd}
        if task.get('fb'):
            ydl.params.pop('extractor_args', None)   # yt-dlp default clients
        else:
            ydl.params['extractor_args'] = {'youtube': {'player_client': C.FAST_CLIENTS}}
        info = ydl.extract_info(task['url'], download=True)
        if S.reject == 'live':
            send({'ev': 'error', 'tid': S.tid, 'kind': 'live', 'msg': 'Live stream or event that has not ended yet'})
            return
        if not info:
            send({'ev': 'error', 'tid': S.tid, 'kind': 'unavailable', 'msg': 'No information returned by YouTube'})
            return
        rd = info.get('requested_downloads') or []
        fp = rd[0].get('filepath') if rd else None
        if not fp or not os.path.exists(fp):
            fp = find_output(tmpd, info.get('id') or task.get('vid'))
        if not fp or not os.path.exists(fp):
            send({'ev': 'error', 'tid': S.tid, 'kind': 'postproc', 'msg': 'Final file not found after the download'})
            return
        send({'ev': 'done', 'tid': S.tid, 'fp': fp,
              'info': {'id': info.get('id'), 'title': info.get('title'), 'artist': info.get('artist'),
                       'track': info.get('track')}})
    except DownloadCancelled:
        send({'ev': 'error', 'tid': S.tid, 'kind': 'other', 'msg': 'cancelled'})
    except BaseException as e:  # noqa: BLE001
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        msg = C.clean_msg(e)
        send({'ev': 'error', 'tid': S.tid, 'msg': msg, 'errno': getattr(e, 'errno', None) if isinstance(e, OSError) else None})
        if C.classify_text(msg) in ('postproc', 'other'):
            try:
                S.ydl.close()
            except Exception:
                pass
            S.ydl = None


def main():
    send({'ev': 'ready', 'ytdlp': yt_dlp.version.__version__})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            task = json.loads(line)
        except ValueError:
            continue
        if task.get('op') == 'quit':
            break
        if task.get('op') == 'task':
            handle(task)


if __name__ == '__main__':
    main()
