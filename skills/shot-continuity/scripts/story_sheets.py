"""End-to-end story pass: the whole cut in order, shot by shot. It exists because a cut can pass every per-shot and per-join check
and still not have been read from start to finish, as a viewer sees it.

  python tools/story_sheets.py CUT.mp4 OUTDIR

Writes OUTDIR/seq_XX.jpg (six shots per sheet, in order: first, middle and last played frame of each, with its time, lyric and board
picture) for reading the film as a sequence, and OUTDIR/join_NNN.jpg (per cut: A -1.0 s, A last, B first, B +1.0 s, with both rows)
plus OUTDIR/joins.json for the join judge (join_judge.py). Decodes the cut once (on the GPU where venc.py finds one) and keeps only
the frames it needs.

Run it from the project folder. It reads storyboard.json there (another name: the environment variable STORYBOARD), a JSON list
of shots in cut order with, per shot: id, t0, t1 (seconds in the cut), and for the labels cap (the lyric), scene (the picture),
type, join and set. The cut must start at the board's 0:00. It is read at 25 frames a second (FPS below): a cut at another
frame rate is resampled, so the frames still land on the board's times.
"""
import json, os, shutil, subprocess, sys
import numpy as np, imageio_ffmpeg
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import venc
from fonts import truetype  # Windows font names -> the closest face on this machine

if len(sys.argv) < 3:
    sys.exit(__doc__)
CUT, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
FPS, W, H = 25, 480, 270
NICE = ["nice", "-n", "19"] if shutil.which("nice") else []  # low priority for the decode; there is no nice on Windows
FB, FR = "arialbd.ttf", "arial.ttf"
sb = json.load(open(os.environ.get("STORYBOARD", "storyboard.json")))  # STORYBOARD=other.json for a board with another name
shots = []
for s in sb:
    a, b = round(s["t0"] * FPS), round(s["t1"] * FPS)
    shots.append(dict(s, f0=a, f1=b, cap=s.get("cap") or s.get("lyric"), scene=s.get("scene") or " | ".join(x for x in (s.get("still_prompt"), s.get("motion")) if x)))  # older boards: lyric/still_prompt/motion
need = set()
for s in shots:
    n = s["f1"] - s["f0"]
    s["pick"] = [s["f0"] + min(2, n // 4), s["f0"] + n // 2, s["f1"] - 1 - min(2, n // 4)]
    need.update(s["pick"])
joins = []
for x, y in zip(shots, shots[1:]):
    c = y["f0"]
    fr = [max(x["f0"], c - FPS), c - 1, c, min(y["f1"] - 1, c + FPS)]
    joins.append((x, y, fr)); need.update(fr)
p = subprocess.Popen([*NICE, FF, "-v", "error", *venc.hwdec(), "-i", CUT, "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
frames, k, sz = {}, 0, W * H * 3
while True:
    buf = p.stdout.read(sz)
    if len(buf) < sz:
        break
    if k in need:
        frames[k] = Image.fromarray(np.frombuffer(buf, np.uint8).reshape(H, W, 3))
    k += 1
p.wait()
f1, f2, f3 = truetype(FB, 17), truetype(FR, 14), truetype(FB, 14)
def ts(f):
    m, s = divmod(f / FPS, 60)
    return f"{int(m)}:{s:04.1f}"
def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) > width:
            lines.append(cur); cur = w
        else:
            cur = t
    return lines + ([cur] if cur else [])
# sequence sheets: 6 shots per sheet
LW = 330
for si in range(0, len(shots), 6):
    grp = shots[si:si + 6]
    im = Image.new("RGB", (LW + 3 * W, len(grp) * (H + 6)), (14, 14, 18)); d = ImageDraw.Draw(im)
    for r, s in enumerate(grp):
        y = r * (H + 6)
        d.text((8, y + 6), f"{s['id']}  {ts(s['f0'])}-{ts(s['f1'])}", fill=(255, 220, 80), font=f1)
        d.text((8, y + 28), f"{s.get('type') or s.get('kind') or '-'}  join in: {s.get('join') or '-'}  set: {s.get('set') or '-'}", fill=(170, 200, 255), font=f2)
        yy = y + 48
        for line in wrap(d, "♪ " + (s.get("cap") or "(music)"), f3, LW - 14)[:3]:
            d.text((8, yy), line, fill=(240, 240, 240), font=f3); yy += 17
        for line in wrap(d, s.get("scene") or "", f2, LW - 14)[:9]:
            d.text((8, yy), line, fill=(185, 185, 190), font=f2); yy += 16
        for c, f in enumerate(s["pick"]):
            if f in frames:
                im.paste(frames[f], (LW + c * W, y))
                d.text((LW + c * W + 5, y + 4), ["first", "middle", "last"][c] + "  " + ts(f), fill=(255, 255, 0), font=f3)
    im.save(os.path.join(OUT, f"seq_{si // 6:02d}.jpg"), quality=84)
# join images for the judge
for i, (x, y, fr) in enumerate(joins, 1):
    im = Image.new("RGB", (4 * W, H + 150), (14, 14, 18)); d = ImageDraw.Draw(im)
    d.text((8, 6), f"CUT {i}  at {ts(y['f0'])}:  {x['id']} -> {y['id']}   (board join type: {y.get('join') or '-'})", fill=(255, 220, 80), font=f1)
    d.text((8, 30), ("A " + x["id"] + ": " + (x.get("scene") or ""))[:245], fill=(200, 200, 205), font=f2)
    d.text((8, 50), ("B " + y["id"] + ": " + (y.get("scene") or ""))[:245], fill=(200, 200, 205), font=f2)
    for c, f in enumerate(fr):
        if f in frames:
            im.paste(frames[f], (c * W, 150))
            d.text((c * W + 5, 132), ["A, 1 s before the cut", "A, last frame", "B, first frame", "B, 1 s after the cut"][c] + "  " + ts(f), fill=(255, 255, 0), font=f3)
    d.line((2 * W - 2, 150, 2 * W - 2, 150 + H), fill=(60, 220, 90), width=4)
    im.save(os.path.join(OUT, f"join_{i:03d}.jpg"), quality=84)
json.dump([{"i": i, "a": x["id"], "b": y["id"], "t": y["t0"], "join": y.get("join")} for i, (x, y, fr) in enumerate(joins, 1)],
          open(os.path.join(OUT, "joins.json"), "w"), indent=1)
print("frames", len(frames), "sheets", (len(shots) + 5) // 6, "joins", len(joins), "->", OUT)
