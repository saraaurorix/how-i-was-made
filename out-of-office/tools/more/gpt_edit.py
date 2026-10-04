"""Stills through ChatGPT image generation (Codex CLI) from a JSON job list, N in parallel; no extra cost on a ChatGPT plan.
Each job: {"id", "out", "prompt", "refs": [paths]}. The prompt is wrapped with the 16:9 + save-path instructions.
Usage: python tools/gpt_edit.py jobs.json [workers=3] [ID,ID]"""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(ROOT)
jobs = json.load(open(sys.argv[1])); W = int(sys.argv[2]) if len(sys.argv) > 2 else 3
only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
def one(j):
    if only and j["id"] not in only: return j["id"], "skip"
    if os.path.exists(j["out"]): return j["id"], "exists"
    p = ("Use your image generation tool to create exactly ONE 16:9 landscape image. " + j["prompt"] +
         f" When the image is generated, copy the image file to ./{j['out']} with a shell command. Do nothing else and reply only with the saved path.")
    args = ["nice", "-n", "10", "codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", ROOT]
    for r in j.get("refs", []): args += ["-i", r]
    t = time.time()
    for attempt in (1, 2):
        r = subprocess.run(args, input=p, capture_output=True, text=True, timeout=900)
        if os.path.exists(j["out"]) and os.path.getsize(j["out"]) > 50000:
            return j["id"], f"ok {round(time.time() - t)}s"
    return j["id"], "FAILED " + (r.stdout + r.stderr)[-200:].replace("\n", " ")
with ThreadPoolExecutor(W) as ex:
    for sid, st in ex.map(one, jobs):
        print(sid, st, flush=True)
