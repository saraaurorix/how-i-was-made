"""Shared bits for the chaining tools: the storyboard, each shot's WINDOW, and the editor's frame arithmetic.

The editor assumption every tool here relies on: the cut runs at 25 fps and plays every source frame once from the shot's WINDOW
(seconds into the clip). So shot A's last USED source frame is  round(window_A * clip_fps) + nf_A - 1,  with
nf_A = round(t1 * 25) - round(t0 * 25). A chained shot B is windowed at 0.04 s (just under one frame at 24 fps: the editor seeks to the
first frame at or after the window, so 0.042 would skip frame 1).

Inputs, all relative to the project folder the tools are run from:
  --sb      the storyboard, a JSON list of shots. These tools read three fields per shot: id, t0 and t1 (seconds in the cut).
  --clips   the clips folder, <id>.mp4 per shot.
  --window  a JSON file of windows: for each shot, the second of its clip at which the cut starts playing it. Either a flat map,
            {"V02": 0.15, "H05": 0.04}, or any JSON object that holds that map under a "WINDOW" key, {"WINDOW": {...}, ...}.
            Write it by hand or export it from your own editor. A shot that is not listed (or no file at all) uses
            --default-window, 0.15 s. A take named "V02_b" falls back to the window of "V02".
"""
import json, os, re, shutil, subprocess
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
NICE = ["nice", "-n", "19"] if shutil.which("nice") else []  # low priority for the heavy ffmpeg runs; there is no nice on Windows
EDIT_FPS = 25
CHAIN_WINDOW = 0.04


def add_common(ap):
    ap.add_argument("--sb", default="storyboard.json", help="the storyboard: id, t0, t1 per shot")
    ap.add_argument("--clips", default="gen/clips", help="the clips folder, <id>.mp4")
    ap.add_argument("--window", default="", help="JSON: {id: seconds} or a file with a WINDOW key")
    ap.add_argument("--default-window", type=float, default=0.15)


def load(a):
    sb = {s["id"]: s for s in json.load(open(a.sb))}
    win = {}
    if a.window and os.path.exists(a.window):
        w = json.load(open(a.window))
        win = w.get("WINDOW", w) if isinstance(w, dict) else {}
    return sb, win


def window(win, sid, default):
    return win.get(sid, win.get(sid.split("_")[0], default))


def probe(path):
    s = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    w, h = map(int, re.search(r", (\d{3,4})x(\d{3,4})", s).groups())
    fps = float(re.search(r"([\d.]+) fps", s).group(1))
    return w, h, fps


def nframes(s):
    return round(s["t1"] * EDIT_FPS) - round(s["t0"] * EDIT_FPS)


def last_used_index(s, w0, clip_fps):
    return round(w0 * clip_fps) + nframes(s) - 1
