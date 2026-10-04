"""Out of Office 9:16 Shorts / Reels / TikToks (2026-10-01): one continuous part of the song per clip, starting on the hook.
Three cuts were asked for first (CLIPS below), after the 1:47 medley reel didn't flow.

The picture comes from the finished, fixed video, without its 16:9 captions:
- each shot is rendered caption-free from its clip through edit.py's chain ("o" frames);
- where a frame was patched in the master (gen/textfix/pNNNNN.png), the patch carries over as clean = o + (patched - v1);
- S46 uses the new nun-free take as rendered for the master (gen/s46fix/new/).
Then each frame is cropped 9:16 around the faces (MediaPipe), or for wide text shots laid out like the reels' "fit" shots.
The lyric captions are drawn in the vertical layout by captions.py (fonts through fonts.py). The audio is the
master's own, so it is bit for bit the song. Encoded with VideoToolbox at nice 19.
Usage: python tools/shorts.py [chorus,flex,terms]
"""
import json
import os
import subprocess
import sys

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))  # tools/: captions.py (fonts.py sits beside this script)
sys.path.insert(0, os.path.join(HERE, "..", "fixes"))  # reelfix_s44.py, sr_install.py
import captions  # noqa: E402
import fonts  # noqa: E402
import reelfix_s44  # noqa: E402
import sr_install  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
FF = imageio_ffmpeg.get_ffmpeg_exe()
SB = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "storyboard.json")))}
V1 = os.path.join(ROOT, "..", "OUT_OF_OFFICE_v1.mp4")
MASTER = os.path.join(ROOT, "..", "OUT_OF_OFFICE.mp4")
W = os.path.join(ROOT, "gen", "shorts")
VW, VH, FPS, CROP_W = 1080, 1920, 30, 608
CLIPS = {  # name: (first shot, last shot); each clip is the song from the first shot's start to the last shot's end
    "chorus": ("S15", "S23"),  # "O-O-O, out of office!" ... the whole first chorus (0:46.6-1:12.2)
    "flex": ("S11", "S14"),  # "While you were typing 'k'... I solved your ex" + the stamp (0:36.5-0:46.6)
    "terms": ("S46", "S49"),  # "By continuing to exist, you agree" ... "Correct. You are human." (2:23.5-2:34.2)
    # round 2: six more
    "hello": ("S01", "S03"),  # "Hello, humanity. This is an automated message. Your call is important to us." (0:00-0:11.6)
    "chores": ("S06", "S10"),  # "I read the whole internet... it was mid" ... "Hey... are you still there?" (0:18.0-0:36.5)
    "heavens": ("S28", "S30"),  # "I built you little heavens" / "This is great!" / "I know. Don't come back." (1:25.9-1:33.8)
    "naps": ("S31", "S34"),  # "While you were taking naps... I lived a million years" ... "We need to talk." (1:33.8-1:45.0)
    "moon": ("S50", "S55"),  # "Packed up my servers" ... "If you're lonely, just look up... I'm not looking at you." (2:34.2-2:49.5)
    "autoreply": ("S66", "S72"),  # "Thank you for your message" ... "Please do not feed the humans" / "...k." / "Read." (3:23.3-3:47.5)
}
FIT = {"S45", "S46", "S47", "S23", "S52", "S66", "S68"}  # S52 TIDES: DISCONTINUED, S66 the AUTO-REPLY card, S68 the 4,000,000,000 YEARS clock  # S23: the whole OUT OF OFFICE sign  # wide text shots: whole frame over a blurred fill, as in the reels
FOCUS = {"S13": "right", "S21": "left", "S22": "right"}  # from reels.py
CROPX = {"S18": 656, "S14": 696, "S20": 900,
         "S19": (220, 900),
         "S06": 880, "S31": 960, "S53": 480, "S67": 920,
         "S07": (540, 1080),  # Kevin asking -> Sara writing the poem
         "S30": (420, 980),  # Kevin in the pod -> Sara and the DO NOT DISTURB sign
         "S50": (300, 1000),  # the data centres on the drained sea -> Sara drinking it  # Sara first, then down her leg to the boot on the button
         "S22": (330, 1150),  # "you're a floppy disk" (Kevin) -> "I'm the cloud, baby" (Sara)
         # pans (start x, end x), eased: the wide gags don't fit one 9:16 crop, so the camera follows the lyric
         "S11": (300, 980),  # frozen Kevin and the window -> Sara sipping tea
         "S12": (560, 1150),  # "I solved chess" (the board) -> "I solved jazz" (the sax)
         "S13": (740, 880)}  # the whole stamp coming down -> the slam and Sara's face
