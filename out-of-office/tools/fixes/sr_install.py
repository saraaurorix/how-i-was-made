"""AI-upscale the three 720p shots in Out of Office (2026-10-01): S09, S24 and S26 came from 720p fix clips; everything
else is 1080p already. The played window of each is upscaled with Apple super-resolution (a small command-line tool around Apple's VideoToolbox super-resolution, not in this repo, into
gen/sr/fix/). Then each shot is rendered through edit.py's chain twice, from the old 720p clip and from the upscaled one.
The caption is carried over as a difference: in the caption area, new + (master - old). Text, shadow and fade come across
exactly as they were, and only the picture underneath gets sharper.
Writes gen/textfix/pNNNNN.png for the master; with --reels, it also does S24 in the 9:16 reels (gen/reelfix/).
Usage: python tools/sr_install.py [--reels]
"""
import json
import os
import subprocess
import sys

import cv2
import imageio_ffmpeg
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
FF = imageio_ffmpeg.get_ffmpeg_exe()
G = os.path.join(ROOT, "gen", "srwork")
MASTER = os.path.join(ROOT, "..", "OUT_OF_OFFICE_textfix6.mp4")
SR_START = {"S09": 0.0, "S24": 0.09, "S26": 0.0}  # where each srscale window starts in its clip
CHAIN = "fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,eq=contrast=1.06:saturation=1.12"


def render(src, seek, speed, n, f0, out_dir, tag):
    os.makedirs(out_dir, exist_ok=True)
    subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vf",
                    f"trim=start={seek:.4f},setpts={1 / speed:.4f}*(PTS-STARTPTS),{CHAIN},tpad=stop_mode=clone:stop_duration=1,trim=end_frame={n},setpts=PTS-STARTPTS",
                    "-fps_mode", "passthrough", "-frames:v", str(n), "-start_number", str(f0), os.path.join(out_dir, tag + "%05d.png")], check=True)


def grab(video, f0, n, out_dir, tag):
    os.makedirs(out_dir, exist_ok=True)
    subprocess.run([FF, "-v", "error", "-y", "-hwaccel", "videotoolbox", "-i", video, "-vf", f"select='between(n\\,{f0}\\,{f0 + n - 1})'",
                    "-vsync", "0", "-start_number", str(f0), os.path.join(out_dir, tag + "%05d.png")], check=True)


def transfer(new, old, mst):
    delta = mst.astype(np.float32) - old.astype(np.float32)
    cap = (np.abs(delta).sum(2) > 24).astype(np.uint8)
    cap = cv2.morphologyEx(cap, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # drop codec noise
    a = cv2.GaussianBlur(cv2.dilate(cap, np.ones((31, 31), np.uint8)).astype(np.float32), (0, 0), 6)[..., None]
    return np.clip(new.astype(np.float32) + delta * a + 0.5, 0, 255).astype(np.uint8)


def main():
    shots = json.load(open(os.path.join(ROOT, "gen", "sr_shots.json")))
    for sid, s in shots.items():
        d = os.path.join(G, sid)
        render(os.path.join(ROOT, "gen", "fix", sid + ".mp4"), s["off"], s["speed"], s["n"], s["f0"], d, "o")
        render(os.path.join(ROOT, "gen", "sr", "fix", sid + ".mp4"), s["off"] - SR_START[sid], s["speed"], s["n"], s["f0"], d, "s")
        grab(MASTER, s["f0"], s["n"], d, "m")
        err = []
        for f in range(s["f0"], s["f0"] + s["n"]):
            o, nw, m = (cv2.imread(os.path.join(d, f"{t}{f:05d}.png")) for t in "osm")
            err.append(np.abs(o[:700].astype(float) - m[:700]).mean())
            cv2.imwrite(os.path.join(ROOT, "gen", "textfix", f"p{f:05d}.png"), transfer(nw, o, m))
        print(sid, s["n"], "frames; old render vs master above the captions: %.2f (alignment check)" % np.mean(err))


REEL24 = dict(r0=1499, r1=1600, shift=680, cx=587)  # reels frame k shows S24's master frame k+680, cropped 608 wide at x=587 (matched)


def reels():
    s = json.load(open(os.path.join(ROOT, "gen", "sr_shots.json")))["S24"]
    d, rd = os.path.join(G, "S24"), os.path.join(ROOT, "gen", "reelfix24")
    last = s["f0"] + s["n"] - 1  # the reels pad the shot by cloning its last frame
    for k in range(REEL24["r0"], REEL24["r1"] + 1):
        f = min(k + REEL24["shift"], last)
        crop = lambda im: cv2.resize(im[:, REEL24["cx"]:REEL24["cx"] + 608], (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        o, nw = crop(cv2.imread(os.path.join(d, f"o{f:05d}.png"))), crop(cv2.imread(os.path.join(d, f"s{f:05d}.png")))
        r = cv2.imread(os.path.join(rd, f"r{k:05d}.png"))
        cv2.imwrite(os.path.join(ROOT, "gen", "reelfix", f"p{k:05d}.png"), transfer(nw, o, r))
    print("reels S24 done")


if __name__ == "__main__":
    reels() if "--reels" in sys.argv else main()
