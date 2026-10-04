"""S44 text fix (2026-10-01): the red-sky TERMS & CONDITIONS tickers scroll in garbage.
- The big banner grows junk glyphs on its left ("CCF", "J-PCCF") as it scrolls.
- The small banner runs a second "TERMS & CONDITIONS" over its own "UPDATED".
Per frame, the glyph pixels are found by their neon hue (magenta / cyan).
- Big banner: cyan glyphs left of the first magenta letter (the T of TERMS) are erased.
- Small banner: everything from its first cyan letter on is erased (it then reads TERMS & CONDITIONS), and so are the cyan glyphs left of its T.
Erasing fills the glyphs and their glow from a clean plate: every frame is aligned to frame REF (SIFT on everything but
the text), and each sky pixel takes the median of the frames where no letter covers it. An inpaint smeared the neon glow
(round 1). Only text pixels change. Master frames 4050-4166 (2:15.0-2:18.9).
Usage: python tools/textfix_s44.py   (reads gen/textfix44/fNNNNN.png, writes gen/textfix/pNNNNN.png)
"""
import os
import sys

import cv2
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SRC, OUT = os.path.join(ROOT, "gen", "textfix44"), os.path.join(ROOT, "gen", "textfix")
FRAMES = range(4050, 4167)
BIG = (330, 1720, 0, 430)  # x0, x1, y0, y1 where the big banner runs
SMALL = (560, 1420, 400, 575)
TOWER = (1330, 1440)  # the tower the small ticker runs into, at 2:17-2:18  # and the small one (its left edge clears the NS sign)


def hue_masks(im, loose=False):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    sv = (s > 35) & (v > 90) if loose else (s > 70) & (v > 140)
    return (h > 135) & (h < 170) & sv, (h > 75) & (h < 105) & sv


def text_in(mask, box, min_h):
    """The text pixels inside box that belong to letter-sized blobs (drops lit windows and specks)."""
    x0, x1, y0, y1 = box
    m = np.zeros_like(mask)
    m[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
    grown = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(grown)
    keep = np.zeros(n, bool)
    keep[1:] = st[1:, cv2.CC_STAT_HEIGHT] >= min_h
    return m & keep[lab]


def fix(im):
    mag, cy = hue_masks(im)
    erase = np.zeros(mag.shape, bool)
    # big banner: cyan junk left of the T of TERMS
    bm, bc = text_in(mag, BIG, 25), text_in(cy, BIG, 25)
    if bm.any():
        xT = np.where(bm.any(0))[0].min()
        erase[:, :xT - 4] |= bc[:, :xT - 4]
    # small banner: junk left of its T, and the overlapping second copy from its first cyan letter on
    sm, sc = text_in(mag, SMALL, 8), text_in(cy, SMALL, 8)
    if sm.any():
        xt = np.where(sm.any(0))[0].min()
        erase[:, :xt - 3] |= sc[:, :xt - 3]
        right = np.where(sc[:, xt:].any(0))[0]
        if len(right):
            xc = xt + right.min() - 3
            erase[:, xc:] |= (sm | sc)[:, xc:]
    if not erase.any():
        return im, erase
    m = cv2.dilate(erase.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))  # glyphs + their glow
    return cv2.inpaint(im, m, 9, cv2.INPAINT_TELEA), m > 0


REF = 4108
MASKS = os.path.join(ROOT, "gen", "s44mask")  # Apple Vision person mattes: the fill must never touch a head (user, 2:18)


