"""Who sings each line? (coarse first pass: confirm every flagged line by ear) Nearest-reference voice ID on the Demucs vocal stem (MFCC timbre; pitch is unreliable on
vocoder vocals). Run BEFORE casting shots: a "Sara" line can turn out to be the male voice.

Edit REFS to a few lines you are sure of per character (seconds), then:
    python tools/voice_id.py            -> prints the best-matching character for every storyboard shot with a caption
"""
import json
import os
import sys

import librosa
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VOCALS = next((os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(ROOT, "sep")) for f in fs if f == "vocals.wav"), "")
if not VOCALS:
    sys.exit("no vocal stem found: expected sep/htdemucs/<take>/vocals.wav in the single's folder "
             "(make it with Demucs: python -m demucs --two-stems vocals -o sep SONG.mp3)")
REFS = {  # character -> [(t0, t1), ...] of lines you are certain about (example times: replace them with your song's)
    "Sara": [(26.1, 28.3), (92.6, 94.4), (111.3, 112.7)],
    "VoiceB": [(0.0, 3.9), (238.9, 242.4)],
    "Kevin": [(234.1, 238.3), (174.95, 176.9)],
}

y, sr = librosa.load(VOCALS, sr=22050)


def feat(t0, t1):
    seg = y[int(t0 * sr):int(t1 * sr)]
    m = librosa.feature.mfcc(y=seg, sr=sr, n_mfcc=20)[1:]
    rms = librosa.feature.rms(y=seg)[0][:m.shape[1]]
    return m[:, rms > np.percentile(rms, 40)].mean(axis=1)


allf = np.array([feat(a, b) for v in REFS.values() for a, b in v])
mu, sd = allf.mean(0), allf.std(0) + 1e-6
cent = {k: (np.mean([feat(a, b) for a, b in v], axis=0) - mu) / sd for k, v in REFS.items()}

if __name__ == "__main__":
    for s in json.load(open(os.path.join(ROOT, "storyboard.json"))):
        if not s.get("cap") or s["t1"] - s["t0"] < 0.6:
            continue
        f = (feat(s["t0"], s["t1"]) - mu) / sd
        d = sorted((np.linalg.norm(f - c), k) for k, c in cent.items())
        expected = {"S": "S", "B": "V", "K": "K", "C": "S"}.get(s.get("voice"), "?")
        confident = d[1][0] - d[0][0] > 0.6  # only flag clear margins; choir/music-heavy shots are noisy
        flag = f"  <-- CHECK by ear: storyboard says {s['voice']}" if expected != "?" and d[0][1][0] != expected and confident else ""
        print(f"{s['id']:5s} {d[0][1]:10s} ({d[0][0]:.1f} vs {d[1][1]} {d[1][0]:.1f})  {s['cap'][:40]}{flag}")
