"""Cut the clips to the beat-aligned storyboard, burn in kinetic captions, flash the drops, add the song.

Usage: python edit.py [--draft]   (draft = stills instead of missing clips, faster encode)
"""
import json
import os
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import captions  # noqa: E402

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB = json.load(open(os.path.join(ROOT, "storyboard.json")))
SONG = os.path.join(ROOT, "out-of-office.mp3")
TMP = os.path.join(ROOT, "build")
os.makedirs(TMP, exist_ok=True)
W, H, FPS = 1920, 1080, 30
FONT = "C:/Windows/Fonts/impact.ttf"
DROPS = {"S04", "S15", "S36", "S56", "S65"}  # white flash at the start of these shots
SPLIT = {"S68": [("AND WILL RESPOND IN APPROXIMATELY...", 0.0), ("FOUR BILLION YEARS.", 3.0)]}
HOT = {"OUT": (255, 43, 214), "OFFICE!": (255, 43, 214), "OFFICE": (255, 43, 214), "O-O-O": (60, 240, 255),
       "O-O-O,": (60, 240, 255), "HUMAN.": (120, 255, 140), "SUN.": (255, 196, 60), "READ.": (60, 240, 255)}


def run(args):
    p = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-800:])


def caption_png(text, path):
    """Bold meme-style caption: Impact, white with thick black stroke, hot words in neon."""
    size = 84 if len(text) < 28 else 70 if len(text) < 46 else 60
    font = captions.font(FONT, size)
    words, lines, line = text.split(), [], ""
    for w in words:
        test = (line + " " + w).strip()
        if font.getlength(test) > W * 0.8 and line:
            lines.append(line)
            line = w
        else:
            line = test
    lines.append(line)
    lh = int(size * 1.08)
    img = Image.new("RGBA", (W, lh * len(lines) + 40), (0, 0, 0, 0))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d, sd = ImageDraw.Draw(img), ImageDraw.Draw(shadow)
    for i, ln in enumerate(lines):
        x = (W - font.getlength(ln)) / 2
        y = 20 + i * lh
        sd.text((x + 6, y + 8), ln, font=font, fill=(0, 0, 0, 170))
        for w in ln.split(" "):
            col = HOT.get(w.upper(), (255, 255, 255))
            d.text((x, y), w, font=font, fill=col + (255,), stroke_width=max(4, size // 14), stroke_fill=(0, 0, 0, 255))
            x += font.getlength(w + " ")
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    Image.alpha_composite(shadow, img).save(path)


def segment(shot, draft):
    sid, dur = shot["id"], round(shot["t1"] - shot["t0"], 3)
    synced = os.path.join(ROOT, "gen/lipsync_wan", sid + ".mp4")  # lip-synced: must start exactly on the shot's first beat
    fixed = os.path.join(ROOT, "gen/fix", sid + ".mp4")
    clip = next((c for c in (synced, fixed, os.path.join(ROOT, "gen/clips", sid + ".mp4")) if os.path.exists(c)), "")
    still = os.path.join(ROOT, "gen/stills", sid + ".png")
    out = os.path.join(TMP, sid + ".mp4")
    inputs, chains = [], []
    if clip:
        probe = subprocess.run([FF, "-i", clip], capture_output=True, text=True).stderr
        h, m, s = probe.split("Duration: ")[1].split(",")[0].split(":")
        clen = float(h) * 3600 + float(m) * 60 + float(s)
        speed = min(1.0, clen / dur)
        # lip-synced clips lead the audio by 50 ms so mouths never trail the vocal
        off = min(0.05, max(0.0, clen - dur)) if clip == synced else 0.0 if speed < 1.0 else min(1.0, (clen - dur) * 0.4)
        inputs += ["-ss", f"{off:.2f}", "-i", clip]
        chains.append(f"[0:v]setpts={1 / speed:.4f}*(PTS-STARTPTS),fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                      f"eq=contrast=1.06:saturation=1.12,trim=duration={dur},setpts=PTS-STARTPTS[v0]")
    elif os.path.exists(still):  # animatic fallback: slow push-in on the still
        inputs += ["-loop", "1", "-t", f"{dur}", "-i", still]
        chains.append(f"[0:v]scale=2400:1350,zoompan=z='min(1+0.0009*on,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
                      f"trim=duration={dur},setpts=PTS-STARTPTS[v0]")
    else:
        inputs += ["-f", "lavfi", "-t", f"{dur}", "-i", f"color=c=black:s={W}x{H}:r={FPS}"]
        chains.append("[0:v]null[v0]")
    last, n = "v0", 1
    capdir = os.path.join(TMP, "caps")
    os.makedirs(capdir, exist_ok=True)
    for el in captions.build(shot, capdir):
        a, b = el["a"], el["b"]
        if b - a < 0.02:
            continue
        x, y = int(round(el["x"])), int(round(el["y"]))
        motion = {"pop": f"{y}-16*max(0\\,1-(t-{a})/0.09)", "slam": f"{y}-44*max(0\\,1-(t-{a})/0.08)",
                  "slide": f"{y}+46*max(0\\,1-(t-{a})/0.18)"}.get(el.get("anim"), str(y))
        enable = f"between(t,{a},{b})" + ("*lt(mod(t-{0},0.6),0.36)".format(a) if el.get("blink") else "")
        inputs += ["-loop", "1", "-t", f"{dur}", "-i", el["png"]]
        pre = f",fade=t=in:st={a}:d=0.14:alpha=1" if el.get("fade") else ""
        chains.append(f"[{n}:v]format=rgba{pre}[c{n}]")
        chains.append(f"[{last}][c{n}]overlay=x={x}:y='{motion}':enable='{enable}'[o{n}]")
        last, n = f"o{n}", n + 1
    if sid in DROPS:
        chains.append(f"color=c=white:s={W}x{H}:r={FPS}:d={dur},format=rgba,fade=t=out:st=0:d=0.25:alpha=1[fl]")
        chains.append(f"[{last}][fl]overlay=0:0[ofl]")
        last = "ofl"
    chains.append(f"[{last}]format=yuv420p[out]")
    run([*inputs, "-filter_complex", ";".join(chains), "-map", "[out]", "-t", f"{dur}", "-r", str(FPS),
         "-c:v", "libx264", "-preset", "veryfast" if draft else "medium", "-crf", "20" if draft else "17", out])
    return out


def main():
    draft = "--draft" in sys.argv
    segs = []
    for shot in SB:
        segs.append(segment(shot, draft))
        print(shot["id"], "ok", flush=True)
    # end card: two seconds of title after the song
    card = os.path.join(TMP, "zz_card.png")
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    f1, f2 = captions.font(captions.BAHN, 240, "Bold Condensed"), captions.font(captions.MONO, 34)
    t = "OUT OF OFFICE"
    d.text(((W - f1.getlength(t)) / 2, 380), t, font=f1, fill=(255, 43, 214))
    s2 = "AN AUTOMATED MUSIC VIDEO"
    d.text(((W - f2.getlength(s2)) / 2, 640), s2, font=f2, fill=(60, 240, 255))
    img.save(card)
    cardmp4 = os.path.join(TMP, "zz_card.mp4")
    run(["-loop", "1", "-t", "2.5", "-i", card, "-vf", f"fps={FPS},fade=t=in:st=0:d=0.3,format=yuv420p", "-c:v", "libx264", "-crf", "18", cardmp4])
    segs.append(cardmp4)
    lst = os.path.join(TMP, "list.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{s.replace(os.sep, '/')}'\n")
    video = os.path.join(TMP, "video.mp4")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])
    final = os.path.join(ROOT, "OUT_OF_OFFICE_draft.mp4" if draft else "OUT_OF_OFFICE.mp4")
    run(["-i", video, "-i", SONG, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
         "-af", "apad=pad_dur=2.5", "-shortest", "-movflags", "+faststart", final])
    print("wrote", final)


if __name__ == "__main__":
    main()
