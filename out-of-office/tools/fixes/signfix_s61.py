"""S61 sign fix (2026-10-01): in Sara's light-speed sprint (3:04.8-3:08.7, master frames 5544-5660) the street's signs read as
garbage ("DYSTOPEEINCY CMEERGRATION", scrambled small signs, a "TEA TAAFMSTTT" ticker). The director loves the clip, and Kling
invents fresh (garbled) signs as the camera swings, so a re-roll would not cure it.
The fix: the sign faces are thrown out of focus, like a shallow depth of field. A magenta sign keeps its colour and glow and
reads as a branded panel; the cyan stock screen keeps its glow. Erasing letter by letter was tried first: it left
half-words and caught the cyan caption.
Masks: the convex hull of each magenta sign; the cyan screen area above the caption band. Each is feathered and the
blur is strong enough that no letter reads.
Usage: python tools/signfix_s61.py  (reads gen/textfix6162/fNNNNN.png, writes gen/textfix/pNNNNN.png)
"""
import os

import cv2
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SRC, OUT = os.path.join(ROOT, "gen", "textfix6162"), os.path.join(ROOT, "gen", "textfix")
FRAMES = range(5544, 5661)
CAPTION_TOP = 900  # captions live below this line; never touch them


def hulls(mask, min_area, close):
    m = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros(mask.shape, np.uint8)
    cv2.drawContours(out, [cv2.convexHull(c) for c in cs if cv2.contourArea(c) > min_area], -1, 1, -1)
    return out


MASKS = os.path.join(ROOT, "gen", "podfix", "s61mask")  # Apple Vision person mattes (made separately, not in this repo), one per frame


def fix(im, person=None):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    mag = (h > 138) & (h < 172) & (s > 80) & (v > 90)
    cy = (h > 78) & (h < 102) & (s > 50) & (v > 110)
    cy[:, :900] = False  # the stock screens are on the right; Sara's suit lines are cyan too
    m = hulls(mag, 1500, 45) | hulls(cy, 4000, 61)
    m[CAPTION_TOP:] = 0
    a = cv2.GaussianBlur(cv2.dilate(m * 255, np.ones((9, 9), np.uint8)).astype(np.float32) / 255, (0, 0), 6)
    if person is not None:  # Sara and the passers-by stay sharp: the hulls cross them
        p = cv2.GaussianBlur(cv2.dilate(person, np.ones((15, 15), np.uint8)).astype(np.float32) / 255, (0, 0), 4)
        a = a * (1 - np.clip(p * 1.5, 0, 1))
    a = a[..., None]
    soft = cv2.GaussianBlur(im, (0, 0), 11)
    return np.clip(im * (1 - a) + soft * a + 0.5, 0, 255).astype(np.uint8)


def main():
    for n in FRAMES:
        person = cv2.imread(os.path.join(MASKS, f"f{n:05d}.png"), 0)
        cv2.imwrite(os.path.join(OUT, f"p{n:05d}.png"), fix(cv2.imread(os.path.join(SRC, f"f{n:05d}.png")), person))
    print("patched", len(FRAMES), "frames")


if __name__ == "__main__":
    main()
