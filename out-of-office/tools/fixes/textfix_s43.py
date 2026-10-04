"""S43 text fix (2026-10-01): Kling garbled the queue sign's YOUR NUMBER into "8, <glyph>,000,000". Rebuild it as 8,000,000,000.

The sign is a flat LED panel, so each frame is rectified with a SIFT homography to frame 4000 (smoothed over time), the
garbled "," + glyph span is replaced by a pixel copy of the sign's own ",000" group from the same frame, and only that
span is warped back. Each frame keeps its own grain and light. Works on frames extracted from the master into gen/textfix/.
Usage: python tools/textfix_s43.py   (reads gen/textfix/fNNNNN.png, writes gen/textfix/pNNNNN.png)
"""
import json
import os

import cv2
import numpy as np
from scipy.signal import savgol_filter

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gen", "textfix")
FRAMES = range(3948, 4050)  # S43 in the master, 30 fps
REF = 4000
CORNERS = np.float32([[322, 322], [1912, 66], [1905, 322], [322, 425]])  # sign panel TL, TR, BR, BL in the ref frame (for tracking)
RW, RH, CAP, BASE = 2400, 200, 40, 160  # rectified size; the rows the text's cap line and baseline land on
XL, XR = 330, 1890  # two vertical lines through the sign in the ref frame


def text_lines(im):
    """Cap line and baseline of the sign's text in the ref frame, as (slope, intercept), fitted to every glyph column.
    Rectifying on these (not on guessed panel corners) keeps a copied digit group on the same line as its neighbours."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    txt = (((h > 75) & (h < 105)) | ((h > 135) & (h < 170))) & (v > 130) & (s > 70)
    txt[:, :XL] = False
    txt[450:] = False
    txt = cv2.morphologyEx(txt.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    tops, bots = [], []
    for x in range(XL + 10, XR - 10, 4):
        ys = np.where(txt[:, x])[0]
        if len(ys) > 20 and ys.max() - ys.min() > 60:
            tops.append((x, ys.min()))
            bots.append((x, ys.max()))
    out = []
    for P in (np.array(tops, float), np.array(bots, float)):
        for _ in range(3):
            k, b = np.polyfit(P[:, 0], P[:, 1], 1)
            r = P[:, 1] - (k * P[:, 0] + b)
            P = P[np.abs(r) < max(3, 2.5 * np.std(r))]
        out.append((k, b))
    return out


def rectifier(im):
    (kc, bc), (kb, bb) = text_lines(im)
    src = np.float32([[XL, kc * XL + bc], [XR, kc * XR + bc], [XR, kb * XR + bb], [XL, kb * XL + bb]])
    return cv2.getPerspectiveTransform(src, np.float32([[0, CAP], [RW, CAP], [RW, BASE], [0, BASE]]))


def runs(rect):
    """Column spans of cyan glyphs in the rectified sign."""
    hsv = cv2.cvtColor(rect, cv2.COLOR_BGR2HSV)
    cy = ((hsv[..., 0] > 75) & (hsv[..., 0] < 105) & (hsv[..., 2] > 120) & (hsv[..., 1] > 60))[CAP - 10:BASE + 10]
    xs = np.where(cy.sum(0) > 2)[0]
    out, s0, p0 = [], xs[0], xs[0]
    for x in xs[1:]:
        if x > p0 + 3:
            out.append((s0, p0))
            s0 = x
        p0 = x
    return out + [(s0, p0)]


def track():
    sift = cv2.SIFT_create(4000)
    ref = cv2.imread(os.path.join(D, f"f{REF:05d}.png"), 0)
    mask = np.zeros_like(ref)
    cv2.fillPoly(mask, [np.int32(CORNERS)], 255)
    kr, dr = sift.detectAndCompute(ref, cv2.dilate(mask, np.ones((15, 15))))
    bf, corners = cv2.BFMatcher(), []
    for n in FRAMES:
        k, d = sift.detectAndCompute(cv2.imread(os.path.join(D, f"f{n:05d}.png"), 0), None)
        m = [a for a, b in bf.knnMatch(dr, d, k=2) if a.distance < 0.75 * b.distance]
        H, _ = cv2.findHomography(np.float32([kr[a.queryIdx].pt for a in m]), np.float32([k[a.trainIdx].pt for a in m]), cv2.RANSAC, 2.0)
        corners.append(cv2.perspectiveTransform(CORNERS[None], H)[0])
    c = savgol_filter(np.array(corners), 9, 2, axis=0)  # take out the per-frame jitter of the fit
    return {n: cv2.getPerspectiveTransform(CORNERS, c[i].astype(np.float32)) for i, n in enumerate(FRAMES)}


def main():
    Hs = track()
    ref = cv2.imread(os.path.join(D, f"f{REF:05d}.png"))
    R = rectifier(ref)
    ref_rect = cv2.warpPerspective(ref, R, (RW, RH), flags=cv2.INTER_CUBIC)
    # find the glyphs: "8" is the first wide cyan run after "1"; commas are the narrow runs
    rs = [r for r in runs(ref_rect) if r[0] > 0.6 * RW]
    eight = rs[0]
    commas = [r for r in rs if r[1] - r[0] < 0.4 * (eight[1] - eight[0])]
    ca, c1, c2 = commas[0], commas[-2], commas[-1]
    # ca: the comma after "8"; c1: the comma of the first good ",000"; c2: the comma of the last ",000"
    pitch = c2[0] - c1[0]
    SRC, DST, LEN = c1[0] - 4, ca[0] - 4, pitch
    X0, X1 = eight[1] + 2, c1[0] - 2
    print("8", eight, "commas", ca, c1, c2, "pitch", pitch, "copy", SRC, "->", DST, "change", X0, X1)
    alpha = np.zeros((RH, RW), np.float32)
    alpha[CAP - 22:BASE + 22, X0:X1] = 1  # the text band only: the panel's borders stay original
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.5)
    new_dbg = ref_rect.copy()
    new_dbg[:, DST:DST + LEN] = ref_rect[:, SRC:SRC + LEN]
    cv2.imwrite(os.path.join(D, "s43_rect_new.png"), np.vstack([ref_rect, new_dbg]))
    for n in FRAMES:
        im = cv2.imread(os.path.join(D, f"f{n:05d}.png"))
        h, w = im.shape[:2]
        M = R @ np.linalg.inv(Hs[n])  # frame -> rectified sign
        rect = cv2.warpPerspective(im, M, (RW, RH), flags=cv2.INTER_CUBIC)
        valid = cv2.warpPerspective(np.ones((h, w), np.uint8), M, (RW, RH), flags=cv2.INTER_NEAREST) > 0
        rect[~valid] = ref_rect[~valid]  # the sign's top edge is off-frame early in the shot
        new = rect.copy()
        new[:, DST:DST + LEN] = rect[:, SRC:SRC + LEN]
        back = cv2.warpPerspective(new, np.linalg.inv(M), (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        a = cv2.warpPerspective(alpha, np.linalg.inv(M), (w, h), flags=cv2.INTER_LINEAR)[..., None]
        out = im * (1 - a) + back * a
        cv2.imwrite(os.path.join(D, f"p{n:05d}.png"), np.clip(out + 0.5, 0, 255).astype(np.uint8))
    json.dump({n: H.tolist() for n, H in Hs.items()}, open(os.path.join(D, "s43_H.json"), "w"))
    print("patched", len(FRAMES), "frames")


if __name__ == "__main__":
    main()
