"""S30 pod fix (2026-10-01): the director saw the pod hall empty behind Sara and Kevin. The agreed free fix is to zoom the
shot so the empty pod at the left edge and most of the empty office drop out of frame. The cut's S30 does not match the clip
now on disk, so the master frames themselves are zoomed. The caption is lifted from each original frame and pasted back at
its own place and size, so it matches the rest of the video.
Master frames 2751-2813 (1:31.7-1:33.8). Usage: python tools/podfix_s30.py  (reads gen/podfix/s30/fNNNNN.png, writes gen/textfix/pNNNNN.png)
"""
import os

import cv2
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SRC, OUT = os.path.join(ROOT, "gen", "podfix", "s30"), os.path.join(ROOT, "gen", "textfix")
FRAMES = range(2751, 2814)
X0, Y0, CW = 260, 0, 1660  # the zoom window (16:9, 1.157x, top-anchored so Sara keeps her head room): drops the left-edge pod
CH = round(CW * 9 / 16)


def caption_mask(im):
    """The caption's letters (white, or cyan for the sung word) plus a thin edge, in the band where captions sit."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    m = ((s < 45) & (v > 215)) | ((h > 80) & (h < 100) & (s > 120) & (v > 200))
    band = np.zeros_like(m)
    band[860:1080, 150:1500] = True
    m = (m & band).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(m, np.ones((3, 3), np.uint8)))
    keep = np.zeros(n, bool)
    keep[1:] = (st[1:, cv2.CC_STAT_HEIGHT] >= 18) & (st[1:, cv2.CC_STAT_HEIGHT] <= 80)  # letter-sized
    m = (keep[lab] & (m > 0)).astype(np.uint8)
    return cv2.GaussianBlur(cv2.dilate(m * 255, np.ones((5, 5), np.uint8)).astype(np.float32) / 255, (0, 0), 1.2)


def main():
    for n in FRAMES:
        im = cv2.imread(os.path.join(SRC, f"f{n:05d}.png"))
        a = caption_mask(im)
        clean = cv2.inpaint(im, cv2.dilate((a > 0.05).astype(np.uint8) * 255, np.ones((9, 9), np.uint8)), 7, cv2.INPAINT_TELEA)  # no second, zoomed caption
        zoom = cv2.resize(clean[Y0:Y0 + CH, X0:X0 + CW], (1920, 1080), interpolation=cv2.INTER_CUBIC)
        a = a[..., None]
        out = zoom * (1 - a) + im * a
        cv2.imwrite(os.path.join(OUT, f"p{n:05d}.png"), np.clip(out + 0.5, 0, 255).astype(np.uint8))
    print("patched", len(FRAMES), "frames")


if __name__ == "__main__":
    main()
