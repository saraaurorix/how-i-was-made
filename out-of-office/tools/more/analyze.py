"""Beat grid and section map for the song, used to time the storyboard cuts."""
import json
import sys

import librosa
import numpy as np

if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"):
    sys.exit("usage: python analyze.py song.mp3 timing.json")
path = sys.argv[1]
y, sr = librosa.load(path, sr=22050, mono=True)
dur = len(y) / sr
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time", tightness=120)
tempo = float(np.atleast_1d(tempo)[0])

hop = 512
rms = librosa.feature.rms(y=y, hop_length=hop)[0]
t_rms = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
low = S[freqs < 150].mean(axis=0)  # kick and bass
high = S[(freqs > 3000)].mean(axis=0)  # hats, air, sibilance

bar = 4 * 60.0 / tempo
start = float(beats[0]) if len(beats) else 0.0
while start - bar > 0:
    start -= bar
bars = []
t = start
while t < dur:
    m = (t_rms >= t) & (t_rms < t + bar)
    if m.any():
        bars.append({"t": round(t, 2), "rms": float(rms[m].mean()), "low": float(low[m].mean()), "high": float(high[m].mean())})
    t += bar

def norm(k):
    v = np.array([b[k] for b in bars])
    v = (v - v.min()) / (v.max() - v.min() + 1e-9)
    for b, x in zip(bars, v):
        b[k] = round(float(x), 2)
for k in ("rms", "low", "high"):
    norm(k)

# structural boundaries from timbre + harmony, at bar resolution
mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop, n_mfcc=13)
chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
feat = np.vstack([librosa.util.normalize(mfcc, axis=1), chroma])
bar_frames = librosa.time_to_frames([b["t"] for b in bars], sr=sr, hop_length=hop)
sync = librosa.util.sync(feat, bar_frames, aggregate=np.median)
k = min(14, max(2, sync.shape[1] // 4))  # about one section per four bars, 14 at most (a song under 14 bars used to crash here)
bounds = librosa.segment.agglomerative(sync, k)
bound_t = sorted({round(bars[min(i, len(bars) - 1)]["t"], 2) for i in bounds})

print(f"duration {dur:.2f}s  tempo {tempo:.1f} bpm  bar {bar:.3f}s  first downbeat~{start:.2f}s  bars {len(bars)}")
print("section boundaries:", bound_t)
print(" bar   time   energy               kick   hats")
for i, b in enumerate(bars):
    mark = "|" if b["t"] in bound_t else " "
    print(f"{i:4d} {b['t']:6.1f}{mark} {'#' * int(b['rms'] * 20):20s} {b['low']:.2f}  {b['high']:.2f}")
json.dump({"duration": dur, "tempo": tempo, "bar": bar, "start": start, "bars": bars, "bounds": bound_t,
           "beats": [round(float(x), 3) for x in beats]}, open(sys.argv[2], "w"), indent=1)
