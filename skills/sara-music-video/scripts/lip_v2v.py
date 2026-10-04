"""Lip-sync route B prep: put Sara's singing mouth on a Kling SINGING base clip with fal's sync.so lipsync-2-pro
The base must be singing: a closed-mouth base failed, because sync.so copies the input's style.

Per shot:
  gen/v2v_in/<id>.mp4       the shot's exact length (+ a run-up) from gen/lipbase/<id>.mp4 (from --start seconds in), 30 fps,
                            encoded through venc.py. COLOUR-CHECK these before paying (a bad encode once came out green)
  lipsync/<id>_mexact.wav   the exact vocal slice with everything outside Sara's sung (Whisper) words muted
  jobs_lipsync.json         fal jobs writing gen/lipsync_v2v/<id>.mp4, which the edit should prefer
  gen/lip_offsets.json      the run-up (--pre) per shot, for the edit to skip. Keep manual sync fixes in the edit.
Usage: python tools/lip_v2v.py N004,N005 [--start 0.5] [--pre 0.3]
Then:  python tools/falgen.py jobs_lipsync.json 4 N004,N005   (quote the cost first; check outputs' colour, frames and props)
"""
import json
import os
import subprocess
import sys
import wave

import imageio_ffmpeg
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import venc  # noqa: E402

if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    sys.exit(__doc__)
FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
import glob  # noqa: E402
# the Demucs vocal stem of the chosen take (prefer the one made from the WAV: sep_wav/, then sep/)
VOCALS = next(iter(sorted(glob.glob(os.path.join(ROOT, "sep_wav/htdemucs/*/vocals.wav"))) +
                   sorted(glob.glob(os.path.join(ROOT, "sep/htdemucs/*/vocals.wav")))), "")
if not VOCALS:
    sys.exit("no vocal stem found: expected sep_wav/htdemucs/<take>/vocals.wav or sep/htdemucs/<take>/vocals.wav in the single's folder "
             "(make it with Demucs: python -m demucs --two-stems vocals -o sep SONG.mp3)")
FPS, SR = 30, 44100
S = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "storyboard.json")))}
WORDS = [w for seg in json.load(open(os.path.join(ROOT, "words.json"))) for w in seg["words"]]


def low_priority():
    """Drop to nice 19 unless already there or lower (a background shell job can start above 19, where os.nice raises)."""
    if os.getpriority(os.PRIO_PROCESS, 0) < 19:
        os.setpriority(os.PRIO_PROCESS, 0, 19)


def masked_exact(sid, pre=0.0, pad_pre=0.06, pad_post=0.10, fade=0.04):
    """pre: seconds of run-up before the shot (silent unless a word starts early), which the edit skips via gen/lip_offsets.json."""
    s = S[sid]
    t0 = round((s["t0"] - pre) * FPS) / FPS
    dur = (round(s["t1"] * FPS) - round(s["t0"] * FPS)) / FPS + pre
    p = subprocess.run([FF, "-v", "error", "-ss", f"{t0:.4f}", "-t", f"{dur:.4f}", "-i", VOCALS, "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    a = np.frombuffer(p.stdout, np.float32).copy()
    a = np.pad(a, (0, max(0, int(round(dur * SR)) - len(a))))[:int(round(dur * SR))]
    t = np.arange(len(a)) / SR + t0
    m = np.zeros_like(a)
    for w in WORDS:
        if w["e"] < s["t0"] - 0.2 or w["s"] > s["t1"]:
            continue  # only the words sung inside this shot drive the mouth
        a0, a1 = w["s"] - pad_pre, w["e"] + pad_post
        m = np.maximum(m, np.clip(np.minimum((t - a0) / fade + 1, (a1 - t) / fade + 1), 0, 1))
    out = os.path.join(ROOT, "lipsync", sid + "_mexact.wav")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with wave.open(out, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((np.clip(a * m, -1, 1) * 32767).astype("<i2").tobytes())
    return out, dur


def video_in(sid, dur, start):
    nf = round(dur * FPS)
    src = os.path.join(ROOT, "gen/lipbase", sid + ".mp4")
    out = os.path.join(ROOT, "gen/v2v_in", sid + ".mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # GPU decode and encode where the machine has one (venc.py); high quality because fal re-encodes it
    subprocess.run([FF, "-v", "error", "-y", *venc.hwdec(), "-ss", f"{start:.2f}", "-i", src, "-vf",
                    f"fps={FPS},scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,tpad=stop_mode=clone:stop_duration=1,format=nv12",
                    "-frames:v", str(nf), "-an", *venc.h264(80), out],
                   check=True, preexec_fn=low_priority)
    return out


def clip_len(path):
    e = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    h, m, s = e.split("Duration: ")[1].split(",")[0].split(":")
    return float(h) * 3600 + float(m) * 60 + float(s)


def main():
    ids = sys.argv[1].split(",")
    start = float(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else 0.5
    pre = float(sys.argv[sys.argv.index("--pre") + 1]) if "--pre" in sys.argv else 0.3
    jobs_path = os.path.join(ROOT, "jobs_lipsync.json")
    jobs = {j["id"]: j for j in json.load(open(jobs_path))} if os.path.exists(jobs_path) else {}
    offs_path = os.path.join(ROOT, "gen/lip_offsets.json")
    offs = json.load(open(offs_path)) if os.path.exists(offs_path) else {}
    total = 0.0
    for sid in ids:
        wav, dur = masked_exact(sid, pre)
        base_len = clip_len(os.path.join(ROOT, "gen/lipbase", sid + ".mp4"))
        vid = video_in(sid, dur, max(0.0, min(start, base_len - dur - 0.05)))  # long shots start earlier in the 5 s base
        offs[sid] = round(pre, 3)  # the edit skips the run-up (off = min(lag, clip length - shot length))
        total += dur
        jobs[sid] = {"id": sid, "endpoint": "fal-ai/sync-lipsync/v2/pro",
                     "args": {"video_url": "@" + os.path.relpath(vid, ROOT).replace(os.sep, "/"),
                              "audio_url": "@" + os.path.relpath(wav, ROOT).replace(os.sep, "/"), "sync_mode": "cut_off"},
                     "out": f"gen/lipsync_v2v/{sid}.mp4"}
        print(sid, f"{dur:.2f}s", vid, wav)
    json.dump(list(jobs.values()), open(jobs_path, "w"), indent=1)
    json.dump(offs, open(offs_path, "w"), indent=1)
    print(f"{len(ids)} shots, {total:.1f}s of video to lip-sync: look up the current price per minute and quote it before running the jobs")


if __name__ == "__main__":
    main()
