"""Prepare lip-sync correction inputs: the exact shot window of the lip-sync clip (no captions) + the exact vocal slice.

Usage: python tools/v2v_prep.py C08,C24 ...   -> gen/v2v_in/<id>.mp4, lipsync/<id>_exact.wav
"""
import json
import os
import subprocess
import sys

import imageio_ffmpeg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import venc  # noqa: E402

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
import glob as _glob  # noqa: E402
_R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# the chosen take's Demucs vocal stem, found automatically (prefer sep_wav/, made from the lossless WAV)
VOCALS = next(iter(sorted(_glob.glob(os.path.join(_R, "sep_wav/htdemucs/*/vocals.wav"))) +
                   sorted(_glob.glob(os.path.join(_R, "sep/htdemucs/*/vocals.wav")))), "")
FPS = 30


def prep(shot):
    sid = shot["id"]
    nf = round(shot["t1"] * FPS) - round(shot["t0"] * FPS)
    dur = nf / FPS
    src = os.path.join(ROOT, "gen/lipsync", sid + ".mp4")
    out = os.path.join(ROOT, "gen/v2v_in", sid + ".mp4")
    wav = os.path.join(ROOT, "lipsync", sid + "_exact.wav")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    os.makedirs(os.path.dirname(wav), exist_ok=True)
    subprocess.run([FF, "-v", "error", "-y", "-i", src, "-vf", f"fps={FPS},scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
                    f"tpad=stop_mode=clone:stop_duration=1", "-frames:v", str(nf), "-an", *venc.h264(80), "-pix_fmt", "yuv420p", out], check=True)  # high quality: fal re-encodes it
    subprocess.run([FF, "-v", "error", "-y", "-ss", f"{round(shot['t0'] * FPS) / FPS:.4f}", "-t", f"{dur:.4f}", "-i", VOCALS,
                    "-ac", "1", "-ar", "44100", wav], check=True)
    return out, wav


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    if not VOCALS:
        sys.exit("no vocal stem found: expected sep_wav/htdemucs/<take>/vocals.wav or sep/htdemucs/<take>/vocals.wav in the single's folder "
                 "(make it with Demucs: python -m demucs --two-stems vocals -o sep SONG.mp3)")
    S = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "storyboard.json")))}
    for sid in sys.argv[1].split(","):
        print(sid, *prep(S[sid]))
