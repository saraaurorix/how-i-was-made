"""S13 text fix (2026-10-01): when Sara lifts the SOLVED stamp toward the camera, Kling scrambles its face into
"BOLVED / SUBVED / HOIVED" (master frames 1302-1321, 0:43.4-0:44.0). Paste a clean SOLVED face onto the block in each frame.

Round 1 pasted the angled, blurred face from frame 1300 and stretched it up to 1.45x to fit the front-on frames: the director
said it looked distorted. Round 2 pastes a sharp front-on face (textfix_s13_face.py: frame 1316 with its U and B
replaced) and only lets it squash for the tilted frames, with at most a small stretch.

The block is found per frame as the largest red blob (a wide opening drops thin red bits of the set), its rotated
rectangle smoothed over the source frames (the 24 -> 30 fps duplicates count once). The letter panel of the frame-1300 face
is mapped onto it, shifted and scaled to where that frame's letter row sits (the face tilts, so the row moves up the block;
found by matching the stroke profile down the block), colour-matched to the frame and smeared along the block's motion.
Usage: python tools/textfix_s13.py   (reads gen/textfix/fNNNNN.png, writes gen/textfix/pNNNNN.png)
"""
import os

import cv2
import numpy as np
from scipy.signal import savgol_filter

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gen", "textfix")
REF = 1300
FRAMES = range(1302, 1322)
SHUTTER = 0.8  # blur length as a share of the per-frame motion, judged against Kling's own smear on 1309-1312
PANEL = (0.07, 0.09, 0.94, 0.60)  # the part of the clean face that is pasted: the letters inside the rim (x0, y0, x1, y1)
FACE = "s13_face.png"  # the clean front-on face from textfix_s13_face.py, in frame 1316's block coordinates
FACE_ROW = 69  # its letter row's centre
SY = (0.75, 1.16)  # allowed vertical scale: squash for the tilted early frames, never a big stretch (round 1 looked distorted)
KEEP = (0.03, 0.05, 0.97, 0.96)  # never paint outside this part of the target block (its outer edges stay original)


def load(n):
    return cv2.imread(os.path.join(D, f"f{n:05d}.png"))


def block(n):
    hsv = cv2.cvtColor(load(n), cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    m = (((h < 8) | (h > 172)) & (s > 110) & (v > 45)).astype(np.uint8) * 255
    m[950:] = 0  # the captions and the ink on the desk
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((35, 35), np.uint8))
    _, lab, st, _ = cv2.connectedComponentsWithStats(m)
    (cx, cy), (w, h), a = cv2.minAreaRect(cv2.findNonZero((lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8)))
    if w < h:
        w, h, a = h, w, a + 90
    if a > 45:
        a -= 180
    return [cx, cy, w, h, a]


def to_frame(p, TW, TH):
    """Affine map from decal pixels to the frame for block params p = (cx, cy, w, h, angle)."""
    cx, cy, w, h, a = p
    r = np.deg2rad(a)
    R = np.array([[np.cos(r), -np.sin(r)], [np.sin(r), np.cos(r)]]) @ np.diag([w / TW, h / TH])
    return np.hstack([R, (np.array([cx, cy]) - R @ np.array([TW / 2, TH / 2]))[:, None]])


