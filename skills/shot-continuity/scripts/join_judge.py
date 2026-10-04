"""Join judge: does each cut read as one continuous story? (the shot-continuity skill, Part 3c)

Why: on a later video the director found breaks that join_check and the intent screen had both passed. A character is outside in
one shot and inside in the next; she is suddenly further down the room; a seated crowd is, one cut later, half way out of the
door; Kevin is suddenly wearing a coat that nobody put on him; a jump jerks and switches. join_check compares
faces, Sara's outfit, place labels and light; the intent screen (clip_screen.py) reads one clip at a time. Neither compares the
STORY STATE across a cut: where everyone is, what they are doing, wearing and holding, and whether the change is shown.

  python join_judge.py DIR [--workers 3] [--only 12,13] [--confirm 1]

DIR holds join_NNN.jpg images and joins.json, both written by story_sheets.py in this folder (per cut: A 1 s before, A last,
B first, B 1 s after, with both board rows). --only takes the cut numbers in joins.json. Writes DIR/JUDGED.md (worst first) and
DIR/judged.json. A severity-3 answer is asked again (--confirm) and stays a FLAG only if the second answer agrees.

The judge is a vision model: ChatGPT through the Codex CLI (`codex exec`, read-only sandbox), so the Codex CLI must be installed
and signed in. Any command-line model that can read an image can be swapped in: change the command in ask(). It gets the join
image and PROMPT (on standard input) and must print the JSON object the prompt asks for.
"""
import argparse, json, os, re, shutil, subprocess, time
from concurrent.futures import ThreadPoolExecutor

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--workers", type=int, default=3)
ap.add_argument("--only", default="")
ap.add_argument("--confirm", type=int, default=1)
a = ap.parse_args()
NICE = ["nice", "-n", "10"] if shutil.which("nice") else []  # there is no nice on Windows

PROMPT = """You are checking ONE CUT in a music video for story continuity. The attached image shows, left to right: shot A one second
before the cut, A's last frame, then (after the green line) B's first frame and B one second after the cut. A viewer sees them back to
back at normal speed. The storyboard lines for A and B are printed at the top, only as context for what was intended; judge what a
viewer SEES, even where the board intended it.

Compare A with B for every character, the crowd and the key props:
- place: which set, inside or outside, where in the room or along its length, which side of the frame;
- what each is doing: sitting, standing, walking, running, kneeling, dancing, playing, leaving;
- what each wears: every garment and accessory (hat, coat or robe, straps, hood, gloves, shoes);
- what each holds.
List every change a viewer would notice. A change is EXPLAINED when the picture shows it happening, when an action clearly carries
across the cut, or when the cut is an obvious move to another scene or a later time that a viewer would follow. It is UNEXPLAINED
when a character is suddenly somewhere else, suddenly dressed differently, a prop or piece of furniture appears or vanishes, a crowd
is suddenly in a different state, or an action jumps, restarts or reverses.

Then:
- flow: does this cut read as one continuous story to a first-time viewer? "yes", "rough" or "no".
- severity for the worst UNEXPLAINED change: 3 = a viewer would notice and be confused or think it is a mistake; 2 = an attentive
  viewer would notice; 1 = only when studying the frames; 0 = none.
Do not run any commands or create any files. Reply with ONLY one JSON object, no other text:
{"unexplained": ["..."], "explained": ["..."], "flow": "...", "severity": 0, "worst": "...", "why": "one short sentence"}"""


def ask(img):
    cmd = [*NICE, "codex", "exec", "--skip-git-repo-check", "-s", "read-only", "-C", os.getcwd(), "-i", img]
    t = time.time()
    for attempt in (1, 2):
        p = subprocess.run(cmd, input=PROMPT, capture_output=True, text=True, timeout=600)
        m = re.findall(r"\{[^{}]*\"why\"[^{}]*\}", p.stdout.replace("\n", " "))
        if m:
            try:
                r = json.loads(m[-1])
                r["secs"] = round(time.time() - t)
                return r
            except ValueError:
                pass
    return {"severity": -1, "worst": "ERROR", "why": (p.stdout + p.stderr)[-200:].replace("\n", " ")}


def sev(r):
    try:
        return int(r.get("severity"))
    except (TypeError, ValueError):
        return 0


joins = json.load(open(os.path.join(a.dir, "joins.json")))
want = {int(x) for x in a.only.split(",")} if a.only else None
todo = [j for j in joins if not want or j["i"] in want]
with ThreadPoolExecutor(a.workers) as ex:
    for j, r in zip(todo, ex.map(lambda j: ask(os.path.join(a.dir, f"join_{j['i']:03d}.jpg")), todo)):
        j["judge"] = r
        print(json.dumps({"i": j["i"], "cut": f"{j['a']}>{j['b']}", "severity": r.get("severity"), "worst": r.get("worst")}), flush=True)
for rnd in range(a.confirm):
    again = [j for j in todo if sev(j["judge"]) >= 3 and not j["judge"].get("unconfirmed")]
    with ThreadPoolExecutor(a.workers) as ex:
        for j, r in zip(again, ex.map(lambda j: ask(os.path.join(a.dir, f"join_{j['i']:03d}.jpg")), again)):
            j["judge"].setdefault("confirm", []).append({k: r.get(k) for k in ("severity", "worst", "unexplained")})
            if sev(r) < 3:
                j["judge"]["unconfirmed"] = True
            print(json.dumps({"i": j["i"], "confirm": r.get("severity")}), flush=True)
for j in todo:
    r = j["judge"]
    j["verdict"] = ("FLAG" if sev(r) >= 3 and not r.get("unconfirmed") else "CHECK" if sev(r) >= 2 else "OK") if sev(r) >= 0 else "ERROR"
json.dump(todo, open(os.path.join(a.dir, "judged.json"), "w"), indent=1)
rank = {"FLAG": 0, "ERROR": 1, "CHECK": 2, "OK": 3}
todo.sort(key=lambda j: (rank[j["verdict"]], -sev(j["judge"]), j["t"]))
lines = ["# Join judge: story continuity at every cut", "",
         "Each cut judged by the vision model from four frames (A 1 s before, A last, B first, B 1 s after) for place, action, costume and "
         "props. FLAG = severity 3 confirmed by a second look; CHECK = severity 2 (or a 3 the second look didn't confirm).", "",
         "| # | Time | Cut | Board join | Verdict | Sev | Flow | Worst | Unexplained |", "|---|---|---|---|---|---|---|---|---|"]
for j in todo:
    r = j["judge"]
    m, s = divmod(j["t"], 60)
    cell = lambda x: str(x).replace("|", "/")
    lines.append(f"| {j['i']} | {int(m)}:{s:04.1f} | {j['a']} → {j['b']} | {j.get('join') or '-'} | {j['verdict']} | {r.get('severity')} | "
                 f"{r.get('flow', '-')} | {cell(r.get('worst') or '-')} | {cell('; '.join(r.get('unexplained') or []) or '-')} |")
open(os.path.join(a.dir, "JUDGED.md"), "w").write("\n".join(lines) + "\n")
print("judged", len(todo), {v: sum(1 for j in todo if j["verdict"] == v) for v in rank})
