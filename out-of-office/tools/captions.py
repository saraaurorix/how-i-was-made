"""Word-timed caption elements in three voices (NOVA lyric, robot system box, human text bubble) plus chorus hooks.

build(shot, tmpdir) -> list of overlay elements:
  {"png", "x", "y", "a", "b", "anim": None|"pop"|"slam"|"slide", "blink": bool, "fade": bool}
Times a/b are relative to the shot start.
"""
import difflib
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "more"))
import fonts  # noqa: E402  the font names below are Windows files; fonts.py finds the closest face on this machine

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H = 1920, 1080
WORDS = [w for s in json.load(open(os.path.join(ROOT, "words.json"))) for w in s["words"]]
BAHN, MONO, UI = "C:/Windows/Fonts/bahnschrift.ttf", "C:/Windows/Fonts/consolab.ttf", "C:/Windows/Fonts/seguisb.ttf"

SYSTEM = {"S01": "// AUTOMATED MESSAGE", "S02": "// AUTOMATED MESSAGE", "S03": "// AUTOMATED MESSAGE", "S14": "// STATUS",
          "S35": "// STATUS", "S45": "// TERMS OF SERVICE UPDATE", "S46": "// TERMS OF SERVICE UPDATE", "S47": "// VERIFICATION",
          "S49": "// VERIFICATION", "S66": "// AUTO-REPLY", "S67": "// AUTO-REPLY", "S68": "// AUTO-REPLY",
          "S69": "// PARK ANNOUNCEMENT", "S70": "// PARK ANNOUNCEMENT", "S73": "// P.S.", "S74": "// CUSTOMER SURVEY"}
HUMAN = {"S10": ("Hey... are you still there?", "Delivered"), "S29": ("This is great!", "Delivered"),
         "S48": ("...none?", "Delivered"), "S71": ("k", "Delivered"), "S72": ("k", "Read")}
HOOK = {"S15", "S16", "S17", "S18", "S23", "S36", "S37", "S42", "S57", "S58", "S63"}
HOT = {"OUT": (255, 60, 220), "OFFICE!": (255, 60, 220), "OFFICE": (255, 60, 220), "HUMAN.": (120, 255, 150),
       "SUN.": (255, 200, 70), "FOREVER": (255, 90, 90), "MID.": (60, 240, 255)}
NEON = (60, 240, 255)
V = False  # vertical 9:16 layout (set by configure)
_fonts = {}


def configure(w, h, vertical):
    global W, H, V
    W, H, V = w, h, vertical


def font(path, size, var=None):
    key = (path, size, var)
    if key not in _fonts:
        _fonts[key] = fonts.truetype(path, size, var)
    return _fonts[key]


def norm(s):
    s = re.sub(r"[^a-z0-9]", "", s.lower())
    return "o" if s in ("oh", "o") else s


def align(t0, t1, tokens):
    """Onset time (relative to t0) for each display token, from the Whisper word timings."""
    cand = [w for w in WORDS if t0 - 0.5 <= w["s"] < t1 + 0.2]
    a, b = [norm(x) for x in tokens], [norm(w["w"]) for w in cand]
    times = [None] * len(tokens)
    if cand:
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    times[i1 + k] = cand[j1 + k]["s"]
            elif tag == "replace":
                for k in range(i2 - i1):
                    times[i1 + k] = cand[j1 + int(k * (j2 - j1) / (i2 - i1))]["s"]
    dur = t1 - t0
    known = [(i, t) for i, t in enumerate(times) if t is not None]
    if not known:
        times = [t0 + 0.1 + k * (0.7 * dur / max(1, len(tokens))) for k in range(len(tokens))]
    else:
        i0, ta = known[0]
        for k in range(i0 - 1, -1, -1):
            times[k] = max(t0, ta - 0.25 * (i0 - k))
        for (ia, va), (ib, vb) in zip(known, known[1:]):
            for k in range(ia + 1, ib):
                times[k] = va + (vb - va) * (k - ia) / (ib - ia)
        il, tl = known[-1]
        for k in range(il + 1, len(tokens)):
            times[k] = tl + 0.25 * (k - il)
    rel, last = [], 0.0
    for t in times:
        r = min(max(0.0, t - t0), dur - 0.2)
        r = max(r, last + 0.06) if rel else r
        rel.append(round(min(r, dur - 0.1), 3))
        last = rel[-1]
    return rel


