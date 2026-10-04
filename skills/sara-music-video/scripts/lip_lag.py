"""Lip-sync lag as the viewer sees it: mouth opening in each rendered build/<id>.mp4 vs the vocal stem at the same song time.

lag > 0 means the mouth trails the voice (the noticeable direction: audio ahead of the lips shows from about 45 ms).
Uses lipscore.py (MediaPipe) for the mouth and the vocal envelope, searches -6..+6 frames and refines the
peak with a parabola, so the estimate is finer than a frame. Scores under 0.3 correlation are noise: judge those by eye.
On one cut it found the mouths trailing by a median +43 ms: the fix is a per-shot nudge of a frame or two in the edit.
build/<id>.mp4 is the edit's rendered segment for each shot.
Usage: python tools/lip_lag.py [N004,N005]   (default: every lip shot)
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lipscore  # noqa: E402  (the one next to this file)

import glob as _glob  # noqa: E402
_R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# the chosen take's Demucs vocal stem, found automatically (prefer sep_wav/, made from the lossless WAV)
VOCALS = next(iter(sorted(_glob.glob(os.path.join(_R, "sep_wav/htdemucs/*/vocals.wav"))) +
                   sorted(_glob.glob(os.path.join(_R, "sep/htdemucs/*/vocals.wav")))), "")
if not VOCALS:
    sys.exit("no vocal stem found: expected sep_wav/htdemucs/<take>/vocals.wav or sep/htdemucs/<take>/vocals.wav in the single's folder "
             "(make it with Demucs: python -m demucs --two-stems vocals -o sep SONG.mp3)")


def low_priority():
    """Drop to nice 19 unless already there or lower (a background shell job can start above 19, where os.nice raises)."""
    if os.getpriority(os.PRIO_PROCESS, 0) < 19:
        os.setpriority(os.PRIO_PROCESS, 0, 19)


def lag(sid, shot, tmp):
    """(correlation at the best lag, correlation at 0, lag in ms) for one rendered segment."""
    wav = os.path.join(tmp, sid + ".wav")
    subprocess.run([lipscore.FF, "-v", "error", "-y", "-ss", f"{shot['t0']:.4f}", "-t", f"{shot['t1'] - shot['t0']:.4f}", "-i", VOCALS, wav],
                   check=True)
    ap, fps = lipscore.apertures(os.path.join(ROOT, "build", sid + ".mp4"))
    ap = np.where(np.isnan(ap), np.nanmean(ap), ap)
    env = lipscore.envelope(wav, fps, len(ap))
    cs = {}
    for k in range(-6, 7):
        a, e = (ap[k:], env[:len(env) - k]) if k >= 0 else (ap[:k], env[-k:])
        cs[k] = float(np.corrcoef(a, e)[0, 1]) if len(a) > 10 and a.std() > 0 and e.std() > 0 else -1.0
    best = max(cs, key=cs.get)
    sub = float(best)
    if -6 < best < 6:
        y0, y1, y2 = cs[best - 1], cs[best], cs[best + 1]
        den = y0 - 2 * y1 + y2
        sub = best + (0.5 * (y0 - y2) / den if den else 0.0)
    return cs[best], cs[0], sub * 1000 / fps


def main():
    low_priority()  # MediaPipe runs on the CPU
    sb = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "storyboard.json")))}
    ids = sys.argv[1].split(",") if len(sys.argv) > 1 else [k for k in sb if sb[k]["type"] == "lip"]
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for sid in ids:
            c, c0, ms = lag(sid, sb[sid], tmp)
            rows.append((sid, sb[sid]["t1"] - sb[sid]["t0"], c, c0, ms))
            print(f"{sid}  corr at best {c:+.2f} (at 0: {c0:+.2f})  lag {ms:+5.0f} ms", flush=True)
    good = [r for r in rows if r[2] >= 0.3]
    if good:
        w, lags = np.array([r[2] * r[1] for r in good]), np.array([r[4] for r in good])
        print(f"usable (corr >= 0.3): {len(good)}/{len(rows)}; weighted mean {np.sum(w * lags) / np.sum(w):+.0f} ms, median {np.median(lags):+.0f} ms, "
              f"middle half {np.percentile(lags, 25):+.0f}..{np.percentile(lags, 75):+.0f} ms; mean corr at 0 over all: {np.mean([r[3] for r in rows]):+.3f}")


if __name__ == "__main__":
    main()
