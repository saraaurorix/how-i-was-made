"""Pick the better take per lip-sync shot and install it where the edit looks (gen/lipsync/ID.mp4).

Scores every gen/lipsync_takes/ID_tN.mp4 against its driving slice with tools/lipscore.py (corr > 0.5 good, 0.3-0.5 loose,
< 0.3 poor; face = share of frames with a face) and keeps the higher corr; ties go to take 1. Writes gen/lipsync_takes/scores.json
and prints the table. Run tools/lipsync_audit.py --write afterwards for per-shot lag offsets.
Usage: python tools/pick_lip_takes.py   (from the single's folder; needs lip_jobs.json from lip_slices.py)
"""
import glob
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lipscore import score  # noqa: E402

TAKES = "gen/lipsync_takes"

if __name__ == "__main__":
    jobs = {j["id"]: j for j in json.load(open("lip_jobs.json"))}
    res = {}
    for sid, j in jobs.items():
        rows = []
        for p in sorted(glob.glob(f"{TAKES}/{sid}_t*.mp4")):
            r = score(p, j["slice"], j["dur"] + 0.3)
            rows.append((r["corr"] if r["corr"] == r["corr"] else -1.0, p, r))
        if not rows:
            print(f"{sid}: no takes yet")
            continue
        best = max(rows, key=lambda x: (x[0], -rows.index(x)))
        os.makedirs("gen/lipsync", exist_ok=True)
        shutil.copyfile(best[1], f"gen/lipsync/{sid}.mp4")
        res[sid] = {"pick": os.path.basename(best[1]), "takes": {os.path.basename(p): r for _, p, r in rows}}
        flag = "GOOD" if best[0] >= 0.5 else "loose" if best[0] >= 0.3 else "POOR"
        print(f"{sid}: " + "  ".join(f"{os.path.basename(p)[-6:-4]} corr {c:5.2f} face {r['face']:.2f}" for c, p, r in rows)
              + f"  -> {os.path.basename(best[1])} ({flag})")
    json.dump(res, open(f"{TAKES}/scores.json", "w"), indent=1)
