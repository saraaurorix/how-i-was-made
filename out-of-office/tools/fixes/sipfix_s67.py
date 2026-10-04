"""S67 fix (2026-10-01): in the cut, after the sip Sara's lip-synced take keeps talking although nothing is sung (the line is
the AUTO-REPLY caption). The director asked for her to just smile after the sip. The plain Kling clip (gen/clips/S67.mp4) does
exactly that: sip, lower the glass, smile and wave with closed lips. It is used from 1.0 s, through edit.py's own chain
(rendered to gen/podfix/s67new/nNNNNN.png by ffmpeg), and the AUTO-REPLY panel is lifted from each master frame and laid back
on, weighted by how visible the panel's cyan border is (so its fade-in matches).
Master frames 6183-6275 (3:26.1-3:29.2). Usage: python tools/sipfix_s67.py
"""
import os

import cv2
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
D = os.path.join(ROOT, "gen", "podfix")
OUT = os.path.join(ROOT, "gen", "textfix")
FRAMES = range(6183, 6276)
X0, X1, Y0, Y1 = 384, 1534, 844, 1006  # the panel, border included


def border(im):
    hsv = cv2.cvtColor(im[Y0:Y0 + 6, X0 + 20:X1 - 20], cv2.COLOR_BGR2HSV)
    return ((hsv[..., 0] > 80) & (hsv[..., 0] < 100) & (hsv[..., 1] > 80) & (hsv[..., 2] > 120)).mean()


def main():
    full = max(border(cv2.imread(os.path.join(D, "s67", f"f{n:05d}.png"))) for n in FRAMES)
    m = np.zeros((1080, 1920), np.float32)
    m[Y0:Y1, X0:X1] = 1
    m = cv2.GaussianBlur(m, (0, 0), 1.0)[..., None]
    for n in FRAMES:
        old = cv2.imread(os.path.join(D, "s67", f"f{n:05d}.png")).astype(np.float32)
        new = cv2.imread(os.path.join(D, "s67new", f"n{n:05d}.png")).astype(np.float32)
        a = m * min(1.0, border(old.astype(np.uint8)) / full * 1.15)
        out = new * (1 - a) + old * a
        cv2.imwrite(os.path.join(OUT, f"p{n:05d}.png"), np.clip(out + 0.5, 0, 255).astype(np.uint8))
    print("patched", len(FRAMES), "frames")


if __name__ == "__main__":
    main()
