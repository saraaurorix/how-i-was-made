"""Vertical 9:16 Reels cut: bar-aligned song ranges, face-aware crops, vertical captions, stem-based audio joins."""
import json
import os
import subprocess

import cv2
import imageio_ffmpeg
import librosa
import numpy as np
from PIL import Image, ImageDraw

import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))  # tools/, for captions.py
import captions  # noqa: E402

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SB = json.load(open(os.path.join(ROOT, "storyboard.json")))
TIM = json.load(open(os.path.join(ROOT, "timing.json")))
STEMS = os.path.join(ROOT, "lipsync/sep/htdemucs/out-of-office")
TMP = os.path.join(ROOT, "build_reel")
os.makedirs(TMP, exist_ok=True)
VW, VH, FPS = 1080, 1920, 30
SW, SH = 1920, 1080
CROP_W = int(round(SH * VW / VH))  # 608 source px wide for a 9:16 crop
captions.configure(VW, VH, True)

# song ranges (bar numbers) kept in the reel, and where the vocal should fade early to avoid a clipped word
BARS = [(0, 12), (24, 41), (73, 91), (117, None)]
VOCAL_END = {0: 22.35}  # range index -> song time to fade the vocal out
FIT = {"S47", "S59", "S43", "S44", "S51", "S52", "S62", "S64", "S66", "S68", "S69", "S70", "S45", "S46", "S53", "S63", "S02", "S58", "S65"}
CROPX = {"S01": 656, "S18": 656, "S74": 656, "S06": 1130}
FOCUS = {"S40": "right", "S21": "left", "S09": "left", "S30": "right", "S13": "right", "S34": "left", "S22": "right"}


def run(args):
    p = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-900:])


def snap_points():
    y, sr = librosa.load(os.path.join(STEMS, "no_vocals.wav"), sr=22050)
    env = librosa.onset.onset_strength(y=y, sr=sr, fmax=200, hop_length=256)
    times = librosa.frames_to_time(np.arange(len(env)), sr=sr, hop_length=256)
    dur = len(y) / sr

    def snap(n):
        g = TIM["start"] + n * TIM["bar"]
        m = (times > g - 0.25) & (times < g + 0.25)
        return float(times[m][np.argmax(env[m])]) if m.any() else g
    r = [(snap(a), snap(b) if b is not None else dur) for a, b in BARS]
    r[0] = (0.0, r[0][1])  # never clip the opening "Hello"
    return r, dur


def clip_for(sid):
    for d in ("gen/lipsync_wan", "gen/fix", "gen/clips"):
        p = os.path.join(ROOT, d, sid + ".mp4")
        if os.path.exists(p):
            return p, d == "gen/lipsync_wan"
    return None, False


def clip_len(p):
    h, m, s = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr.split("Duration: ")[1].split(",")[0].split(":")
    return float(h) * 3600 + float(m) * 60 + float(s)


CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def crop_x(clip, t_from, t_to, sid):
    """Left edge of the 9:16 crop, centred on the faces in the used part of the clip."""
    cap = cv2.VideoCapture(clip)
    faces = []
    for f in (0.25, 0.5, 0.75):
        cap.set(cv2.CAP_PROP_POS_MSEC, (t_from + (t_to - t_from) * f) * 1000)
        ok, fr = cap.read()
        if not ok:
            continue
        sx = SW / fr.shape[1]
        g = cv2.cvtColor(cv2.resize(fr, (SW, SH)), cv2.COLOR_BGR2GRAY)
        for (x, y, w, h) in CASCADE.detectMultiScale(g, 1.1, 6, minSize=(90, 90)):
            faces.append((x + w / 2, w * h))
    cap.release()
    if not faces:
        return None
    xs = sorted(x for x, _ in faces)
    if FOCUS.get(sid) == "right":
        cx = xs[-1]
    elif FOCUS.get(sid) == "left":
        cx = xs[0]
    elif xs[-1] - xs[0] < CROP_W * 0.8:
        cx = (xs[0] + xs[-1]) / 2
    else:
        cx = max(faces, key=lambda f: f[1])[0]
    return int(min(max(cx - CROP_W / 2, 0), SW - CROP_W))


