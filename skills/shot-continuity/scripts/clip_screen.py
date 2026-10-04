"""Intent screen: does each clip do what its board row says, and nothing else? (the shot-continuity skill, Part 3b)

Why: on a later video two clips passed every continuity check and still made no sense to a viewer. In one, Sara waved a prop
about with no evident purpose: the row's gag never happened. In the other, the video model had put an object behind the
characters that the joke needed to be absent. Strips had been read for faces, outfits and sides, never against the row's action.
This screen reads every clip against its row.

  python clip_screen.py [--sb storyboard.json] [--clips gen/clips] [--editor tools/cut.py] [--only ID,ID] [--lips]
                        [--judge] [--workers 3] [--out review/screen]

Run it from the project folder. Per clip (gen/clips/<id>.mp4) it samples 8 frames over the seconds the cut actually PLAYS and
writes review/screen/<id>.jpg: the frames with shot-time labels, the lyric, the row's picture and its action line. Automatic flags
(hints, like join_check's):
  TRAVEL   Sara's face moves across or toward the frame (centre moves > 22 % of the width, or her face grows or shrinks > 1.7x)
           when the row has no travel word (walk, strut, run, slide, surf, ride...): the "she wanders about instead of doing the gag"
           failure. Tuned for Sara: her face is found by join_check.py's test (cyan irises, platinum fringe), loaded from this
           script's folder; change the test there for your own character.
  SLIDE    a large part of the picture (> 22 % of it) slides one way while the camera is meant to hold: floating crowds, cards,
           or props dragged across the frame.

The storyboard is a JSON list of shots; per shot this reads id, t0, t1 (seconds in the cut), type ("lip" shots are skipped without
--lips and read from --lipdir, "edit" shots are graphics and always skipped), cap (the lyric), scene (PICTURE), motion (ACTION),
staging and scene_id (for EARLIER).

--editor: where the seconds of each clip that the cut plays come from. The file is read as text, never run, and only for three
tables, each optional, each written as one Python dict literal that starts at the beginning of a line and has no nested braces:
  WINDOW = {"V02": 0.15, "H05": 0.04}            shot id -> seconds into the clip where the cut starts playing it (default 0.15)
  CLIPEND = {"R01": 4.6}                         shot id -> seconds into the clip where the cut stops playing it (default: its end)
  RAMP = {"M08": [(0.04, 0.0), (2.48, 3.26)]}    shot id -> (clip seconds, shot seconds) knots of a speed ramp, joined by straight lines
An edit script that defines them like that works as it is; otherwise write them in a small text file and pass that. With no file,
every clip is taken to play from 0.15 s. The rest of the timing is this editor's: the cut runs at --fps (25), every source frame
plays once from the window, and a clip that is shorter than its shot is slowed, by 1.35x at most.

With --judge, each strip also goes to a vision model with a fixed checklist and the row's full text (lyric, PICTURE, ACTION,
STAGING, plus EARLIER: what the scene's previous shots already showed). It answers in JSON: does the row's action happen (and
when), does anything appear or move that the row doesn't name or that contradicts it, would the joke read in one second, any
morphs or broken bodies, and a SEVERITY for a first-time viewer on a phone (3 confusing or looks like a mistake, 2 an attentive
viewer notices, 1 only in still frames, 0 nothing).
The judge is ChatGPT through the Codex CLI (`codex exec`, read-only sandbox), so --judge needs the Codex CLI installed and signed
in. Any command-line model that can read an image can be swapped in: change the command in judge(). It gets the strip and the
prompt (on standard input) and must print the JSON object the prompt asks for.
Verdict: FAIL = severity 3 (fix before anyone sees it); CHECK = severity 2, or the action never happens (read the strip by eye);
OK otherwise. Results: review/screen/SCREEN.md (one row per clip, worst first) and screen.json. The judge is a second pair of eyes,
not the verdict: every CHECK and FAIL is confirmed by eye on its strip before anything is remade.

Calibration (one cut of a later video, 77 clips, of which the director had flagged exactly two; those are the positives and the
other 75 were accepted): v1 FAILed on any "appears" or "moves wrong" answer and failed 37 clips, both positives among them. A vision
model can always fill those lists, so v1 was a noise machine. v2 asks for the severity and FAILs only on 3. The numbers are in the
skill's references/intent-screen-calibration.md. Re-run the calibration on a cut you have already accepted whenever the question
changes:
  python clip_screen.py --rejudge review/screen_old --out review/screen_cal
(--rejudge re-asks the judge about an earlier run's strips without re-sampling the clips.)
"""
import argparse
import ast
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fonts import truetype  # Windows font names -> the closest face on this machine

