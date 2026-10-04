"""Reels fix (2026-10-01): the reels hold S46 at reel frames 1851-1967 = master frames 4305-4421, in the "fit" layout,
with the reels' own TERMS OF SERVICE panel at the box below. The new nun-free take is laid out like reelfix_s44.layout,
and the reel's panel is moved onto it with rework_s46.rebuild (old layout vs the reel frame gives the panel's transparency).
Usage: python tools/reelfix_s46.py   (writes gen/reelfix/pNNNNN.png)
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reelfix_s44 as R  # noqa: E402
import rework_s46 as W  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
REEL, MASTER, N = 1851, 4305, 117
BOX = (110, 970, 1345, 1508)


def main():
    for k in range(N):
        old = R.layout(cv2.imread(os.path.join(W.D, "old", f"b{MASTER + k:05d}.png"))).astype(np.float32)
        new = R.layout(cv2.imread(os.path.join(W.D, "new", f"b{MASTER + k:05d}.png"))).astype(np.float32)
        reel = cv2.imread(os.path.join(ROOT, "gen", "reelfix46", f"r{REEL + k:05d}.png")).astype(np.float32)
        out = W.rebuild(old, new, reel, BOX)
        cv2.imwrite(os.path.join(ROOT, "gen", "reelfix", f"p{REEL + k:05d}.png"), np.clip(out + 0.5, 0, 255).astype(np.uint8))
    print("rebuilt", N, "reel frames")


if __name__ == "__main__":
    main()