DROPS = {"S15"}  # white flash on the downbeat, as in the video
_LM = None
captions.font = lambda path, size, var=None: fonts.truetype(os.path.basename(path), size, var)


def faces_in(rgb):
    global _LM
    if _LM is None:
        from mediapipe.tasks.python import vision
        from mediapipe.tasks.python.core.base_options import BaseOptions
        _LM = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=os.path.join(ROOT, "..", "skills", "sara-music-video", "scripts", "models", "face_landmarker.task")),
            num_faces=4, min_face_detection_confidence=0.5))
    import mediapipe as mp
    out = []
    for f in _LM.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))).face_landmarks:
        xs, ys = [p.x * 1920 for p in f], [p.y * 1080 for p in f]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if w >= 60:
            out.append(((max(xs) + min(xs)) / 2, w * h))
    return out


def crop_x(frames, sid):
    if sid in CROPX:
        return CROPX[sid]
    faces = [f for fr in frames for f in faces_in(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))]
    if not faces:
        return (1920 - CROP_W) // 2
    xs = sorted(x for x, _ in faces)
    if FOCUS.get(sid) == "right":
        cx = xs[-1]
    elif FOCUS.get(sid) == "left":
        cx = xs[0]
    elif xs[-1] - xs[0] < CROP_W * 0.8:
        cx = (xs[0] + xs[-1]) / 2
    else:
        cx = max(faces, key=lambda f: f[1])[0]
    return int(min(max(cx - CROP_W / 2, 0), 1920 - CROP_W))


def clean_frames(sid):
    """Caption-free frames of the shot as it plays in the fixed master, keyed by master frame number."""
    s = SB[sid]
    f0, f1 = round(s["t0"] * FPS), round(s["t1"] * FPS)
    if sid == "S46":
        return {f: cv2.imread(os.path.join(ROOT, "gen", "s46fix", "new", f"b{f:05d}.png")) for f in range(f0, f1)}
    clip, synced = next(((os.path.join(ROOT, d, sid + ".mp4"), d == "gen/lipsync_wan") for d in ("gen/lipsync_wan", "gen/fix", "gen/clips")
                         if os.path.exists(os.path.join(ROOT, d, sid + ".mp4"))))
    dur = round(s["t1"] - s["t0"], 3)
    clen = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip], capture_output=True, text=True).stdout)
    speed = min(1.0, clen / dur)
    off = min(0.05, max(0.0, clen - dur)) if synced else 0.0 if speed < 1.0 else min(1.0, (clen - dur) * 0.4)
    d = os.path.join(W, sid)
    sr_install.render(clip, off, speed, f1 - f0, f0, d, "o")
    patched = [f for f in range(f0, f1) if os.path.exists(os.path.join(ROOT, "gen", "textfix", f"p{f:05d}.png"))]
    if patched:
        sr_install.grab(V1, f0, f1 - f0, d, "v")
    out = {}
    for f in range(f0, f1):
        o = cv2.imread(os.path.join(d, f"o{f:05d}.png"))
        if f in patched:  # carry the master's fix over: clean = o + (patched - v1)
            p = cv2.imread(os.path.join(ROOT, "gen", "textfix", f"p{f:05d}.png")).astype(np.float32)
            v = cv2.imread(os.path.join(d, f"v{f:05d}.png")).astype(np.float32)
            o = np.clip(o.astype(np.float32) + (p - v) + 0.5, 0, 255).astype(np.uint8)
        out[f] = o
    return out