ap = argparse.ArgumentParser()
ap.add_argument("--sb", default="storyboard.json")
ap.add_argument("--clips", default="gen/clips")
ap.add_argument("--lipdir", default="gen/lip_omni", help="the lip-sync clips folder, <id>.mp4 (shots of type lip, with --lips)")
ap.add_argument("--editor", default="tools/cut.py", help="a text file with WINDOW = {...}, CLIPEND = {...}, RAMP = {...} (see the docstring)")
ap.add_argument("--only", default="")
ap.add_argument("--lips", action="store_true", help="screen lip-sync shots too")
ap.add_argument("--judge", action="store_true", help="ask the vision model about every strip")
ap.add_argument("--workers", type=int, default=3)
ap.add_argument("--out", default="review/screen")
ap.add_argument("--fps", type=int, default=25)
ap.add_argument("--clip", default="", help="screen this file instead of the shot's clip (with --only ID): e.g. a rejected take")
ap.add_argument("--rejudge", default="", help="an earlier run's folder: re-ask the judge about its strips (no re-sampling), results to --out")
ap.add_argument("--keep", action="store_true", help="with --rejudge: keep that run's answers and only run the confirm pass")
ap.add_argument("--confirm", type=int, default=1, help="re-ask about every severity-3 clip this many times; FAIL only if every answer is 3 (0 = off)")
a = ap.parse_args()
FF = imageio_ffmpeg.get_ffmpeg_exe()
os.makedirs(os.path.join(a.out, "_f"), exist_ok=True)
FB = "arialbd.ttf"
FR = "arial.ttf"
NICE = ["nice", "-n", "10"] if shutil.which("nice") else []  # there is no nice on Windows

# Sara's face finder from join_check.py (cyan irises, platinum fringe), loaded without running its main()
_here = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv
sys.argv = ["join_check.py", "--stills", "--sb", a.sb, "--from", "1e9", "--to", "1e9", "--out", os.path.join(a.out, "_jc")]
_spec = importlib.util.spec_from_file_location("join_check", os.path.join(_here, "join_check.py"))
jc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jc)
sys.argv = _argv

TRAVEL_WORDS = re.compile(r"\b(walk|walks|walking|strut|struts|strutting|run|runs|running|sprint|sprints|slide|slides|sliding|knee-slide|"
                          r"surf|surfs|surfing|ride|rides|riding|glide|glides|gliding|march|marches|marching|step|steps|jump|jumps|leap|leaps|"
                          r"dance|dances|dancing|pivot|pivots|spin|spins|twirl|twirls|chase|chases|fly|flies|flying|drive|drives|taxi|taxis|"
                          r"push|pushes|toward the camera|towards the camera|away from the camera|travels|tracks|pull-back|pulls back|zoom)\b", re.I)
CAMERA_WORDS = re.compile(r"\b(pan|pans|tracks|travels|pull-back|pulls back|push|pushes|crane|zoom|aerial|whip|orbit)\b", re.I)


def editor_timing():
    """WINDOW, CLIPEND and RAMP from the editor, if it has them (the seconds of each clip the cut plays, and how fast).
    RAMP: {id: [(clip s, shot s), ...]} knots joined by straight lines; the first knot is where the cut starts playing the clip."""
    w, ce, rp = {}, {}, {}
    if os.path.exists(a.editor):
        src = open(a.editor).read()
        for name, d in (("WINDOW", w), ("CLIPEND", ce), ("RAMP", rp)):
            m = re.search(r"^" + name + r" = (\{[^}]*\})", src, re.M)
            if m:
                try:
                    d.update(ast.literal_eval(m.group(1)))
                except (ValueError, SyntaxError):
                    pass
    return w, ce, rp


WINDOW, CLIPEND, RAMP = editor_timing()


def probe(path):
    e = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    fps = float(a.fps)
    for part in e.split("Video:")[1].split(",") if "Video:" in e else []:
        if part.strip().endswith(" fps"):
            fps = float(part.strip()[:-4])
    h, m, s = e.split("Duration: ")[1].split(",")[0].split(":")
    return fps, float(h) * 3600 + float(m) * 60 + float(s)


