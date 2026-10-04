"""Contact sheets of stills (or first frames), 4 columns x 4 rows, labelled.

Usage: python tools/contact.py STILLS_DIR out_prefix [ID,ID]   -> out_prefix_1.jpg, out_prefix_2.jpg ...
"""
import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFont

if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
    sys.exit(__doc__)
src, out_prefix = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(out_prefix) or ".", exist_ok=True)
ids = sys.argv[3].split(",") if len(sys.argv) > 3 else None
files = sorted(glob.glob(os.path.join(src, "*.png")) + glob.glob(os.path.join(src, "*.jpg")))
if ids:
    files = [f for f in files if os.path.splitext(os.path.basename(f))[0] in ids]
tw, th, cols, rows = 480, 270, 4, 4
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fonts import truetype  # noqa: E402
font = truetype("ariblk.ttf", 22)
for page in range(0, len(files), cols * rows):
    batch = files[page:page + cols * rows]
    sheet = Image.new("RGB", (cols * tw, ((len(batch) + cols - 1) // cols) * th), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(batch):
        im = Image.open(f).convert("RGB").resize((tw, th))
        x, y = (i % cols) * tw, (i // cols) * th
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + 70, y + 30], fill=(0, 0, 0))
        d.text((x + 6, y + 2), os.path.splitext(os.path.basename(f))[0], font=font, fill=(255, 255, 0))
    sheet.save(f"{out_prefix}_{page // (cols * rows) + 1}.jpg", quality=82)
    print(f"{out_prefix}_{page // (cols * rows) + 1}.jpg")
