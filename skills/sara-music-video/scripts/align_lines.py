"""Pin every lyric line (lines.json) to song time using the Whisper words (words.json).

Aligns the lyric word sequence to the transcript word sequence with difflib, then gives each
line t0 = first matched word start and t1 = last matched word end. Lines with no match are
interpolated between their neighbours and flagged. Writes lines_timed.json and prints a table.
Usage: python tools/align_lines.py [words.json] [lines.json]
"""
import difflib
import json
import re
import sys

words_p = sys.argv[1] if len(sys.argv) > 1 else "words.json"
lines_p = sys.argv[2] if len(sys.argv) > 2 else "lines.json"
segs = json.load(open(words_p, encoding="utf-8"))
lines = json.load(open(lines_p, encoding="utf-8"))

norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower().replace("'", ""))
tw = [w for s in segs for w in s["words"] if norm(w["w"])]
tn = [norm(w["w"]) for w in tw]

lw, owner = [], []
for i, l in enumerate(lines):
    for w in l["text"].split():
        if norm(w):
            lw.append(norm(w))
            owner.append(i)

sm = difflib.SequenceMatcher(None, lw, tn, autojunk=False)
hits = {}
for a, b, n in sm.get_matching_blocks():
    for k in range(n):
        hits.setdefault(owner[a + k], []).append(tw[b + k])

for i, l in enumerate(lines):
    h = hits.get(i, [])
    nwords = sum(1 for w in l["text"].split() if norm(w))
    l["match"] = f"{len(h)}/{nwords}"
    if h:
        l["t0"], l["t1"] = h[0]["s"], h[-1]["e"]
    else:
        l["t0"] = l["t1"] = None

# interpolate missing lines between neighbours
for i, l in enumerate(lines):
    if l["t0"] is None:
        prev = next((lines[j]["t1"] for j in range(i - 1, -1, -1) if lines[j]["t1"] is not None), 0.0)
        nxt = next((lines[j]["t0"] for j in range(i + 1, len(lines)) if lines[j]["t0"] is not None), prev + 2)
        l["t0"], l["t1"], l["guess"] = prev, nxt, True

json.dump(lines, open("lines_timed.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for l in lines:
    flag = "  <-- GUESS" if l.get("guess") else ("  <-- partial" if l["match"].split("/")[0] != l["match"].split("/")[1] else "")
    print(f"{l['n']:3} {l['t0']:7.2f}-{l['t1']:7.2f} {l['v']} {l['match']:>5}  {l['text'][:60]}{flag}")
