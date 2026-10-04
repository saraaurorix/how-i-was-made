"""Re-encode the Out of Office master with the text-fixed frames swapped in (2026-10-01).

edit.py renders with libx264 on the CPU (Windows era) and its captions use Windows fonts, so the master is not re-rendered:
it is decoded once, the patched frames from gen/textfix/pNNNNN.png replace their master frames (S13 1302-1321, S43
3948-4049), and the whole picture goes through one VideoToolbox encode at nice 19. The audio is copied untouched.
Usage: python tools/textfix_render.py [in.mp4] [out.mp4] [patch_dir=gen/textfix]  (also used for the reels: gen/reelfix)
"""
import glob
import os
import re
import subprocess
import sys

import cv2
import imageio_ffmpeg
import numpy as np

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
W, H, FPS = 1920, 1080, 30


def low():
    try:
        os.setpriority(os.PRIO_PROCESS, 0, 19)
    except PermissionError:  # already started under nice 19
        pass


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "..", "OUT_OF_OFFICE.mp4")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "..", "OUT_OF_OFFICE_textfix.mp4")
    pdir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "gen", "textfix")
    low()
    global W, H
    W, H = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0", src],
                                   capture_output=True, text=True).stdout.strip().split(","))
    patched = {int(re.search(r"p(\d+)\.png", p).group(1)): p for p in glob.glob(os.path.join(pdir, "p*.png"))}
    dec = subprocess.Popen([FF, "-v", "error", "-hwaccel", "videotoolbox", "-i", src, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           stdout=subprocess.PIPE, preexec_fn=low)
    tmp = out + ".video.mp4"
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "h264_videotoolbox", "-allow_sw", "0", "-profile:v", "high", "-g", str(FPS * 2), "-q:v", "78",
                            "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE, preexec_fn=low)
    n, used, size = 0, 0, W * H * 3
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        if n in patched:
            frame = cv2.imread(patched[n])
            buf, used = frame.tobytes(), used + 1
        enc.stdin.write(buf)
        n += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    subprocess.run([FF, "-v", "error", "-y", "-i", tmp, "-i", src, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", out], check=True)
    os.remove(tmp)
    print(f"{n} frames, {used} patched of {len(patched)}, wrote {out}")


if __name__ == "__main__":
    main()
