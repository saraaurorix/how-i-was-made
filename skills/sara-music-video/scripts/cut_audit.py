"""Audit storyboard cuts against the Whisper word timings. Flags lip-sync shots that cut mid-word or before the singer
finishes the line (held notes run long). Not checked here: lip-sync models also have a minimum audio length (Wan 2.7
needs >= 3 s, MiniMax lip-sync >= 5 s: pad the slice with the following vocal and trim in the edit).

    python tools/cut_audit.py
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
WORDS = os.path.join(ROOT, "words_merged.json")  # words.json with the transcribe_gaps.py recoveries merged in, when there is one
if not os.path.exists(WORDS):
    WORDS = os.path.join(ROOT, "words.json")
W = sorted((w for s in json.load(open(WORDS)) for w in s["words"]), key=lambda w: w["s"])
S = json.load(open(os.path.join(ROOT, "storyboard.json")))

for a, b in zip(S, S[1:]):
    if a.get("type") != "lip":
        continue
    t = a["t1"]
    straddle = [w for w in W if w["s"] < t - 0.05 and w["e"] > t + 0.12]
    nxt = next((w for w in W if w["s"] >= t - 0.05), None)
    notes = []
    if straddle:
        notes.append(f"cuts mid-word '{straddle[0]['w']}' ({straddle[0]['s']}-{straddle[0]['e']}): move the cut to >= {straddle[0]['e']}")
    if nxt and nxt["s"] - t < 0.12 and b.get("voice") == a.get("voice") and b.get("type") != "lip":
        notes.append(f"the same singer's line continues into {b['id']} ('{nxt['w']}' @ {nxt['s']}): end the lip shot after the phrase")
    if notes:
        print(a["id"], "->", b["id"], f"cut {t}:", "; ".join(notes))
print("audit done")
