"""Review sheet: for each finished clip, frames at the start, middle and end of the part the edit will use.

Usage: python tools/clipsheet.py out_prefix [ID,ID]
"""
import json
import os
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB = json.load(open(os.path.join(ROOT, "storyboard.json")))
TW, TH, PER = int(os.environ.get("TW", 400)), int(os.environ.get("TH", 225)), int(os.environ.get("PER", 4))  # thumb size, clips per row
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fonts import truetype  # noqa: E402
font = truetype("ariblk.ttf", 20)


def clip_of(sid):
    for d in ("gen/lipsync", "gen/fix", "gen/clips"):
        p = os.path.join(ROOT, d, sid + ".mp4")
        if os.path.exists(p):
            return p
    return None


def frame(path, t):
    p = subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-vf", f"scale={TW}:{TH}",
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    from io import BytesIO
    return Image.open(BytesIO(p.stdout)).convert("RGB") if p.stdout else Image.new("RGB", (TW, TH))


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    prefix = sys.argv[1]
    want = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    items = [(s["id"], clip_of(s["id"]), s["t1"] - s["t0"]) for s in SB if (not want or s["id"] in want)]
    items = [i for i in items if i[1]]
    rows = [items[k:k + PER] for k in range(0, len(items), PER)]
    for page in range(0, len(rows), 5):
        chunk = rows[page:page + 5]
        sheet = Image.new("RGB", (PER * (3 * TW + 16), len(chunk) * (TH + 4)), (0, 0, 0))
        d = ImageDraw.Draw(sheet)
        for r, row in enumerate(chunk):
            for c, (sid, path, dur) in enumerate(row):
                x0, y0 = c * (3 * TW + 16), r * (TH + 4)
                for k, t in enumerate((0.1, dur * 0.5, max(0.1, dur - 0.1))):
                    sheet.paste(frame(path, t), (x0 + k * TW, y0))
                d.rectangle([x0, y0, x0 + 64, y0 + 28], fill=(0, 0, 0))
                d.text((x0 + 4, y0 + 2), sid, font=font, fill=(255, 255, 0))
        out = f"{prefix}_{page // 5 + 1}.jpg"
        sheet.save(out, quality=80)
        print(out)


if __name__ == "__main__":
    main()
