"""Casting check, step 2: a labelled listening clip for the director's ear.

One title card per PASSAGE (a run of lines, not single lines: the listener answers per card and names the odd line
inside it, e.g. "all voice B but line 31 is Sara"), then the passage itself from the full mix.
Card 1 is always a CONTROL passage you are sure of, so the listener can calibrate their ear.
Every card shows: n of N, the time range, the lines, "Sheet: X  Detector: Y", and "Who sings it: Sara or voice B?".
The encode goes through venc.py (the GPU encoder where the machine has one), -g 30.

Usage (from the single's folder; needs casting.json from casting_scan.py):
  python tools/casting_clip.py --wav audio/<take>.wav --out casting_check/CASTING_CHECK.mp4 \
      "Control: Verse 1 ending|12|13|Sara|Sara" "Verse 2|27|34|Sara|VOICE B (timbre)" ...
Each passage is "label|first line n|last line n|sheet says|detector says".
Record the answers back into casting.json as "ear" per line (S/B), plus casting.md.
"""
import argparse
import json
import os
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import venc  # noqa: E402
from fonts import truetype  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--wav", required=True)
ap.add_argument("--casting", default="casting.json")
ap.add_argument("--out", default="casting_check/CASTING_CHECK.mp4")
ap.add_argument("passages", nargs="+")
a = ap.parse_args()

FF = imageio_ffmpeg.get_ffmpeg_exe()
C = {c["n"]: c for c in json.load(open(a.casting))}
tag = os.path.splitext(os.path.basename(a.out))[0]
pdir = os.path.join(os.path.dirname(a.out) or ".", f"parts_{tag}")
os.makedirs(pdir, exist_ok=True)
big, mid, small = (truetype("bahnschrift.ttf", s, "Bold Condensed") for s in (50, 38, 30))
P = [p.split("|") for p in a.passages]
parts = []
for i, (label, n0, n1, sheet, guess) in enumerate(P, 1):
    n0, n1 = int(n0), int(n1)
    t0, t1 = max(0, C[n0]["t0"] - 0.4), C[n1]["t1"] + 0.5
    im = Image.new("RGB", (1280, 720), (14, 14, 18))
    d = ImageDraw.Draw(im)
    d.text((60, 50), f"{i} of {len(P)}   {int(t0 // 60)}:{t0 % 60:04.1f} - {int(t1 // 60)}:{t1 % 60:04.1f}", font=small, fill=(0, 229, 255))
    d.text((60, 100), label, font=big, fill="white")
    y = 190
    for n in range(n0, n1 + 1):
        if y > 520:
            d.text((60, y), "...", font=small, fill=(170, 170, 170))
            break
        d.text((60, y), C[n]["text"][:70], font=small, fill=(210, 210, 210))
        y += 40
    d.text((60, 580), f"Sheet: {sheet}    Detector: {guess}", font=small, fill=(255, 200, 0))
    d.text((60, 630), "Who sings it: Sara or voice B?", font=mid, fill=(0, 229, 255))
    png, mp4 = f"{pdir}/{i:02d}.png", f"{pdir}/{i:02d}.mp4"
    im.save(png)
    subprocess.run(["nice", "-n", "19", FF, "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", png,
                    "-ss", f"{t0:.2f}", "-to", f"{t1:.2f}", "-i", a.wav, "-map", "0:v", "-map", "1:a", "-shortest",
                    *venc.h264(60, gop=30), "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", mp4], check=True)
    parts.append(mp4)
    print(i, label, f"{t1 - t0:.1f}s")
lst = f"{pdir}/list.txt"
open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", a.out], check=True)
print(a.out)
