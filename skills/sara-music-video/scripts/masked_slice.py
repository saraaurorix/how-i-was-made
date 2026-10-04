"""Word-masked driving audio for lip-sync: keep the vocal only inside Whisper word spans (padded), silence everything else
(applause, crowd, FX and choir bleed in the Demucs stem), so the mouth moves on words and closes between them.
Usage: python tools/masked_slice.py ID[,ID]   -> lipsync/<ID>_m.wav (run from the single's folder)"""
import os
import json
import subprocess
import sys
import wave

import imageio_ffmpeg
import numpy as np

FF = imageio_ffmpeg.get_ffmpeg_exe()
import glob
import glob as _glob  # noqa: E402
_R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# the chosen take's Demucs vocal stem, found automatically (prefer sep_wav/, made from the lossless WAV)
VOCALS = next(iter(sorted(_glob.glob(os.path.join(_R, "sep_wav/htdemucs/*/vocals.wav"))) +
                   sorted(_glob.glob(os.path.join(_R, "sep/htdemucs/*/vocals.wav")))), "")
FPS, SR = 30, 44100
if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    sys.exit(__doc__)
if not VOCALS:
    sys.exit("no vocal stem found: expected sep_wav/htdemucs/<take>/vocals.wav or sep/htdemucs/<take>/vocals.wav in the single's folder "
             "(make it with Demucs: python -m demucs --two-stems vocals -o sep SONG.mp3)")
# words.json with the transcribe_gaps.py recoveries merged in, when there is one
W = [w for s in json.load(open("words_merged.json" if os.path.exists("words_merged.json") else "words.json")) for w in s["words"]]
S = {s["id"]: s for s in json.load(open("storyboard.json", encoding="utf-8"))}


def make(sid, suffix="_m", pad_pre=0.06, pad_post=0.10, fade=0.04):
    s = S[sid]
    t0 = round(s["t0"] * FPS) / FPS
    length = max(3.0, s["t1"] - s["t0"] + 0.15)
    p = subprocess.run([FF, "-v", "error", "-ss", f"{t0:.4f}", "-t", f"{length:.3f}", "-i", VOCALS, "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.float32).copy()
    a = np.pad(a, (0, max(0, int(length * SR) - len(a))))
    t = np.arange(len(a)) / SR + t0
    m = np.zeros_like(a)
    for w in W:
        if w["e"] < s["t0"] - 0.2 or w["s"] > s["t1"]:
            continue  # only words sung inside this shot drive the mouth
        a0, a1 = w["s"] - pad_pre, w["e"] + pad_post
        m = np.maximum(m, np.clip(np.minimum((t - a0) / fade + 1, (a1 - t) / fade + 1), 0, 1))
    out = f"lipsync/{sid}{suffix}.wav"
    os.makedirs("lipsync", exist_ok=True)
    with wave.open(out, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(a * m, -1, 1) * 32767).astype("<i2").tobytes())
    return out


if __name__ == "__main__":
    for sid in sys.argv[1].split(","):
        print(sid, make(sid))