def played(s, path, lip):
    """(clip time where the cut starts playing it, clip seconds played, clip time -> shot time)."""
    fps, clen = probe(path)
    nf = round(s["t1"] * a.fps) - round(s["t0"] * a.fps)
    dur = nf / a.fps
    if lip:
        return 0.3, min(dur, clen - 0.35), lambda t: t - 0.3
    clen = min(clen, CLIPEND.get(s["id"], clen))
    if s["id"] in RAMP and not a.clip:
        k = RAMP[s["id"]]
        cs, ss = [c for c, _ in k], [x for _, x in k]
        # the last line carries on past its knot, as in the editor
        def shot_t(t, cs=cs, ss=ss):
            return float(np.interp(t, cs, ss)) if t <= cs[-1] else ss[-1] + (t - cs[-1]) * (ss[-1] - ss[-2]) / (cs[-1] - cs[-2])
        end = cs[-1] + (dur - ss[-1]) * (cs[-1] - cs[-2]) / (ss[-1] - ss[-2])
        return cs[0], min(end, clen - 0.05) - cs[0], shot_t
    seek = WINDOW.get(s["id"], 0.15)
    base = fps / a.fps
    rate = base * min(1.35, max(1.0, dur / max(0.1, (clen - seek) * base)))
    return seek, min(dur / rate, clen - seek - 0.05), lambda t: (t - seek) * rate  # the editor: setpts = rate * (PTS - STARTPTS)