def people(n):
    m = cv2.imread(os.path.join(MASKS, f"f{n:05d}.png"), 0)
    return np.zeros((1080, 1920), bool) if m is None else cv2.dilate((m > 60).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
ROI = (300, 1760, 0, 660)  # where the banners and their fills live


def erase_mask(im):
    """Big banner: its cyan junk left of the T of TERMS. Small banner: all of it (it's garbled at every moment, and
    no frame shows the sky behind it, so it goes)."""
    mag, cy = hue_masks(im)
    lm, lc = hue_masks(im, loose=True)
    erase = np.zeros(mag.shape, bool)
    bm, bc = text_in(mag, BIG, 25), text_in(cy, BIG, 25)
    if bm.any():
        xT = np.where(bm.any(0))[0].min()
        junk = bc.copy()
        junk[:, xT - 4:] = False
        if junk.any():
            ys, xs = np.where(junk)
            box = np.zeros_like(junk)
            box[max(0, ys.min() - 25):ys.max() + 25, max(0, xs.min() - 25):xT - 4] = True
            erase |= box & (lc | lm | junk)
    x0, x1, y0, y1 = SMALL
    small = np.zeros_like(erase)
    small[y0:y1, x0:x1] = (lm | lc)[y0:y1, x0:x1]
    sm = text_in(mag | cy, SMALL, 8)
    if sm.any():
        ys, xs = np.where(sm)
        band = np.zeros_like(erase)
        band[ys.min() - 12:ys.max() + 12, xs.min() - 15:xs.max() + 15] = True
        erase |= small & band
    return cv2.dilate(erase.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))) > 0


