"""Join check: every cut in a music video, looked at as a join between two shots (the shot-continuity skill).

  python join_check.py --cut CUT.mp4 [--sb storyboard.json] [--out review/joins] [--from S --to S] [--montage-sets rap,cctv]
  python join_check.py --stills [--sb storyboard.json] [--out review/joins_stills] [...]

Run it from the project folder (paths are relative to it). The storyboard is a JSON list of shots, in cut order. Per shot it needs
id, t0, t1 (seconds in the cut) and a place field (`set`, else `fmt`). Optional: `look` (the lead's outfit, for LOOK), `join` (FLOW,
SAME, JUMP, TRANSITION, MONTAGE: the cut INTO this shot), `scene_id` (shots of one scene; the place is used without it), `scene` and
`staging` (the row's picture and set, printed under each join; a `scene` that names KEVIN turns the Kevin test on), `still_file`
(for --stills; gen/stills/<id>.png without it). A shot whose place is "edit" is a graphic: no PLACE or LIGHT flag around it.
The cut must run at --fps (25 by default) and start at the board's 0:00; --from and --to (seconds) check part of it.

Per join (shot A -> shot B):
  --cut     four frames from the cut, as the viewer sees it: A at -0.6 s, A's last frame, B's first frame, B at +0.6 s.
  --stills  A's still and B's still (the planned first frame of each shot), before any clip is generated.
Automatic flags. They are hints for the eye, never the verdict:
  SIDES    Sara and another face are in frame on both sides of the cut and their left/right order reverses (the 180-degree
           rule). Sara is found by her glowing cyan irises (FaceLandmarker iris landmarks), not by her hair: white wigs are white too.
  LOOK     Sara's look (storyboard `look`) changes between two shots in the same place.
  PLACE    the place changes. Fine when the board marks the join TRANSITION, JUMP or MONTAGE and the picture carries a device.
  LIGHT    same place, but the colour or brightness jumps (measured above the caption band).
  MOTION   (info) the dominant movement across the frame reverses at the cut (optical flow, camera and subject together).
Outputs in --out: min_MM_x.jpg sheets (one join per row, at most 8 rows a sheet), joins.json, JOINS_auto.md (the reviewer copies it
to JOINS.md and fills in the verdict and fix columns).

The face tests are tuned for this series' two characters and nobody else: Sara by her glowing cyan irises and her blunt platinum
fringe, Kevin by his thick dark moustache. They drive SIDES here, face_sheet.py and clip_screen.py's TRAVEL flag. For your own
characters change the tests at the end of faces() (the lines that set `sara` and `kevin`); LOOK, PLACE, LIGHT and MOTION don't use
them. Needs models/face_landmarker.task beside this script (Google MediaPipe's Face Landmarker model, in this folder).
"""
import argparse
import json
import math
import os
import subprocess
import sys

import cv2
import imageio_ffmpeg
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fonts import truetype  # Windows font names -> the closest face on this machine

FF = imageio_ffmpeg.get_ffmpeg_exe()
MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "face_landmarker.task")
FPS = 25
W, H = 1920, 1080
TW, TH = 400, 225
ROWS = 8
FONT_B = "arialbd.ttf"
FONT_R = "arial.ttf"
NEUTRAL = {"edit"}  # graphics (a frozen frame, a survey card): no PLACE or LIGHT flag into or out of them

ap = argparse.ArgumentParser()
ap.add_argument("--cut", default="")
ap.add_argument("--stills", action="store_true")
ap.add_argument("--sb", default="storyboard.json")
ap.add_argument("--out", default="")
ap.add_argument("--from", dest="t_from", type=float, default=0.0)
ap.add_argument("--to", dest="t_to", type=float, default=1e9)
ap.add_argument("--montage-sets", default="", help="places whose internal cuts are a list by design (a rap montage)")
ap.add_argument("--fps", type=int, default=FPS)
a = ap.parse_args()
if not a.cut and not a.stills:
    ap.error("give --cut FILE or --stills")
FPS = a.fps
if a.cut:
    print(f"reading the cut at {FPS} fps (--fps): give the cut's own rate or every frame below is off")
