"""Lip-sync audit, run before anyone sees a cut. Two checks:

1. LAG: every lip-sync clip (type "lip") vs its word-masked driving slice, searched over +-600 ms. Wan mouths can run
   0.2-0.5 s early or late even though the embedded audio is aligned exactly. Confident shifts (best corr >= 0.5 and
   >= 0.2 better than at 0) are written to gen/lip_offsets.json (positive = skip into the clip, negative = hold the
   first frame), for the edit to apply. Chorus shots with choir bleed are reported but not auto-shifted.
2. MOUTHING: every non-lip shot with Sara in it (refs contain "s"): lip-opening std above ~0.012 means a character is
   mouthing someone else's line (Kling does this). Re-render with "lips pressed together in a tight closed-mouth
   smirk, never opens her mouth", or fall back to a push-in on the still.

Usage: python tools/lipsync_audit.py [--write]
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lipscore import apertures, envelope  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def clip_of(sid):
    for d in ("gen/lipsync_v2v", "gen/lipsync", "gen/fix", "gen/clips"):
        p = os.path.join(ROOT, d, sid + ".mp4")
        if os.path.exists(p):
            return p
    return None


def main():
    S = json.load(open(os.path.join(ROOT, "storyboard.json")))
    offs_path = os.path.join(ROOT, "gen/lip_offsets.json")
    offs = json.load(open(offs_path)) if os.path.exists(offs_path) else {}
    print("== LAG (lip-sync shots) ==")
    for s in S:
        if s["type"] != "lip" or not clip_of(s["id"]):
            continue
        sid = s["id"]
        wav = next((os.path.join(ROOT, "lipsync", f"{sid}{sfx}.wav") for sfx in ("_m", "") if os.path.exists(os.path.join(ROOT, "lipsync", f"{sid}{sfx}.wav"))), None)
        if not wav:
            print(f"{sid:5s} no driving slice lipsync/{sid}_m.wav: run lip_slices.py (or masked_slice.py) first")
            continue
        ap, fps = apertures(clip_of(sid))
        env = envelope(wav, fps, len(ap))
        ap = np.where(np.isnan(ap), np.nanmean(ap), ap)
        n = int((s["t1"] - s["t0"] + 0.4) * fps)
        ap, env = ap[:n], env[:n]
        rows = []
        for lag in range(-18, 19):
            a, e = (ap[lag:], env[:len(env) - lag]) if lag >= 0 else (ap[:lag], env[-lag:])
            if len(a) > 10 and a.std() > 0 and e.std() > 0:
                rows.append((float(np.corrcoef(a, e)[0, 1]), lag))
        c0 = dict((lag, c) for c, lag in rows).get(0, 0.0)
        cb, lb = max(rows)
        shift = lb / fps
        confident = cb >= 0.5 and cb - c0 >= 0.2 and s["voice"] != "C"
        note = f"-> offset {shift:+.2f}s" if confident else ("(check by eye)" if cb < 0.3 else "")
        if confident:
            offs[sid] = round(shift, 2)
        print(f"{sid:5s} corr@0 {c0:5.2f}  best {cb:5.2f} @ {shift*1000:+5.0f} ms  {note}  {s['cap'][:36]}")
    print("\n== MOUTHING (non-lip shots with Sara) ==")
    for s in S:
        if s["type"] == "lip" or "s" not in s.get("refs", "") or not clip_of(s["id"]):
            continue
        ap, fps = apertures(clip_of(s["id"]), s["t1"] - s["t0"] + 0.5)
        if np.mean(~np.isnan(ap)) < 0.5:
            continue
        mv = float(np.nanstd(ap))
        if mv > 0.012:
            print(f"{s['id']:5s} mouth-move {mv:.4f}  voice {s['voice']}  <-- someone is mouthing; re-render closed-mouthed (unless it's intended, e.g. Kevin singing)")
    if "--write" in sys.argv:
        json.dump(offs, open(offs_path, "w"), indent=1)
        print("\nwrote", offs_path)


if __name__ == "__main__":
    main()