def main():
    x0, x1, y0, y1 = ROI
    sift, bf = cv2.SIFT_create(3000), cv2.BFMatcher()
    def feats(im):
        mag, cy = hue_masks(im)
        keep = np.full(mag.shape, 255, np.uint8)
        keep[cv2.dilate((mag | cy).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0] = 0
        keep[700:] = 0  # the crowd moves
        return sift.detectAndCompute(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), keep)
    ref = cv2.imread(os.path.join(SRC, f"f{REF:05d}.png"))
    kr, dr = feats(ref)
    frames, Hs = {}, {}
    for n in FRAMES:
        im = cv2.imread(os.path.join(SRC, f"f{n:05d}.png"))
        k, d = feats(im)
        m = [a for a, b in bf.knnMatch(d, dr, k=2) if a.distance < 0.75 * b.distance]
        H, _ = cv2.findHomography(np.float32([k[a.queryIdx].pt for a in m]), np.float32([kr[a.trainIdx].pt for a in m]), cv2.RANSAC, 3.0)
        frames[n], Hs[n] = im, H  # H: frame -> ref
    # the clean plate, in ref coordinates: median over the frames where the pixel is not text
    stack, valid = [], []
    for n in list(FRAMES)[::2]:
        im = frames[n]
        mag, cy = hue_masks(im, loose=True)
        text = cv2.dilate((mag | cy).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (33, 33)))
        w = cv2.warpPerspective(im, Hs[n], (1920, 1080), flags=cv2.INTER_LINEAR)[y0:y1, x0:x1]
        ok = cv2.warpPerspective(1 - text, Hs[n], (1920, 1080), flags=cv2.INTER_NEAREST)[y0:y1, x0:x1] > 0
        inside = cv2.warpPerspective(np.ones(im.shape[:2], np.uint8), Hs[n], (1920, 1080), flags=cv2.INTER_NEAREST)[y0:y1, x0:x1] > 0
        stack.append(w.astype(np.float32))
        valid.append(ok & inside)
    S, V = np.stack(stack), np.stack(valid)
    S[~V] = np.nan
    plate = np.nanmedian(S, axis=0)
    have = ~np.isnan(plate[..., 0])
    plate_full = np.zeros((1080, 1920, 3), np.float32)
    plate_full[y0:y1, x0:x1] = np.nan_to_num(plate)
    have_full = np.zeros((1080, 1920), np.uint8)
    have_full[y0:y1, x0:x1] = have
    for n in FRAMES:
        im = frames[n]
        er = erase_mask(im) & ~people(n)
        back = cv2.warpPerspective(plate_full, np.linalg.inv(Hs[n]), (1920, 1080), flags=cv2.INTER_LINEAR)
        hv = cv2.warpPerspective(have_full, np.linalg.inv(Hs[n]), (1920, 1080), flags=cv2.INTER_NEAREST) > 0
        hole = er & ~hv  # never uncovered (the small banner's band): inpaint from the sky around it
        hole = cv2.dilate(hole.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        hv = hv & ~hole
        base = cv2.inpaint(im, hole.astype(np.uint8) * 255, 15, cv2.INPAINT_TELEA) if hole.any() else im
        fill = np.where(hv[..., None], back, base.astype(np.float32))
        a = cv2.GaussianBlur(er.astype(np.float32), (0, 0), 2.0)[..., None]
        out = im * (1 - a) + fill * a
        cv2.imwrite(os.path.join(OUT, f"p{n:05d}.png"), np.clip(out + 0.5, 0, 255).astype(np.uint8))
    print("patched", len(FRAMES), "frames; plate coverage %.3f" % have.mean())


if __name__ == "__main__" and "--cleanup" not in sys.argv and "--band" not in sys.argv:
    main()


def cleanup():
    """Second pass (2026-10-01): the clean plate still carried a cyan smear left of TERMS (the junk scrolls through every
    frame there, so the median kept some). Any cyan-hued pixel left of the T of TERMS, in the big banner's band, is
    filled from the cloud around it. Runs on the written pNNNNN.png frames."""
    for n in FRAMES:
        p = os.path.join(OUT, f"p{n:05d}.png")
        im = cv2.imread(p)
        orig = cv2.imread(os.path.join(SRC, f"f{n:05d}.png"))
        mag, _ = hue_masks(orig)
        bm = text_in(mag, BIG, 25)
        if not bm.any():
            continue
        xT = np.where(bm.any(0))[0].min()
        ys = np.where(bm.any(1))[0]
        hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        cyan = (h > 70) & (h < 110) & (s > 25) & (v > 60)
        box = np.zeros(cyan.shape, bool)
        box[max(0, ys.min() - 60):ys.max() + 60, max(0, xT - 520):xT - 2] = True
        m = cv2.dilate((cyan & box).astype(np.uint8) * 255, np.ones((11, 11), np.uint8))
        m[~box] = 0
        m[people(n)] = 0
        if m.any():
            cv2.imwrite(p, cv2.inpaint(im, m, 11, cv2.INPAINT_TELEA))
    print("cleaned", len(FRAMES), "frames")


if __name__ == "__main__" and "--cleanup" in sys.argv:
    cleanup()


def band_pass():
    """Third pass (2026-10-01): where the small ticker was erased, the plate/inpaint fill read as a grey smear sliding into
    the man's head at 2:18 (user flag). Refill that band with the sky just above it (same frame, shifted down by the
    column's band thickness) with a feathered blend, so the clouds carry through; stop tight at the people (no dilation of the matte)."""
    x0, x1, y0, y1 = SMALL
    for n in FRAMES:
        orig = cv2.imread(os.path.join(SRC, f"f{n:05d}.png"))
        p = os.path.join(OUT, f"p{n:05d}.png")
        cur = cv2.imread(p)
        band = np.zeros(orig.shape[:2], bool)
        band[y0 - 20:y1 + 15, x0 - 20:x1] = True
        m = erase_mask(orig) & band
        if not m.any():
            continue
        m = cv2.dilate(m.astype(np.uint8), np.ones((13, 13), np.uint8)) > 0
        pm = cv2.imread(os.path.join(MASKS, f"f{n:05d}.png"), 0)
        tight = (pm > 128) if pm is not None else np.zeros_like(m)
        m &= ~tight
        runs = m.sum(0)
        h = int(np.percentile(runs[runs > 0], 90)) + 10  # the band's own thickness, not its slanted bounding box (that pulled the big banner down)
        src = np.roll(cur, h, axis=0)  # the sky just above each column, moved down onto the band
        # on the tower at the right the sky-from-above copied its round badge down; take the tower's windows from below instead
        ramp = np.clip((np.arange(cur.shape[1]) - TOWER[0]) / 25.0, 0, 1)[None, :, None]
        src = src * (1 - ramp) + np.roll(cur, -h, axis=0).astype(np.float32) * ramp
        a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3)
        a[tight] = 0
        sm_, sc_ = hue_masks(np.clip(src, 0, 255).astype(np.uint8), loose=True)  # never copy the big banner's letters down
        neon = cv2.dilate((sm_ | sc_).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(np.float32)
        a *= 1 - cv2.GaussianBlur(neon, (0, 0), 4)
        out = cur * (1 - a[..., None]) + src * a[..., None]
        cv2.imwrite(p, np.clip(out + 0.5, 0, 255).astype(np.uint8))
    print("band refilled", len(FRAMES), "frames")


if __name__ == "__main__" and "--band" in sys.argv:
    band_pass()
