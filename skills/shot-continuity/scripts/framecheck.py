"""Every Nth frame of the seconds the cut uses from a clip, as one timestamped grid per shot: what strips miss (one object drawn over another,
a morph, a pop, something that jumps between frames).
Usage: python framecheck.py ID[,ID] [--every 2] [--tw 480] [--pad 0] [--out review] [--sb storyboard.json] [--clips gen/clips] [--window windows.json]
Run it from the project folder. An ID like V02_b reads gen/clips/V02_b.mp4 (a second take) against the board row V02.
--sb, --clips and --window (a JSON file {shot id: seconds into the clip where the cut starts playing it}) are described in chainlib.py."""
import argparse, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chainlib as C
ap = argparse.ArgumentParser(); ap.add_argument("ids"); ap.add_argument("--every", type=int, default=2); ap.add_argument("--tw", type=int, default=480)
ap.add_argument("--pad", type=float, default=0.0); ap.add_argument("--out", default="review"); C.add_common(ap)
a = ap.parse_args(); sb, win = C.load(a); os.makedirs(a.out, exist_ok=True)
TW = a.tw; TH = TW * 9 // 16
for sid in a.ids.split(","):
    base = sid.split("_")[0]; w0 = C.window(win, sid, a.default_window); dur = C.nframes(sb[base]) / C.EDIT_FPS + a.pad
    r = subprocess.run([*C.NICE, C.FF, "-v", "error", "-ss", f"{w0:.3f}", "-t", f"{dur:.3f}", "-i", os.path.join(a.clips, sid + ".mp4"),
                        "-vf", f"fps={C.EDIT_FPS},scale={TW}:{TH}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    fr = np.frombuffer(r.stdout, np.uint8).reshape(-1, TH, TW, 3)[::a.every]
    cols = min(6, len(fr)); rows = (len(fr) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TW, rows * TH), "black"); d = ImageDraw.Draw(sheet)
    for k, f in enumerate(fr):
        x, y = (k % cols) * TW, (k // cols) * TH; sheet.paste(Image.fromarray(f), (x, y))
        d.rectangle((x, y, x + 70, y + 16), fill="black"); d.text((x + 4, y + 3), f"{sid} {w0 + k * a.every / C.EDIT_FPS:.2f}", fill="yellow")
    p = os.path.join(a.out, f"fc_{sid}.jpg"); sheet.save(p, quality=84); print(p, len(fr), "frames", sheet.size)
