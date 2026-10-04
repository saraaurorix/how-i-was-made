"""Frame-level lip re-timing (free): warp an existing lip-sync clip so its mouth openings land on the sung words and the
mouth rests in the silences. Dynamic time warping between the clip's lip-opening curve and the word-masked vocal envelope;
each output frame picks a source frame (play on, hold, or skip one), within +-0.8 s.
Writes gen/lipsync_v2v/<id>.mp4 covering exactly the shot window (the editor prefers it, with no extra offset).

Usage: python tools/lip_retime.py ID [source_clip]
"""
import json
import os
import subprocess
import sys

import cv2
import imageio_ffmpeg
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import venc  # noqa: E402
from lipscore import apertures, envelope  # noqa: E402

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FPS, W, H = 30, 1920, 1080


def low_priority():
    """nice 19 for ffmpeg children (os.nice(19) raises when a background job already starts above 19)."""
    if os.getpriority(os.PRIO_PROCESS, 0) < 19:
        os.setpriority(os.PRIO_PROCESS, 0, 19)


def z(x):
    x = np.convolve(x, np.ones(3) / 3, mode="same")
    return (x - x.mean()) / (x.std() + 1e-9)


def retime(sid, src=None):
    S = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "storyboard.json")))}
    s = S[sid]
    nf = round(s["t1"] * FPS) - round(s["t0"] * FPS)
    src = src or os.path.join(ROOT, "gen/lipsync", sid + ".mp4")
    wav = os.path.join(ROOT, "lipsync", f"{sid}_m.wav")
    frames = []
    cap = cv2.VideoCapture(src)
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        frames.append(cv2.resize(fr, (W, H)))
    ap, fps = apertures(src)
    ap = np.where(np.isnan(ap), np.nanmean(ap), ap)
    env = envelope(wav, fps, nf)
    a, e = z(ap), z(env)
    ns, band, pen = len(a), int(0.8 * fps), float(os.environ.get("PEN", 0.35))
    INF = 1e18
    D = np.full((nf, ns), INF)
    B = np.zeros((nf, ns), np.int8)
    for s0 in range(min(ns, band + 1)):
        D[0, s0] = (a[s0] - e[0]) ** 2 + 0.02 * s0
    for t in range(1, nf):
        lo, hi = max(0, t - band), min(ns, t + band + 1)
        for j in range(lo, hi):
            c = (a[j] - e[t]) ** 2
            best, arg = D[t - 1, j - 1] if j >= 1 else INF, 0  # play on
            if D[t - 1, j] + pen < best:
                best, arg = D[t - 1, j] + pen, 1  # hold
            if j >= 2 and D[t - 1, j - 2] + pen < best:
                best, arg = D[t - 1, j - 2] + pen, 2  # skip one
            D[t, j] = c + best
            B[t, j] = arg
    j = int(np.argmin(D[nf - 1]))
    path = [j]
    for t in range(nf - 1, 0, -1):
        j = j - 1 if B[t, j] == 0 else (j if B[t, j] == 1 else j - 2)
        path.append(j)
    path = path[::-1]
    # smooth the warp (frame-by-frame holds/skips stutter): low-pass the DTW path into a gentle, even speed change
    # (0.75-1.25x), then blend neighbouring source frames instead of jumping between them
    raw = np.array(path, float)
    k = int(os.environ.get("SMOOTH", 21))
    sm = np.convolve(np.pad(raw, k // 2, mode="edge"), np.ones(k) / k, mode="valid")[:nf]
    for t in range(1, nf):
        sm[t] = min(max(sm[t], sm[t - 1] + 0.75), sm[t - 1] + 1.25)
    sm = np.clip(sm, 0, len(frames) - 1)
    out = os.path.join(ROOT, "gen/lipsync_v2v", sid + ".mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          *venc.h264(80), "-pix_fmt", "yuv420p", out],
                         stdin=subprocess.PIPE, preexec_fn=low_priority)  # low priority; venc.py picks the GPU encoder where there is one
    for x in sm:
        i0 = int(np.floor(x)); i1 = min(i0 + 1, len(frames) - 1); f = x - i0
        fr = frames[i0] if f < 0.08 or i1 == i0 else (frames[i1] if f > 0.92 else cv2.addWeighted(frames[i0], 1 - f, frames[i1], f, 0))
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    warped = np.interp(sm, np.arange(len(a)), a)
    path = [int(round(x)) for x in sm]
    before = float(np.corrcoef(a[:nf], e)[0, 1]) if ns >= nf else float("nan")
    after = float(np.corrcoef(warped, e)[0, 1])
    holds = sum(1 for x, y in zip(path, path[1:]) if y == x)
    skips = sum(1 for x, y in zip(path, path[1:]) if y == x + 2)
    print(f"{sid}: corr {before:.2f} -> {after:.2f}; holds {holds}, skips {skips}, source frames {path[0]}..{path[-1]} of {ns}; wrote {out}")
    return after


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    retime(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
