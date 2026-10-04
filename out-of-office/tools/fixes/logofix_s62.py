"""S62 logo fix (2026-10-01): the corporate logo top right of the floppy-disk shot (3:08.7-3:12.1, master frames 5661-5762) tears
and warps as the shot turns, and its tagline reads "-TCH CORPORATE". One clean, rigid copy of the logo (drawn: Arial Black C and S,
DIN tagline reading CORPORATE, laid out on frame REF's) is tracked through the shot by template matching
(position and scale). Each frame's own logo is erased under it first, so no warped edge peeks out.
Usage: python tools/logofix_s62.py   (reads gen/textfix6162/fNNNNN.png, writes gen/textfix/pNNNNN.png)
"""
import os

import cv2
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SRC, OUT = os.path.join(ROOT, "gen", "textfix6162"), os.path.join(ROOT, "gen", "textfix")
FRAMES = range(5661, 5763)
REF = 5710
BOX = (1490, 1810, 100, 385)  # x0, x1, y0, y1 around the logo in the ref frame
SEARCH = (1300, 1920, 0, 560)


def logo_mask(im):
    """Logo pixels: the magenta C and the beige S and tagline."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    mag = (h > 140) & (h < 172) & (s > 90) & (v > 120)
    beige = (h > 8) & (h < 35) & (s > 25) & (s < 120) & (v > 130)
    return mag | beige


def synthetic(tw, th):
    """A clean drawing of the logo in the ref frame's layout: magenta C, beige S over it, CORPORATE under the S."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    sup = "/System/Library/Fonts/Supplemental/"
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    def glyph(ch, font, box, fill):
        x0, x1, y0, y1 = box
        l, t, r, b = d.textbbox((0, 0), ch, font=font)
        g = Image.new("RGBA", (r - l, b - t), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((-l, -t), ch, font=font, fill=fill)
        img.alpha_composite(g.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))
    big = ImageFont.truetype(sup + "Arial Black.ttf", 300)
    glyph("C", big, (30, 200, 39, 252), (228, 2, 203, 255))  # boxes measured off the ref frame's magenta / beige masks
    glyph("S", big, (148, 300, 40, 231), (182, 173, 130, 255))
    glyph("CORPORATE", ImageFont.truetype(sup + "DIN Condensed Bold.ttf", 120), (118, 296, 238, 264), (182, 173, 130, 255))
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    a = np.asarray(img).astype(np.float32)
    return np.ascontiguousarray(a[..., 2::-1]), a[..., 3] / 255


def template():
    im = cv2.imread(os.path.join(SRC, f"f{REF:05d}.png"))
    x0, x1, y0, y1 = BOX
    crop = im[y0:y1, x0:x1].copy()
    m = logo_mask(crop).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    # the tagline row: keep only from the C of CORPORATE (the widest gap from the left in that row)
    rows = np.where(m.any(1))[0]
    tag = m[rows.max() - 30:rows.max() + 1]
    cols = np.where(tag.any(0))[0]
    gaps = np.diff(cols)
    first_word_end = cols[np.argmax(gaps[: len(gaps) // 2]) ] if len(gaps) else cols[0]
    m[rows.max() - 30:, :first_word_end + 2] = 0
    clean, a = synthetic(x1 - x0, y1 - y0)  # copying the ref frame's logo kept its tearing (round 1): draw it clean
    return clean, a, im[y0:y1, x0:x1]


def main():
    clean, alpha, ref = template()
    th, tw = alpha.shape
    tgray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    sx0, sx1, sy0, sy1 = SEARCH
    track = []
    for n in FRAMES:
        im = cv2.imread(os.path.join(SRC, f"f{n:05d}.png"))
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)[sy0:sy1, sx0:sx1]
        best = None
        for s in np.arange(0.85, 1.16, 0.025):
            t = cv2.resize(tgray, None, fx=s, fy=s)
            r = cv2.matchTemplate(g, t, cv2.TM_CCOEFF_NORMED)
            _, v, _, loc = cv2.minMaxLoc(r)
            if best is None or v > best[0]:
                best = (v, s, loc)
        track.append([best[1], best[2][0] + sx0, best[2][1] + sy0, best[0]])
    tr = np.array(track, float)
    from scipy.signal import savgol_filter
    sm = savgol_filter(tr[:, :3], 9, 2, axis=0)  # steady the logo: no frame-to-frame jitter
    for i, n in enumerate(FRAMES):
        im = cv2.imread(os.path.join(SRC, f"f{n:05d}.png"))
        s, x, y = sm[i]
        old = cv2.dilate(logo_mask(im[sy0:sy1, sx0:sx1]).astype(np.uint8) * 255, np.ones((15, 15), np.uint8))
        full = np.zeros(im.shape[:2], np.uint8)
        full[sy0:sy1, sx0:sx1] = old
        im = cv2.inpaint(im, full, 7, cv2.INPAINT_TELEA)
        M = np.float32([[s, 0, x], [0, s, y]])
        c = cv2.warpAffine(clean, M, (im.shape[1], im.shape[0]), flags=cv2.INTER_CUBIC).astype(np.float32)
        a = cv2.warpAffine(alpha, M, (im.shape[1], im.shape[0]), flags=cv2.INTER_LINEAR)[..., None]
        out = im * (1 - a) + c * a
        cv2.imwrite(os.path.join(OUT, f"p{n:05d}.png"), np.clip(out + 0.5, 0, 255).astype(np.uint8))
    print("patched", len(FRAMES), "frames; match score min %.2f" % tr[:, 3].min())


if __name__ == "__main__":
    main()
