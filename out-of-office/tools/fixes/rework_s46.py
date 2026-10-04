"""S46 rework (2026-10-01): the director flagged a nun bowing to the I AGREE button at 2:25 (religious imagery is out of bounds for this project).
New take: the still with the nun swapped for an office worker (ChatGPT edit, gen/s46fix/S46_nonun_b.png), lip-synced to
the same audio with Wan 2.7 on fal (take w4: the crowd stands still, Kevin taps the button). Four paid takes.
The semi-transparent TERMS OF SERVICE panel is rebuilt over the new take. Its transparency is measured per frame from
the old cut: on the panel's fill, master = a * old_frame + b. The letters, which are near opaque, come straight from
the old master.
Master frames 4305-4421 (2:23.5-2:27.4). Usage: python tools/rework_s46.py
"""
import os

import cv2
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
D = os.path.join(ROOT, "gen", "s46fix")
OUT = os.path.join(ROOT, "gen", "textfix")
FRAMES = range(4305, 4422)
X0, X1, Y0, Y1 = 455, 1466, 847, 1004  # the panel, border included


def rebuild(old, new, mst, box):
    """Lay the panel from mst (made over old) onto new, inside box = (x0, x1, y0, y1)."""
    x0, x1, y0, y1 = box
    out = new.copy()
    po, pn, pm = old[y0:y1, x0:x1], new[y0:y1, x0:x1], mst[y0:y1, x0:x1]
    if np.abs(pm - po).sum(2).mean() < 6:  # panel not up yet (it fades in)
        return out
    lum = pm.mean(2)
    fill = lum < np.percentile(lum, 80)  # the dark fill, not the letters or the border
    fits = [np.polyfit(po[..., c][fill], pm[..., c][fill], 1) for c in range(3)]
    rec = np.stack([np.polyval(fits[c], pn[..., c]) for c in range(3)], 2)
    resid = np.abs(pm - np.stack([np.polyval(fits[c], po[..., c]) for c in range(3)], 2)).sum(2)
    ink = cv2.GaussianBlur(np.clip((resid - 25) / 40, 0, 1).astype(np.float32), (0, 0), 0.8)[..., None]
    out[y0:y1, x0:x1] = rec * (1 - ink) + pm * ink  # letters and border: what the fit can't explain is the panel's own ink
    return out


def main():
    for n in FRAMES:
        old = cv2.imread(os.path.join(D, "old", f"b{n:05d}.png")).astype(np.float32)
        new = cv2.imread(os.path.join(D, "new", f"b{n:05d}.png")).astype(np.float32)
        mst = cv2.imread(os.path.join(D, "m", f"f{n:05d}.png")).astype(np.float32)
        out = rebuild(old, new, mst, (X0, X1, Y0, Y1))
        cv2.imwrite(os.path.join(OUT, f"p{n:05d}.png"), np.clip(out + 0.5, 0, 255).astype(np.uint8))
    print("rebuilt", len(FRAMES), "frames")


if __name__ == "__main__":
    main()
