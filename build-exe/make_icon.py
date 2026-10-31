#!/usr/bin/env python3
"""Creates build-exe/icon.ico (the icon of YT-Grabber.exe) with the same design as the app icons: rounded square
pink-orange gradient with the download arrow. Pure Python, no external libraries."""
import math
import os
import struct
import sys
import zlib

C0, C1 = (244, 63, 94), (251, 122, 92)
SIZES = (16, 24, 32, 48, 64, 128, 256)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def rrect_inside(px, py, r):
    cx = min(max(px, r), 1 - r)
    cy = min(max(py, r), 1 - r)
    return math.hypot(px - cx, py - cy) <= r


def render_png(size):
    w = 0.075 if size >= 32 else 0.11   # on tiny icons the stroke must be thicker to stay readable
    segs = [((0.5, 0.22), (0.5, 0.58)), ((0.5, 0.60), (0.33, 0.43)), ((0.5, 0.60), (0.67, 0.43)), ((0.29, 0.77), (0.71, 0.77))]
    ss = 4 if size <= 64 else 3
    rows = []
    for j in range(size):
        row = bytearray()
        for i in range(size):
            bg = fg = 0
            for sj in range(ss):
                for si in range(ss):
                    px = (i + (si + .5) / ss) / size
                    py = (j + (sj + .5) / ss) / size
                    if rrect_inside(px, py, 0.22):
                        bg += 1
                        if any(seg_dist(px, py, a[0], a[1], b[0], b[1]) <= w / 2 for a, b in segs):
                            fg += 1
            if not bg:
                row += bytes((0, 0, 0, 0))
                continue
            t = (i + j) / (2.0 * size)
            f = fg / bg
            r, g, b = [(C0[k] + (C1[k] - C0[k]) * t) * (1 - f) + 255 * f for k in range(3)]
            row += bytes((int(r), int(g), int(b), int(255 * bg / (ss * ss))))
        rows.append(bytes(row))
    raw = b''.join(b'\x00' + r for r in rows)

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
    pngs = [(s, render_png(s)) for s in SIZES]
    head = struct.pack('<HHH', 0, 1, len(pngs))
    offset = 6 + 16 * len(pngs)
    entries, blobs = b'', b''
    for s, data in pngs:
        entries += struct.pack('<BBBBHHII', 0 if s >= 256 else s, 0 if s >= 256 else s, 0, 0, 1, 32, len(data), offset)
        blobs += data
        offset += len(data)
    with open(out, 'wb') as f:
        f.write(head + entries + blobs)
    print('Created', out, '(%d KB, sizes: %s)' % (os.path.getsize(out) // 1024, ', '.join(map(str, SIZES))))


if __name__ == '__main__':
    sys.exit(main())
