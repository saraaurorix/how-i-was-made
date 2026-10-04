"""Build a clean, front-on SOLVED stamp face (2026-10-01, round 2 of the S13 fix).

Frame 1316 shows the stamp face sharp and front-on but reading "SUBVED". Its U and B are erased (inpainted) and replaced by
the O and L from frame 1300 (the last frame that reads SOLVED), scaled to the same letter height and matched to the colour
of the letters they replace. The result, gen/textfix/s13_face.png, is the face textfix_s13.py pastes, at its natural
proportions, so nothing is stretched.
Usage: python tools/textfix_s13_face.py
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textfix_s13 as T  # noqa: E402

# letter boxes in each frame's block coordinates (x0, x1, y0, y1), read off gridded close-ups
O_1300, L_1300 = (101, 160, 97, 165), (167, 212, 97, 165)
UB_1316, ROW_1316 = (96, 224, 26, 112), (31, 76)  # the U and B to replace; the letter row's top and height
PAD = 6


def rect(n):
    p = T.block(n)
    TW, TH = int(round(p[2])), int(round(p[3]))
    return cv2.warpAffine(T.load(n), cv2.invertAffineTransform(T.to_frame(p, TW, TH)), (TW, TH), flags=cv2.INTER_CUBIC)


def lab(img):
    return cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)


def main():
    a, b = rect(1300), rect(1316)
    x0, x1, y0, y1 = UB_1316
    target = lab(b[y0:y1, x0:x1]).reshape(-1, 3)  # the colour of the letters being replaced, with their background
    m = np.zeros(b.shape[:2], np.uint8)
    m[y0:y1, x0:x1] = 255
    face = cv2.inpaint(b, m, 9, cv2.INPAINT_TELEA).astype(np.float32)
    top, h = ROW_1316
    x = x0 + 3
    for (lx0, lx1, ly0, ly1) in (O_1300, L_1300):
        src = a[ly0 - PAD:ly1 + PAD, lx0 - PAD:lx1 + PAD].astype(np.float32)
        s = h / (ly1 - ly0)
        src = cv2.resize(src, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        L = lab(src).reshape(-1, 3)
        L = (L - L.mean(0)) / (L.std(0) + 1e-3) * target.std(0) + target.mean(0)
        src = cv2.cvtColor(np.clip(L.reshape(src.shape), 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
        H, W = src.shape[:2]
        pad = int(round(PAD * s))
        al = np.zeros((H, W), np.float32)
        al[pad:H - pad, pad:W - pad] = 1
        al = cv2.GaussianBlur(al, (0, 0), pad / 2 + 0.5)[..., None]
        reg = face[top - pad:top - pad + H, x - pad:x - pad + W]
        face[top - pad:top - pad + H, x - pad:x - pad + W] = reg * (1 - al) + src * al
        x += W - 2 * pad + 6
    out = os.path.join(T.D, "s13_face.png")
    cv2.imwrite(out, np.clip(face + 0.5, 0, 255).astype(np.uint8))
    print("wrote", out, face.shape)


if __name__ == "__main__":
    main()