def frames(path, t0, span, n=8, w=640, h=360):
    out = []
    for k in range(n):
        t = t0 + span * (k + 0.5) / n
        p = subprocess.run([FF, "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf", f"scale={w}:{h}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
        if len(p.stdout) == w * h * 3:
            out.append((t, np.frombuffer(p.stdout, np.uint8).reshape(h, w, 3)))
    return out


def full_frames(path, times):
    out = []
    for t in times:
        p = subprocess.run([FF, "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf", "scale=1920:1080",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
        if len(p.stdout) == 1920 * 1080 * 3:
            out.append(np.frombuffer(p.stdout, np.uint8).reshape(1080, 1920, 3))
    return out


def travel(fulls):
    """Sara's face track over the samples: (centre movement as a fraction of the width, size ratio), or None."""
    pts = []
    for f in fulls:
        fs = [x for x in jc.faces(f, thorough=True) if x["sara"]]
        if fs:
            s = max(fs, key=lambda x: x["w"])
            pts.append((s["x"], s["y"], s["w"]))
    if len(pts) < 3:
        return None
    xs, ys, ws = zip(*pts)
    move = max(math.hypot(xa - xb, ya - yb) for xa, ya, _ in pts for xb, yb, _ in pts)
    return round(move, 3), round(max(ws) / max(1e-3, min(ws)), 2), len(pts)


def slide(fr):
    """The largest coherent motion between consecutive samples: the fraction of the frame moving the same way, fast."""
    best = 0.0
    g = [cv2.cvtColor(cv2.resize(f, (320, 180)), cv2.COLOR_RGB2GRAY) for _, f in fr]
    for p, q in zip(g, g[1:]):
        fl = cv2.calcOpticalFlowFarneback(p, q, None, 0.5, 3, 21, 3, 5, 1.2, 0)
        mag = np.hypot(fl[..., 0], fl[..., 1])
        fast = mag > 3.0
        if fast.mean() < 0.05:
            continue
        ang = np.arctan2(fl[..., 1], fl[..., 0])[fast]
        hist, _ = np.histogram(ang, bins=8, range=(-math.pi, math.pi))
        best = max(best, float(hist.max()) / fast.size)
    return round(best, 3)


def strip(s, fr, path, shot_t, flags):
    TW, TH, cols = 480, 270, 4
    rows = (len(fr) + cols - 1) // cols
    head = 150
    im = Image.new("RGB", (cols * TW, head + rows * (TH + 24)), (18, 18, 22))
    d = ImageDraw.Draw(im)
    f1, f2 = truetype(FB, 18), truetype(FR, 15)
    m, sec = divmod(s["t0"], 60)
    d.text((8, 6), f"{s['id']}  {int(m)}:{sec:04.1f}  {s['type']}  {os.path.basename(path)}  lyric: {s.get('cap') or '(music)'}"[:170], fill=(255, 220, 80), font=f1)
    d.text((8, 32), ("PICTURE: " + (s.get("scene") or ""))[:230], fill=(225, 225, 230), font=f2)
    d.text((8, 52), ("PICTURE: " + (s.get("scene") or ""))[230:460], fill=(225, 225, 230), font=f2) if len(s.get("scene") or "") > 221 else None
    d.text((8, 74), ("ACTION: " + (s.get("motion") or ""))[:230], fill=(160, 220, 255), font=f2)
    d.text((8, 96), ("STAGING (the set, expected in frame): " + (s.get("staging") or "-"))[:230], fill=(190, 190, 200), font=f2)
    d.text((8, 118), "  |  ".join(flags) or "no automatic flag: read it against the row", fill=(255, 110, 110) if flags else (150, 200, 160), font=f2)
    for k, (t, f) in enumerate(fr):
        x, y = (k % cols) * TW, head + (k // cols) * (TH + 24)
        im.paste(Image.fromarray(f).resize((TW, TH)), (x, y))
        d.text((x + 6, y + TH + 3), f"frame {k + 1}   shot +{shot_t(t):.1f}s", fill=(255, 255, 0), font=f2)
    p = os.path.join(a.out, f"{s['id']}.jpg")
    im.save(p, quality=85)
    return p


JUDGE = """You are checking one shot of a comedy music video against its storyboard row. The attached image is a strip of 8 frames,
in time order, from the part of the clip the edit actually plays; frame 1 is the start, and each frame is labelled with its time in
the shot. The row is below. PICTURE is what should be in frame, ACTION what should happen. STAGING is the set: things it names are
expected (for example a front row of spectators). EARLIER is what the previous shots of this scene already showed, so those things
are not new or unexplained here.

{row}

Look at every frame, including the background and the sky. Then answer:
1. action: does the ACTION happen? "yes", "partly" or "no"; and from which frame number (1-8), 0 if never.
2. appears: things a viewer would notice that APPEAR after frame 1, or that none of PICTURE, STAGING and EARLIER explains and that
   change the meaning (a vehicle or aircraft, an animal, an extra person or figure, a prop out of nowhere). Not lighting, flashes or
   small background detail. Empty list if none.
3. moves_wrong: things that move by themselves or against the ACTION, that a viewer would notice: a prop sliding or turning on its
   own, a crowd or a group sliding like a flat picture, a vehicle going backwards, a character walking about or leaving when the
   ACTION doesn't say so, something going the opposite way to the ACTION. Empty list if none. When the camera itself travels with
   the characters (a tracking shot or a pan), the background moves past them: that is normal, not sliding. Judge sliding only
   against what the camera holds still.
4. reads: would a viewer who sees this shot once, at phone size, get the point of the ACTION within about one second? "yes" or "no".
5. broken: visual errors a viewer would notice: a face or body morphing, extra or missing limbs, objects passing through each
   other, garbled text that should be readable, an outfit changing. Empty list if none.
6. viewer_read: picture a first-time viewer watching the finished video once, at normal speed, on a phone; this shot lasts about
   four seconds between other shots. In a few words, what would they think the main character is doing?
7. severity: how much would the worst problem you found bother that viewer?
   3 = they would notice it and be confused, or think it is a mistake. For example: they could not say what a main character is
       doing (she moves about or waves a prop with no evident purpose); something big on screen that should not be there, or that
       contradicts the joke; something large moving in a way that makes no physical sense; a face or body visibly melting.
   2 = an attentive viewer might notice something odd, but the shot still makes sense.
   1 = only visible when studying still frames; at speed the shot reads fine. A gag that lands only partly, or an action that is
       small or quick, is 1, as long as the viewer can still tell what everyone is doing.
   0 = nothing wrong.
8. worst: that one problem in a few words ("" if severity is 0).
Do not run any commands or create any files. Reply with ONLY one JSON object, no other text:
{{"action": "...", "from_frame": 0, "appears": [], "moves_wrong": [], "reads": "...", "broken": [], "viewer_read": "...", "severity": 0, "worst": "", "why": "one short sentence"}}"""


def row_text(s, sb):
    """The row as the judge reads it: lyric, PICTURE, ACTION, STAGING and EARLIER (the scene's previous two shots)."""
    prev = [x for x in sb if x.get("scene_id") and x.get("scene_id") == s.get("scene_id") and x["t0"] < s["t0"]
            and x.get("type") != "edit"][-2:]
    earlier = " | ".join(f"{x['id']}: {x.get('scene', '')}" for x in prev) or "-"
    return (f"LYRIC: {s.get('cap') or '(music)'}\nPICTURE: {s.get('scene') or '-'}\nACTION: {s.get('motion') or '-'}\n"
            f"STAGING: {s.get('staging') or '-'}\nEARLIER: {earlier}")


def verdict(j):
    """The screen's verdict from the judge's answers. FAIL: severity 3, a viewer would be confused (fix before anyone sees it).
    CHECK: severity 2, or the ACTION never happens (read the strip by eye). v1 FAILed on any appears / moves_wrong answer: 37 of 77."""
    if not j or "action" not in j:
        return "ERROR"
    sev = int(j.get("severity") or 0) if str(j.get("severity", "0")).isdigit() else 0
    if sev >= 3:
        return "FAIL"
    if sev == 2 or j.get("action") == "no":
        return "CHECK"
    return "OK"


def verdict_v1(j):
    """The first rule, kept for the calibration table: any content error FAILs."""
    if not j or "action" not in j:
        return "ERROR"
    if j.get("action") == "no" or j.get("appears") or j.get("moves_wrong"):
        return "FAIL"
    if j.get("action") == "partly" or j.get("reads") == "no" or j.get("broken"):
        return "CHECK"
    return "OK"


def judge(s, path, sb):
    cmd = [*NICE, "codex", "exec", "--skip-git-repo-check", "-s", "read-only", "-C", os.getcwd(), "-i", path]
    t = time.time()
    prompt = JUDGE.format(row=row_text(s, sb))
    for attempt in (1, 2):
        p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=600)
        m = re.findall(r"\{[^{}]*\"why\"[^{}]*\}", p.stdout.replace("\n", " "))
        if m:
            try:
                r = json.loads(m[-1])
                r["secs"] = round(time.time() - t)
                r["verdict"] = verdict(r)
                r["verdict_v1"] = verdict_v1(r)
                return r
            except ValueError:
                pass
    return {"verdict": "ERROR", "why": (p.stdout + p.stderr)[-200:].replace("\n", " ")}


def screen(s, sb):
    lip = s.get("type") == "lip"
    path = a.clip if a.clip else os.path.join(a.lipdir if lip else a.clips, s["id"] + ".mp4")
    if not os.path.exists(path):
        return {"id": s["id"], "skip": "no clip"}
    t0, span, shot_t = played(s, path, lip)
    fr = frames(path, t0, span)
    fulls = full_frames(path, [t0 + span * (k + 0.5) / 6 for k in range(6)])
    text = f"{s.get('scene', '')} {s.get('motion', '')}"
    flags, info = [], {}
    tr = travel(fulls)
    info["travel"] = tr
    if tr and not TRAVEL_WORDS.search(text) and (tr[0] > 0.22 or tr[1] > 1.7):
        flags.append(f"TRAVEL Sara moves {tr[0]:.0%} of the width / grows {tr[1]}x, and the row has no travel word")
    sl = slide(fr)
    info["slide"] = sl
    if sl > 0.22 and not CAMERA_WORDS.search(text):
        flags.append(f"SLIDE {sl:.0%} of the picture slides one way")
    p = strip(s, fr, path, shot_t, flags)
    r = {"id": s["id"], "t0": s["t0"], "strip": p, "flags": flags, "clip": path, **info}
    print(json.dumps({k: r[k] for k in ("id", "flags")}), flush=True)
    return r


def main():
    sb = json.load(open(a.sb))
    # older boards: kind/lyric/still_prompt+motion instead of type/cap/scene/action
    sb = [dict(x, type=x.get('type') or x.get('kind') or '-', cap=x.get('cap') or x.get('lyric'), scene=x.get('scene') or x.get('still_prompt') or '', action=x.get('action') or x.get('motion') or '') for x in sb]
    want = set(a.only.split(",")) if a.only else None
    shots = [s for s in sb if s.get("type") != "edit" and (a.lips or s.get("type") != "lip") and (not want or s["id"] in want)]
    if a.rejudge:  # re-ask the judge about an earlier run's strips (the clips are not re-sampled)
        old = json.load(open(os.path.join(a.rejudge, "screen.json")))
        ids = {s["id"] for s in shots}
        here = lambda p: os.path.join(a.rejudge, os.path.basename(p)) if os.path.exists(os.path.join(a.rejudge, os.path.basename(p))) else p
        res = [dict(r, strip=here(r["strip"]), judge=r.get("judge") if a.keep else None) for r in old if "strip" in r and r["id"] in ids]
        a.judge = not a.keep
    else:  # the automatic part is quick and serial; the judge runs in parallel afterwards
        res = [screen(s, sb) for s in shots]
    if a.judge:
        todo = [r for r in res if "strip" in r]
        with ThreadPoolExecutor(a.workers) as ex:
            for r, j in zip(todo, ex.map(lambda r: judge(next(s for s in shots if s["id"] == r["id"]), r["strip"], sb), todo)):
                r["judge"] = j
                print(json.dumps({"id": r["id"], "judge": j}), flush=True)
    # the confirm pass: the judge's severity flips between runs on borderline clips (in the calibration: 3 -> 2, 3 -> 1, 1 -> 3),
    # while the clips the director had flagged scored 3 every time. So a FAIL needs every fresh answer to agree; otherwise it drops to CHECK.
    for rnd in range(a.confirm):
        again = [r for r in res if (r.get("judge") or {}).get("verdict") == "FAIL"]
        if not again:
            break
        with ThreadPoolExecutor(a.workers) as ex:
            for r, j2 in zip(again, ex.map(lambda r: judge(next(s for s in shots if s["id"] == r["id"]), r["strip"], sb), again)):
                j = r["judge"]
                j.setdefault("confirm", []).append({k: j2.get(k) for k in ("severity", "worst", "viewer_read", "why")})
                if str(j2.get("severity")) != "3":
                    j["verdict"] = "CHECK"
                    j["why"] = f"(not confirmed: a second look gave severity {j2.get('severity')}) " + str(j.get("why", ""))
                print(json.dumps({"id": r["id"], "confirm": j["confirm"][-1], "verdict": j["verdict"]}), flush=True)
    rank = {"FAIL": 0, "ERROR": 1, "CHECK": 2, "OK": 3}
    sev = lambda r: -int((r.get("judge") or {}).get("severity") or 0) if str((r.get("judge") or {}).get("severity", "0")).isdigit() else 0
    res.sort(key=lambda r: (rank.get((r.get("judge") or {}).get("verdict"), 3 if not r.get("flags") else 2), sev(r), r.get("t0", 0)))
    json.dump(res, open(os.path.join(a.out, "screen.json"), "w"), indent=1)
    counts = {}
    for r in res:
        v = (r.get("judge") or {}).get("verdict", "-")
        counts[v] = counts.get(v, 0) + 1
    lines = ["# Intent screen", "", "Each clip against its board row: the automatic flags, the judge's answers, and the strip to read by eye. "
             "Verdict: FAIL = severity 3 (a first-time viewer would be confused); CHECK = severity 2, or the action never happens.", "",
             "Totals: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: rank.get(kv[0], 9))), "",
             "| Shot | Time | Flags | Verdict | Sev | Worst | A viewer would think | Action | Appears | Moves wrong | Reads | Broken | Why | Strip |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res:
        if "strip" not in r:
            continue
        j = r.get("judge") or {}
        m, sec = divmod(r["t0"], 60)
        cell = lambda x: str(x).replace("|", "/")
        lines.append(f"| {r['id']} | {int(m)}:{sec:04.1f} | {'; '.join(r['flags']) or '-'} | {j.get('verdict', '-')} | {j.get('severity', '-')} | "
                     f"{cell(j.get('worst') or '-')} | {cell(j.get('viewer_read') or '-')} | {j.get('action', '-')} | {cell('; '.join(j.get('appears') or []) or '-')} | "
                     f"{cell('; '.join(j.get('moves_wrong') or []) or '-')} | {j.get('reads', '-')} | {cell('; '.join(j.get('broken') or []) or '-')} | "
                     f"{cell(j.get('why', ''))} | {os.path.basename(r['strip'])} |")
    open(os.path.join(a.out, "SCREEN.md"), "w").write("\n".join(lines) + "\n")
    print("screened", len(res), "->", a.out, counts)


if __name__ == "__main__":
    main()