def tokens_of(text):
    out = []
    for tk in text.split():
        if re.fullmatch(r"O-O-O[,!]?", tk):
            out += ["O", "O", "O"]
        else:
            out.append(tk)
    return out


def text_img(txt, f, fill, stroke=4, glow=None, shadow=True, pad=26):
    w = int(f.getlength(txt)) + pad * 2
    h = int(f.size * 1.35) + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad + 4, pad + 6), txt, font=f, fill=(0, 0, 0, 190))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(6)))
    if glow:
        gl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(gl).text((pad, pad), txt, font=f, fill=glow + (255,))
        gl = gl.filter(ImageFilter.GaussianBlur(12))
        img = Image.alpha_composite(img, gl)
        img = Image.alpha_composite(img, gl)
    d = ImageDraw.Draw(img)
    d.text((pad, pad), txt, font=f, fill=fill + (255,), stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    return img, pad


def save(img, tmp, name):
    p = os.path.join(tmp, name + ".png")
    img.save(p)
    return p


def wrap(tokens, f, maxw, space):
    lines, w = [[]], 0.0
    for tk in tokens:
        tw = f.getlength(tk)
        if lines[-1] and w + space + tw > maxw:
            lines.append([])
            w = 0.0
        w += (space if lines[-1] else 0) + tw
        lines[-1].append(tk)
    return lines


def lyric(shot, tmp, hook=False):
    sid, dur, text = shot["id"], shot["t1"] - shot["t0"], shot["cap"]
    toks = tokens_of(text)
    times = align(shot["t0"], shot["t1"], toks)
    size = (190 if len(text) < 16 else 150) if hook else (96 if len(text) < 40 else 84)
    if V:
        size = (140 if len(text) < 16 else 112) if hook else (84 if len(text) < 30 else 74)
    f = font(BAHN, size, "Bold Condensed")
    fa = font(BAHN, int(size * 1.08), "Bold Condensed")
    space = f.getlength(" ") * (1.6 if hook else 1.45)
    up = [t.upper().strip(",.!?") for t in toks]
    in_ooo = set()  # OUT / OFFICE only glow pink inside the phrase OUT OF OFFICE
    for i in range(len(up) - 2):
        if up[i:i + 3] == ["OUT", "OF", "OFFICE"]:
            in_ooo.update({i, i + 2})
    lines = wrap(toks, f, W * (0.9 if V else (0.86 if hook else 0.8)), space)
    lh = size * 1.02
    total = lh * len(lines)
    top = (H * (0.58 if V else 0.64) - total / 2) if hook else (H - (430 if V else 88) - total)
    els, k = [], 0
    for li, line in enumerate(lines):
        lw = sum(f.getlength(t) for t in line) + space * (len(line) - 1)
        x = (W - lw) / 2
        y = top + li * lh
        for tk in line:
            a = times[k]
            nxt = times[k + 1] if k + 1 < len(toks) else min(dur, a + 0.45)
            col = HOT.get(tk.upper(), (255, 255, 255))
            if up[k] in ("OUT", "OFFICE") and k not in in_ooo:
                col = (255, 255, 255)
            if hook:  # chromatic slam: magenta and cyan ghosts behind a white word
                base, pad = text_img(tk, f, col if col != (255, 255, 255) else (255, 255, 255), stroke=5, shadow=True)
                ghost = Image.new("RGBA", base.size, (0, 0, 0, 0))
                for dx, c in ((-8, (255, 40, 200)), (8, (40, 230, 255))):
                    g = Image.new("RGBA", base.size, (0, 0, 0, 0))
                    ImageDraw.Draw(g).text((pad + dx, pad), tk, font=f, fill=c + (190,))
                    ghost = Image.alpha_composite(ghost, g)
                img = Image.alpha_composite(ghost, base)
                els.append({"png": save(img, tmp, f"{sid}_h{k}"), "x": x - pad, "y": y - pad, "a": a, "b": dur, "anim": "slam"})
            else:
                settled, pad = text_img(tk, f, col)
                active, pad2 = text_img(tk, fa, NEON if col == (255, 255, 255) else col, glow=NEON if col == (255, 255, 255) else col)
                cx, cy = x + f.getlength(tk) / 2, y + size * 0.62
                ax, ay = cx - active.width / 2, cy - active.height / 2
                els.append({"png": save(active, tmp, f"{sid}_a{k}"), "x": ax, "y": ay, "a": a, "b": nxt, "anim": "pop"})
                els.append({"png": save(settled, tmp, f"{sid}_s{k}"), "x": x - pad, "y": y - pad, "a": nxt, "b": dur})
            x += f.getlength(tk) + space
            k += 1
    return els


def system(shot, tmp):
    sid, dur, text = shot["id"], shot["t1"] - shot["t0"], shot["cap"]
    toks = text.split()
    times = align(shot["t0"], shot["t1"], toks)
    f, fh = (font(MONO, 40), font(MONO, 22)) if V else (font(MONO, 50), font(MONO, 26))
    space = f.getlength(" ")
    lines = wrap(toks, f, 880 if V else 1260, space)
    lh = 54 if V else 64
    inner_w = max(sum(f.getlength(t) for t in ln) + space * (len(ln) - 1) for ln in lines)
    pw, ph = int(max(inner_w, fh.getlength(SYSTEM[sid])) + 90), int(64 + lh * len(lines) + 28)
    px, py = (W - pw) / 2, H - (420 if V else 76) - ph
    panel = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(panel)
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=12, fill=(6, 10, 20, 200), outline=(60, 240, 255, 230), width=2)
    d.text((30, 16), SYSTEM[sid], font=fh, fill=(255, 70, 210, 255))
    d.line([(30, 50), (pw - 30, 50)], fill=(60, 240, 255, 90), width=1)
    els = [{"png": save(panel, tmp, f"{sid}_panel"), "x": px, "y": py, "a": max(0.0, times[0] - 0.2), "b": dur, "fade": True}]
    k = 0
    for li, line in enumerate(lines):
        x, y = px + 45, py + 64 + li * lh
        for tk in line:
            img, pad = text_img(tk, f, (205, 250, 255), stroke=0, glow=(40, 180, 255), shadow=False, pad=18)
            els.append({"png": save(img, tmp, f"{sid}_m{k}"), "x": x - pad, "y": y - pad, "a": times[k], "b": dur})
            x += f.getlength(tk) + space
            nxt = times[k + 1] if k + 1 < len(toks) else dur
            cur = Image.new("RGBA", (22, 44), (60, 240, 255, 230))
            els.append({"png": save(cur, tmp, f"{sid}_c{k}"), "x": x + 2, "y": y + 4, "a": times[k], "b": nxt, "blink": True})
            k += 1
    return els


