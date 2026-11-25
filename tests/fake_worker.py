"""A stand-in for program/ytworker.py that never touches the network (the server starts it when YTG_WORKER points here).

It speaks the same protocol: JSON lines on stdin (tasks) and on stdout (events). What a video id does:

    starts with SLOW   downloads in many small steps (about 3 seconds), so that a test can cancel or look at it halfway
    starts with ERRPRIV fails with "Private video" (not retried)
    starts with ERRNET  always fails with a network error
    starts with FLAKY   fails with a network error on the first attempt and works on the second
    starts with SAME    has the title "Same" (to check that two videos with one title are both kept)
    anything else       works at once; the title is "Title <id>"

The file written is <tmp>/<id>.m4a and contains "content of <id>".
"""
import json
import os
import sys
import time

OUT = sys.stdout
sys.stdout = sys.stderr


def send(obj):
    OUT.write(json.dumps(obj) + '\n')
    OUT.flush()


def title_of(vid):
    return 'Same' if vid.startswith('SAME') else 'Title ' + vid


def handle(task):
    tid, vid, tmp = task['tid'], task.get('vid') or '', task['tmp']
    attempt = int(tid.rsplit('-', 1)[-1])
    if vid.startswith('ERRPRIV'):
        send({'ev': 'error', 'tid': tid, 'kind': 'private', 'msg': 'Private video. Sign in if you have been granted access'})
        return
    if vid.startswith('ERRNET') or (vid.startswith('FLAKY') and attempt == 1):
        send({'ev': 'error', 'tid': tid, 'msg': 'Unable to download webpage: connection reset by peer'})
        return
    os.makedirs(tmp, exist_ok=True)
    steps = 8 if vid.startswith('SLOW') else 2
    for i in range(1, steps + 1):
        send({'ev': 'progress', 'tid': tid, 'pct': 90.0 * i / steps, 'speed': 1000000, 'eta': steps - i, 'size': 1000, 'stage': 'Download'})
        if vid.startswith('SLOW'):
            time.sleep(0.2)
    path = os.path.join(tmp, vid + '.m4a')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('content of ' + vid)
    send({'ev': 'phase', 'tid': tid, 'stage': 'Converting audio'})
    send({'ev': 'done', 'tid': tid, 'fp': path, 'info': {'id': vid, 'title': title_of(vid)}})


def main():
    send({'ev': 'ready', 'ytdlp': 'fake'})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        task = json.loads(line)
        if task.get('op') == 'quit':
            break
        if task.get('op') == 'task':
            handle(task)


if __name__ == '__main__':
    main()