def segment(shot, a, b, idx):
    """Part [a, b) (song time) of a shot as a vertical segment."""
    sid, t0, dur = shot["id"], shot["t0"], round(b - a, 3)
    tau0 = a - t0
    clip, synced = clip_for(sid)
    out = os.path.join(TMP, f"{idx:03d}_{sid}.mp4")
    sdur = shot["t1"] - t0
    clen = clip_len(clip)
    speed = min(1.0, clen / sdur)
    off = min(0.05, max(0.0, clen - sdur)) if synced else 0.0 if speed < 1.0 else min(1.0, (clen - sdur) * 0.4)
    seek = max(0.0, off + tau0 * speed)
    base = f"setpts={1 / speed:.4f}*(PTS-STARTPTS),fps={FPS},scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH},eq=contrast=1.06:saturation=1.12,tpad=stop_mode=clone:stop_duration=3"
    cx = CROPX.get(sid) if sid in CROPX else None if sid in FIT else crop_x(clip, seek, seek + dur * speed, sid)
    if cx is None:  # whole frame over a blurred fill
        chain = (f"[0:v]{base},split[a][b];[a]scale={VW}:{VH}:force_original_aspect_ratio=increase,crop={VW}:{VH},gblur=sigma=28,eq=brightness=-0.18[bg];"
                 f"[b]scale={VW}:-2[fg];[bg][fg]overlay=0:(H-h)/2-140,trim=duration={dur},setpts=PTS-STARTPTS[v0]")
    else:
        chain = f"[0:v]{base},crop={CROP_W}:{SH}:{cx}:0,scale={VW}:{VH}:flags=lanczos,trim=duration={dur},setpts=PTS-STARTPTS[v0]"
    inputs, chains, last, n = ["-ss", f"{seek:.3f}", "-i", clip], [chain], "v0", 1
    capdir = os.path.join(TMP, "caps")
    os.makedirs(capdir, exist_ok=True)
    for el in captions.build(shot, capdir):
        ea, eb = el["a"] - tau0, el["b"] - tau0
        if eb <= 0.02:
            continue
        ea = max(0.0, ea)
        eb = min(eb, dur)
        x, y = int(round(el["x"])), int(round(el["y"]))
        motion = {"pop": f"{y}-14*max(0\\,1-(t-{ea})/0.09)", "slam": f"{y}-40*max(0\\,1-(t-{ea})/0.08)",
                  "slide": f"{y}+40*max(0\\,1-(t-{ea})/0.18)"}.get(el.get("anim"), str(y)) if el["a"] >= tau0 else str(y)
        enable = f"between(t,{ea:.3f},{eb:.3f})" + (f"*lt(mod(t-{ea:.3f},0.6),0.36)" if el.get("blink") else "")
        inputs += ["-loop", "1", "-t", f"{dur}", "-i", el["png"]]
        pre = f",fade=t=in:st={ea:.3f}:d=0.14:alpha=1" if el.get("fade") and el["a"] >= tau0 else ""
        chains.append(f"[{n}:v]format=rgba{pre}[c{n}]")
        chains.append(f"[{last}][c{n}]overlay=x={x}:y='{motion}':enable='{enable}'[o{n}]")
        last, n = f"o{n}", n + 1
    if sid in {"S04", "S15", "S56", "S65"} and tau0 < 0.05:
        chains.append(f"color=c=white:s={VW}x{VH}:r={FPS}:d={dur},format=rgba,fade=t=out:st=0:d=0.25:alpha=1[fl]")
        chains.append(f"[{last}][fl]overlay=0:0[ofl]")
        last = "ofl"
    chains.append(f"[{last}]format=yuv420p[out]")
    run([*inputs, "-filter_complex", ";".join(chains), "-map", "[out]", "-t", f"{dur}", "-r", str(FPS),
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", out])
    return out, "fit" if cx is None else f"crop@{cx}"


def main():
    ranges, song_dur = snap_points()
    print("ranges:", [(round(a, 2), round(b, 2)) for a, b in ranges])
    segs, idx = [], 0
    for ri, (a, b) in enumerate(ranges):
        parts = [[shot, max(a, shot["t0"]), min(b, shot["t1"])] for shot in SB if min(b, shot["t1"]) - max(a, shot["t0"]) >= 0.04]
        if len(parts) > 1 and parts[0][2] - parts[0][1] < 0.35:  # fold a sliver at the join into the next shot
            parts[1][1] = parts[0][1]
            parts = parts[1:]
        if len(parts) > 1 and parts[-1][2] - parts[-1][1] < 0.35:
            parts[-2][2] = parts[-1][2]
            parts = parts[:-1]
        for shot, s0, s1 in parts:
            path, mode = segment(shot, s0, s1, idx)
            segs.append(path)
            print(f"{shot['id']} {s0:7.2f}-{s1:7.2f} {mode}", flush=True)
            idx += 1
    # end card
    card = Image.new("RGB", (VW, VH), (0, 0, 0))
    d = ImageDraw.Draw(card)
    f1, f2 = captions.font(captions.BAHN, 190, "Bold Condensed"), captions.font(captions.MONO, 30)
    for i, word in enumerate(("OUT OF", "OFFICE")):
        d.text(((VW - f1.getlength(word)) / 2, 700 + i * 200), word, font=f1, fill=(255, 60, 220))
    s = "AN AUTOMATED MUSIC VIDEO"
    d.text(((VW - f2.getlength(s)) / 2, 1140), s, font=f2, fill=(60, 240, 255))
    card.save(os.path.join(TMP, "zz_card.png"))
    cardmp4 = os.path.join(TMP, "zz_card.mp4")
    run(["-loop", "1", "-t", "2.5", "-i", os.path.join(TMP, "zz_card.png"), "-vf", f"fps={FPS},fade=t=in:st=0:d=0.3,format=yuv420p",
         "-c:v", "libx264", "-crf", "18", cardmp4])
    segs.append(cardmp4)
    lst = os.path.join(TMP, "list.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{p.replace(os.sep, '/')}'\n" for p in segs)
    video = os.path.join(TMP, "video.mp4")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])
    # audio: instrumental stem cut on the bar lines; vocal stem the same, but faded early where a new line would be clipped
    parts, k = [], 0
    args = ["-i", os.path.join(STEMS, "no_vocals.wav"), "-i", os.path.join(STEMS, "vocals.wav")]
    for ri, (a, b) in enumerate(ranges):
        d = b - a
        ve = VOCAL_END.get(ri, b) - a
        parts.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={d - 0.03:.3f}:d=0.03[i{k}]")
        parts.append(f"[1:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={max(0.0, ve - 0.09):.3f}:d=0.08[v{k}]")
        parts.append(f"[i{k}][v{k}]amix=inputs=2:normalize=0[r{k}]")
        k += 1
    parts.append("".join(f"[r{i}]" for i in range(k)) + f"concat=n={k}:v=0:a=1,apad=pad_dur=2.5[aud]")
    audio = os.path.join(TMP, "audio.wav")
    run([*args, "-filter_complex", ";".join(parts), "-map", "[aud]", audio])
    final = os.path.join(ROOT, "..", "OUT_OF_OFFICE_reels.mp4")
    run(["-i", video, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
         "-shortest", "-movflags", "+faststart", final])
    print("wrote", os.path.abspath(final))


if __name__ == "__main__":
    main()
