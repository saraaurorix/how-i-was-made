"""Casting check, step 1: who sings each lyric line?

Per timed line (lines_timed.json from align_lines.py), on the Demucs vocal stem:
  * TIMBRE (primary): MFCC nearest-centroid, Sara (S) vs the second voice (B). References are lines you are certain
    of: a vocal stem with both voices (--ref-vocals) and its timed lines marked "v": "S" or "B" (--ref-lines), best
    from an earlier song with the same two voices, plus a stretch of THIS song you are sure Sara sings (--sara 46-74).
    It agreed with the director's ear on 35 of 40 lines of one song.
  * PITCH (a hint only): pyin median and the share of frames under 150 Hz. It misled on 14/36 lines: the second voice
    raps in a female pitch range, and Sara's pitch-shifted backing copies sit an octave down (the "87 Hz" readings).
Writes casting.json (adds f0, low150, pitch, mfcc, margin per line) and prints a table with CHECK flags.
Then group the flagged lines into passages and run casting_clip.py for a listener. The ear decides.

Usage (from the single's folder):
  python tools/casting_scan.py --vocals sep/htdemucs/<take>/vocals.wav --sara 46-74 \
      --ref-vocals <ref song>/vocals.wav --ref-lines <ref song>/lines_timed.json
Options: --lines lines_timed.json  --out casting.json
"""
import argparse
import json

import librosa
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--vocals", required=True)
ap.add_argument("--lines", default="lines_timed.json")
ap.add_argument("--sara", default=None, help="t0-t1 of a stretch in THIS song that is certainly Sara")
ap.add_argument("--ref-vocals", required=True, help="a vocal stem in which both voices sing lines you are certain of")
ap.add_argument("--ref-lines", required=True, help="that stem's timed lines (t0, t1, v = S or B)")
ap.add_argument("--out", default="casting.json")
a = ap.parse_args()

SR = 22050
ref = librosa.load(a.ref_vocals, sr=SR)[0]
song = librosa.load(a.vocals, sr=SR)[0]


def feat(y, t0, t1):
    seg = y[int(t0 * SR):int(t1 * SR)]
    m = librosa.feature.mfcc(y=seg, sr=SR, n_mfcc=20)[1:]
    rms = librosa.feature.rms(y=seg)[0][:m.shape[1]]
    keep = rms > np.percentile(rms, 40)
    return m[:, keep].mean(axis=1) if keep.sum() > 5 else None


refs = {"S": [], "B": []}
for l in json.load(open(a.ref_lines)):
    if l.get("t0") is None or l["t1"] - l["t0"] < 1.2 or l.get("v") not in refs:
        continue
    f = feat(ref, l["t0"], l["t1"])
    if f is not None:
        refs[l["v"]].append(f)
if a.sara:
    s0, s1 = map(float, a.sara.split("-"))
    refs["S"] += [f for f in (feat(song, t, t + 2) for t in np.arange(s0, s1, 2)) if f is not None]
allf = np.array([f for v in refs.values() for f in v])
mu, sd = allf.mean(0), allf.std(0) + 1e-6
cent = {k: np.mean([(f - mu) / sd for f in v], axis=0) for k, v in refs.items()}
print("references:", {k: len(v) for k, v in refs.items()})

out = []
for l in json.load(open(a.lines)):
    t0, t1 = l["t0"], max(l["t1"], l["t0"] + 0.8)
    f = feat(song, t0, t1)
    seg = librosa.resample(song[int(t0 * SR):int(t1 * SR)], orig_sr=SR, target_sr=16000)
    f0, vf, _ = librosa.pyin(seg, fmin=65, fmax=700, sr=16000, frame_length=1024)
    v = f0[vf]
    med = float(np.median(v)) if len(v) > 5 else None
    low = float((v < 150).mean()) if len(v) > 5 else None
    call, margin = None, 0.0
    if f is not None:
        f = (f - mu) / sd
        d = {k: float(np.linalg.norm(f - c)) for k, c in cent.items()}
        call, margin = min(d, key=d.get), abs(d["S"] - d["B"])
    pitch = None if med is None else ("B" if low > 0.6 else "S" if low < 0.3 else "?")
    l.update(f0=None if med is None else round(med), low150=None if low is None else round(low, 2),
             pitch=pitch, mfcc=call, margin=round(margin, 2))
    out.append(l)
    flag = "" if call == l.get("v") else "  <-- CHECK (timbre disagrees with the sheet)"
    if not flag and pitch not in (None, "?", l.get("v")):
        flag = "  <-- check (pitch only; often an octave copy)"
    print(f"{l['n']:3d} {l['t0']:6.1f} {l.get('v')}  timbre {call} ({margin:.2f})  f0 {str(l['f0']):>4} {pitch}  {l['text'][:44]}{flag}")
json.dump(out, open(a.out, "w"), indent=1)
print("wrote", a.out)
