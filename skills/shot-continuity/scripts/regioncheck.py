"""One region of a clip's used window at full resolution, every Nth frame: for depth order and small props (is one thing in front
of another? did a small prop stay?), where a whole-frame grid is too small. Region as fractions of the frame: x0,y0,x1,y1.
Usage: python regioncheck.py ID x0,y0,x1,y1 [--every 3] [--pad 0] [--t0 S --dur S] [--out review] [--sb storyboard.json] [--clips gen/clips] [--window windows.json]
Run it from the project folder. An ID like V02_b reads gen/clips/V02_b.mp4 (a second take) against the board row V02. --t0 and --dur
(seconds into the clip) replace the window and the shot's length.
--sb, --clips and --window (a JSON file {shot id: seconds into the clip where the cut starts playing it}) are described in chainlib.py."""
import argparse, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chainlib as C
ap = argparse.ArgumentParser(); ap.add_argument("id"); ap.add_argument("box"); ap.add_argument("--every", type=int, default=3)
ap.add_argument("--pad", type=float, default=0); ap.add_argument("--t0", type=float); ap.add_argument("--dur", type=float); ap.add_argument("--out", default="review"); C.add_common(ap)
a = ap.parse_args(); sb, win = C.load(a); os.makedirs(a.out, exist_ok=True)
base = a.id.split("_")[0]; t0 = a.t0 if a.t0 is not None else C.window(win, a.id, a.default_window); dur = a.dur or C.nframes(sb[base]) / C.EDIT_FPS + a.pad
x0, y0, x1, y1 = map(float, a.box.split(","))
src = os.path.join(a.clips, a.id + ".mp4"); W, H, _ = C.probe(src)
r = subprocess.run([C.FF, "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", src, "-vf", f"fps={C.EDIT_FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
fr = np.frombuffer(r.stdout, np.uint8).reshape(-1, H, W, 3)[::a.every]
cw, ch = int((x1 - x0) * W), int((y1 - y0) * H)
cols = min(8, len(fr)); rows = (len(fr) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cw, rows * ch)); d = ImageDraw.Draw(sheet)
for k, f in enumerate(fr):
    c = Image.fromarray(f[int(y0 * H):int(y0 * H) + ch, int(x0 * W):int(x0 * W) + cw]); x, y = (k % cols) * cw, (k // cols) * ch
    sheet.paste(c, (x, y)); d.rectangle((x, y, x + 44, y + 14), fill="black"); d.text((x + 3, y + 2), f"{t0 + k * a.every / C.EDIT_FPS:.2f}", fill="yellow")
p = os.path.join(a.out, f"region_{a.id}.jpg"); sheet.save(p, quality=88); print(p, len(fr), sheet.size)
