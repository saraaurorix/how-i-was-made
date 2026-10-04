"""Character sheet: one face per shot, in story order, so identity drift shows at a glance (the shot-continuity skill).

  python face_sheet.py --cut CUT.mp4 [--who sara|kevin] [--sb storyboard.json] [--out review/joins/faces_sara.jpg]
  python face_sheet.py --stills [--who sara|kevin] ...

Run it from the project folder. For each shot (a frame at 40 % into it, or the still: the board's `still_file`, else
gen/stills/<id>.png): Sara is the face with cyan irises or her platinum fringe, and Kevin the face with his dark moustache, in shots
whose storyboard `scene` names KEVIN. The crop is square around the face with room for the hair, labelled with the shot id, time and
look. Look along a row for: seams on the jaw and cheeks, eye colour, make-up, the fringe line, glasses and moustache, the crown, the
neckline, anything that comes and goes.

Tuned for this series' two characters: the face tests are join_check.py's (the end of its faces() function), which this script
loads from its own folder. Change them there for your own characters, and the --who choices here to match.
The storyboard fields read: id, t0, t1, look, scene, and type or set/fmt (a shot marked "edit" is a graphic and is skipped).
"""
import argparse
import importlib.util
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fonts import truetype  # Windows font names -> the closest face on this machine

ap = argparse.ArgumentParser()
ap.add_argument("--cut", default="")
ap.add_argument("--stills", action="store_true")
ap.add_argument("--who", default="sara", choices=["sara", "kevin"])
ap.add_argument("--sb", default="storyboard.json")
ap.add_argument("--out", default="")
ap.add_argument("--cols", type=int, default=10)
a = ap.parse_args()
if not a.cut and not a.stills:
    ap.error("give --cut FILE or --stills")

# reuse join_check's frame grabber and face finder without running its main()
_here = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["join_check.py", "--stills" if a.stills else "--cut", *([] if a.stills else [a.cut]), "--sb", a.sb,
            "--from", "1e9", "--to", "1e9", "--out", os.path.join(os.path.dirname(a.out or "review/joins/x"), "_fs")]
spec = importlib.util.spec_from_file_location("join_check", os.path.join(_here, "join_check.py"))
jc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jc)

SB = json.load(open(a.sb))
T = 150
F = truetype("arialbd.ttf", 13)
tiles = []
for s in SB:
    if s.get("type") == "edit" or (s.get("set") or s.get("fmt")) == "edit":
        continue
    if a.who == "kevin" and "KEVIN" not in (s.get("scene") or ""):
        continue
    if a.stills:
        img = jc.still(s)
    else:
        fr = jc.frames_at(s["t0"] + 0.4 * (s["t1"] - s["t0"]), 1)
        img = fr[0] if fr else None
    if img is None:
        continue
    fs = jc.faces(img, thorough=True)
    if a.who == "sara":
        cand = [f for f in fs if f["sara"]]
    else:  # Kevin by his moustache (join_check's measure), never just "the biggest other face"
        cand = [f for f in fs if f.get("kevin")]
    if not cand:
        continue
    f = max(cand, key=lambda f: f["w"])
    h, w = img.shape[:2]
    cx, cy, half = f["x"] * w, f["y"] * h, max(40, f["w"] * w * 0.95)
    box = [int(max(0, cx - half)), int(max(0, cy - half * 1.15)), int(min(w, cx + half)), int(min(h, cy + half * 0.85))]
    crop = Image.fromarray(img).crop(box).resize((T, T))
    m, sec = divmod(s["t0"], 60)
    tiles.append((crop, f"{s['id']} {int(m)}:{sec:04.1f}", s.get("look") or ""))

cols = a.cols
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * T, max(1, rows) * (T + 34)), (18, 18, 22))
d = ImageDraw.Draw(sheet)
for k, (crop, lab, look) in enumerate(tiles):
    x, y = (k % cols) * T, (k // cols) * (T + 34)
    sheet.paste(crop, (x, y))
    d.text((x + 4, y + T + 2), lab, fill=(255, 220, 80), font=F)
    d.text((x + 4, y + T + 17), look, fill=(190, 190, 200), font=F)
out = a.out or f"review/joins/faces_{a.who}.jpg"
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
sheet.save(out, quality=86)
print(out, len(tiles), "faces")