OUT = a.out or ("review/joins_stills" if a.stills else "review/joins")
os.makedirs(os.path.join(OUT, "_f"), exist_ok=True)
MONTAGE = {x for x in a.montage_sets.split(",") if x}
SB = json.load(open(a.sb))
place = lambda s: s.get("set") or s.get("fmt") or "?"
_lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.IMAGE, num_faces=6,
    min_face_detection_confidence=0.35, min_face_presence_confidence=0.35))


# ---------------------------------------------------------------- frames
def frames_at(t, n, w=W, h=H):
    """n consecutive frames of the cut from time t, as uint8 RGB arrays (frame-accurate: output seeking re-decodes)."""
    p = subprocess.run([FF, "-v", "error", "-ss", f"{max(0.0, t):.4f}", "-i", a.cut, "-frames:v", str(n), "-vf", f"scale={w}:{h}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    buf = np.frombuffer(p.stdout, np.uint8)
    k = len(buf) // (w * h * 3)
    return [buf[i * w * h * 3:(i + 1) * w * h * 3].reshape(h, w, 3) for i in range(k)]


def still(s):
    p = s.get("still_file") or f"gen/stills/{s['id']}.png"
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGB")
    k = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return np.asarray(im.crop((x, y, x + W, y + H)))


# ---------------------------------------------------------------- analysis
def _detect(tile):
    return _lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(tile))).face_landmarks


