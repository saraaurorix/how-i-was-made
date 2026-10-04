"""Reels fix (2026-10-01): the 9:16 reels hold S44 (the red-sky ticker) at reel frames 1633-1712 = master frames 4086-4165,
in reels.py's "fit" layout (the 16:9 frame at 1080 wide, 140 px above centre, over a blurred, darkened fill of itself).
Rebuild those frames from the text-fixed master with the same layout, into gen/reelfix/pNNNNN.png.
Usage: python tools/reelfix_s44.py
"""
import os

import cv2
import numpy as np

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gen", "reelfix")
REEL, MASTER, N = 1633, 4086, 80
VW, VH = 1080, 1920


def layout(fr):
    s = max(VW / fr.shape[1], VH / fr.shape[0])
    big = cv2.resize(fr, (round(fr.shape[1] * s), round(fr.shape[0] * s)), interpolation=cv2.INTER_AREA)
    x = (big.shape[1] - VW) // 2
    bg = cv2.GaussianBlur(big[:, x:x + VW], (0, 0), 28).astype(np.float32)
    bg = np.clip(bg - 0.18 * 255, 0, 255)
    fg = cv2.resize(fr, (VW, round(fr.shape[0] * VW / fr.shape[1] / 2) * 2), interpolation=cv2.INTER_AREA)
    y = (VH - fg.shape[0]) // 2 - 140
    bg[y:y + fg.shape[0]] = fg
    return np.clip(bg + 0.5, 0, 255).astype(np.uint8)


def main():
    for k in range(N):
        cv2.imwrite(os.path.join(D, f"p{REEL + k:05d}.png"), layout(cv2.imread(os.path.join(D, f"m{MASTER + k:05d}.png"))))
    print("rebuilt", N, "reel frames")


if __name__ == "__main__":
    main()
