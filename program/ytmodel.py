"""What a download is: Item (one video) and Job (a link and its items). They hold data only: the server does the work."""
import time
from collections import Counter, deque


class ItemFailure(Exception):
    def __init__(self, kind, msg):
        super().__init__(msg)
        self.kind = kind


SKIP_BY_USER = 'user'   # emsg of an item in state k that the user deselected (the page shows its own text)


class Item:
    __slots__ = ('idx', 'vid', 'url', 'title', 'duration', 'uploader', 'dupn', 'state', 'progress', 'speed', 'eta',
                 'size', 'stage', 'attempts', 'ekind', 'emsg', 'file', 'ver', 'not_before', 'files_seen', 'fb',
                 'lastp', 'reject', 'slot')

    def __init__(self, idx, vid, url, title='', duration=None, uploader='', dupn=1):
        self.idx = idx
        self.vid = vid
        self.url = url
        self.title = title or ''
        self.duration = duration
        self.uploader = uploader or ''
        self.dupn = dupn
        self.slot = False    # occupies one of the 10 download slots
        self.state = 'q'     # q queued | a downloading | p converting | d done | e error | s already present | c cancelled
        #                      k skipped: it was already there when the subscription ("only new videos") started, or the user
        #                        deselected it (then emsg is SKIP_BY_USER)
        self.progress = 0.0
        self.speed = 0
        self.eta = None
        self.size = None
        self.stage = ''
        self.attempts = 0
        self.ekind = ''
        self.emsg = ''
        self.file = ''
        self.ver = 0
        self.not_before = 0.0
        self.files_seen = []
        self.fb = False
        self.lastp = 0.0
        self.reject = ''

    def key(self):
        base = self.vid or ('idx%d' % self.idx)
        return base if self.dupn <= 1 else '%s#%d' % (base, self.dupn)

    def to_json(self, now):
        return {
            'i': self.idx, 's': self.state, 'v': self.vid, 't': self.title, 'p': round(self.progress, 1),
            'sp': int(self.speed or 0), 'eta': self.eta, 'sz': self.size, 'st': self.stage, 'a': self.attempts,
            'ek': self.ekind, 'em': self.emsg, 'f': self.file, 'd': self.duration, 'u': self.uploader,
            'rt': int(max(0, self.not_before - now)) if (self.state == 'q' and self.not_before > now) else 0,
            'ver': self.ver,
        }


class Job:
    def __init__(self, jid, url, opts, urls=None):
        self.id = jid
        self.url = url
        self.urls = urls or []       # for the "single videos"
        self.opts = opts
        self.title = ''
        self.kind = 'playlist'       # playlist | single
        self.status = 'enumerating'  # enumerating | running | done | cancelled | error
        self.paused = False
        self.interrupted = False
        self.items = []
        self.counts = Counter()
        self.seq = 0
        self.queue = deque()
        self.delayed = []
        self.declared = None
        self.pad = None              # None = not known yet; 0 = no numbering
        self.enum_done = False
        self.pid = ''
        self.dir = ''
        self.created = time.time()
        self.finished = None
        self.warning = ''
        self.message = ''
        self.recent = deque(maxlen=200)
        self.seen = Counter()
        self.run_started = time.time()
        self.cancel = False
        self.dirty = True
        self.enum_thread = None
        self.pp_done = False
        self.sub_id = ''             # set when this job is a run of a subscription
        self.sub_auto = False        # True for the checks started by the scheduler (they vanish if nothing is new)
        self.choosing = False        # the user asked to choose the videos first: the job waits (paused) until they press Start

    # all the following methods must be called with LOCK held
    def touch(self, it):
        self.seq += 1
        it.ver = self.seq

    def set_state(self, it, st):
        if it.state == st:
            self.touch(it)
            return
        self.counts[it.state] -= 1
        self.counts[st] += 1
        it.state = st
        self.touch(it)
        self.dirty = True

    def add_item(self, it, enqueue=True):
        self.items.append(it)
        self.counts[it.state] += 1
        self.touch(it)
        self.dirty = True
        if it.state == 'q' and enqueue:
            self.queue.append(it)

    def numbered(self):
        return bool(self.pad)

    def summary(self, now=None):
        now = now or time.time()
        c = self.counts
        total = len(self.items)
        speed = 0
        err_idx = []
        by_user = 0
        for it in self.items:
            if it.state == 'a':
                speed += it.speed or 0
            elif it.state == 'e' and len(err_idx) < 80:
                err_idx.append(it.idx)
            elif it.state == 'k' and it.emsg == SKIP_BY_USER:
                by_user += 1
        finished_n = c['d'] + c['s'] + c['e'] + c['c'] + c['k']
        eta = None
        if self.status in ('running', 'enumerating') and not self.paused:
            win = [t for t in self.recent if now - t <= 90]
            remaining = c['q'] + c['a'] + c['p']
            if len(win) >= 3 and remaining:
                span = max(5.0, now - win[0])
                rate = len(win) / span
                eta = int(remaining / rate) if rate > 0 else None
        return {
            'id': self.id, 'url': self.url, 'title': self.title or self.url, 'kind': self.kind, 'status': self.status,
            'paused': self.paused, 'interrupted': self.interrupted, 'dir': self.dir, 'created': self.created,
            'finished': self.finished, 'warning': self.warning, 'message': self.message, 'seq': self.seq,
            'declared': self.declared, 'enum_done': self.enum_done, 'total': total, 'pad': self.pad or 0,
            'counts': {k: c[k] for k in ('q', 'a', 'p', 'd', 'e', 's', 'c', 'k')}, 'speed': int(speed), 'eta': eta,
            'processed': finished_n, 'opts': self.opts, 'err_idx': err_idx,
            'cover': self.items[0].vid if self.items else '', 'choosing': self.choosing, 'skipped_by_user': by_user,
        }

    def to_disk(self):
        return {
            'v': 1, 'id': self.id, 'url': self.url, 'urls': self.urls, 'opts': self.opts, 'title': self.title,
            'kind': self.kind, 'status': self.status, 'paused': self.paused, 'declared': self.declared,
            'pad': self.pad, 'enum_done': self.enum_done, 'pid': self.pid, 'dir': self.dir, 'created': self.created,
            'finished': self.finished, 'warning': self.warning, 'message': self.message, 'sub': self.sub_id,
            'choosing': self.choosing,
            'items': [[i.idx, i.vid, i.title, i.state, i.ekind, i.emsg, i.file, i.duration, i.uploader, i.attempts,
                       i.dupn, i.url] for i in self.items],
        }