def profile(img, TW):
    """Vertical-edge strength per row of a block image: high on the letter strokes."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)[:, int(.12 * TW):int(.88 * TW)]
    return np.abs(np.diff(g, axis=1)).mean(1)


def align(dec_p, frm_p, TH, c):
    """(dy, sy) that best lays the decal's letter row onto the frame's, scaling about row c."""
    best, ys = (-2, 0, 1), np.arange(TH)
    for sy in np.arange(SY[0], SY[1], 0.05):
        for dy in range(-int(.4 * TH), int(.4 * TH)):
            src = (ys - c - dy) / sy + c  # decal row that lands on frame row y
            ok = (src >= 0) & (src <= TH - 1)
            if ok.sum() < TH * 0.6:
                continue
            r = np.corrcoef(np.interp(src[ok], ys, dec_p), frm_p[ok])[0, 1]
            if r > best[0]:
                best = (r, dy, sy)
    return best


def main():
    ids = list(range(REF - 2, FRAMES[-1] + 3))
    raw = {n: block(n) for n in ids}
    uniq, seen = [], None  # one entry per source frame
    for n in ids:
        if seen is None or np.abs(np.array(raw[n]) - seen).max() > 0.01:
            uniq.append(n)
            seen = np.array(raw[n])
    sm = savgol_filter(np.array([raw[n] for n in uniq]), 5, 2, axis=0)
    par = {}
    for n in ids:
        par[n] = sm[max(i for i, u in enumerate(uniq) if u <= n)]
    decal = cv2.imread(os.path.join(D, FACE))
    TH, TW = decal.shape[:2]
    dec_p, c = profile(decal, TW), FACE_ROW
    fit = {}
    for n in FRAMES:
        A = to_frame(par[n], TW, TH)
        fit[n] = align(dec_p, profile(cv2.warpAffine(load(n), cv2.invertAffineTransform(A), (TW, TH), flags=cv2.INTER_CUBIC), TW), TH, c)
    raw_fit = np.array([fit[n][1:] for n in FRAMES], float)
    good = np.array([fit[n][0] >= 0.9 for n in FRAMES])  # a weak match (the tilted, smeared frames) is interpolated instead
    for j in range(2):
        raw_fit[~good, j] = np.interp(np.flatnonzero(~good), np.flatnonzero(good), raw_fit[good, j])
    fs = savgol_filter(raw_fit, 7, 2, axis=0)
    for i, n in enumerate(FRAMES):
        print(n, "r=%.2f dy=%d sy=%.2f -> dy=%.1f sy=%.3f" % (*fit[n], *fs[i]))
    x0, y0, x1, y1 = (int(PANEL[0] * TW), int(PANEL[1] * TH), int(PANEL[2] * TW), int(PANEL[3] * TH))
    alpha = np.zeros((TH, TW), np.float32)
    alpha[y0:y1, x0:x1] = 1
    keep = np.zeros((TH, TW), np.float32)
    keep[int(KEEP[1] * TH):int(KEEP[3] * TH), int(KEEP[0] * TW):int(KEEP[2] * TW)] = 1
    for i, n in enumerate(FRAMES):
        dy, sy = fs[i]
        S = np.array([[1, 0, 0], [0, sy, (1 - sy) * c + dy], [0, 0, 1]])
        im = load(n)
        H, W = im.shape[:2]
        A = to_frame(par[n], TW, TH)
        dec_b = cv2.warpAffine(decal, S[:2], (TW, TH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        a_b = cv2.GaussianBlur(cv2.warpAffine(alpha, S[:2], (TW, TH), flags=cv2.INTER_LINEAR) * keep, (0, 0), 3)
        dec = cv2.warpAffine(dec_b, A, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        a = cv2.warpAffine(a_b, A, (W, H), flags=cv2.INTER_LINEAR)
        # smear along the block's motion between the neighbouring frames
        v = (np.array(par[n + 1][:2]) - np.array(par[n - 1][:2])) / 2
        L = max(1, int(round(np.hypot(*v) * SHUTTER)))
        if L > 1:
            k = np.zeros((L * 2 + 1, L * 2 + 1), np.float32)
            d = v / (np.hypot(*v) + 1e-6)
            for t in np.linspace(-L / 2, L / 2, L * 4):
                k[int(round(L + t * d[1])), int(round(L + t * d[0]))] = 1
            k /= k.sum()
            dec = cv2.filter2D(dec, -1, k)
            a = np.clip(cv2.filter2D(a, -1, k) * 2, 0, 1)  # a steep edge: a soft smeared one lets the old letters show through
        # match the frame's colour and contrast inside the panel
        m = a > 0.9
        src = cv2.cvtColor(np.clip(dec, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
        ref = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
        for c in range(3):
            s_m, s_s, r_m, r_s = src[..., c][m].mean(), src[..., c][m].std(), ref[..., c][m].mean(), ref[..., c][m].std()
            src[..., c] = (src[..., c] - s_m) * (r_s / (s_s + 1e-6) if c == 0 else 1) + r_m
        dec = cv2.cvtColor(np.clip(src, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
        out = im * (1 - a[..., None]) + dec * a[..., None]
        cv2.imwrite(os.path.join(D, f"p{n:05d}.png"), np.clip(out + 0.5, 0, 255).astype(np.uint8))
    print("patched", len(FRAMES), "frames")


if __name__ == "__main__":
    main()
