"""Outfit-drift audit: one row per look, the look's anchor still first (red border), then every other still of that look.
Drift shows as a row where a neckline, colour, cut or material changes. Run after every stills round and before the animatic.
Optional --clips: add each clip's last frame (gen/clips/<ID>.mp4, gen/lip_omni/<ID>.mp4) after its still, to catch drift inside video.
Storyboard rows need "look", "still" (the still's label) and "still_file" (its path). The anchor for a look is its first still,
unless an optional outfit_ref.json ({"look": "still:<label>"}) names another.
Usage: python tools/outfit_audit.py [--clips]  ->  review/outfit_audit.jpg"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fonts import truetype  # noqa: E402
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); os.chdir(ROOT)
FF = imageio_ffmpeg.get_ffmpeg_exe()
TW, TH, PAD, LAB = 256, 144, 6, 150
FONT = truetype("arialbd.ttf", 16)
CLIPS = "--clips" in sys.argv
shots = json.load(open("storyboard.json"))
try:  # the anchor for each look is its outfit_ref.json still when there is one, else its first still
    ref = json.load(open("outfit_ref.json"))
except Exception:
    ref = {}


def last_frame(mp4):
    out = os.path.join(tempfile.gettempdir(), f"_oa_{os.path.basename(mp4)}.jpg")
    subprocess.run([FF, "-v", "error", "-y", "-sseof", "-0.2", "-i", mp4, "-frames:v", "1", out], check=False)
    return out if os.path.exists(out) else None


rows = {}
for s in shots:
    if not s["look"]:
        continue
    items = rows.setdefault(s["look"], [])
    if not any(p == s["still_file"] for _, p in items):
        items.append((s["still"], s["still_file"]))
    if CLIPS:
        for mp4 in (f"gen/lip_omni/{s['id']}.mp4", f"gen/clips/{s['id']}.mp4"):
            if os.path.exists(mp4) and (f := last_frame(mp4)):
                items.append((s["id"] + " end", f))
for look, items in rows.items():
    anchor = ref.get(look, "")
    anchor = anchor[6:] if anchor.startswith("still:") else None
    if anchor:
        items.sort(key=lambda it: it[0] != anchor)
cols = max(len(v) for v in rows.values())
W = LAB + cols * (TW + PAD); H = len(rows) * (TH + 24 + PAD)
sheet = Image.new("RGB", (W, H), (18, 12, 30)); d = ImageDraw.Draw(sheet)
y = 0
for look, items in rows.items():
    d.text((8, y + TH // 2), look, fill="white", font=FONT)
    for i, (label, path) in enumerate(items):
        x = LAB + i * (TW + PAD)
        try:
            im = Image.open(path).convert("RGB"); im.thumbnail((TW, TH)); sheet.paste(im, (x, y))
        except Exception:
            d.text((x + 8, y + 8), "missing", fill="red", font=FONT)
        if i == 0:
            d.rectangle([x - 2, y - 2, x + TW + 1, y + TH + 1], outline=(255, 60, 60), width=3)
        d.text((x + 4, y + TH + 3), label + ("  (anchor)" if i == 0 else ""), fill="white", font=FONT)
    y += TH + 24 + PAD
os.makedirs("review", exist_ok=True)
sheet.save("review/outfit_audit.jpg", quality=82)
print("review/outfit_audit.jpg", len(rows), "looks,", sum(len(v) for v in rows.values()), "tiles")