def faces(rgb, fine=False, thorough=False):
    """Prominent faces: x centre and width (fractions of the frame) and whether the irises glow cyan (Sara).
    The landmarker's detector only finds faces that fill a good part of its input, so it runs on the whole frame and on nine
    overlapping half-size tiles (a mid-shot face is twice as big in a tile), and the detections are merged. When that finds no
    Sara, a second pass on sixteen third-size tiles looks again: it finds faces turned down to a prop, which the first pass misses."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, w = rgb.shape[:2]
    if fine:
        th, tw = h // 3, w // 3
        boxes = [(int(x), int(y), int(x) + tw, int(y) + th) for y in np.linspace(0, h - th, 4) for x in np.linspace(0, w - tw, 4)]
    else:
        th, tw = h // 2, w // 2
        boxes = [(0, 0, w, h)] + [(x, y, x + tw, y + th) for y in (0, th // 2, h - th) for x in (0, tw // 2, w - tw)]
    found = []
    for x0t, y0t, x1t, y1t in boxes:
        for lms in _detect(rgb[y0t:y1t, x0t:x1t]):
            pts = [((p.x * (x1t - x0t) + x0t), (p.y * (y1t - y0t) + y0t)) for p in lms]
            xs, ys = [p[0] / w for p in pts], [p[1] / h for p in pts]
            fw = max(xs) - min(xs)
            if fw < 0.03:  # tiny background faces are noise for this check
                continue
            cyan, n = 0, 0
            if len(pts) >= 478:
                for c, ring in ((468, (469, 470, 471, 472)), (473, (474, 475, 476, 477))):
                    cx, cy = pts[c]
                    r = np.mean([math.hypot(pts[j][0] - cx, pts[j][1] - cy) for j in ring])
                    if r < 1.5:
                        continue
                    y0, y1 = int(max(0, cy - r)), int(min(h, cy + r + 1))
                    x0, x1 = int(max(0, cx - r)), int(min(w, cx + r + 1))
                    if y1 - y0 < 2 or x1 - x0 < 2:  # the eye is off the edge of the frame
                        continue
                    yy, xx = np.mgrid[y0:y1, x0:x1]
                    m = (xx - cx) ** 2 + (yy - cy) ** 2 <= (0.85 * r) ** 2
                    px = hsv[y0:y1, x0:x1][m]
                    n += len(px)
                    cyan += int(((px[:, 0] >= 75) & (px[:, 0] <= 108) & (px[:, 1] >= 80) & (px[:, 2] >= 110)).sum())
            c = cyan / n if n else 0.0
            # Sara's blunt platinum fringe covers her forehead down to the brows; everyone else shows skin there (a white wig
            # starts above the forehead). Sample a disc on the mid-forehead (mesh point 151) for "platinum": bright and colourless.
            fx, fy = pts[151]
            rr = max(2.0, 0.07 * fw * w)
            y0, y1 = int(max(0, fy - rr)), int(min(h, fy + rr + 1))
            x0, x1 = int(max(0, fx - rr)), int(min(w, fx + rr + 1))
            if y1 - y0 >= 2 and x1 - x0 >= 2:
                yy, xx = np.mgrid[y0:y1, x0:x1]
                px = hsv[y0:y1, x0:x1][(xx - fx) ** 2 + (yy - fy) ** 2 <= rr ** 2]
                fr = float(((px[:, 1] < 60) & (px[:, 2] > 150)).mean()) if len(px) else 0.0
            else:
                fr = 0.0
            # Kevin, the series' everyman, always has a thick dark moustache: the upper lip between the nose and the mouth is far
            # darker than his cheeks (measured on one video's cut: Kevin 0.36-0.43, everyone else 0.83 or more)
            def _v(cx, cy, r):
                yy0, yy1 = int(max(0, cy - r)), int(min(h, cy + r + 1))
                xx0, xx1 = int(max(0, cx - r)), int(min(w, cx + r + 1))
                return float(hsv[yy0:yy1, xx0:xx1, 2].mean()) if yy1 - yy0 >= 2 and xx1 - xx0 >= 2 else None
            fwp = fw * w
            px_, py_ = (pts[2][0] + pts[0][0]) / 2, (pts[2][1] + pts[0][1]) / 2
            rm = max(2.0, 0.035 * fwp)
            mv = [_v(px_, py_, rm), _v(px_ - 0.12 * fwp, py_ + 0.01 * fwp, rm), _v(px_ + 0.12 * fwp, py_ + 0.01 * fwp, rm)]
            cv = [_v(*pts[50], rm * 1.5), _v(*pts[280], rm * 1.5)]
            must = (float(np.mean(mv)) / max(1.0, float(np.mean(cv)))) if None not in mv and None not in cv else None
            eyes_seen = n >= 12
            if c >= 0.22 or (fr >= 0.55 and c > 0.04):
                sara = True
            elif fr >= 0.7 and not eyes_seen:  # eyes down or shut, but the fringe is there
                sara = True
            elif eyes_seen and c <= 0.04:  # eyes clearly visible and not cyan: someone else (a fringed white wig included)
                sara = False
            else:
                sara = None
            found.append({"x": round(float(np.mean(xs)), 3), "y": round(float(np.mean(ys)), 3), "w": round(float(fw), 3),
                          "sara": sara, "c": round(c, 2), "fringe": round(fr, 2), "n": n,
                          "kevin": (sara is not True and must is not None and must < 0.6), "must": None if must is None else round(must, 2)})
    out = []
    for f in sorted(found, key=lambda f: (f["sara"] is not True, -f["n"])):  # merge the same face found in several tiles
        if all(abs(f["x"] - g["x"]) > 0.6 * max(f["w"], g["w"]) or abs(f["y"] - g["y"]) > 0.6 * max(f["w"], g["w"]) for g in out):
            out.append(f)
    if not fine and (thorough or not any(f["sara"] for f in out)):
        more = faces(rgb, fine=True)
        out += [f for f in more if all(abs(f["x"] - g["x"]) > 0.6 * max(f["w"], g["w"]) or
                                       abs(f["y"] - g["y"]) > 0.6 * max(f["w"], g["w"]) for g in out)]
    return out


def order(fs, kevin_ok=True):
    """(side, who): which side of the other person Sara is on. 'who' is 'kevin' when Kevin is identified (his moustache), else
    'other' for a plain two-shot (Sara plus exactly one other face of comparable size). Crowds and a small face behind a close-up
    give None: the side of an extra is not a continuity fact."""
    s = [f for f in fs if f["sara"]]
    if len(s) != 1:
        return None
    k = [f for f in fs if f.get("kevin")] if kevin_ok else []
    if len(k) == 1:
        o, who = k[0], "kevin"
    else:
        others = [f for f in fs if f["sara"] is False and f["w"] >= 0.5 * s[0]["w"]]
        if len(others) != 1 or len([f for f in fs if f["sara"] is False]) > 3:
            return None
        o, who = others[0], "other"
    if abs(s[0]["x"] - o["x"]) < 0.08:
        return None
    return ("L" if s[0]["x"] < o["x"] else "R", who)


_SHOT = {}
SCENE_SIDE = {}  # scene (or place) -> (Sara's side of the other person the last time it showed both, shot id)


def shot_sides(s):
    """(side at the shot's start, side at its end): Sara left or right of the other face, read from six frames spread over the
    whole shot (nearest each end first). Sides rarely change inside a shot, and Sara often looks down near a cut, which hides
    the cyan irises that identify her, so the whole shot is searched."""
    if s["id"] in _SHOT:
        return _SHOT[s["id"]]
    if a.stills:
        img = still(s)
        o = order(faces(img, thorough=True), "KEVIN" in (s.get("scene") or "")) if img is not None else None
        _SHOT[s["id"]] = (o, o)
        return _SHOT[s["id"]]
    d = s["t1"] - s["t0"]
    ts = [s["t0"] + d * (k + 0.5) / 6 for k in range(6)]
    found = []
    kev = "KEVIN" in (s.get("scene") or "")  # a moustache only counts as Kevin in a shot the board says he is in
    for t in ts:
        fr = frames_at(t, 1)
        found.append((t, order(faces(fr[0], thorough=True), kev) if fr else None))
    first = next((o for _, o in found if o), None)
    last = next((o for _, o in reversed(found) if o), None)
    _SHOT[s["id"]] = (first, last)
    return _SHOT[s["id"]]


def colour(rgb):
    """Mean Lab and an HSV histogram over the top 70 % of the frame (the caption band sits below)."""
    top = rgb[: int(rgb.shape[0] * 0.70)]
    small = cv2.resize(top, (192, int(192 * top.shape[0] / top.shape[1])), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(small, cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(float)
    lab[:, 0] *= 100 / 255
    lab[:, 1:] -= 128
    hist = cv2.calcHist([cv2.cvtColor(small, cv2.COLOR_RGB2HSV)], [0, 1, 2], None, [16, 4, 4], [0, 180, 0, 256, 0, 256])
    return lab.mean(axis=0), cv2.normalize(hist, hist).flatten()


def flow(seq):
    """Movement over a short run of frames at 320 px wide: median horizontal and vertical shift (camera and subject together)
    and activity, the 75th-percentile speed (pixels per frame), which is high in a whip, a surf or a slide and near 0 in a pose."""
    g = [cv2.cvtColor(cv2.resize(f, (320, 180), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY) for f in seq]
    dx, dy, act = [], [], []
    for p, q in zip(g, g[1:]):
        fl = cv2.calcOpticalFlowFarneback(p, q, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        dx.append(float(np.median(fl[..., 0]))); dy.append(float(np.median(fl[..., 1])))
        act.append(float(np.percentile(np.hypot(fl[..., 0], fl[..., 1]), 75)))
    return (float(np.median(dx)), float(np.median(dy)), float(np.median(act))) if dx else (0.0, 0.0, 0.0)


# ---------------------------------------------------------------- per join
def check(sa, sb):
    ka = round(sb["t0"] * FPS)  # first frame of B in the cut
    info = {"cut": round(ka / FPS, 2), "a": sa["id"], "b": sb["id"], "place_a": place(sa), "place_b": place(sb),
            "look_a": sa.get("look"), "look_b": sb.get("look"), "join": sb.get("join", ""), "flags": [], "info": []}
    if a.stills:
        fa, fb = still(sa), still(sb)
        if fa is None or fb is None:
            info["flags"].append("MISSING still"); return info, [fa, fb]
        tiles = [fa, fb]
    else:
        run_a = frames_at((ka - 6) / FPS - 0.002, 6)
        run_b = frames_at(ka / FPS - 0.002, 6)
        pre = frames_at(max(sa["t0"], ka / FPS - 0.6), 1)
        post = frames_at(min(sb["t1"] - 1 / FPS, ka / FPS + 0.6), 1)
        if not run_a or not run_b:
            info["flags"].append("MISSING frames"); return info, []
        fa, fb = run_a[-1], run_b[0]
        pre, post = (pre[0] if pre else fa), (post[0] if post else fb)
        tiles = [pre, fa, fb, post]
        (dxa, dya, aa), (dxb, dyb, ab) = flow(run_a), flow(run_b)
        info["flow"] = [round(dxa, 2), round(dya, 2), round(dxb, 2), round(dyb, 2)]
        info["activity"] = [round(aa, 2), round(ab, 2)]
        if abs(dxa) > 0.8 and abs(dxb) > 0.8 and dxa * dxb < 0:
            info["info"].append(f"MOTION reverses ({'right' if dxa > 0 else 'left'} then {'right' if dxb > 0 else 'left'})")
        if aa > 2.5 and ab < 0.8:
            info["info"].append("A ends mid-movement and B starts still: does the action carry over?")
    info["faces_a"], info["faces_b"] = faces(fa), faces(fb)
    oa, ob = shot_sides(sa)[1], shot_sides(sb)[0]
    info["sara_side"] = [oa, ob]  # (side, who) or None
    scene_same = (sa.get("scene_id") == sb.get("scene_id")) if sa.get("scene_id") else place(sa) == place(sb)
    j0 = (sb.get("join") or "").upper()
    montage = place(sa) in MONTAGE and place(sb) in MONTAGE  # a list: every shot is its own place, so sides reset at each cut
    side = lambda o: "left" if o == "L" else "right"
    who = lambda o: "Kevin" if o[1] == "kevin" else "the other person"
    ok_join = scene_same and not montage and j0 not in ("TRANSITION", "MONTAGE")
    flipped_here = bool(oa and ob and oa[1] == ob[1] and oa[0] != ob[0])
    if flipped_here and ok_join:
        info["flags"].append(f"SIDES Sara is {side(oa[0])} of {who(oa)} in A, {side(ob[0])} in B")
    # the scene's line for Sara and Kevin: the first shot of the scene that shows them both sets it, and every later shot is held
    # to it, even across a cutaway or a solo shot (a flip that returns after a cutaway is still a flip)
    for s_ in (sa, sb):
        o_ = shot_sides(s_)[0]
        k_ = s_.get("scene_id") or place(s_)
        if o_ and o_[1] == "kevin" and place(s_) not in MONTAGE and k_ not in SCENE_SIDE:
            SCENE_SIDE[k_] = (o_[0], s_["id"])
    key = sb.get("scene_id") or place(sb)
    est = SCENE_SIDE.get(key)
    if (ob and ob[1] == "kevin" and est and est[1] != sb["id"] and est[0] != ob[0] and not flipped_here
            and place(sb) not in MONTAGE and j0 not in ("TRANSITION", "MONTAGE")):
        info["flags"].append(f"SIDES Sara is {side(ob[0])} of Kevin in B, but {side(est[0])} where this scene set its line ({est[1]})")
    same = place(sa) == place(sb)
    neutral = place(sa) in NEUTRAL or place(sb) in NEUTRAL
    j = (sb.get("join") or "").upper()
    if same and sa.get("look") and sb.get("look") and sa["look"] != sb["look"]:
        info["flags"].append(f"LOOK {sa['look']} -> {sb['look']} in the same place")
    if not same and not neutral and j not in ("TRANSITION", "JUMP", "MONTAGE") and not (place(sa) in MONTAGE and place(sb) in MONTAGE):
        info["flags"].append(f"PLACE {place(sa)} -> {place(sb)}: needs a transition in the picture")
    flash = False
    if not a.stills:  # a white flash on B's first frames (the edit's flash on a drop) is a transition device: compare B once it has faded
        lf = colour(fb)[0][0]
        later = frames_at(ka / FPS + 0.36, 1)
        if later and lf > 80 and lf - colour(later[0])[0][0] > 20:
            flash, fb = True, later[0]
            info["info"].append("white flash on B (a transition device)")
    (la, ha), (lb, hb) = colour(fa), colour(fb)
    de = float(np.linalg.norm(la - lb))
    bh = float(cv2.compareHist(ha.astype(np.float32), hb.astype(np.float32), cv2.HISTCMP_BHATTACHARYYA))
    info["colour"] = {"dE": round(de, 1), "hist": round(bh, 2), "dL": round(float(lb[0] - la[0]), 1)}
    if same and not neutral and not flash and place(sa) not in MONTAGE and j not in ("TRANSITION", "JUMP", "MONTAGE") and (de > 16 or bh > 0.55):
        info["flags"].append(f"LIGHT jump in the same place (dE {de:.0f}, hist {bh:.2f})")
    return info, tiles


# ---------------------------------------------------------------- sheets
def label_font(n, bold=True):
    return truetype(FONT_B if bold else FONT_R, n)


def sheet(rows, path):
    ncol = 2 if a.stills else 4
    gap, lab = 14, 70
    im = Image.new("RGB", (ncol * TW + gap, len(rows) * (TH + lab)), (18, 18, 22))
    d = ImageDraw.Draw(im)
    heads = ["A", "B"] if a.stills else ["A -0.6s", "A last", "B first", "B +0.6s"]
    for r, (info, tiles, sa, sb) in enumerate(rows):
        y = r * (TH + lab)
        for k, t in enumerate(tiles):
            x = k * TW + (gap if k >= ncol // 2 else 0)
            im.paste(Image.fromarray(t).resize((TW, TH)), (x, y))
            d.text((x + 5, y + 4), heads[k], fill=(255, 255, 0), font=label_font(14))
        d.rectangle([ncol // 2 * TW, y, ncol // 2 * TW + gap - 1, y + TH], fill=(255, 70, 70) if info["flags"] else (70, 200, 110))
        m, sec = divmod(info["cut"], 60)
        head = (f"{int(m)}:{sec:04.1f}  {sa['id']} -> {sb['id']}   {place(sa)} -> {place(sb)}   "
                f"look {sa.get('look') or '-'} -> {sb.get('look') or '-'}" + (f"   join {info['join']}" if info["join"] else ""))
        d.text((6, y + TH + 3), head, fill=(255, 220, 80), font=label_font(16))
        txt = "  |  ".join(info["flags"] + info["info"]) or "no automatic flag: check it by eye"
        d.text((6, y + TH + 25), txt[:190], fill=(255, 110, 110) if info["flags"] else (160, 200, 170), font=label_font(15, False))
        intent = (sb.get("staging") or sb.get("scene") or "")
        d.text((6, y + TH + 46), ("B is meant to be: " + intent)[:200], fill=(170, 170, 185), font=label_font(13, False))
    im.save(path, quality=85)


def main():
    shots = [s for s in SB if s["t1"] > a.t_from and s["t0"] < a.t_to]
    pairs = [(x, y) for x, y in zip(shots, shots[1:]) if a.t_from <= y["t0"] <= a.t_to]
    results, bucket = [], {}
    for sa, sb in pairs:
        info, tiles = check(sa, sb)
        results.append(info)
        if tiles:
            bucket.setdefault(int(info["cut"] // 60), []).append((info, tiles, sa, sb))
        print(f"{info['cut']:7.2f}  {sa['id']}->{sb['id']}  " + ("; ".join(info["flags"] + info["info"]) or "-"), flush=True)
    for m, rows in sorted(bucket.items()):
        for k in range(0, len(rows), ROWS):
            sheet(rows[k:k + ROWS], os.path.join(OUT, f"min_{m:02d}_{'abcdefgh'[k // ROWS]}.jpg"))
    json.dump(results, open(os.path.join(OUT, "joins.json"), "w"), indent=1)
    lines = ["# Joins (automatic pass)", "",
             f"Source: {'the stills' if a.stills else a.cut}. Flags are hints; every join still gets the eye check in the skill.", "",
             "| # | Cut | A -> B | Places | Automatic flags | Verdict | Category | Fix |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(results, 1):
        m, sec = divmod(r["cut"], 60)
        lines.append(f"| {i} | {int(m)}:{sec:04.1f} | {r['a']} -> {r['b']} | {r['place_a']} -> {r['place_b']} | "
                     f"{'; '.join(r['flags'] + r['info']) or '-'} |  |  |  |")
    open(os.path.join(OUT, "JOINS_auto.md"), "w").write("\n".join(lines) + "\n")
    print(f"{len(results)} joins, {sum(1 for r in results if r['flags'])} with flags -> {OUT}")


if __name__ == "__main__":
    main()