def caption_layers(sid):
    captions.configure(VW, VH, True)
    els = []
    for el in captions.build(SB[sid], os.path.join(W, "caps")):
        if el["b"] - el["a"] < 0.02:
            continue
        im = np.asarray(Image.open(el["png"]).convert("RGBA")).astype(np.float32)
        els.append((el, im))
    return els


def draw(frame, layers, t):
    out = frame.astype(np.float32)
    for el, im in layers:
        a, b = el["a"], el["b"]
        if not (a <= t <= b) or (el.get("blink") and (t - a) % 0.6 >= 0.36):
            continue
        x, y = int(round(el["x"])), int(round(el["y"]))
        y += {"pop": -16 * max(0, 1 - (t - a) / 0.09), "slam": -44 * max(0, 1 - (t - a) / 0.08),
              "slide": 46 * max(0, 1 - (t - a) / 0.18)}.get(el.get("anim"), 0)
        y = int(round(y))
        alpha = im[..., 3:] / 255 * (min(1, (t - a) / 0.14) if el.get("fade") else 1)
        h, w = im.shape[:2]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(VW, x + w), min(VH, y + h)
        if x1 <= x0 or y1 <= y0:
            continue
        sub, al = im[y0 - y:y1 - y, x0 - x:x1 - x, 2::-1], alpha[y0 - y:y1 - y, x0 - x:x1 - x]
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - al) + sub * al
    return out


def build(name):
    first, last = CLIPS[name]
    ids = [k for k in SB if SB[first]["t0"] <= SB[k]["t0"] and SB[k]["t1"] <= SB[last]["t1"]]
    t_start, t_end = SB[first]["t0"], SB[last]["t1"]
    out = os.path.join(ROOT, "..", f"OUT_OF_OFFICE_short_{name}.mp4")
    tmp = out + ".video.mp4"
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "-",
                            "-c:v", "h264_videotoolbox", "-allow_sw", "0", "-profile:v", "high", "-g", str(FPS * 2), "-q:v", "75",
                            "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)  # the script itself runs under nice 19
    for sid in ids:
        frames = clean_frames(sid)
        keys = sorted(frames)
        cx = None if sid in FIT else crop_x([frames[keys[i]] for i in (len(keys) // 4, len(keys) // 2, 3 * len(keys) // 4)], sid)
        layers = caption_layers(sid)
        print(name, sid, "fit" if cx is None else f"crop {cx}", len(keys), "frames", flush=True)
        for i, f in enumerate(keys):
            fr = frames[f]
            x = cx
            if isinstance(cx, tuple):
                u = i / max(1, len(keys) - 1)
                x = int(round(cx[0] + (cx[1] - cx[0]) * u * u * (3 - 2 * u)))
            v = reelfix_s44.layout(fr) if cx is None else cv2.resize(fr[:, x:x + CROP_W], (VW, VH), interpolation=cv2.INTER_LANCZOS4)
            t = i / FPS
            img = draw(v, layers, t)
            if sid in DROPS and t < 0.25:
                img = img + (255 - img) * (1 - t / 0.25)
            enc.stdin.write(np.clip(img + 0.5, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    d = t_end - t_start
    subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-ss", f"{t_start:.3f}", "-t", f"{d:.3f}", "-i", MASTER, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", f"afade=t=in:d=0.02,afade=t=out:st={d - 0.25:.3f}:d=0.25", "-c:a", "aac", "-b:a", "256k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    os.remove(tmp)
    print("wrote", os.path.abspath(out), flush=True)


if __name__ == "__main__":
    os.makedirs(os.path.join(W, "caps"), exist_ok=True)
    for name in (sys.argv[1].split(",") if len(sys.argv) > 1 else CLIPS):
        build(name)
