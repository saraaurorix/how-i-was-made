"""Masked driving audio for Sara's lip-sync shots, gated on the vocal stem's own energy (Whisper word times were ~0.3 s off
on one song). The vocal is kept only where it's actually sounding inside the shot window [t0, t1], with 60 ms pre-roll and
100 ms release; everything else (the next singer, FX, bleed) is silenced. The slice starts exactly on the shot's first frame
(round(t0*30)/30) and lasts n = max(3, ceil(dur + 0.1)) seconds, the Wan 2.7 duration it will be generated at.
Writes lipsync/<ID>_m.wav and lip_jobs.json (id, duration, slice). Usage: python tools/lip_slices.py [ID,ID]
"""
import json
import math
import os
import sys
import wave

import numpy as np
import soundfile as sf

import glob as _glob  # noqa: E402
_R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# the chosen take's Demucs vocal stem, found automatically (prefer sep_wav/, made from the lossless WAV)
VOCALS = next(iter(sorted(_glob.glob(os.path.join(_R, "sep_wav/htdemucs/*/vocals.wav"))) +
                   sorted(_glob.glob(os.path.join(_R, "sep/htdemucs/*/vocals.wav")))), "")
if not VOCALS:
    sys.exit("no vocal stem found: expected sep_wav/htdemucs/<take>/vocals.wav or sep/htdemucs/<take>/vocals.wav in the single's folder "
             "(make it with Demucs: python -m demucs --two-stems vocals -o sep SONG.mp3)")
FPS = 30
S = [s for s in json.load(open("storyboard.json", encoding="utf-8")) if s["type"] == "lip"]
only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
y, sr = sf.read(VOCALS)
y = y.mean(1) if y.ndim > 1 else y
os.makedirs("lipsync", exist_ok=True)
jobs = []
for s in S:
    sid = s["id"]
    t0 = round(s["t0"] * FPS) / FPS
    dur = s["t1"] - s["t0"]
    n = max(3, math.ceil(dur + 0.1))
    a = y[int(t0 * sr):int((t0 + n) * sr)].copy()
    a = np.pad(a, (0, max(0, int(n * sr) - len(a))))
    hop = int(0.01 * sr)
    rms = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a), hop)])
    inside = np.arange(len(rms)) * 0.01 < (s["t1"] - t0 + 0.05)
    thr = 0.12 * rms[inside].max()
    on = (rms > thr) & inside
    gate = np.zeros_like(rms)
    for i in np.flatnonzero(on):  # 60 ms pre-roll, 100 ms release
        gate[max(0, i - 6):i + 11] = 1.0
    gate[~inside] = 0.0
    k = np.ones(4) / 4  # 40 ms fades
    gate = np.convolve(gate, k, mode="same")
    m = np.repeat(gate, hop)[:len(a)]
    out = f"lipsync/{sid}_m.wav"
    with wave.open(out, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes((np.clip(a * m, -1, 1) * 32767).astype("<i2").tobytes())
    jobs.append({"id": sid, "duration": n, "slice": out, "t0": t0, "dur": round(dur, 2)})
    print(f"{sid} {dur:.2f}s -> {n}s slice, voiced {100 * on.mean():.0f}%")
if not only:
    json.dump(jobs, open("lip_jobs.json", "w"), indent=1)
    print("total seconds", sum(j["duration"] for j in jobs))
