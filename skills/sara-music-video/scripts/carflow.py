"""Which way do the cars in a clip actually move? Mean horizontal optical flow of the moving pixels in a region, per ~0.12 s.

Compare the sign with the cars' nose direction in the still: nose left + negative flow = forward; nose left + positive = tail-first.
Eyeballing thumbnails got this wrong more than once, so check every moving-car clip with this.
Usage: python tools/carflow.py CLIP [x0 x1 y0 y1]   (region as fractions of the frame; default 0.45 1 0.35 0.8)
"""
import sys

import cv2
import numpy as np


def flow_x(path, x0=0.45, x1=1.0, y0=0.35, y1=0.8, fps=8, thr=2.0):
    cap = cv2.VideoCapture(path)
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 24
    step = max(1, round(src_fps / fps))
    prev, i, out = None, 0, []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % step == 0:
            h, w = f.shape[:2]
            g = cv2.cvtColor(cv2.resize(f[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)], None, fx=0.5, fy=0.5), cv2.COLOR_BGR2GRAY)
            if prev is not None:
                fl = cv2.calcOpticalFlowFarneback(prev, g, None, 0.5, 3, 21, 3, 5, 1.1, 0)
                m = np.hypot(fl[..., 0], fl[..., 1]) > thr
                if m.sum() > 200:
                    out.append((round(i / src_fps, 2), round(float(fl[..., 0][m].mean()), 1)))
            prev = g
        i += 1
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    args = [float(a) for a in sys.argv[2:6]] if len(sys.argv) >= 6 else []
    for t, dx in flow_x(sys.argv[1], *args):
        print(f"{t:5.2f}s  {'>' * min(20, int(dx)) if dx > 0 else '<' * min(20, int(-dx))}  {dx:+.1f}")
