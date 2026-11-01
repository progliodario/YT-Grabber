#!/usr/bin/env python3
"""Fills a data folder with a few downloads and subscriptions, so the page can be checked without a network or a download.

    python tests/a11y/seed.py DATA_ROOT        then:  YTG_DATA_ROOT=DATA_ROOT python program/server.py --no-browser

It writes the same files the program writes itself (data/jobs/*.json, data/subscriptions.json, data/settings.json): finished
and failed items, skipped ones, a paused job, a single-video job, an active subscription and a paused one with a problem.
"""
import json
import os
import sys
import time


def vid(n):
    return ('dQw4w9WgX%02d' % n)[:11]


def item(idx, state, title, ekind='', emsg='', file='', duration=212, uploader='Demo channel'):
    # idx, video id, title, state, error kind, error message, file, duration, uploader, attempts, duplicate number, url
    return [idx, vid(idx), title, state, ekind, emsg, file, duration, uploader, 1 if state == 'e' else 0, 1,
            'https://www.youtube.com/watch?v=' + vid(idx)]


def seed(root, download_dir=None):
    data = os.path.join(root, 'data')
    jobs = os.path.join(data, 'jobs')
    os.makedirs(jobs, exist_ok=True)
    download_dir = download_dir or os.path.join(root, 'downloads')
    now = time.time()
    opts = {'mode': 'audio', 'audio_format': 'mp3', 'mp3_bitrate': '192', 'video_height': '1080', 'embed': True,
            'single_only': False, 'force': False, 'cookies_browser': '', 'lang': '', 'check_updates': False, 'notify_done': False}

    names = ['Morning light', 'Slow river', 'Paper boats', 'Northern wind', 'Small hours', 'Glass garden', 'Open window',
             'Late train', 'Lemon tree', 'Quiet storm', 'Wide sky', 'Last chord']
    items = []
    for i, title in enumerate(names, 1):
        if i <= 6:
            items.append(item(i, 'd', title, file='%02d - %s.mp3' % (i, title)))
        elif i <= 8:
            items.append(item(i, 's', title, file='%02d - %s.mp3' % (i, title)))
        elif i == 9:
            items.append(item(i, 'e', title, 'private', 'Private video. Sign in if you have been granted access'))
        elif i == 10:
            items.append(item(i, 'e', title, 'geo', 'The uploader has not made this video available in your country'))
        else:
            items.append(item(i, 'k', title))
    jobs_data = [
        {'v': 1, 'id': 'a1000000001', 'url': 'https://www.youtube.com/playlist?list=PLdemo000001', 'urls': [], 'opts': opts,
         'title': 'Demo album: songs for a long train ride', 'kind': 'playlist', 'status': 'done', 'paused': False, 'declared': 12,
         'pad': 2, 'enum_done': True, 'pid': 'PLdemo000001', 'dir': os.path.join(download_dir, 'Demo album'), 'created': now - 7200,
         'finished': now - 7000, 'warning': '', 'message': '', 'sub': '', 'items': items},
        {'v': 1, 'id': 'a1000000002', 'url': 'https://www.youtube.com/playlist?list=PLdemo000002', 'urls': [], 'opts': opts,
         'title': 'Interrupted playlist', 'kind': 'playlist', 'status': 'running', 'paused': True, 'declared': 4,
         'pad': 2, 'enum_done': True, 'pid': 'PLdemo000002', 'dir': os.path.join(download_dir, 'Interrupted playlist'),
         'created': now - 600, 'finished': None, 'warning': '', 'message': '', 'sub': '',
         'items': [item(1, 'd', 'First song', file='01 - First song.mp3'), item(2, 'q', 'Second song'),
                   item(3, 'q', 'Third song'), item(4, 'q', 'Fourth song')]},
        {'v': 1, 'id': 'a1000000003', 'url': '2 videos', 'urls': ['https://www.youtube.com/watch?v=' + vid(1), 'https://www.youtube.com/watch?v=' + vid(2)],
         'opts': opts, 'title': 'Single videos', 'kind': 'single', 'status': 'done', 'paused': False, 'declared': 2, 'pad': 0,
         'enum_done': True, 'pid': '', 'dir': os.path.join(download_dir, 'Singles'), 'created': now - 60, 'finished': now - 30,
         'warning': '', 'message': '', 'sub': '',
         'items': [item(1, 'd', 'A single video', file='A single video.mp3'), item(2, 'd', 'Another single video', file='Another single video.mp3')]},
    ]
    for j in jobs_data:
        with open(os.path.join(jobs, j['id'] + '.json'), 'w', encoding='utf-8') as f:
            json.dump(j, f, ensure_ascii=False)

    subs = [
        {'id': 's1000000001', 'url': 'https://www.youtube.com/@demo/videos', 'title': 'Demo channel - Videos', 'opts': opts, 'hours': 24,
         'enabled': True, 'created': now - 86400, 'last_check': now - 3600, 'next_check': now + 80000, 'last_new': 2, 'status': 'ok',
         'message': '', 'only_new': True, 'seen': [vid(i) for i in range(1, 13)]},
        {'id': 's1000000002', 'url': 'https://www.youtube.com/playlist?list=PLdemo000009', 'title': 'Weekly mixes', 'opts': opts, 'hours': 168,
         'enabled': False, 'created': now - 86400 * 9, 'last_check': now - 86400, 'next_check': now + 500000, 'last_new': 0, 'status': 'error',
         'message': 'Playlist not found', 'only_new': False, 'seen': None},
    ]
    with open(os.path.join(data, 'subscriptions.json'), 'w', encoding='utf-8') as f:
        json.dump(subs, f, ensure_ascii=False)
    settings = dict(opts, download_dir=download_dir)
    with open(os.path.join(data, 'settings.json'), 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False)
    return root


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    seed(sys.argv[1])
    print('seeded', sys.argv[1])