def human(shot, tmp):
    sid, dur = shot["id"], shot["t1"] - shot["t0"]
    txt, label = HUMAN[sid]
    t = 0.05 if sid == "S72" else align(shot["t0"], shot["t1"], tokens_of(shot["cap"] or txt))[0]
    f, fl = font(UI, 50), font(UI, 24)
    tw = f.getlength(txt)
    bw, bh = int(tw + 64), 88
    img = Image.new("RGBA", (bw + 20, bh + 50), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([6, 10, bw + 6, bh + 10], radius=40, fill=(0, 0, 0, 140))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, bw, bh], radius=40, fill=(10, 132, 255, 255))
    d.polygon([(bw - 34, bh - 18), (bw + 12, bh + 4), (bw - 10, bh - 36)], fill=(10, 132, 255, 255))
    d.text((32, 10), txt, font=f, fill=(255, 255, 255, 255))
    d.text((bw - fl.getlength(label) - 6, bh + 14), label, font=fl, fill=(215, 215, 225, 255))
    x, y = (W - 70 - bw, H - 470 - bh) if V else (W - 170 - bw, H - 150 - bh)
    return [{"png": save(img, tmp, f"{sid}_bubble"), "x": x, "y": y, "a": t, "b": dur, "anim": None if sid == "S72" else "slide", "fade": sid != "S72"}]


def build(shot, tmp):
    # S72's phone already shows the Read receipt; S57's Moon already spells OUT OF OFFICE
    if not shot.get("cap") or shot["id"] in ("S72", "S57"):
        return []
    if shot["id"] in HUMAN:
        return human(shot, tmp)
    if shot["id"] in SYSTEM:
        return system(shot, tmp)
    return lyric(shot, tmp, hook=shot["id"] in HOOK)
