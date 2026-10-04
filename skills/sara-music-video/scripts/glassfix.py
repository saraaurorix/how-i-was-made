"""Put back a prop that sync.so lip-sync erased: composite it from the lip-sync INPUT over fal's OUTPUT, only inside the box fal
repainted (from under the eyes to the chin). Made for a shot where Sara lowers a pair of sunglasses through her mouth box and
lipsync-2-pro wiped the lenses; the mouth stays fal's.

Usage: python tools/glassfix.py gen/v2v_in/ID.mp4 gen/old/.../ID.mp4 out.mp4   (input, fal output, result; same size and frame count)
The mask is tuned for GOLD RIMS + BROWN LENSES (HSV hue 9-32): for another prop (a mic, a glass, a hand) change `lens`/`rim` in
glasses_mask() and check a few frames first (base | fal | composite sheet) before building the whole clip. Keep fal's original.
"""
import os, subprocess, sys
import cv2, numpy as np
import imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import venc  # noqa: E402
FF = imageio_ffmpeg.get_ffmpeg_exe()
cv2.setNumThreads(2)

def size(p):
    import re
    e = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    return tuple(int(v) for v in re.search(r"Video:.*?, (\d+)x(\d+)", e).groups())


def frames(p):
    w, h = size(p)
    o = subprocess.run([FF, "-v", "error", "-i", p, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(o, np.uint8).reshape(-1, h, w, 3)

def glasses_mask(a, b):
    hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
    h, s, v = (hsv[..., k].astype(int) for k in range(3))
    changed = np.abs(a.astype(int) - b.astype(int)).sum(axis=2) > 40
    zone = cv2.dilate(changed.astype(np.uint8), np.ones((31, 31), np.uint8)) > 0   # only where fal repainted
    lens = (h >= 9) & (h <= 28) & (s >= 70) & (v <= 190)
    rim = (h >= 14) & (h <= 32) & (s >= 90) & (v >= 120)
    m = ((lens | rim) & zone).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))          # join broken rims and speckled lenses
    ff = m.copy(); cv2.floodFill(ff, np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8), (0, 0), 255)
    m = m | cv2.bitwise_not(ff)                                                      # fill closed rim loops (the lenses)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    out = np.zeros_like(m)
    small = []
    for k in range(1, n):
        comp = (lab == k).astype(np.uint8)
        if stats[k, cv2.CC_STAT_AREA] >= 1500:                                       # a lens (or both): solid convex shape
            cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.fillPoly(out, [cv2.convexHull(np.vstack(cnts))], 255)
        elif stats[k, cv2.CC_STAT_AREA] >= 40:
            small.append(comp)
    near = cv2.dilate(out, np.ones((31, 31), np.uint8)) > 0
    for comp in small:                                                               # rim, bridge, arms: only touching a lens,
        if (comp.astype(bool) & near).any() or not out.any():                        # so stray specks on the chin stay fal's
            out[comp > 0] = 255
    return out & (zone.astype(np.uint8) * 255)

def composite(a, b, m):
    soft = cv2.GaussianBlur(m, (0, 0), 1.5).astype(np.float32)[..., None] / 255
    return (b * (1 - soft) + a * soft).astype(np.uint8)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    base, fal, out = sys.argv[1:4]
    A, B = frames(base), frames(fal)
    assert len(A) == len(B), (len(A), len(B))
    w, h = size(fal)
    enc = subprocess.Popen(["nice", "-n", "19", FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", "30",
                            "-i", "-", "-i", fal, "-map", "0:v", "-map", "1:a?", "-vf", "format=nv12", *venc.h264(80),
                            "-c:a", "copy", "-shortest", out], stdin=subprocess.PIPE)
    for a, b in zip(A, B):
        enc.stdin.write(composite(a, b, glasses_mask(a, b)).tobytes())
    enc.stdin.close()
    sys.exit(enc.wait())
